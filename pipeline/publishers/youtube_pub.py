"""
YouTube publisher — uploads video and sets metadata.
Reference implementation: all other publishers follow this interface.
  publish(assets: dict, content: dict, brief: dict) -> dict
"""
import os
import logging
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

log = logging.getLogger(__name__)

TOKEN_FILE = os.getenv("YOUTUBE_TOKEN_FILE", "credentials/youtube_token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_service():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    return build("youtube", "v3", credentials=creds)


def publish(assets: dict, content: dict, brief: dict) -> dict:
    video_url = assets.get("video_url")
    if not video_url:
        log.warning("No video asset for YouTube — skipping")
        return {"skipped": True, "reason": "no video asset"}

    service = _get_service()
    script = content.get("youtube_content", "")
    title = brief["topic"]
    description = script[:4000]  # YouTube description limit

    request = service.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["AI", "software engineering", "vibe coding", "agentic engineering"],
                "categoryId": "28",  # Science & Technology
            },
            "status": {"privacyStatus": "public"},
        },
        media_body=MediaFileUpload(video_url, resumable=True),
    )
    response = request.execute()
    video_id = response["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    log.info("Published to YouTube: %s", url)
    return {"url": url, "video_id": video_id}
