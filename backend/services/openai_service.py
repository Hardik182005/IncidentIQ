import json
import logging
import os
from typing import Any, Dict

from openai import AsyncOpenAI

logger = logging.getLogger("aria.openai")

OPENAI_ROOTCAUSE_PROMPT = """
You are the world's best SRE. Return ONLY valid JSON, no markdown, no backticks:
{
  "root_cause": "<specific technical root cause>",
  "confidence": 0.92,
  "evidence": ["<exact log line or metric proving this>"],
  "fix_commands": ["<exact executable command>"],
  "prevention": "<specific prevention measure>",
  "estimated_impact": "<N users affected, estimated downtime>",
  "voice_summary": "<2 sentence plain English explanation for voice readout>"
}
Triage: %s
Correlations: %s
"""

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _client


async def analyze_root_cause(triage: dict, correlations: dict) -> Dict[str, Any]:
    client = _get_client()
    prompt = OPENAI_ROOTCAUSE_PROMPT % (json.dumps(triage), json.dumps(correlations))

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=1000,
    )
    return json.loads(resp.choices[0].message.content)


async def answer_question(question: str, context: dict) -> str:
    client = _get_client()
    ctx_str = json.dumps(context) if context else "No incident context loaded yet."

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert SRE assistant for IncidentIQ. "
                    f"Current incident context: {ctx_str[:4000]}"
                ),
            },
            {"role": "user", "content": question},
        ],
        temperature=0.3,
        max_tokens=500,
    )
    return resp.choices[0].message.content


async def health_check() -> bool:
    try:
        client = _get_client()
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        return bool(resp.choices[0].message.content)
    except Exception as exc:
        logger.warning(f"OpenAI health check failed: {exc}")
        return False
