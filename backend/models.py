from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    incident_id: Optional[str] = None
    source: str = "direct"  # direct | gcp | datadog | grafana
    logs: Optional[List[Dict[str, Any]]] = None
    gcp_logs: Optional[List[Dict[str, Any]]] = None
    webhook_payload: Optional[Dict[str, Any]] = None


class AnalyzeRequest(BaseModel):
    incident_id: Optional[str] = None
    logs: Optional[List[Dict[str, Any]]] = None
    deployment_events: Optional[List[Dict[str, Any]]] = None


class SpeakRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    message: str
    incident_id: Optional[str] = None
    # Compact snapshot of the incidents currently visible on the dashboard feed,
    # sent by the voice orb so IQ-Sentry can answer "what's happening right now"
    # even when no single incident is selected.
    live_incidents: Optional[List[Dict[str, Any]]] = None


class ChaosRequest(BaseModel):
    scenario: str  # db_connection_leak | memory_leak | api_cascade


class SlackAlertRequest(BaseModel):
    incident_id: str


class AgentStartRequest(BaseModel):
    datadog_enabled: Optional[bool] = True
    grafana_enabled: Optional[bool] = True
    newrelic_enabled: Optional[bool] = True
    poll_interval_seconds: Optional[int] = 30
    window_minutes: Optional[int] = 5
    auto_analyze: Optional[bool] = True
    min_logs_to_analyze: Optional[int] = 1
    error_severity_only: Optional[bool] = False


class IntegrationSyncRequest(BaseModel):
    providers: Optional[List[str]] = None
    window_minutes: Optional[int] = 10
    auto_analyze: Optional[bool] = True


class RunbookStep(BaseModel):
    text: str
    cmd: str = ""


class RunbookCreateRequest(BaseModel):
    title: str
    cat: str = "service"  # database | memory | network | service | security
    desc: str = ""
    ai: bool = False
    steps_detail: List[RunbookStep] = Field(default_factory=list)
