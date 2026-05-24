import json
import logging
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from fastapi import WebSocket

logger = logging.getLogger("aria.store")


class WebSocketManager:
    def __init__(self):
        self._active: List[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._active.append(ws)
        logger.info(f"WS client connected. Total: {len(self._active)}")

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._active:
            self._active.remove(ws)
        logger.info(f"WS client disconnected. Total: {len(self._active)}")

    async def broadcast(self, message: str) -> None:
        dead: List[WebSocket] = []
        for ws in list(self._active):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


class IncidentStore:
    MAX_INCIDENTS = 100

    def __init__(self):
        self._incidents: OrderedDict[str, dict] = OrderedDict()
        self._logs: Dict[str, List[dict]] = {}

    def store_logs(self, incident_id: str, logs: List[dict], timestamp: str) -> None:
        self._logs[incident_id] = logs

    def get_logs(self, incident_id: str) -> List[dict]:
        return self._logs.get(incident_id, [])

    def store_incident(self, incident_id: str, incident: dict) -> None:
        if incident_id in self._incidents:
            del self._incidents[incident_id]
        self._incidents[incident_id] = incident
        while len(self._incidents) > self.MAX_INCIDENTS:
            self._incidents.popitem(last=False)

    def get_incident(self, incident_id: str) -> Optional[dict]:
        return self._incidents.get(incident_id)

    def get_all_incidents(self) -> List[dict]:
        return sorted(
            self._incidents.values(),
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )


_DEFAULT_RUNBOOKS = [
    {
        "id": "rb-001", "cat": "database", "catCol": "#F59E0B", "catBg": "rgba(245,158,11,0.1)",
        "title": "DB Connection Pool Exhaustion",
        "desc": "Resolve PostgreSQL connection pool saturation. Covers drain, scale, and timeout config reset.",
        "steps": 4, "lastUsed": "2 min ago", "lastInc": "INC-2847", "ai": True,
        "steps_detail": [
            {"text": "Check current pool utilization", "cmd": "psql $DB_URL -c \"SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';\""},
            {"text": "Terminate idle connections older than 5 minutes", "cmd": "psql $DB_URL -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - INTERVAL '5 min';\""},
            {"text": "Scale pool limit via environment variable", "cmd": "kubectl set env deployment/payments-api DB_POOL_MAX=200 -n production"},
            {"text": "Monitor recovery — error rate should drop within 2 minutes", "cmd": "watch -n2 \"kubectl top pod -l app=payments-api -n production\""},
        ],
    },
    {
        "id": "rb-002", "cat": "memory", "catCol": "#8B5CF6", "catBg": "rgba(139,92,246,0.1)",
        "title": "Memory Leak Investigation",
        "desc": "Identify and mitigate unbounded heap growth on production pods before OOM kill.",
        "steps": 5, "lastUsed": "3h ago", "lastInc": "INC-2838", "ai": False,
        "steps_detail": [
            {"text": "Identify top memory-consuming pods", "cmd": "kubectl top pod --sort-by=memory -n production"},
            {"text": "Capture heap dump for offline analysis", "cmd": "kubectl exec -it <pod-name> -- node --heapsnapshot-signal=SIGUSR2"},
            {"text": "Rolling restart the affected deployment", "cmd": "kubectl rollout restart deployment/<name> -n production"},
            {"text": "Verify memory usage after restart", "cmd": "kubectl top pod -l app=<name> -n production --sort-by=memory"},
        ],
    },
    {
        "id": "rb-003", "cat": "network", "catCol": "#06B6D4", "catBg": "rgba(6,182,212,0.1)",
        "title": "API Cascade Failure Recovery",
        "desc": "Recover from gateway timeout cascades affecting multiple downstream services.",
        "steps": 4, "lastUsed": "2h ago", "lastInc": "INC-2843", "ai": False,
        "steps_detail": [
            {"text": "Identify which upstream service is the source of 503s", "cmd": "kubectl logs -l app=gateway-api --tail=100 | grep 'upstream connect error'"},
            {"text": "Open circuit breaker manually if auto-trip failed", "cmd": "kubectl set env deployment/gateway-api CIRCUIT_BREAKER_FORCED=open"},
            {"text": "Restart the degraded upstream service", "cmd": "kubectl rollout restart deployment/<upstream-svc> -n production"},
            {"text": "Close circuit breaker and monitor error rate", "cmd": "kubectl set env deployment/gateway-api CIRCUIT_BREAKER_FORCED="},
        ],
    },
]


class RunbookStore:
    """In-memory runbook store seeded with default SRE runbooks, supports create."""

    def __init__(self):
        self._runbooks: "OrderedDict[str, dict]" = OrderedDict()
        for rb in _DEFAULT_RUNBOOKS:
            self._runbooks[rb["id"]] = dict(rb)

    def get_all(self) -> List[dict]:
        return list(self._runbooks.values())

    def create(self, rb: dict) -> dict:
        import uuid
        rb_id = rb.get("id") or f"rb-{uuid.uuid4().hex[:8]}"
        cat = (rb.get("cat") or "service").lower()
        cat_palette = {
            "database": ("#F59E0B", "rgba(245,158,11,0.1)"),
            "memory": ("#8B5CF6", "rgba(139,92,246,0.1)"),
            "network": ("#06B6D4", "rgba(6,182,212,0.1)"),
            "service": ("#10B981", "rgba(16,185,129,0.1)"),
            "security": ("#EF4444", "rgba(239,68,68,0.1)"),
        }
        col, bg = cat_palette.get(cat, cat_palette["service"])
        steps_detail = rb.get("steps_detail") or []
        record = {
            "id": rb_id,
            "cat": cat,
            "catCol": col,
            "catBg": bg,
            "title": rb.get("title", "Untitled Runbook"),
            "desc": rb.get("desc", ""),
            "steps": len(steps_detail),
            "lastUsed": "just now",
            "lastInc": rb.get("lastInc", "—"),
            "ai": bool(rb.get("ai", False)),
            "steps_detail": steps_detail,
        }
        self._runbooks[rb_id] = record
        return record


incident_store = IncidentStore()
ws_manager = WebSocketManager()
runbook_store = RunbookStore()
