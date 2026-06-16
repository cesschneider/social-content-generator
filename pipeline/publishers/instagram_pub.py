"""
Instagram publisher — publishes carousels and reels via the Instagram Graph API.
Videos must be hosted URLs (Cloudinary).
"""
import os
import logging
import requests

log = logging.getLogger(__name__)

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
BASE_URL = "https://graph.facebook.com/v19.0"


def _post(endpoint: str, data: dict) -> dict:
    resp = requests.post(f"{BASE_URL}/{endpoint}", data={**data, "access_token": ACCESS_TOKEN})
    resp.raise_for_status()
    return resp.json()


def publish(assets: dict, content: dict, brief: dict) -> dict:
    carousel_urls = assets.get("carousel_urls", [])
    caption = content.get("instagram_content", brief["topic"])

    if not carousel_urls:
        log.warning("No carousel images — skipping Instagram")
        return {"skipped": True, "reason": "no carousel images"}

    # Create media containers for each slide
    children = []
    for url in carousel_urls:
        container = _post(f"{ACCOUNT_ID}/media", {"image_url": url, "is_carousel_item": "true"})
        children.append(container["id"])

    # Create the carousel container
    carousel = _post(f"{ACCOUNT_ID}/media", {
        "media_type": "CAROUSEL",
        "caption": caption,
        "children": ",".join(children),
    })

    # Publish it
    result = _post(f"{ACCOUNT_ID}/media_publish", {"creation_id": carousel["id"]})
    post_id = result["id"]
    url = f"https://www.instagram.com/p/{post_id}/"
    log.info("Published to Instagram: %s", url)
    return {"url": url, "post_id": post_id}
