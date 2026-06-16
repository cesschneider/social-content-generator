# System Specification — Social Content Automation Pipeline

## 1. Overview & Purpose

This pipeline automates the end-to-end production and publishing of a 30-day social media content series titled "The New SDLC With Vibe Coding: From Ad-hoc Prompting to Agentic Engineering."

Each day, the pipeline:
1. Reads the daily content brief from a Notion database
2. Generates platform-native text for each active platform using Claude
3. Generates video assets via HeyGen (talking-head) and Higgsfield (B-roll)
4. Generates carousel images via HuggingFace FLUX
5. Uploads all assets to Cloudinary for stable, signed URLs
6. Publishes to each active platform via their respective APIs
7. Logs published URLs and metadata to Supabase

Target platforms: YouTube, LinkedIn, Instagram, TikTok, X (Twitter), Substack/Ghost.

---

## 2. Architecture — Four-Layer Pipeline

```
Layer 1: INGESTION
  Notion Calendar Database
    └─ content_brief.py → structured brief dict

Layer 2: GENERATION
  brief dict
    ├─ text_gen.py   → Claude API → platform text (all platforms)
    ├─ video_gen.py  → HeyGen API → talking-head video (YouTube, LinkedIn, TikTok)
    ├─ image_gen.py  → HuggingFace FLUX → carousel slides (Instagram)
    └─ audio_gen.py  → ElevenLabs → voiceover MP3 (optional overlay)

Layer 3: PROCESSING
  raw assets
    ├─ video_editor.py  → FFmpeg → captions, resize, format conversion
    └─ media_host.py    → Cloudinary → upload, get stable HTTPS URLs

Layer 4: PUBLISHING
  Cloudinary URLs + generated text
    ├─ youtube_pub.py   → YouTube Data API v3
    ├─ linkedin_pub.py  → LinkedIn UGC Posts API
    ├─ instagram_pub.py → Instagram Graph API (carousel/reel)
    ├─ tiktok_pub.py    → TikTok Content Posting API v2
    ├─ twitter_pub.py   → X API v2 (thread)
    └─ substack_pub.py  → Substack or Ghost Admin API

TRACKING (cross-cutting)
  Supabase → content_log table (day, platform, url, published_at)
```

---

## 3. Data Flow Diagram

```
Notion DB ──► get_daily_brief(day) ──► brief: dict
                                            │
                    ┌───────────────────────┤
                    │                       │
              text_gen                video_gen / image_gen
                    │                       │
              content: dict           raw_assets: list[path]
                    │                       │
                    └──────────┬────────────┘
                               │
                        media_host.py
                               │ (Cloudinary upload)
                               │
                        assets: dict (secure_url values)
                               │
                    ┌──────────┴──────────┐
                    │                     │
             dry_run=True          dry_run=False
                    │                     │
              return results      publisher_map[platform].publish(
                                      assets, content, brief
                                  ) → {"url": ..., ...}
                                         │
                                   Supabase log
```

---

## 4. Module Responsibilities

| Module | Responsibility |
|---|---|
| `pipeline/orchestrator.py` | Entry point. Orchestrates all layers for a given day number. |
| `pipeline/content_brief.py` | Queries Notion by day number. Returns normalized brief dict. Falls back to stub when Notion is unconfigured. |
| `pipeline/generators/text_gen.py` | Loads prompt templates, calls Claude API, returns per-platform text strings. |
| `pipeline/generators/video_gen.py` | Submits video job to HeyGen, polls for completion. Also wraps Higgsfield for B-roll. |
| `pipeline/generators/image_gen.py` | Calls HuggingFace Inference API (FLUX) to generate carousel slide images. Saves locally. |
| `pipeline/generators/audio_gen.py` | Calls ElevenLabs text-to-speech. Saves MP3 locally. |
| `pipeline/processors/video_editor.py` | FFmpeg wrapper: add captions, resize for platform aspect ratios, concatenate B-roll. |
| `pipeline/processors/media_host.py` | Uploads local files and remote video URLs to Cloudinary. Returns secure_url values. |
| `pipeline/publishers/youtube_pub.py` | Reference publisher. Uploads via resumable upload, sets snippet+status metadata. |
| `pipeline/publishers/linkedin_pub.py` | Posts via UGC Posts API. Reads access token from env. |
| `pipeline/publishers/instagram_pub.py` | Creates carousel containers, then publishes via Graph API. |
| `pipeline/publishers/tiktok_pub.py` | Initiates video publish via PULL_FROM_URL. Handles token refresh. |
| `pipeline/publishers/twitter_pub.py` | Parses thread format (Tweet N: lines) and posts as a reply chain. |
| `pipeline/publishers/substack_pub.py` | Creates draft via Substack API or Ghost Admin API (auto-detected by env). |
| `pipeline/auth/setup.py` | CLI tool for browser-based OAuth flows: YouTube (InstalledAppFlow), LinkedIn (code exchange), TikTok (PKCE). |

---

## 5. Publisher Interface Contract

Every publisher module must expose exactly one public function:

```python
def publish(assets: dict, content: dict, brief: dict) -> dict:
    ...
```

### Input types

**`assets`** — Cloudinary URLs after `upload_all_assets()`:
```python
{
    "video_url": "https://res.cloudinary.com/.../video.mp4",   # optional
    "carousel_urls": ["https://res.cloudinary.com/.../slide_01.png", ...],  # optional
}
```

**`content`** — Generated text keyed by `{platform_lower}_content`:
```python
{
    "linkedin_content": "...",
    "youtube_content": "...",
    "instagram_content": "...",
    "tiktok_content": "...",
    "x_content": "...",
    "substack_content": "...",
}
```

