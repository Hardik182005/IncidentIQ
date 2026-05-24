import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx

logger = logging.getLogger("aria.grafana")


def _base_url() -> str:
    return os.getenv("GRAFANA_URL", "").rstrip("/")


def _loki_url() -> str:
    return os.getenv("GRAFANA_LOKI_URL", "").rstrip("/")


def _headers() -> Dict[str, str]:
    token = os.getenv("GRAFANA_API_KEY", "")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def is_configured() -> bool:
    return bool(os.getenv("GRAFANA_API_KEY") and _base_url())


def _severity_from_state(state: str) -> str:
    s = (state or "").lower()
    if s in ("alerting", "firing", "error"):
        return "ERROR"
    if s in ("pending", "warning", "no_data", "nodata"):
        return "WARN"
    return "INFO"


async def fetch_alerts(window_minutes: int = 10) -> List[Dict[str, Any]]:
    """Fetch Grafana unified alerting alerts (Alertmanager-compatible endpoint)."""
    if not is_configured():
        return []

    url = f"{_base_url()}/api/alertmanager/grafana/api/v2/alerts"
    out: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            r = await client.get(url, headers=_headers())
            if r.status_code == 404:
                # Fallback to legacy alerts endpoint
                r = await client.get(f"{_base_url()}/api/alerts", headers=_headers())
            if r.status_code >= 400:
                logger.warning(f"Grafana alerts API {r.status_code}: {r.text[:200]}")
                return []
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
            for alert in r.json():
                labels = alert.get("labels", {}) or {}
                annotations = alert.get("annotations", {}) or {}
                status = alert.get("status", {})
                state = status.get("state") if isinstance(status, dict) else alert.get("state", "alerting")
                starts_at = alert.get("startsAt") or alert.get("newStateDate") or datetime.now(timezone.utc).isoformat()
                try:
                    ts_dt = datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
                except Exception:
                    ts_dt = datetime.now(timezone.utc)
                if ts_dt < cutoff:
                    continue
                service = labels.get("service") or labels.get("job") or labels.get("app") or "unknown"
                summary = (
                    annotations.get("summary")
                    or annotations.get("description")
                    or labels.get("alertname")
                    or "Grafana alert fired"
                )
                out.append({
                    "timestamp": ts_dt.isoformat(),
                    "severity": _severity_from_state(state),
                    "service": service,
                    "message": f"Grafana alert: {labels.get('alertname', 'unknown')} — {summary}",
                    "source": "grafana-alert",
                    "meta": {"labels": labels, "state": state},
                })
    except Exception as exc:
        logger.error(f"Grafana fetch_alerts error: {exc}")
    return out


