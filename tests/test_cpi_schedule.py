"""CPI schedule helpers (no AppKit)."""

from datetime import date

from resources import upcoming_cpi_lines


def test_upcoming_cpi_filters_and_orders():
    doc = {
        "releases": [
            {"date": "2026-05-20", "label": "B"},
            {"date": "2026-05-14", "label": "A"},
            {"date": "2026-05-10", "label": "Past"},
        ]
    }
    ref = date(2026, 5, 14)
    lines = upcoming_cpi_lines(doc, ref, limit=10)
    assert lines[0].startswith("A")
    assert lines[1].startswith("B")
    assert len(lines) == 2


def test_upcoming_cpi_respects_limit():
    doc = {
        "releases": [
            {"date": "2026-05-14", "label": "1"},
            {"date": "2026-05-15", "label": "2"},
            {"date": "2026-05-16", "label": "3"},
        ]
    }
    lines = upcoming_cpi_lines(doc, date(2026, 5, 14), limit=2)
    assert len(lines) == 2
