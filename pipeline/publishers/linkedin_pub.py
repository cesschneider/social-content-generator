"""
LinkedIn publisher — posts text content and optional image/video.
"""
import os
import logging
import requests

log = logging.getLogger(__name__)

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
PERSON_URN = os.getenv("LINKEDIN_PERSON_URN", "")
BASE_URL = "https://api.linkedin.com/v2"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def publish(assets: dict, content: dict, brief: dict) -> dict:
    text = content.get("linkedin_content", brief["topic"])
    post_body = {
        "author": PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    resp = requests.post(f"{BASE_URL}/ugcPosts", headers=_headers(), json=post_body)
    resp.raise_for_status()
    post_id = resp.headers.get("X-RestLi-Id", "")
    url = f"https://www.linkedin.com/feed/update/{post_id}/"
    log.info("Published to LinkedIn: %s", url)
    return {"url": url, "post_id": post_id}
