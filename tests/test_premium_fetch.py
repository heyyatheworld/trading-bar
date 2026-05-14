"""Tests for premium_fetch (no AppKit)."""

from unittest.mock import MagicMock

import pytest
import requests

from premium_fetch import fetch_premium


def test_fetch_premium_success():
    session = MagicMock()

    def fake_get(url, timeout):
        r = MagicMock()
        r.raise_for_status = MagicMock()
        if "coinbase" in url.lower():
            r.json.return_value = {"price": "100000.0"}
        else:
            r.json.return_value = {"price": "99500.0"}
        return r

    session.get.side_effect = fake_get

    price, amount, pct = fetch_premium("BTC", session)
    assert price == 100_000.0
    assert amount == pytest.approx(500.0)
    assert pct == pytest.approx((500.0 / 99500.0) * 100)


def test_fetch_premium_http_error():
    session = MagicMock()
    r = MagicMock()
    r.raise_for_status.side_effect = requests.HTTPError("boom")
    session.get.return_value = r

    price, amount, pct = fetch_premium("BTC", session)
    assert price is None
    assert amount == 0.0
    assert pct == 0.0