**`brief`** — The normalized daily brief from `get_daily_brief()`:
```python
{
    "day": 1,
    "topic": "...",
    "theme": "...",
    "platforms": ["LinkedIn", "YouTube", ...],
    "notes": "...",
    "notion_page_id": "...",
}
```

### Return type

Always return a dict with at minimum one of:
- `{"url": "https://...", ...}` — successful publish with public URL
- `{"skipped": True, "reason": "..."}` — graceful skip (missing asset, etc.)
- `{"error": "..."}` — caught error (orchestrator handles this)

---

## 6. Configuration System

### Environment Variables

All credentials and configuration values are loaded from `.env` via `python-dotenv`. See `.env.example` for the full list grouped by service. No values are ever hardcoded or committed.

### `config/platforms.yaml`

Defines per-platform format constraints (dimensions, duration, word count, tone, cadence). Loaded by generators and publishers to enforce platform-native specs without hardcoding them in Python.

### `config/prompts/` — Prompt Templates

Markdown files with Python `.format()` placeholders (`{day}`, `{topic}`, `{core_insight}`, etc.). The `text_gen.py` module loads the appropriate template, substitutes brief fields, and sends the result to Claude. This makes prompt editing a content operation, not a code change.

### Token Files

OAuth tokens are stored in `credentials/*.json` (gitignored). The auth setup CLI (`pipeline/auth/setup.py`) writes these on first run. The TikTok publisher auto-refreshes expired tokens using the stored refresh token.

---

## 7. Error Handling and Retry Strategy

The orchestrator wraps each publisher call in a `try/except`:

```python
try:
    results[platform] = publisher_map[platform].publish(assets, content, brief)
except Exception as e:
    log.error(f"Failed to publish to {platform}: {e}")
    results[platform] = {"error": str(e)}
```

This ensures one platform failure does not block others. The full `results` dict is returned regardless.

**Long-polling** (HeyGen, Higgsfield) uses a `while time.time() - start < timeout` loop with `time.sleep()` intervals. Raises `TimeoutError` if the job does not complete within the configured window (600s for HeyGen, 300s for Higgsfield).

**Recommended additions** for production:
- `tenacity` library for exponential backoff on API calls
- Dead-letter queue (Supabase table) for failed publish attempts
- Scheduled retry job for `{"error": ...}` rows in `content_log`

---

## 8. Logging and Observability

Logging is configured in `orchestrator.py` at startup:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),         # stdout
        logging.FileHandler("logs/pipeline.log"),  # rotating file
    ],
)
```

Each module gets its own named logger via `logging.getLogger(__name__)`.

**Supabase `content_log` table** (expected schema):
```sql
CREATE TABLE content_log (
    id          BIGSERIAL PRIMARY KEY,
    day         INTEGER NOT NULL,
    platform    TEXT NOT NULL,
    url         TEXT,
    status      TEXT,   -- 'published', 'skipped', 'error'
    detail      JSONB,
    published_at TIMESTAMPTZ DEFAULT NOW()
);
```

The orchestrator should write a row per platform per day run after each `publish()` call.

---

## 9. Security Model

| Rule | Enforcement |
|---|---|
| No secrets in source code | All keys via `os.getenv()` / `os.environ[]` — hardcoded values raise a code review failure |
| `.env` never committed | `.gitignore` includes `.env` |
| OAuth tokens never committed | `.gitignore` includes `credentials/*.json` and `credentials/*.pickle` |
| `credentials/` directory | Contains only `.gitkeep` in the repo; tokens written at runtime |
| Output files ignored | `output/` is gitignored — generated media never committed |
| Cloudinary upload | All assets uploaded to Cloudinary before passing URLs to social APIs — no direct local file path exposure |
| Minimal OAuth scopes | Each platform's auth setup requests only the scopes needed (e.g., `youtube.upload`, `w_member_social`) |

---

## 10. Dependencies and Versions

| Package | Version | Purpose |
|---|---|---|
| `anthropic` | >=0.25.0 | Claude API client |
| `python-dotenv` | >=1.0.0 | Load .env at startup |
| `requests` | >=2.31.0 | HTTP client (HeyGen, ElevenLabs, TikTok, LinkedIn, Instagram) |
| `pyyaml` | >=6.0 | Load platforms.yaml |
| `notion-client` | >=2.2.0 | Notion API for content calendar |
| `google-api-python-client` | >=2.100.0 | YouTube Data API v3 |
| `google-auth-httplib2` | >=0.1.1 | HTTP transport for Google auth |
| `google-auth-oauthlib` | >=1.1.0 | OAuth flow for YouTube |
| `tweepy` | >=4.14.0 | X API v2 thread posting |
| `cloudinary` | >=1.36.0 | Asset upload and URL generation |
| `elevenlabs` | >=0.2.27 | Text-to-speech voiceover |
| `huggingface-hub` | >=0.20.0 | FLUX image generation inference |
| `Pillow` | >=10.0.0 | Image file handling |
| `supabase` | >=2.0.0 | Logging to content_log table |
| `python-slugify` | >=8.0.1 | Safe filenames for generated assets |
| `click` | >=8.1.7 | CLI tooling |
| `httpx` | >=0.25.0 | Async HTTP (reserved for future use) |
| `tqdm` | >=4.66.0 | Progress bars for batch operations |
| `PyJWT` | >=2.8.0 | Ghost Admin API JWT signing |

Runtime requirements: Python 3.11+, FFmpeg installed and on PATH.
