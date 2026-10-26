"""Priced input-token equivalents ("eq"). One eq = one fresh input token.

Anthropic prompt caching bills cache writes at 1.25x (5-minute TTL) or 2x
(1-hour TTL) the input price, and cache reads at 0.1x. Dollars are left to
the caller (--usd-per-mtok) because prices and plans change.
"""

from __future__ import annotations

from .model import ModelCall

W_INPUT = 1.0
W_CACHE_WRITE_5M = 1.25
W_CACHE_WRITE_1H = 2.0
W_CACHE_READ = 0.1

TTL_5M = 300
TTL_1H = 3600


def priced_input(call: ModelCall) -> float:
    return (call.input * W_INPUT + call.cache_write_5m * W_CACHE_WRITE_5M
            + call.cache_write_1h * W_CACHE_WRITE_1H + call.cache_read * W_CACHE_READ)
