"""
Daily content pipeline orchestrator.
Run: python -m pipeline.orchestrator --day 1
Dry run: python -m pipeline.orchestrator --day 1 --dry-run
"""
import argparse
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from pipeline.content_brief import get_daily_brief
from pipeline.generators.text_gen import generate_all_platform_text
from pipeline.generators.video_gen import generate_video
from pipeline.generators.image_gen import generate_carousel_images
from pipeline.processors.media_host import upload_all_assets
from pipeline import publishers

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/pipeline.log"),
    ],
)
log = logging.getLogger("orchestrator")


def run_day(day_number: int, dry_run: bool = False) -> dict:
    log.info(f"Starting Day {day_number} (dry_run={dry_run})")

    brief = get_daily_brief(day_number)
    log.info(f"Brief loaded — topic: {brief['topic']}, platforms: {brief['platforms']}")

    content = generate_all_platform_text(brief)
    log.info("Text generation complete")

    video_url = None
    if "YouTube" in brief["platforms"] or "LinkedIn" in brief["platforms"]:
        video_url = generate_video(
            script=content.get("youtube_content", content.get("linkedin_content", "")),
            title=brief["topic"],
        )
        log.info(f"Video generated: {video_url}")

    carousel_urls: list[str] = []
    if "Instagram" in brief["platforms"]:
        carousel_urls = generate_carousel_images(slides=content.get("instagram_slides", []))
        log.info(f"Carousel images generated: {len(carousel_urls)} slides")

    assets = upload_all_assets(video_url=video_url, carousel_urls=carousel_urls, day=day_number)
    log.info("Assets uploaded to Cloudinary")

    if dry_run:
        log.info("Dry run — skipping publish")
        return {"dry_run": True, "assets": assets, "content": content}

    results: dict[str, dict] = {}
    publisher_map = {
        "YouTube": publishers.youtube_pub,
        "LinkedIn": publishers.linkedin_pub,
        "Instagram": publishers.instagram_pub,
        "TikTok": publishers.tiktok_pub,
        "X": publishers.twitter_pub,
        "Substack": publishers.substack_pub,
    }

    for platform in brief["platforms"]:
        if platform in publisher_map:
            try:
                results[platform] = publisher_map[platform].publish(assets, content, brief)
                log.info(f"Published to {platform}: {results[platform].get('url', 'ok')}")
            except Exception as e:
                log.error(f"Failed to publish to {platform}: {e}")
                results[platform] = {"error": str(e)}

    log.info(f"Day {day_number} complete — published to: {list(results.keys())}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the content pipeline for a given day.")
    parser.add_argument("--day", type=int, required=True, help="Day number (1–30)")
    parser.add_argument("--dry-run", action="store_true", help="Generate but do not publish")
    args = parser.parse_args()
    run_day(args.day, dry_run=args.dry_run)
