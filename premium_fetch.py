"""Coinbase vs Binance spot premium (no AppKit — safe for unit tests)."""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 5

COINBASE_TICKER = "https://api.exchange.coinbase.com/products/{pair}/ticker"
BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/price?symbol={symbol}"


def fetch_premium(
    coin: str, session: requests.Session
) -> tuple[float | None, float, float]:
    """Return (Coinbase price, premium amount vs Binance, premium %)."""
    pair_cb = f"{coin}-USD"
    symbol_bn = f"{coin}USDT"
    try:
        cb_res = session.get(
            COINBASE_TICKER.format(pair=pair_cb), timeout=REQUEST_TIMEOUT
        )
        cb_res.raise_for_status()
        price_cb = float(cb_res.json()["price"])

        bn_res = session.get(
            BINANCE_TICKER.format(symbol=symbol_bn), timeout=REQUEST_TIMEOUT
        )
        bn_res.raise_for_status()
        price_bn = float(bn_res.json()["price"])

        premium_amount = price_cb - price_bn
        premium_pct = (premium_amount / price_bn) * 100
        return price_cb, premium_amount, premium_pct
    except (requests.RequestException, KeyError, ValueError) as e:
        logger.debug("Premium fetch failed for %s: %s", coin, e)
        return None, 0.0, 0.0
