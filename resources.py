"""Resolve bundled data paths (dev tree vs PyInstaller _MEIPASS)."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

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
