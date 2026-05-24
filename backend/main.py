import asyncio
import json
import logging
import os
import sys
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("incidentiq")

LOGS_DIR = Path(tempfile.gettempdir()) / "incidentiq_logs"

from models import (
    AgentStartRequest,
    AnalyzeRequest,
    ChaosRequest,
    ChatRequest,
    IngestRequest,
    IntegrationSyncRequest,
    SlackAlertRequest,
    SpeakRequest,
)
from services import datadog_service, grafana_service, newrelic_service
from services.chaos_service import generate_chaos_logs
from services.elevenlabs_service import text_to_speech, health_check as elevenlabs_health
from services.gemini_service import correlate_logs, health_check as gemini_health
from services.groq_service import triage_logs, transcribe_audio, health_check as groq_health
from services.monitoring_agent import agent
from services.openai_service import analyze_root_cause, answer_question, health_check as openai_health
from services.slack_service import send_incident_alert
from store import incident_store, ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    agent.on_incident_analyzed = _agent_analyze_hook
    agent.on_logs_collected = _agent_logs_collected_hook
    logger.info(f"IncidentIQ backend started | logs dir: {LOGS_DIR}")
    if os.getenv("AGENT_AUTOSTART", "false").lower() == "true":
        await agent.start()
        logger.info("Agent autostarted")
    yield
    if agent.running:
        await agent.stop()
    logger.info("IncidentIQ backend shutting down")


