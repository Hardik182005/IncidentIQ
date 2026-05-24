import logging
import os
from typing import Any, Dict

import aiohttp

logger = logging.getLogger("iqsentry.slack")

_SEVERITY_EMOJI = {
    "critical": ":red_circle:",
    "high": ":large_orange_circle:",
    "medium": ":large_yellow_circle:",
    "low": ":large_green_circle:",
    "unknown": ":white_circle:",
}


async def send_incident_alert(incident: Dict[str, Any]) -> bool:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping Slack alert")
        return False

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    severity = str(incident.get("severity", "unknown")).lower()
    emoji = _SEVERITY_EMOJI.get(severity, ":white_circle:")
    incident_id = incident.get("incident_id", "unknown")

    root_cause_obj = incident.get("root_cause", {})
    triage_obj = incident.get("triage", {})

    root_cause_text = (
        root_cause_obj.get("root_cause", "") if isinstance(root_cause_obj, dict) else str(root_cause_obj)
    )
    fix_commands = root_cause_obj.get("fix_commands", []) if isinstance(root_cause_obj, dict) else []
    confidence = root_cause_obj.get("confidence", 0.0) if isinstance(root_cause_obj, dict) else 0.0
    affected = triage_obj.get("affected_services", incident.get("affected_services", []))
    first_fix = fix_commands[0] if fix_commands else "No fix command available"
    processing_ms = incident.get("total_processing_ms", incident.get("processing_ms", 0))
    scenario = incident.get("scenario", "")

    dashboard_url = f"{frontend_url}/screens/dashboard.html?incident={incident_id}"
    runbook_url = f"{frontend_url}/screens/runbooks.html?incident={incident_id}"
    if scenario:
        runbook_url += f"&scenario={scenario}"

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji.replace(':', '')} IncidentIQ Alert — {severity.upper()}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Incident ID:*\n`{incident_id}`"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Root Cause:*\n{root_cause_text[:280] or 'Analyzing...'}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Affected Services:*\n{', '.join(affected) if affected else 'Unknown'}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*AI Confidence:*\n{int(float(confidence) * 100)}%",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Analysis Time:*\n{processing_ms}ms",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Fix Command:*\n```{first_fix[:300]}```",
                },
            },
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Dashboard", "emoji": True},
                        "url": dashboard_url,
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Open Runbook", "emoji": True},
                        "url": runbook_url,
                    },
                ],
            },
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                body = await resp.text()
                if resp.status == 200:
                    logger.info(f"Slack alert sent: {incident_id}")
                    return True
                logger.error(f"Slack returned {resp.status}: {body}")
                return False
    except Exception as exc:
        logger.error(f"Slack alert failed: {exc}")
        return False
