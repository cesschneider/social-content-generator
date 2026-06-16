"""
Cloudinary upload and URL management.
All assets must be hosted on Cloudinary before being passed to social APIs.
"""
import os
import logging
import cloudinary
import cloudinary.uploader

log = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


def upload_asset(local_path: str, public_id: str) -> str:
    log.info("Uploading %s to Cloudinary as %s", local_path, public_id)
    result = cloudinary.uploader.upload(local_path, public_id=public_id, resource_type="auto")
    return result["secure_url"]


def upload_all_assets(video_url: str | None, carousel_urls: list[str], day: int) -> dict:
    assets: dict[str, str | list] = {}

    if video_url:
        # video_url from HeyGen is already a remote URL; upload to Cloudinary for consistency
        result = cloudinary.uploader.upload(
            video_url, public_id=f"day_{day:02d}/video", resource_type="video"
        )
        assets["video_url"] = result["secure_url"]

    if carousel_urls:
        hosted = []
        for i, path in enumerate(carousel_urls):
            url = upload_asset(path, f"day_{day:02d}/carousel_slide_{i+1:02d}")
            hosted.append(url)
        assets["carousel_urls"] = hosted

    return assets