app = FastAPI(
    title="IncidentIQ — AI Incident Intelligence Platform",
    description="Production-grade AI root-cause incident analysis backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ok(data: Any) -> dict:
    return {"success": True, "data": data, "error": None}


def _fail(msg: str, status: int = 500):
    raise HTTPException(
        status_code=status,
        detail={"success": False, "data": None, "error": msg},
    )


def _format_logs(logs: List[dict]) -> str:
    lines = []
    for l in logs:
        ts = l.get("timestamp", "?")
        sev = l.get("severity", "INFO")
        svc = l.get("service", "unknown")
        msg = l.get("message", "")
        lines.append(f"[{ts}] [{sev}] [{svc}] {msg}")
    return "\n".join(lines)


def _sample_logs(logs: List[dict], cap: int = 300) -> List[dict]:
    if len(logs) <= cap:
        return logs
    step = max(1, len(logs) // cap)
    head = logs[:20]
    tail = logs[-20:]
    middle = logs[20:-20:step][: cap - 40]
    return head + middle + tail


# ── 3-Stage AI Pipeline ───────────────────────────────────────────────────────

async def _run_pipeline(
    logs: List[dict],
    deployment_events: Optional[List[dict]] = None,
) -> tuple[dict, dict, dict, dict]:
    deployment_events = deployment_events or []
    stage_ms: dict = {}

    triage_text = _format_logs(_sample_logs(logs, 80))   # Groq free tier ~12k TPM
    full_text = _format_logs(logs)

    # Stage 1 — Groq llama-3.3-70b-versatile (fast triage, target <2s)
    t1 = time.monotonic()
    try:
        triage = await triage_logs(triage_text)
        logger.info(
            f"[Stage 1 Groq] severity={triage.get('severity')} "
            f"services={triage.get('affected_services')}"
        )
    except Exception as exc:
        logger.error(f"[Stage 1 Groq] FAILED: {exc}")
        triage = {
            "anomalies": [],
            "spike_at": None,
            "severity": "unknown",
            "affected_services": [],
            "summary": f"Triage unavailable: {exc}",
        }
    stage_ms["stage1_groq_ms"] = round((time.monotonic() - t1) * 1000)

    # Stage 2 — Gemini 2.0 Flash (correlation, target <5s)
    t2 = time.monotonic()
    try:
        correlation = await correlate_logs(
            anomalies=triage.get("anomalies", []),
            logs=full_text[:800_000],
            deployments=deployment_events,
        )
        logger.info(
            f"[Stage 2 Gemini] trigger={str(correlation.get('probable_trigger', ''))[:80]}"
        )
    except Exception as exc:
        logger.error(f"[Stage 2 Gemini] FAILED: {exc}")
        correlation = {
            "correlated_events": [],
            "probable_trigger": "",
            "blast_radius": [],
            "timeline": [],
        }
    stage_ms["stage2_gemini_ms"] = round((time.monotonic() - t2) * 1000)

    # Stage 3 — OpenAI gpt-4o-mini (root cause, target <8s)
    t3 = time.monotonic()
    try:
        root_cause = await analyze_root_cause(triage=triage, correlations=correlation)
        logger.info(f"[Stage 3 OpenAI] confidence={root_cause.get('confidence')}")
    except Exception as exc:
        logger.error(f"[Stage 3 OpenAI] FAILED: {exc}")
        root_cause = {
            "root_cause": "",
            "confidence": 0.0,
            "evidence": [],
            "fix_commands": [],
            "prevention": "",
            "estimated_impact": "",
            "voice_summary": "",
        }
    stage_ms["stage3_openai_ms"] = round((time.monotonic() - t3) * 1000)

    return triage, correlation, root_cause, stage_ms


# ── Agent hooks ───────────────────────────────────────────────────────────────

async def _agent_logs_collected_hook(logs: List[dict], polled_at: str) -> None:
    """Broadcast new live logs to dashboard subscribers."""
    await ws_manager.broadcast(json.dumps({
        "type": "agent_logs",
        "data": {"count": len(logs), "polled_at": polled_at, "logs": logs[:50]},
    }))


async def _agent_analyze_hook(payload: dict) -> None:
    """Run the full pipeline on agent-collected logs and broadcast the incident."""
    incident_id = payload["incident_id"]
    logs = payload["logs"]
    t0 = time.monotonic()

    incident_store.store_logs(incident_id, logs, datetime.now(timezone.utc).isoformat())

    triage, correlation, root_cause, stage_ms = await _run_pipeline(logs)
    total_ms = round((time.monotonic() - t0) * 1000)

    incident = {
        "incident_id": incident_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": triage.get("severity", "unknown"),
        "affected_services": triage.get("affected_services", []),
        "triage": triage,
        "correlations": correlation,
        "root_cause": root_cause,
        "root_cause_summary": root_cause.get("root_cause", ""),
        "confidence": root_cause.get("confidence", 0.0),
        "status": "active",
        "processing_ms": total_ms,
        "total_processing_ms": total_ms,
        "log_count": len(logs),
        "sources": payload.get("sources", []),
        "trigger": payload.get("trigger", "agent"),
        **stage_ms,
    }
    incident_store.store_incident(incident_id, incident)
    await ws_manager.broadcast(json.dumps({"type": "new_incident", "data": incident}))
    if triage.get("severity") in {"critical", "high"}:
        asyncio.create_task(send_incident_alert(incident))


# ── /api/health ───────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    results = await asyncio.gather(
        groq_health(),
        gemini_health(),
        openai_health(),
        elevenlabs_health(),
        return_exceptions=True,
    )
    providers = {
        "groq": results[0] is True,
        "gemini": results[1] is True,
        "openai": results[2] is True,
        "elevenlabs": results[3] is True,
    }
    status = "healthy" if all(providers.values()) else "degraded"
    return _ok({"status": status, "providers": providers, "timestamp": datetime.now(timezone.utc).isoformat()})


# ── /api/ingest ───────────────────────────────────────────────────────────────

@app.post("/api/ingest")
async def ingest(req: IngestRequest):
    incident_id = req.incident_id or str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()
    logs: List[dict] = list(req.logs or [])

    # GCP Cloud Logging format
    if req.source == "gcp" and req.gcp_logs:
        for entry in req.gcp_logs:
            logs.append({
                "timestamp": entry.get("timestamp", ts),
                "severity": entry.get("severity", "INFO"),
                "message": (
                    entry.get("textPayload")
                    or json.dumps(entry.get("jsonPayload", {}))
                ),
                "service": (
                    entry.get("resource", {})
                    .get("labels", {})
                    .get("service_name", "unknown")
                ),
            })

    # Datadog webhook format
    if req.source == "datadog" and req.webhook_payload:
        p = req.webhook_payload
        tags = p.get("tags") or []
        logs.append({
            "timestamp": p.get("date_happened", ts),
            "severity": "ERROR" if p.get("alert_type") == "error" else "WARN",
            "message": p.get("body", p.get("title", "")),
            "service": tags[0] if isinstance(tags, list) and tags else "unknown",
        })

    # Grafana webhook format
    if req.source == "grafana" and req.webhook_payload:
        for alert in req.webhook_payload.get("alerts", []):
            logs.append({
                "timestamp": alert.get("startsAt", ts),
                "severity": "ERROR" if alert.get("status") == "firing" else "WARN",
                "message": (
                    alert.get("annotations", {}).get("summary", "")
                    or alert.get("labels", {}).get("alertname", "")
                ),
                "service": alert.get("labels", {}).get("service", "unknown"),
            })

    incident_store.store_logs(incident_id, logs, ts)

    try:
        async with aiofiles.open(LOGS_DIR / f"{incident_id}.json", "w") as f:
            await f.write(
                json.dumps(
                    {"incident_id": incident_id, "timestamp": ts, "logs": logs},
                    indent=2,
                )
            )
    except Exception as exc:
        logger.warning(f"Disk write failed for {incident_id}: {exc}")

    return _ok({"incident_id": incident_id, "log_count": len(logs), "timestamp": ts})


# ── /api/analyze ──────────────────────────────────────────────────────────────

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    t0 = time.monotonic()

    logs = (
        incident_store.get_logs(req.incident_id)
        if req.incident_id
        else list(req.logs or [])
    )
    if not logs:
        _fail("No logs found. Call /api/ingest first or pass logs[] in the request body.", 400)

    triage, correlation, root_cause, stage_ms = await _run_pipeline(
        logs, req.deployment_events
    )
    total_ms = round((time.monotonic() - t0) * 1000)
    incident_id = req.incident_id or str(uuid.uuid4())

    incident = {
        "incident_id": incident_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": triage.get("severity", "unknown"),
        "affected_services": triage.get("affected_services", []),
        "triage": triage,
        "correlations": correlation,
        "root_cause": root_cause,
        "root_cause_summary": root_cause.get("root_cause", ""),
        "confidence": root_cause.get("confidence", 0.0),
        "status": "active",
        "processing_ms": total_ms,
        "total_processing_ms": total_ms,
        **stage_ms,
    }

    incident_store.store_incident(incident_id, incident)
    await ws_manager.broadcast(json.dumps({"type": "new_incident", "data": incident}))

    if triage.get("severity") == "critical":
        asyncio.create_task(send_incident_alert(incident))

    return _ok(incident)


# ── /api/incidents ────────────────────────────────────────────────────────────

@app.get("/api/incidents")
async def list_incidents():
    return _ok(incident_store.get_all_incidents())


@app.get("/api/incidents/{incident_id}/logs")
async def get_incident_logs(incident_id: str):
    return _ok(incident_store.get_logs(incident_id))


@app.get("/api/metrics")
async def get_live_metrics():
    # Baseline healthy stats
    metrics = {
        "gateway-api": {"status": "Healthy", "error_rate": 0.1, "latency": 42, "throughput": 1247, "uptime": 99.98},
        "auth-service": {"status": "Healthy", "error_rate": 0.2, "latency": 58, "throughput": 847, "uptime": 99.95},
        "payments-api": {"status": "Healthy", "error_rate": 0.3, "latency": 75, "throughput": 1102, "uptime": 99.92},
        "user-service": {"status": "Healthy", "error_rate": 0.15, "latency": 45, "throughput": 1150, "uptime": 99.97},
        "postgres-primary": {"status": "Healthy", "error_rate": 0.05, "latency": 8, "throughput": 2341, "uptime": 99.99},
        "redis-cache": {"status": "Healthy", "error_rate": 0.0, "latency": 2, "throughput": 4821, "uptime": 100.0},
        "notification-worker": {"status": "Healthy", "error_rate": 0.4, "latency": 110, "throughput": 128, "uptime": 99.85},
    }

    # Inspect active incidents
    active_incidents = [inc for inc in incident_store.get_all_incidents() if inc.get("status", "").lower() == "active"]
    
    for inc in active_incidents:
        affected = inc.get("affected_services", []) or []
        severity = str(inc.get("severity", "CRITICAL")).upper()
        scenario = inc.get("scenario", "")
        
        # If it's a database deadlock or connection leak, postgres and payments are affected
        if "postgres" in affected or "db" in scenario or "postgres" in str(inc.get("root_cause_summary", "")).lower():
            metrics["postgres-primary"] = {
                "status": severity,
                "error_rate": 12.1 if severity == "CRITICAL" else 4.2,
                "latency": 4200 if severity == "CRITICAL" else 850,
                "throughput": 91,
                "uptime": 91.3,
            }
            metrics["payments-api"] = {
                "status": severity,
                "error_rate": 8.7 if severity == "CRITICAL" else 3.2,
                "latency": 1240 if severity == "CRITICAL" else 450,
                "throughput": 203,
                "uptime": 94.2,
            }
        
        # If it's network latency or API cascade, gateway, payments, and auth are degraded
        elif "gateway" in affected or "cascade" in scenario or "latency" in scenario:
            metrics["gateway-api"] = {
                "status": severity,
                "error_rate": 5.4 if severity == "CRITICAL" else 1.8,
                "latency": 8500 if severity == "CRITICAL" else 620,
                "throughput": 1045,
                "uptime": 98.42,
            }
            metrics["payments-api"] = {
                "status": severity,
                "error_rate": 6.8 if severity == "CRITICAL" else 2.1,
                "latency": 14200 if severity == "CRITICAL" else 840,
                "throughput": 150,
                "uptime": 96.1,
            }
            metrics["auth-service"] = {
                "status": "DEGRADED" if severity == "CRITICAL" else "HEALTHY",
                "error_rate": 2.8,
                "latency": 450,
                "throughput": 520,
                "uptime": 99.15,
            }

        # If it's a memory leak, user-service and cache might be degraded
        elif "user" in affected or "memory" in scenario or "oom" in str(inc.get("root_cause_summary", "")).lower():
            metrics["user-service"] = {
                "status": severity,
                "error_rate": 9.4 if severity == "CRITICAL" else 3.2,
                "latency": 2800 if severity == "CRITICAL" else 490,
                "throughput": 820,
                "uptime": 93.4,
            }
            metrics["notification-worker"] = {
                "status": "DEGRADED",
                "error_rate": 2.4,
                "latency": 890,
                "throughput": 128,
                "uptime": 98.2,
            }

        # Generic mapping fallback
        else:
            for svc in affected:
                if svc in metrics:
                    metrics[svc] = {
                        "status": severity,
                        "error_rate": 6.5,
                        "latency": 1250,
                        "throughput": 500,
                        "uptime": 96.5,
                    }

    # Add random micro-variance for live realism to healthy services
    import random
    for name, svc in metrics.items():
        if svc["status"] == "Healthy":
            # Add tiny variations to error_rate, latency, throughput
            svc["error_rate"] = max(0.0, round(svc["error_rate"] + random.uniform(-0.05, 0.05), 2))
            svc["latency"] = max(1, int(svc["latency"] + random.randint(-4, 4)))
            svc["throughput"] = max(10, int(svc["throughput"] + random.randint(-20, 20)))

    # Format numbers into strings (e.g. latency -> "42ms") as the frontend expects
    formatted = {}
    for name, svc in metrics.items():
        status_label = svc["status"].capitalize() if svc["status"] in ("Healthy", "Degraded", "Critical") else svc["status"]
        formatted[name] = {
            "status": status_label,
            "error_rate": f"{svc['error_rate']:.1f}%" if name != "redis-cache" else "0.0%",
            "latency": f"{svc['latency']:,}ms",
            "throughput": f"{svc['throughput']:,}/s" if name != "notification-worker" else f"{svc['throughput']:,}",
            "uptime": f"{svc['uptime']:.2f}%" if name != "redis-cache" else "100.0%",
            "raw": svc
        }

    return _ok(formatted)



# ── /api/voice/speak ──────────────────────────────────────────────────────────

@app.post("/api/voice/speak")
async def voice_speak(req: SpeakRequest):
    if not req.text.strip():
        _fail("text is required", 400)
    try:
        return StreamingResponse(text_to_speech(req.text), media_type="audio/mpeg")
    except Exception as exc:
        logger.error(f"TTS error: {exc}")
        _fail(str(exc))


# ── /api/chat ─────────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Conversational SRE assistant. Answers with OpenAI, grounded in the
    selected incident's full analysis (Groq triage + Gemini correlation +
    OpenAI root cause) when an incident_id is provided."""
    if not req.message.strip():
        _fail("message is required", 400)

    context: dict = {}
    if req.incident_id:
        incident = incident_store.get_incident(req.incident_id)
        if incident:
            context = {
                "incident_id": incident.get("incident_id"),
                "severity": incident.get("severity"),
                "affected_services": incident.get("affected_services"),
                "triage": incident.get("triage"),
                "correlations": incident.get("correlations"),
                "root_cause": incident.get("root_cause"),
            }

    try:
        answer = await answer_question(req.message, context)
    except Exception as exc:
        logger.error(f"Chat error: {exc}")
        _fail(str(exc))
    return _ok({"response": answer, "incident_id": req.incident_id})


# ── /api/voice/listen (WebSocket) ─────────────────────────────────────────────

@app.websocket("/api/voice/listen")
async def voice_listen(ws: WebSocket):
    await ws.accept()
    audio_chunks: List[bytes] = []
    incident_context: dict = {}

    try:
        while True:
            msg = await ws.receive()

            if msg.get("bytes"):
                audio_chunks.append(msg["bytes"])
                continue

            if not msg.get("text"):
                continue

            payload = json.loads(msg["text"])
            msg_type = payload.get("type", "")

            if msg_type == "end_of_speech":
                if not audio_chunks:
                    await ws.send_json({"error": "No audio data received"})
                    continue

                audio_bytes = b"".join(audio_chunks)
                audio_chunks = []

                try:
                    transcript = await transcribe_audio(audio_bytes)
                except Exception as exc:
                    await ws.send_json({"error": f"Transcription failed: {exc}"})
                    continue

                lower = transcript.lower()
                analyze_kw = {
                    "analyze", "root cause", "what's wrong", "investigate",
                    "debug", "what happened", "incident", "diagnose", "problem",
                }
                is_analyze = any(k in lower for k in analyze_kw)
                incident_id = payload.get("incident_id")

                if is_analyze and incident_id:
                    try:
                        logs = incident_store.get_logs(incident_id)
                        if logs:
                            tri, corr, rc, _ = await _run_pipeline(logs)
                            incident_context = rc
                            response_text = rc.get("voice_summary", "Analysis complete.")
                            action = "analyze"
                        else:
                            response_text = "No logs found for this incident ID."
                            action = "error"
                    except Exception as exc:
                        response_text = f"Analysis failed: {exc}"
                        action = "error"
                else:
                    try:
                        response_text = await answer_question(transcript, incident_context)
                        action = "answer"
                    except Exception as exc:
                        response_text = f"Could not answer: {exc}"
                        action = "error"

                await ws.send_json({
                    "transcript": transcript,
                    "action": action,
                    "response": response_text,
                })

            elif msg_type == "set_context":
                incident_context = payload.get("context", {})
                await ws.send_json({"type": "context_set", "ok": True})

    except WebSocketDisconnect:
        logger.info("Voice WebSocket client disconnected")
    except Exception as exc:
        logger.error(f"Voice WebSocket error: {exc}")


# ── /ws/live ──────────────────────────────────────────────────────────────────

@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)


# ── /api/chaos ────────────────────────────────────────────────────────────────

@app.post("/api/chaos")
async def chaos(req: ChaosRequest):
    valid = {"db_connection_leak", "memory_leak", "api_cascade", "network_latency_spike", "database_deadlock"}
    if req.scenario not in valid:
        _fail(f"Unknown scenario '{req.scenario}'. Valid options: {sorted(valid)}", 400)

    t0 = time.monotonic()
    logs = generate_chaos_logs(req.scenario)
    incident_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    incident_store.store_logs(incident_id, logs, ts)

    try:
        async with aiofiles.open(LOGS_DIR / f"{incident_id}.json", "w") as f:
            await f.write(
                json.dumps(
                    {
                        "incident_id": incident_id,
                        "scenario": req.scenario,
                        "log_count": len(logs),
                        "logs": logs,
                    },
                    indent=2,
                )
            )
    except Exception as exc:
        logger.warning(f"Disk write failed for chaos {incident_id}: {exc}")

    triage, correlation, root_cause, stage_ms = await _run_pipeline(logs)
    total_ms = round((time.monotonic() - t0) * 1000)

    incident = {
        "incident_id": incident_id,
        "timestamp": ts,
        "scenario": req.scenario,
        "severity": triage.get("severity", "critical"),
        "affected_services": triage.get("affected_services", []),
        "triage": triage,
        "correlations": correlation,
        "root_cause": root_cause,
        "root_cause_summary": root_cause.get("root_cause", ""),
        "confidence": root_cause.get("confidence", 0.0),
        "status": "active",
        "processing_ms": total_ms,
        "total_processing_ms": total_ms,
        "log_count": len(logs),
        **stage_ms,
    }

    incident_store.store_incident(incident_id, incident)
    await ws_manager.broadcast(json.dumps({"type": "new_incident", "data": incident}))
    asyncio.create_task(send_incident_alert(incident))

    return _ok(incident)


# ── /api/slack ────────────────────────────────────────────────────────────────

@app.post("/api/slack")
async def slack_notify(req: SlackAlertRequest):
    incident = incident_store.get_incident(req.incident_id)
    if not incident:
        _fail("Incident not found", 404)
    sent = await send_incident_alert(incident)
    return _ok({"sent": sent, "incident_id": req.incident_id})


# ── /api/integrations ─────────────────────────────────────────────────────────

@app.get("/api/integrations/status")
async def integrations_status():
    results = await asyncio.gather(
        datadog_service.health_check(),
        grafana_service.health_check(),
        newrelic_service.health_check(),
        return_exceptions=True,
    )
    return _ok({
        "datadog": results[0] if not isinstance(results[0], Exception) else {"ok": False, "error": str(results[0])},
        "grafana": results[1] if not isinstance(results[1], Exception) else {"ok": False, "error": str(results[1])},
        "newrelic": results[2] if not isinstance(results[2], Exception) else {"ok": False, "error": str(results[2])},
    })


@app.post("/api/integrations/sync")
async def integrations_sync(req: IntegrationSyncRequest):
    """One-shot pull from all (or selected) providers. Optionally auto-analyze."""
    providers = set(req.providers) if req.providers else {"datadog", "grafana", "newrelic"}
    window = req.window_minutes or 10

    tasks: Dict[str, Any] = {}
    if "datadog" in providers and datadog_service.is_configured():
        tasks["datadog"] = datadog_service.fetch_all(window)
    if "grafana" in providers and grafana_service.is_configured():
        tasks["grafana"] = grafana_service.fetch_all(window)
    if "newrelic" in providers and newrelic_service.is_configured():
        tasks["newrelic"] = newrelic_service.fetch_all(window)

    by_source: Dict[str, List[dict]] = {p: [] for p in providers}
    if tasks:
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for (name, _), r in zip(tasks.items(), results):
            by_source[name] = [] if isinstance(r, Exception) else r

    all_logs = [l for logs in by_source.values() for l in logs]

    incident = None
    if req.auto_analyze and all_logs:
        incident_id = str(uuid.uuid4())
        t0 = time.monotonic()
        incident_store.store_logs(incident_id, all_logs, datetime.now(timezone.utc).isoformat())
        triage, correlation, root_cause, stage_ms = await _run_pipeline(all_logs)
        total_ms = round((time.monotonic() - t0) * 1000)
        incident = {
            "incident_id": incident_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": triage.get("severity", "unknown"),
            "affected_services": triage.get("affected_services", []),
            "triage": triage,
            "correlations": correlation,
            "root_cause": root_cause,
            "root_cause_summary": root_cause.get("root_cause", ""),
            "confidence": root_cause.get("confidence", 0.0),
            "status": "active",
            "processing_ms": total_ms,
            "total_processing_ms": total_ms,
            "log_count": len(all_logs),
            "sources": list(by_source.keys()),
            "trigger": "manual_sync",
            **stage_ms,
        }
        incident_store.store_incident(incident_id, incident)
        await ws_manager.broadcast(json.dumps({"type": "new_incident", "data": incident}))

    return _ok({
        "by_source_counts": {k: len(v) for k, v in by_source.items()},
        "total_logs": len(all_logs),
        "incident": incident,
    })


# ── /api/agent ────────────────────────────────────────────────────────────────

@app.post("/api/agent/start")
async def agent_start(req: AgentStartRequest):
    cfg = {k: v for k, v in req.dict().items() if v is not None}
    started = await agent.start(cfg)
    return _ok({"started": started, "status": agent.status()})


@app.post("/api/agent/stop")
async def agent_stop():
    stopped = await agent.stop()
    return _ok({"stopped": stopped, "status": agent.status()})


@app.get("/api/agent/status")
async def agent_status():
    return _ok(agent.status())


@app.post("/api/agent/poll")
async def agent_poll_once():
    """Trigger a single poll cycle manually (useful for testing)."""
    summary = await agent.poll_once()
    return _ok(summary)


# ── Static frontend ───────────────────────────────────────────────────────────
# Serves the bundled dashboard UI from the same Cloud Run service. Mounted last so
# all /api/* and WebSocket routes above take precedence. Skipped when the frontend
# directory is absent (e.g. local API-only dev).
from fastapi.staticfiles import StaticFiles  # noqa: E402

_FRONTEND_DIR = Path(__file__).parent / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
    logger.info(f"Serving static frontend from {_FRONTEND_DIR}")
else:
    logger.info("No frontend directory found — running API-only")
