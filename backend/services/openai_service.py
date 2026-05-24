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
  "confidence": <a calibrated float 0.0-1.0: how certain you are GIVEN the evidence. Use the FULL range — low (0.4-0.6) when logs are sparse/ambiguous or stages disagree, high (0.85+) only when multiple log lines and the correlation clearly point to one cause. Do NOT default to a round number.>,
  "evidence": ["<exact log line or metric proving this>"],
  "fix_commands": ["<exact executable command>"],
  "prevention": "<specific prevention measure>",
  "estimated_impact": "<N users affected, estimated downtime>",
  "voice_summary": "<2 sentence plain English explanation for voice readout>"
}
Triage: %s
Correlations: %s
"""


def _compute_confidence(
    triage: dict, correlations: dict, root_cause: dict, model_conf: Any
) -> float:
    """Derive a real, evidence-grounded confidence instead of a fixed value.

    The model's self-reported confidence is blended in only when it looks
    genuine (not the tell-tale 0.92 placeholder it tends to echo). Everything
    else is computed from how much corroborating signal each stage actually
    produced, so identical inputs yield identical scores and weak incidents
    score lower than well-evidenced ones.
    """
    score = 0.40

    evidence = root_cause.get("evidence") or []
    score += min(len(evidence), 4) * 0.07          # up to +0.28

    anomalies = triage.get("anomalies") or []
    score += min(len(anomalies), 5) * 0.02          # up to +0.10

    if correlations.get("probable_trigger"):
        score += 0.08
    if correlations.get("correlated_events"):
        score += 0.05
    if correlations.get("blast_radius"):
        score += 0.04

    rc_text = root_cause.get("root_cause") or ""
    if len(rc_text) > 80:
        score += 0.05
    if root_cause.get("fix_commands"):
        score += 0.04

    # Penalize when an upstream stage clearly failed/degraded.
    if not anomalies and not triage.get("affected_services"):
        score -= 0.12
    if not rc_text:
        score -= 0.20

    try:
        mc = float(model_conf)
        if 0.0 < mc <= 1.0 and abs(mc - 0.92) > 1e-9:
            score = 0.6 * score + 0.4 * mc           # blend in genuine self-report
    except (TypeError, ValueError):
        pass

    return round(max(0.35, min(0.98, score)), 2)

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
    result = json.loads(resp.choices[0].message.content)
    # Override the model's tendency to echo the placeholder confidence with a
    # real, evidence-derived score.
    result["confidence"] = _compute_confidence(
        triage, correlations, result, result.get("confidence")
    )
    return result


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
