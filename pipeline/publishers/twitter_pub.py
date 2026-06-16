"""
X (Twitter) publisher — posts threads and single tweets via X API v2.
Uses tweepy for OAuth 1.0a (required for media uploads).
"""
import os
import logging
import tweepy

log = logging.getLogger(__name__)


def _get_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )


def _parse_thread(content: str) -> list[str]:
    tweets = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("Tweet ") and ":" in line:
            tweet_text = line.split(":", 1)[1].strip()
            if tweet_text:
                tweets.append(tweet_text[:280])
    return tweets if tweets else [content[:280]]


def publish(assets: dict, content: dict, brief: dict) -> dict:
    client = _get_client()
    thread_content = content.get("x_content", content.get("twitter_content", brief["topic"]))
    tweets = _parse_thread(thread_content)

    if not tweets:
        return {"skipped": True, "reason": "no tweet content"}

    reply_to_id = None
    published_ids = []

    for tweet in tweets:
        kwargs = {"text": tweet}
        if reply_to_id:
            kwargs["in_reply_to_tweet_id"] = reply_to_id
        resp = client.create_tweet(**kwargs)
        tweet_id = resp.data["id"]
        published_ids.append(tweet_id)
        reply_to_id = tweet_id

    url = f"https://twitter.com/i/web/status/{published_ids[0]}"
    log.info("Published X thread (%d tweets): %s", len(published_ids), url)
    return {"url": url, "tweet_ids": published_ids}
