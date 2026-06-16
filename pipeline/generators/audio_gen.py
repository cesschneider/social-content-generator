"""
Audio/voiceover generation via ElevenLabs.
"""
import os
import logging
import requests
from pathlib import Path

log = logging.getLogger(__name__)


def generate_voiceover(text: str, output_filename: str) -> str | None:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    if not api_key or not voice_id:
        log.warning("ElevenLabs not configured — skipping voiceover")
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()

    output_dir = Path("output/audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename

    with open(output_path, "wb") as f:
        f.write(resp.content)

    log.info("Voiceover saved to %s", output_path)
    return str(output_path)
