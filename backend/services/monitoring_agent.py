import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from services import datadog_service, grafana_service, newrelic_service

logger = logging.getLogger("aria.agent")


def _fingerprint(log: dict) -> str:
    """Stable hash so the same upstream event isn't re-analyzed every poll."""
    key = (
        log.get("source", ""),
        log.get("service", ""),
        log.get("severity", ""),
        (log.get("message") or "")[:160],
        log.get("meta", {}).get("monitor_id") if isinstance(log.get("meta"), dict) else None,
        log.get("meta", {}).get("issue_id") if isinstance(log.get("meta"), dict) else None,
        log.get("meta", {}).get("event_id") if isinstance(log.get("meta"), dict) else None,
    )
    return hashlib.sha1(repr(key).encode()).hexdigest()


class MonitoringAgent:
    def __init__(self):
        self.running: bool = False
        self.task: Optional[asyncio.Task] = None

        self.config: Dict[str, Any] = {
            "datadog_enabled": True,
            "grafana_enabled": True,
            "newrelic_enabled": True,
            "poll_interval_seconds": 30,
            "window_minutes": 5,
            "auto_analyze": True,
            "min_logs_to_analyze": 1,
            "error_severity_only": False,
        }

        self.stats: Dict[str, Any] = {
            "started_at": None,
            "last_poll_at": None,
            "polls_completed": 0,
            "logs_collected_total": 0,
            "incidents_detected": 0,
            "analyses_triggered": 0,
            "errors": [],
            "by_source": {"datadog": 0, "grafana": 0, "newrelic": 0},
            "last_poll_summary": {},
        }

        self._seen_fingerprints: set[str] = set()
        self._max_seen = 5000

        # Hooks (injected by main.py to avoid circular imports)
        self.on_logs_collected: Optional[Callable[[List[dict], str], Awaitable[None]]] = None
        self.on_incident_analyzed: Optional[Callable[[dict], Awaitable[None]]] = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def configured_providers(self) -> Dict[str, bool]:
        return {
            "datadog": datadog_service.is_configured(),
            "grafana": grafana_service.is_configured(),
            "newrelic": newrelic_service.is_configured(),
        }

    async def start(self, config: Optional[Dict[str, Any]] = None) -> bool:
        if self.running:
            return False
        if config:
            self.config.update(config)
        self.running = True
        self.stats["started_at"] = datetime.now(timezone.utc).isoformat()
        self.task = asyncio.create_task(self._loop())
        logger.info(f"Monitoring agent STARTED | config={self.config} | providers={self.configured_providers()}")
        return True

    async def stop(self) -> bool:
        if not self.running:
            return False
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except (asyncio.CancelledError, Exception):
                pass
            self.task = None
        logger.info("Monitoring agent STOPPED")
        return True

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "config": self.config,
            "providers": self.configured_providers(),
            "stats": self.stats,
        }

    # ── Polling loop ─────────────────────────────────────────────────────────

    async def _loop(self):
        while self.running:
            try:
                await self.poll_once()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                err_str = f"{datetime.now(timezone.utc).isoformat()} {exc}"
                self.stats["errors"].append(err_str)
                self.stats["errors"] = self.stats["errors"][-20:]
                logger.error(f"Agent loop error: {exc}")
            try:
                await asyncio.sleep(self.config["poll_interval_seconds"])
            except asyncio.CancelledError:
                break

    async def poll_once(self) -> Dict[str, Any]:
        """Single poll cycle. Returns summary of this poll."""
        window = self.config["window_minutes"]
        tasks: Dict[str, Awaitable] = {}

        if self.config["datadog_enabled"] and datadog_service.is_configured():
            tasks["datadog"] = datadog_service.fetch_all(window)
        if self.config["grafana_enabled"] and grafana_service.is_configured():
            tasks["grafana"] = grafana_service.fetch_all(window)
        if self.config["newrelic_enabled"] and newrelic_service.is_configured():
            tasks["newrelic"] = newrelic_service.fetch_all(window)

        per_source: Dict[str, List[dict]] = {k: [] for k in tasks}
        if tasks:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for (name, _), result in zip(tasks.items(), results):
                if isinstance(result, Exception):
                    self.stats["errors"].append(f"{name}: {result}")
                    self.stats["errors"] = self.stats["errors"][-20:]
                    continue
                per_source[name] = result
                self.stats["by_source"][name] += len(result)

        all_logs = [log for logs in per_source.values() for log in logs]

        # De-dup against fingerprints we've already analyzed
        new_logs: List[dict] = []
        for log in all_logs:
            fp = _fingerprint(log)
            if fp not in self._seen_fingerprints:
                self._seen_fingerprints.add(fp)
                new_logs.append(log)

        if len(self._seen_fingerprints) > self._max_seen:
            self._seen_fingerprints = set(list(self._seen_fingerprints)[-self._max_seen:])

        if self.config.get("error_severity_only"):
            new_logs = [l for l in new_logs if l.get("severity") in {"ERROR", "WARN"}]

        self.stats["last_poll_at"] = datetime.now(timezone.utc).isoformat()
        self.stats["polls_completed"] += 1
        self.stats["logs_collected_total"] += len(new_logs)

        summary = {
            "polled_at": self.stats["last_poll_at"],
            "new_logs": len(new_logs),
            "total_logs_in_window": len(all_logs),
            "by_source": {k: len(v) for k, v in per_source.items()},
        }
        self.stats["last_poll_summary"] = summary

        if new_logs and self.on_logs_collected:
            try:
                await self.on_logs_collected(new_logs, summary.get("polled_at"))
            except Exception as exc:
                logger.error(f"on_logs_collected hook failed: {exc}")

        # Auto-analyze when we have enough new signal
        if (
            self.config.get("auto_analyze")
            and len(new_logs) >= self.config.get("min_logs_to_analyze", 1)
            and self.on_incident_analyzed
        ):
            try:
                incident_id = str(uuid.uuid4())
                await self.on_incident_analyzed({
                    "incident_id": incident_id,
                    "logs": new_logs,
                    "trigger": "agent_auto_poll",
                    "sources": list(per_source.keys()),
                })
                self.stats["analyses_triggered"] += 1
                self.stats["incidents_detected"] += 1
            except Exception as exc:
                logger.error(f"on_incident_analyzed hook failed: {exc}")

        logger.info(f"Agent poll: {summary}")
        return summary


agent = MonitoringAgent()
