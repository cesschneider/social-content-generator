"""
FFmpeg-based video processing: captions, resizing, platform format conversion.
"""
import subprocess
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def add_captions(video_path: str, srt_path: str, output_path: str) -> str:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style='FontSize=24,PrimaryColour=&HFFFFFF'",
            "-c:a", "copy", output_path,
        ],
        check=True,
    )
    return output_path


def resize_for_platform(video_path: str, platform: str, output_path: str) -> str:
    profiles = {
        "tiktok":    ("1080:1920", "9:16"),
        "instagram": ("1080:1920", "9:16"),
        "youtube":   ("1920:1080", "16:9"),
        "linkedin":  ("1920:1080", "16:9"),
    }
    scale, _ = profiles.get(platform, ("1920:1080", "16:9"))
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:(ow-iw)/2:(oh-ih)/2",
            "-c:a", "copy", output_path,
        ],
        check=True,
    )
    return output_path


def merge_video_broll(main_video: str, broll_video: str, output_path: str) -> str:
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", main_video,
            "-i", broll_video,
            "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
            "-map", "[v]", "-map", "0:a",
            output_path,
        ],
        check=True,
    )
    return output_path
