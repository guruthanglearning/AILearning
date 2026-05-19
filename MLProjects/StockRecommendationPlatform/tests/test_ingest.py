"""Tests for app/ingest.py — warm_cache and _warm_one."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ingest import warm_cache
from app.providers.base import MarketDataProvider, ProviderError


def _mock_provider(quote_effect=None, chain_effect=None) -> MagicMock:
    prov = MagicMock(spec=MarketDataProvider)
    prov.get_quote = AsyncMock(side_effect=quote_effect) if quote_effect else AsyncMock(return_value={"last_price": 100.0, "source": "mock"})
    prov.get_option_chain = AsyncMock(side_effect=chain_effect) if chain_effect else AsyncMock(return_value={"expiries": [], "source": "mock"})
    return prov


@pytest.mark.asyncio
async def test_warm_cache_calls_quote_and_chain():
    prov = _mock_provider()
    await warm_cache(["AAPL", "MSFT"], prov)
    assert prov.get_quote.call_count == 2
    assert prov.get_option_chain.call_count == 2


@pytest.mark.asyncio
async def test_warm_cache_empty_list():
    prov = _mock_provider()
    await warm_cache([], prov)
    prov.get_quote.assert_not_called()


@pytest.mark.asyncio
async def test_warm_cache_continues_on_provider_error():
    prov = _mock_provider(quote_effect=ProviderError("rate limited"))
    await warm_cache(["AAPL", "MSFT"], prov)
    # Should not raise; provider errors are swallowed


@pytest.mark.asyncio
async def test_warm_cache_continues_on_unexpected_exception():
    prov = _mock_provider(chain_effect=RuntimeError("unexpected"))
    await warm_cache(["AAPL"], prov)
    # Should not raise


@pytest.mark.asyncio
async def test_warm_cache_single_symbol():
    prov = _mock_provider()
    await warm_cache(["AAPL"], prov)
    prov.get_quote.assert_awaited_once_with("AAPL")
    prov.get_option_chain.assert_awaited_once_with("AAPL")
