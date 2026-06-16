# CLAUDE.md

## Project Purpose
Python pipeline that generates and publishes a 30-day social media content series about "The New SDLC With Vibe Coding: From Ad-hoc Prompting to Agentic Engineering."

## Pipeline Commands
- Run single day: `python -m pipeline.orchestrator --day N`
- Dry run (generate, no publish): `python -m pipeline.orchestrator --day N --dry-run`
- OAuth setup: `python -m pipeline.auth.setup --platform [youtube|linkedin|tiktok]`
- Test single publisher: `python -m pipeline.publishers.linkedin_pub --test`

## Architecture
Content Calendar (Notion) → Text Generation (Claude API) → Visual Generation (HeyGen/FLUX/Canva) → Processing (FFmpeg/Cloudinary) → Publishing (Platform APIs)

## Rules
- Load all keys from .env via python-dotenv. Never hardcode credentials.
- Cloudinary is the media host for all assets. Always upload before passing URLs to social APIs.
- When adding a new publisher, follow the interface pattern in publishers/youtube_pub.py.
- All publishers must implement: `publish(assets: dict, content: dict, brief: dict) -> dict`
- Log all published URLs to Supabase content_log table.

## Key Files
- config/platforms.yaml — format specs per platform
- config/prompts/ — Claude prompt templates per platform
- credentials/ — OAuth tokens (gitignored, never commit)
- .env — all API keys (gitignored, never commit)
