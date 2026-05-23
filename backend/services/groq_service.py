import io
import json
import logging
import os
import re
from typing import Any, Dict

from groq import AsyncGroq

logger = logging.getLogger("aria.groq")

GROQ_TRIAGE_PROMPT = """
You are an SRE on-call. Analyze these logs and return ONLY valid JSON, no markdown:
{
  "anomalies": ["<specific error with exact timestamp>"],
  "spike_at": "<ISO 8601 timestamp of peak error density>",
  "severity": "critical",
  "affected_services": ["<service names from logs>"],
  "summary": "<2 sentence technical summary>"
}
Logs:
%s
"""

_client: AsyncGroq | None = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", ""))
    return _client


def _strip_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return json.loads(text.strip())


async def triage_logs(log_text: str) -> Dict[str, Any]:
    client = _get_client()
    prompt = GROQ_TRIAGE_PROMPT % log_text[:48_000]

    resp = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1024,
    )
    return _strip_json(resp.choices[0].message.content)


async def transcribe_audio(audio_bytes: bytes) -> str:
    client = _get_client()
    audio_file = ("recording.webm", io.BytesIO(audio_bytes), "audio/webm")
    resp = await client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=audio_file,
        response_format="text",
    )
    return resp if isinstance(resp, str) else getattr(resp, "text", str(resp))


async def health_check() -> bool:
    try:
        client = _get_client()
        resp = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        return bool(resp.choices[0].message.content)
    except Exception as exc:
        logger.warning(f"Groq health check failed: {exc}")
        return False
