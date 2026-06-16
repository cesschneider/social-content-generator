"""
Reads the Notion content calendar and returns a structured brief for a given day.
Falls back to a local YAML/JSON brief if Notion is not configured.
"""
import os
import logging
from notion_client import Client

log = logging.getLogger(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_CALENDAR_DATABASE_ID")


def get_daily_brief(day_number: int) -> dict:
    if NOTION_API_KEY and NOTION_DATABASE_ID:
        return _fetch_from_notion(day_number)
    log.warning("Notion not configured — returning stub brief for day %d", day_number)
    return _stub_brief(day_number)


def _fetch_from_notion(day_number: int) -> dict:
    notion = Client(auth=NOTION_API_KEY)
    results = notion.databases.query(
        database_id=NOTION_DATABASE_ID,
        filter={
            "property": "Day",
            "number": {"equals": day_number},
        },
    ).get("results", [])

    if not results:
        raise ValueError(f"No Notion entry found for day {day_number}")

    page = results[0]
    props = page["properties"]

    def text(prop_name: str) -> str:
        prop = props.get(prop_name, {})
        rich = prop.get("rich_text") or prop.get("title") or []
        return "".join(t["plain_text"] for t in rich)

    def multi(prop_name: str) -> list[str]:
        return [o["name"] for o in props.get(prop_name, {}).get("multi_select", [])]

    return {
        "day": day_number,
        "topic": text("Topic"),
        "theme": text("Theme"),
        "platforms": multi("Platform"),
        "notes": text("Notes"),
        "notion_page_id": page["id"],
    }


def _stub_brief(day_number: int) -> dict:
    """Minimal stub for development without Notion."""
    return {
        "day": day_number,
        "topic": f"Day {day_number} — Placeholder Topic",
        "theme": "The New SDLC",
        "platforms": ["LinkedIn", "X", "Instagram", "TikTok"],
        "notes": "",
        "notion_page_id": None,
    }
