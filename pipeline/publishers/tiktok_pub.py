"""
TikTok publisher — uploads video via TikTok Content Posting API.
Access token expires in 24 hours; uses refresh token for renewal.
"""
import os
import json
import logging
import requests
from pathlib import Path

log = logging.getLogger(__name__)

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TOKEN_FILE = "credentials/tiktok_token.json"


def _load_tokens() -> dict:
    if Path(TOKEN_FILE).exists():
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return {}


def _refresh_access_token(refresh_token: str) -> dict:
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data={
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    resp.raise_for_status()
    new_tokens = resp.json()
    with open(TOKEN_FILE, "w") as f:
        json.dump(new_tokens, f, indent=2)
    return new_tokens


def _get_access_token() -> str:
    tokens = _load_tokens()
    access_token = tokens.get("access_token", os.getenv("TIKTOK_ACCESS_TOKEN", ""))
    if not access_token:
        refresh = tokens.get("refresh_token", os.getenv("TIKTOK_REFRESH_TOKEN", ""))
        if refresh:
            tokens = _refresh_access_token(refresh)
            access_token = tokens["access_token"]
    return access_token


def publish(assets: dict, content: dict, brief: dict) -> dict:
    video_url = assets.get("video_url")
    if not video_url:
        log.warning("No video asset for TikTok — skipping")
        return {"skipped": True, "reason": "no video asset"}

    access_token = _get_access_token()
    caption = content.get("tiktok_content", brief["topic"])[:2200]
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    # Initialize upload
    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers=headers,
        json={
            "post_info": {"title": caption, "privacy_level": "PUBLIC_TO_EVERYONE"},
            "source_info": {"source": "PULL_FROM_URL", "video_url": video_url},
        },
    )
    init_resp.raise_for_status()
    publish_id = init_resp.json()["data"]["publish_id"]
    log.info("TikTok publish initiated: %s", publish_id)
    return {"publish_id": publish_id, "status": "initiated"}