async def fetch_loki_logs(
    query: str = '{level=~"error|warn"}',
    window_minutes: int = 10,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Fetch logs via Loki query_range API."""
    base = _loki_url() or _base_url()
    if not base or not os.getenv("GRAFANA_API_KEY"):
        return []

    end_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)
    start_ns = end_ns - int(window_minutes * 60 * 1e9)

    url = f"{base}/loki/api/v1/query_range"
    # Grafana Cloud Loki needs basic auth (instance id : token). Use it when the
    # numeric Loki user is configured; otherwise fall back to the Bearer header.
    loki_user = os.getenv("GRAFANA_LOKI_USER", "")
    loki_token = os.getenv("GRAFANA_LOKI_TOKEN") or os.getenv("GRAFANA_API_KEY", "")
    auth = (loki_user, loki_token) if loki_user else None
    headers = {"Accept": "application/json"} if loki_user else _headers()
    out: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
            r = await client.get(
                url,
                headers=headers,
                auth=auth,
                params={
                    "query": query,
                    "start": str(start_ns),
                    "end": str(end_ns),
                    "limit": str(limit),
                    "direction": "backward",
                },
            )
            if r.status_code >= 400:
                logger.warning(f"Grafana Loki API {r.status_code}: {r.text[:200]}")
                return []
            result = r.json().get("data", {}).get("result", [])
            for stream in result:
                labels = stream.get("stream", {})
                service = labels.get("service") or labels.get("app") or labels.get("job") or "unknown"
                level = labels.get("level") or labels.get("severity") or "INFO"
                for ts_ns_str, line in stream.get("values", []):
                    ts_dt = datetime.fromtimestamp(int(ts_ns_str) / 1e9, tz=timezone.utc)
                    out.append({
                        "timestamp": ts_dt.isoformat(),
                        "severity": level.upper(),
                        "service": service,
                        "message": line,
                        "source": "grafana-loki",
                        "meta": {"labels": labels},
                    })
    except Exception as exc:
        logger.error(f"Grafana fetch_loki_logs error: {exc}")
    return out


def _demo_lines() -> List[Dict[str, str]]:
    return [
        {"service": "payments-api", "level": "error", "line": "sqlalchemy.exc.TimeoutError: QueuePool limit reached on payments_db, connection timed out after 5s"},
        {"service": "postgres-primary", "level": "error", "line": "FATAL: remaining connection slots are reserved for superuser connections"},
        {"service": "postgres-primary", "level": "warn", "line": "deadlock detected: process 4821 waits for ShareLock on transaction 99213"},
        {"service": "gateway-api", "level": "error", "line": "upstream connect error 503 from payments-api; circuit breaker open"},
        {"service": "auth-service", "level": "warn", "line": "JWT validation latency p99=842ms after cert rotation"},
        {"service": "order-service", "level": "error", "line": "retry storm to payments-api: 1240 retries/min, backoff saturated"},
    ]


async def push_demo_logs(repeat: int = 3) -> Dict[str, Any]:
    """Push demo logs to Grafana Cloud Loki so they show in Explore → Loki.

    Grafana Cloud Loki push needs basic-auth (numeric instance id : access-policy
    token with logs:write). If GRAFANA_LOKI_USER is set we use it; otherwise we try
    the service-account token as a Bearer (works on some self-hosted setups)."""
    base = _loki_url() or _base_url()
    token = os.getenv("GRAFANA_LOKI_TOKEN") or os.getenv("GRAFANA_API_KEY", "")
    if not base or not token:
        return {"ok": False, "error": "GRAFANA_LOKI_URL/GRAFANA_API_KEY not set"}

    now_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)
    lines = _demo_lines() * max(1, repeat)
    # Group by (service, level) into Loki streams
    streams: Dict[tuple, Dict[str, Any]] = {}
    for i, l in enumerate(lines):
        key = (l["service"], l["level"])
        streams.setdefault(key, {"stream": {"service": l["service"], "level": l["level"], "env": "demo", "source": "incidentiq-seed"}, "values": []})
        streams[key]["values"].append([str(now_ns + i * 1_000_000), l["line"]])
    body = {"streams": list(streams.values())}

    url = f"{base}/loki/api/v1/push"
    loki_user = os.getenv("GRAFANA_LOKI_USER", "")
    headers = {"Content-Type": "application/json"}
    auth = None
    if loki_user:
        auth = (loki_user, token)
    else:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
            r = await client.post(url, json=body, headers=headers, auth=auth)
            ok = r.status_code in (200, 204)
            return {
                "ok": ok,
                "status_code": r.status_code,
                "count": len(lines),
                "error": None if ok else (r.text[:200] + " — set GRAFANA_LOKI_USER (numeric instance id) + a logs:write token to enable Loki push"),
            }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


async def fetch_all(window_minutes: int = 10) -> List[Dict[str, Any]]:
    import asyncio
    alerts, loki = await asyncio.gather(
        fetch_alerts(window_minutes), fetch_loki_logs(window_minutes=window_minutes),
        return_exceptions=False,
    )
    return alerts + loki


async def health_check() -> Dict[str, Any]:
    if not is_configured():
        return {"ok": False, "configured": False, "error": "GRAFANA_URL/GRAFANA_API_KEY not set"}
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            r = await client.get(f"{_base_url()}/api/health", headers=_headers())
            return {"ok": r.status_code == 200, "configured": True, "status_code": r.status_code}
    except Exception as exc:
        return {"ok": False, "configured": True, "error": str(exc)}
