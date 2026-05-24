import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

logger = logging.getLogger("iqsentry.newrelic")

NERDGRAPH_URL = "https://api.newrelic.com/graphql"
NERDGRAPH_URL_EU = "https://api.eu.newrelic.com/graphql"


def _endpoint() -> str:
    return NERDGRAPH_URL_EU if os.getenv("NEW_RELIC_REGION", "US").upper() == "EU" else NERDGRAPH_URL


def _headers() -> Dict[str, str]:
    return {
        "API-Key": os.getenv("NEW_RELIC_API_KEY", ""),
        "Content-Type": "application/json",
    }


def _account_id() -> int:
    raw = os.getenv("NEW_RELIC_ACCOUNT_ID", "0")
    try:
        return int(raw)
    except ValueError:
        return 0


def is_configured() -> bool:
    return bool(os.getenv("NEW_RELIC_API_KEY") and _account_id() > 0)


def _severity_from_priority(priority: str) -> str:
    p = (priority or "").lower()
    if p in ("critical", "high"):
        return "ERROR"
    if p in ("warning", "medium"):
        return "WARN"
    return "INFO"


async def _nerdgraph(query: str, variables: dict = None) -> dict:
    payload = {"query": query, "variables": variables or {}}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(_endpoint(), json=payload, headers=_headers())
        if r.status_code >= 400:
            logger.warning(f"New Relic NerdGraph {r.status_code}: {r.text[:200]}")
            return {}
        return r.json()


async def fetch_incidents(window_minutes: int = 10) -> List[Dict[str, Any]]:
    if not is_configured():
        return []

    account_id = _account_id()
    query = """
    query($accountId: Int!) {
      actor {
        account(id: $accountId) {
          aiIssues {
            issues(filter: {states: [ACTIVATED]}) {
              issues {
                issueId
                title
                description
                priority
                state
                createdAt
                updatedAt
                entityNames
                conditionFamilyId
              }
            }
          }
        }
      }
    }
    """
    out: List[Dict[str, Any]] = []
    try:
        data = await _nerdgraph(query, {"accountId": account_id})
        issues = (
            data.get("data", {})
            .get("actor", {})
            .get("account", {})
            .get("aiIssues", {})
            .get("issues", {})
            .get("issues", [])
        )
        for issue in issues:
            created_ms = issue.get("createdAt", 0)
            ts_dt = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc) if created_ms else datetime.now(timezone.utc)
            entities = issue.get("entityNames", []) or []
            service = entities[0] if entities else "unknown"
            title = issue.get("title", ["New Relic incident"])
            title_str = title[0] if isinstance(title, list) and title else str(title)
            desc = issue.get("description", [])
            desc_str = desc[0] if isinstance(desc, list) and desc else ""
            out.append({
                "timestamp": ts_dt.isoformat(),
                "severity": _severity_from_priority(issue.get("priority", "")),
                "service": service,
                "message": f"New Relic incident: {title_str}. {desc_str[:240]}",
                "source": "newrelic-incident",
                "meta": {
                    "issue_id": issue.get("issueId"),
                    "state": issue.get("state"),
                    "priority": issue.get("priority"),
                    "entities": entities,
                },
            })
    except Exception as exc:
        logger.error(f"New Relic fetch_incidents error: {exc}")
    return out


async def fetch_nrql_logs(
    nrql: str = "SELECT * FROM Log WHERE level IN ('ERROR','WARN') SINCE 10 minutes ago LIMIT 200",
) -> List[Dict[str, Any]]:
    if not is_configured():
        return []

    account_id = _account_id()
    query = """
    query($accountId: Int!, $nrql: Nrql!) {
      actor {
        account(id: $accountId) {
          nrql(query: $nrql) {
            results
          }
        }
      }
    }
    """
    out: List[Dict[str, Any]] = []
    try:
        data = await _nerdgraph(query, {"accountId": account_id, "nrql": nrql})
        results = (
            data.get("data", {})
            .get("actor", {})
            .get("account", {})
            .get("nrql", {})
            .get("results", [])
            or []
        )
        for r in results:
            ts = r.get("timestamp") or r.get("ts")
            if isinstance(ts, (int, float)):
                ts_dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                ts_iso = ts_dt.isoformat()
            else:
                ts_iso = datetime.now(timezone.utc).isoformat()
            out.append({
                "timestamp": ts_iso,
                "severity": str(r.get("level") or r.get("severity") or "INFO").upper(),
                "service": str(r.get("service") or r.get("entity.name") or r.get("appName") or "unknown"),
                "message": str(r.get("message") or r.get("body") or r),
                "source": "newrelic-log",
                "meta": {k: r[k] for k in r if k not in {"timestamp", "level", "service", "message"}},
            })
    except Exception as exc:
        logger.error(f"New Relic fetch_nrql_logs error: {exc}")
    return out


