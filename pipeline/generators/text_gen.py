"""
Text generation via Claude API.
Generates content for all platforms in a single brief pass.
"""
import os
import logging
import anthropic
from pathlib import Path

log = logging.getLogger(__name__)

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        # Use ANTHROPIC_API_KEY from env if present; otherwise the SDK uses session credentials.
        api_key = os.getenv("ANTHROPIC_API_KEY")
        _client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    return _client


def _load_prompt(platform: str) -> str:
    path = Path(f"config/prompts/{platform}.md")
    if path.exists():
        return path.read_text()
    return "Generate {platform} content for the topic: {topic}"


def generate_platform_content(platform: str, brief: dict) -> str:
    template = _load_prompt(platform)
    prompt = template.format(
        day=brief.get("day", ""),
        topic=brief.get("topic", ""),
        theme=brief.get("theme", ""),
        core_insight=brief.get("core_insight", brief.get("topic", "")),
        hook=brief.get("hook", ""),
        content_points=brief.get("notes", ""),
        word_count=1000,
        duration_seconds=45,
        duration_minutes=12,
        slide_count=8,
        tweet_count=6,
        source_excerpts=brief.get("source_excerpts", ""),
    )

    log.info("Generating %s content via Claude", platform)
    message = _get_client().messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def generate_all_platform_text(brief: dict) -> dict:
    platform_prompt_map = {
        "YouTube": "youtube_script",
        "Substack": "substack_article",
        "LinkedIn": "linkedin_post",
        "Instagram": "instagram_carousel",
        "TikTok": "tiktok_script",
        "X": "twitter_thread",
    }

    content: dict[str, str] = {}
    for platform in brief.get("platforms", []):
        prompt_key = platform_prompt_map.get(platform)
        if prompt_key:
            content[f"{platform.lower()}_content"] = generate_platform_content(prompt_key, brief)

    return content
