"""
Image generation via HuggingFace (FLUX) or Bannerbear for branded carousels.
"""
import os
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def generate_carousel_images(slides: list[dict]) -> list[str]:
    """
    Generate carousel slide images.
    Returns list of local file paths.
    """
    if not slides:
        log.warning("No slides provided for carousel generation")
        return []

    hf_key = os.getenv("HUGGINGFACE_API_KEY")
    if hf_key:
        return _generate_via_huggingface(slides, hf_key)

    log.warning("HUGGINGFACE_API_KEY not set — skipping image generation")
    return []


def _generate_via_huggingface(slides: list[dict], api_key: str) -> list[str]:
    from huggingface_hub import InferenceClient

    client = InferenceClient(token=api_key)
    output_dir = Path("output/images")
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []

    for i, slide in enumerate(slides):
        prompt = slide.get("visual_note") or slide.get("title", f"Slide {i+1}")
        full_prompt = (
            f"Clean, modern tech infographic slide. {prompt}. "
            "Dark background, developer aesthetic, minimal text, high contrast."
        )
        log.info("Generating image for slide %d: %s", i + 1, prompt[:60])
        image = client.text_to_image(full_prompt, model="black-forest-labs/FLUX.1-dev")
        path = output_dir / f"slide_{i+1:02d}.png"
        image.save(str(path))
        paths.append(str(path))

    return paths
