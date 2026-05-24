import json
import logging
import os
import re
from typing import Any, Dict, List

logger = logging.getLogger("aria.gemini")

GEMINI_CORRELATION_PROMPT = """
You are a distributed systems expert. Find correlations between anomalies and logs. Return ONLY valid JSON:
{
  "correlated_events": [{"time": "<ISO>", "event": "<description>", "service": "<name>"}],
  "probable_trigger": "<root event that started the cascade>",
  "blast_radius": ["<downstream services affected>"],
  "timeline": [{"time": "<ISO>", "event": "<what happened>"}]
}
Anomalies: %s
Full logs: %s
Deployment events: %s
"""

_client = None
_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _get_client():
    """Gemini API client using GOOGLE_API_KEY (no ADC / Vertex AI required)."""
    global _client
    if _client is None:
        from google import genai

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        _client = genai.Client(api_key=api_key)
    return _client


def _strip_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return json.loads(text.strip())


async def correlate_logs(
    anomalies: List[str],
    logs: str,
    deployments: List[dict],
) -> Dict[str, Any]:
    from google.genai import types

    client = _get_client()
    prompt = GEMINI_CORRELATION_PROMPT % (
        json.dumps(anomalies),
        logs[:800_000],
        json.dumps(deployments),
    )

    resp = await client.aio.models.generate_content(
        model=_MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=2048,
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    return _strip_json(resp.text)


async def health_check() -> bool:
    try:
        from google.genai import types

        client = _get_client()
        resp = await client.aio.models.generate_content(
            model=_MODEL_NAME,
            contents="Say OK",
            config=types.GenerateContentConfig(
                max_output_tokens=10,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return bool(resp.text)
    except Exception as exc:
        logger.warning(f"Gemini health check failed: {exc}")
        return False
