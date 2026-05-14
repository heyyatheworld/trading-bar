"""Resolve bundled data paths (dev tree vs PyInstaller _MEIPASS)."""

from __future__ import annotations

import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

DEFAULT_SESSIONS: list[dict] = [
    {
        "id": "HKG",
        "mkt": "HKEX ",
        "type": "MAIN",
        "tz": "Asia/Hong_Kong",
        "open": 9,
        "close": 18,
        "icon": "🏮",
        "venue": "exchange",
    },
    {
        "id": "FRA",
        "mkt": "XETRA",
        "type": "MAIN",
        "tz": "Europe/Berlin",
        "open": 9,
        "close": 17.5,
        "icon": "🇩🇪",
        "venue": "exchange",
    },
    {
        "id": "LDN",
        "mkt": "LSE  ",
        "type": "MAIN",
        "tz": "Europe/London",
        "open": 8,
        "close": 16,
        "icon": "🔵",
        "venue": "exchange",
    },
    {
        "id": "NYC",
        "mkt": "NYSE ",
        "type": "PRE ",
        "tz": "America/New_York",
        "open": 4,
        "close": 9.5,
        "icon": "🌤️",
        "venue": "exchange",
    },
    {
        "id": "NYC",
        "mkt": "NYSE ",
        "type": "MAIN",
        "tz": "America/New_York",
        "open": 9.5,
        "close": 16,
        "icon": "🗽",
        "venue": "exchange",
    },
    {
        "id": "CHI",
        "mkt": "CME  ",
        "type": "CME ",
        "tz": "America/Chicago",
        "open": 17,
        "close": 16,
        "icon": "📊",
        "venue": "cme",
    },
]


def app_data_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "data"
    return Path(__file__).resolve().parent / "data"


def load_sessions() -> list[dict]:
    path = app_data_dir() / "sessions.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("sessions.json must be a JSON array")
        return data
    except (OSError, json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to load sessions.json, using defaults: %s", e)
        return list(DEFAULT_SESSIONS)


def load_cpi_document() -> dict:
    path = app_data_dir() / "cpi_dates.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("cpi_dates.json must be a JSON object")
        return data
    except (OSError, json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to load cpi_dates.json: %s", e)
        return {"releases": []}


def upcoming_cpi_lines(doc: dict, ref_date: date, limit: int = 4) -> list[str]:
    """Human-readable lines for releases on or after ref_date (ISO calendar day)."""
    releases = doc.get("releases", [])
    if not isinstance(releases, list):
        return []
    lines: list[str] = []
    try:
        sorted_r = sorted(
            (r for r in releases if isinstance(r, dict)),
            key=lambda r: str(r.get("date", "")),
        )
    except (TypeError, ValueError):
        return []
    for r in sorted_r:
        ds = r.get("date")
        if not ds:
            continue
        try:
            d = datetime.fromisoformat(str(ds)).date()
        except ValueError:
            continue
        if d < ref_date:
            continue
        label = r.get("label") or str(ds)
        lines.append(f"{label} — {ds} (ET calendar)")
        if len(lines) >= limit:
            break
    return lines


def menu_lines_for_cpi_section() -> list[str]:
    ref = datetime.now(ZoneInfo("America/New_York")).date()
    doc = load_cpi_document()
    lines = upcoming_cpi_lines(doc, ref)
    if not lines:
        return ["No upcoming CPI rows — edit data/cpi_dates.json"]
    return lines