def _demo_lines() -> List[Dict[str, str]]:
    return [
        {"service": "payments-api", "level": "ERROR", "message": "sqlalchemy.exc.TimeoutError: QueuePool limit reached on payments_db"},
        {"service": "postgres-primary", "level": "ERROR", "message": "FATAL: remaining connection slots are reserved for superuser connections"},
        {"service": "postgres-primary", "level": "WARN", "message": "deadlock detected: process 4821 waits for ShareLock on transaction 99213"},
        {"service": "gateway-api", "level": "ERROR", "message": "upstream connect error 503 from payments-api; circuit breaker open"},
        {"service": "auth-service", "level": "WARN", "message": "JWT validation latency p99=842ms after cert rotation"},
        {"service": "order-service", "level": "ERROR", "message": "retry storm to payments-api: 1240 retries/min"},
    ]


def _log_api_url() -> str:
    return "https://log-api.eu.newrelic.com/log/v1" if os.getenv("NEW_RELIC_REGION", "US").upper() == "EU" else "https://log-api.newrelic.com/log/v1"


async def push_demo_logs(repeat: int = 3) -> Dict[str, Any]:
    """Push demo logs to the New Relic Log API so they appear in Logs UI.

    The Log API needs an INGEST/LICENSE key (not the NRAK user key). Uses
    NEW_RELIC_LICENSE_KEY / NEW_RELIC_INGEST_KEY if present, else falls back to
    NEW_RELIC_API_KEY (which will 403 if it's a user key)."""
    key = os.getenv("NEW_RELIC_LICENSE_KEY") or os.getenv("NEW_RELIC_INGEST_KEY") or os.getenv("NEW_RELIC_API_KEY", "")
    if not key:
        return {"ok": False, "error": "No New Relic key set"}

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    lines = _demo_lines() * max(1, repeat)
    logs = [
        {
            "timestamp": now_ms + i * 100,
            "message": l["message"],
            "attributes": {"service": l["service"], "level": l["level"], "logtype": "incidentiq-seed", "env": "demo"},
        }
        for i, l in enumerate(lines)
    ]
    body = [{"common": {"attributes": {"source": "incidentiq-seed"}}, "logs": logs}]
    headers = {"Api-Key": key, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(_log_api_url(), json=body, headers=headers)
            ok = r.status_code in (200, 202)
            return {
                "ok": ok,
                "status_code": r.status_code,
                "count": len(logs),
                "error": None if ok else (r.text[:160] + " — set NEW_RELIC_LICENSE_KEY (an ingest/license key, not the NRAK user key) to enable log push"),
            }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


async def fetch_all(window_minutes: int = 10) -> List[Dict[str, Any]]:
    import asyncio
    incidents, logs = await asyncio.gather(
        fetch_incidents(window_minutes),
        fetch_nrql_logs(
            f"SELECT * FROM Log WHERE level IN ('ERROR','WARN') SINCE {window_minutes} minutes ago LIMIT 200"
        ),
        return_exceptions=False,
    )
    return incidents + logs


async def health_check() -> Dict[str, Any]:
    if not is_configured():
        return {"ok": False, "configured": False, "error": "NEW_RELIC_API_KEY/NEW_RELIC_ACCOUNT_ID not set"}
    try:
        query = """{ actor { user { email name } } }"""
        data = await _nerdgraph(query)
        user = data.get("data", {}).get("actor", {}).get("user")
        return {"ok": user is not None, "configured": True, "user": user}
    except Exception as exc:
        return {"ok": False, "configured": True, "error": str(exc)}
