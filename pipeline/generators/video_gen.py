"""
Video generation via HeyGen (talking-head) and Higgsfield (B-roll/cinematic).
"""
import os
import time
import logging
import requests

log = logging.getLogger(__name__)

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "")
HEYGEN_AVATAR_ID = os.getenv("HEYGEN_AVATAR_ID", "")
HEYGEN_VOICE_ID = os.getenv("HEYGEN_VOICE_ID", "")
HIGGSFIELD_API_KEY = os.getenv("HIGGSFIELD_API_KEY", "")


def generate_video(script: str, title: str) -> str | None:
    if not HEYGEN_API_KEY:
        log.warning("HEYGEN_API_KEY not set — skipping video generation")
        return None
    return _generate_heygen_video(script, title)


def _generate_heygen_video(script: str, title: str) -> str:
    headers = {"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": HEYGEN_AVATAR_ID,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script[:5000],  # HeyGen script length limit
                    "voice_id": HEYGEN_VOICE_ID,
                },
            }
        ],
        "dimension": {"width": 1920, "height": 1080},
        "title": title,
    }
    resp = requests.post("https://api.heygen.com/v2/video/generate", json=payload, headers=headers)
    resp.raise_for_status()
    video_id = resp.json()["data"]["video_id"]
    log.info("HeyGen video job created: %s", video_id)
    return _poll_heygen(video_id)


def _poll_heygen(video_id: str, timeout_seconds: int = 600) -> str:
    headers = {"X-Api-Key": HEYGEN_API_KEY}
    url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    start = time.time()
    while time.time() - start < timeout_seconds:
        resp = requests.get(url, headers=headers)
        data = resp.json().get("data", {})
        status = data.get("status")
        if status == "completed":
            return data["video_url"]
        if status == "failed":
            raise RuntimeError(f"HeyGen video generation failed: {data}")
        log.info("HeyGen status: %s — waiting...", status)
        time.sleep(15)
    raise TimeoutError(f"HeyGen video not ready after {timeout_seconds}s")


def generate_broll(prompt: str, duration_seconds: int = 5) -> str | None:
    if not HIGGSFIELD_API_KEY:
        log.warning("HIGGSFIELD_API_KEY not set — skipping B-roll generation")
        return None
    headers = {"Authorization": f"Bearer {HIGGSFIELD_API_KEY}"}
    payload = {"prompt": prompt, "duration": duration_seconds, "aspect_ratio": "9:16"}
    resp = requests.post("https://api.higgsfield.ai/v1/generate", json=payload, headers=headers)
    resp.raise_for_status()
    job_id = resp.json()["job_id"]
    return _poll_higgsfield(job_id)


def _poll_higgsfield(job_id: str, timeout_seconds: int = 300) -> str:
    headers = {"Authorization": f"Bearer {HIGGSFIELD_API_KEY}"}
    start = time.time()
    while time.time() - start < timeout_seconds:
        resp = requests.get(f"https://api.higgsfield.ai/v1/status/{job_id}", headers=headers)
        data = resp.json()
        if data.get("status") == "completed":
            return data["video_url"]
        if data.get("status") == "failed":
            raise RuntimeError(f"Higgsfield job failed: {data}")
        time.sleep(10)
    raise TimeoutError("Higgsfield job timed out")
