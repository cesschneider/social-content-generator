"""
Substack publisher — creates draft posts via Substack API.
Falls back to Ghost API if GHOST_ADMIN_API_KEY is configured.
"""
import os
import logging
import requests

log = logging.getLogger(__name__)


def publish(assets: dict, content: dict, brief: dict) -> dict:
    ghost_key = os.getenv("GHOST_ADMIN_API_KEY")
    if ghost_key:
        return _publish_ghost(content, brief)
    return _publish_substack(content, brief)


def _publish_substack(content: dict, brief: dict) -> dict:
    api_key = os.environ["SUBSTACK_API_KEY"]
    pub_url = os.environ["SUBSTACK_PUBLICATION_URL"].rstrip("/")
    article = content.get("substack_content", brief["topic"])

    resp = requests.post(
        f"{pub_url}/api/v1/posts",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "draft": True,
            "title": brief["topic"],
            "body": article,
        },
    )
    resp.raise_for_status()
    post = resp.json()
    url = post.get("url", pub_url)
    log.info("Created Substack draft: %s", url)
    return {"url": url, "draft": True}


def _publish_ghost(content: dict, brief: dict) -> dict:
    import jwt
    import time

    api_key = os.environ["GHOST_ADMIN_API_KEY"]
    api_url = os.environ["GHOST_API_URL"].rstrip("/")
    key_id, key_secret = api_key.split(":")
    iat = int(time.time())
    token = jwt.encode(
        {"iat": iat, "exp": iat + 300, "aud": "/admin/"},
        bytes.fromhex(key_secret),
        algorithm="HS256",
        headers={"kid": key_id},
    )

    article = content.get("substack_content", brief["topic"])
    resp = requests.post(
        f"{api_url}/ghost/api/admin/posts/",
        headers={"Authorization": f"Ghost {token}"},
        json={"posts": [{"title": brief["topic"], "html": article, "status": "draft"}]},
    )
    resp.raise_for_status()
    post = resp.json()["posts"][0]
    log.info("Created Ghost draft: %s", post["url"])
    return {"url": post["url"], "draft": True}
