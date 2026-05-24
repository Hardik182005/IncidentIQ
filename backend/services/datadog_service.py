import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("aria.datadog")


def _site() -> str:
    return os.getenv("DATADOG_SITE", "datadoghq.com").strip()


def _base_url() -> str:
    return f"https://api.{_site()}"


def _headers() -> Dict[str, str]:
    return {
        "DD-API-KEY": os.getenv("DATADOG_API_KEY", ""),
        "DD-APPLICATION-KEY": os.getenv("DATADOG_APP_KEY", ""),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def is_configured() -> bool:
    return bool(os.getenv("DATADOG_API_KEY") and os.getenv("DATADOG_APP_KEY"))


def _severity_from_dd_status(status: str) -> str:
    return {
        "error": "ERROR",
        "warn": "WARN",
        "warning": "WARN",
        "info": "INFO",
        "ok": "INFO",
        "alert": "ERROR",
        "critical": "ERROR",
    }.get((status or "").lower(), "INFO")


async def fetch_logs(window_minutes: int = 10, query: str = "*", limit: int = 200) -> List[Dict[str, Any]]:
    if not is_configured():
        return []

    to_ts = datetime.now(timezone.utc)
    from_ts = to_ts - timedelta(minutes=window_minutes)

    payload = {
        "filter": {
            "from": from_ts.isoformat().replace("+00:00", "Z"),
            "to": to_ts.isoformat().replace("+00:00", "Z"),
            "query": query,
        },
        "sort": "-timestamp",
        "page": {"limit": min(limit, 1000)},
    }

    url = f"{_base_url()}/api/v2/logs/events/search"
    out: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(url, json=payload, headers=_headers())
            if r.status_code >= 400:
                logger.warning(f"Datadog logs API {r.status_code}: {r.text[:200]}")
                return []
            data = r.json()
            for entry in data.get("data", []):
                attrs = entry.get("attributes", {})
                out.append({
                    "timestamp": attrs.get("timestamp", to_ts.isoformat()),
                    "severity": _severity_from_dd_status(attrs.get("status", "info")),
                    "service": attrs.get("service", attrs.get("attributes", {}).get("service", "unknown")),
                    "message": attrs.get("message", ""),
                    "source": "datadog",
                    "meta": {"host": attrs.get("host"), "tags": attrs.get("tags", [])},
                })
    except Exception as exc:
        logger.error(f"Datadog fetch_logs error: {exc}")
    return out


async def fetch_recent_monitors(window_minutes: int = 10) -> List[Dict[str, Any]]:
    """Return triggered/alerting monitors as log-shaped events."""
    if not is_configured():
        return []

    url = f"{_base_url()}/api/v1/monitor"
    out: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                url,
                headers=_headers(),
                params={"group_states": "alert,warn,no data", "page_size": 100},
            )
            if r.status_code >= 400:
                logger.warning(f"Datadog monitors API {r.status_code}: {r.text[:200]}")
                return []
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
            for mon in r.json():
                state = mon.get("overall_state", "OK")
                if state in ("OK", "No Data"):
                    continue
                modified = mon.get("modified")
                ts_str = modified or datetime.now(timezone.utc).isoformat()
                try:
                    ts_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except Exception:
                    ts_dt = datetime.now(timezone.utc)
                if ts_dt < cutoff:
                    continue
                tags = mon.get("tags", [])
                service = "unknown"
                for tag in tags:
                    if isinstance(tag, str) and tag.startswith("service:"):
                        service = tag.split(":", 1)[1]
                        break
                out.append({
                    "timestamp": ts_dt.isoformat(),
                    "severity": "ERROR" if state == "Alert" else "WARN",
                    "service": service,
                    "message": f"Datadog monitor [{state}] {mon.get('name', '')}: {mon.get('query', '')[:160]}",
                    "source": "datadog-monitor",
                    "meta": {"monitor_id": mon.get("id"), "state": state, "tags": tags},
                })
    except Exception as exc:
        logger.error(f"Datadog fetch_monitors error: {exc}")
    return out


