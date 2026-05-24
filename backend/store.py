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


incident_store = IncidentStore()
ws_manager = WebSocketManager()
