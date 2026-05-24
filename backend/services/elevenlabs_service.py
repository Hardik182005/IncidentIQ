import logging
import os
from typing import Iterator

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

logger = logging.getLogger("iqsentry.elevenlabs")

VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
MODEL_ID = "eleven_turbo_v2_5"

_client: ElevenLabs | None = None


def _get_client() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY", ""))
    return _client


def text_to_speech(text: str) -> Iterator[bytes]:
    client = _get_client()
    stream = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id=MODEL_ID,
        text=text,
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
        ),
        output_format="mp3_44100_128",
    )
    for chunk in stream:
        if chunk:
            yield chunk


async def health_check() -> bool:
    try:
        client = _get_client()
        voices = client.voices.get_all()
        return len(voices.voices) > 0
    except Exception as exc:
        logger.warning(f"ElevenLabs health check failed: {exc}")
        return False