async def fetch_events(window_minutes: int = 10) -> List[Dict[str, Any]]:
    if not is_configured():
        return []

    now = int(datetime.now(timezone.utc).timestamp())
    start = now - window_minutes * 60
    url = f"{_base_url()}/api/v1/events"
    out: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                url,
                headers=_headers(),
                params={"start": start, "end": now, "priority": "normal"},
            )
            if r.status_code >= 400:
                logger.warning(f"Datadog events API {r.status_code}: {r.text[:200]}")
                return []
            for ev in r.json().get("events", []):
                ts_unix = ev.get("date_happened", now)
                tags = ev.get("tags", [])
                service = "unknown"
                for tag in tags:
                    if isinstance(tag, str) and tag.startswith("service:"):
                        service = tag.split(":", 1)[1]
                        break
                out.append({
                    "timestamp": datetime.fromtimestamp(ts_unix, tz=timezone.utc).isoformat(),
                    "severity": _severity_from_dd_status(ev.get("alert_type", "info")),
                    "service": service,
                    "message": f"{ev.get('title', '')}: {ev.get('text', '')[:240]}",
                    "source": "datadog-event",
                    "meta": {"event_id": ev.get("id"), "tags": tags},
                })
    except Exception as exc:
        logger.error(f"Datadog fetch_events error: {exc}")
    return out


def _demo_lines() -> List[Dict[str, str]]:
    return [
        {"service": "payments-api", "status": "error", "message": "psycopg2.OperationalError: connection pool exhausted (200/200 in use) on payments_db"},
        {"service": "payments-api", "status": "error", "message": "sqlalchemy.exc.TimeoutError: QueuePool limit of size 200 overflow 10 reached, connection timed out"},
        {"service": "postgres-primary", "status": "error", "message": "FATAL: remaining connection slots are reserved for non-replication superuser connections"},
        {"service": "postgres-primary", "status": "warn", "message": "deadlock detected: process 4821 waits for ShareLock on transaction 99213; blocked by process 4830"},
        {"service": "auth-service", "status": "warn", "message": "JWT validation latency p99=842ms (threshold 300ms) after cert rotation"},
        {"service": "gateway-api", "status": "error", "message": "upstream connect error: 503 from payments-api, circuit breaker tripping"},
        {"service": "order-service", "status": "error", "message": "retry storm: 1240 retries/min to payments-api, exponential backoff saturated"},
        {"service": "redis-cache", "status": "warn", "message": "evicted 4821 keys under maxmemory pressure, hit ratio dropped to 71%"},
    ]


async def push_demo_logs(repeat: int = 3) -> Dict[str, Any]:
    """Push realistic demo error logs to Datadog Logs intake so they appear in the
    Datadog Logs Explorer (and can then be pulled back by /api/integrations/sync)."""
    api_key = os.getenv("DATADOG_API_KEY", "")
    if not api_key:
        return {"ok": False, "error": "DATADOG_API_KEY not set"}

    lines = _demo_lines() * max(1, repeat)
    payload = [
        {
            "ddsource": "incidentiq",
            "service": l["service"],
            "hostname": f"{l['service']}-prod-1",
            "status": l["status"],
            "message": l["message"],
            "ddtags": f"env:demo,team:sre,service:{l['service']},source:incidentiq-seed",
        }
        for l in lines
    ]
    url = f"https://http-intake.logs.{_site()}/api/v2/logs"
    headers = {"DD-API-KEY": api_key, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(url, json=payload, headers=headers)
            ok = r.status_code in (200, 202)
            return {
                "ok": ok,
                "status_code": r.status_code,
                "count": len(payload),
                "explorer": f"https://app.{_site()}/logs?query=source%3Aincidentiq-seed",
                "error": None if ok else r.text[:200],
            }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


async def fetch_all(window_minutes: int = 10) -> List[Dict[str, Any]]:
    import asyncio
    logs, monitors, events = await asyncio.gather(
        fetch_logs(window_minutes), fetch_recent_monitors(window_minutes), fetch_events(window_minutes),
        return_exceptions=False,
    )
    return logs + monitors + events


async def health_check() -> Dict[str, Any]:
    if not is_configured():
        return {"ok": False, "configured": False, "error": "DATADOG_API_KEY/DATADOG_APP_KEY not set"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{_base_url()}/api/v1/validate", headers=_headers())
            return {"ok": r.status_code == 200, "configured": True, "status_code": r.status_code}
    except Exception as exc:
        return {"ok": False, "configured": True, "error": str(exc)}
