"""Auth, watchlist, alert offline tests — no DB, no network."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.auth import generate_key, hash_key
from app.schemas.user import (
    AlertCondition,
    AlertCreate,
    WatchlistCreate,
)


# ---------------------------------------------------------------------------
# API key generation
# ---------------------------------------------------------------------------


def test_generate_key_format():
    raw, prefix, digest = generate_key()
    assert raw.startswith("sk-")
    assert len(raw) == 43          # "sk-" + 40 hex chars
    assert prefix == raw[:8]
    assert len(digest) == 64       # SHA-256 hex
    assert all(c in "0123456789abcdef" for c in digest)


def test_hash_key_deterministic():
    raw = "sk-" + "a" * 40
    assert hash_key(raw) == hash_key(raw)


def test_generate_key_unique():
    keys = {generate_key()[0] for _ in range(10)}
    assert len(keys) == 10


# ---------------------------------------------------------------------------
# Alert schema validation
# ---------------------------------------------------------------------------


def test_alert_create_price_above_requires_threshold():
    with pytest.raises(ValidationError, match="threshold_value"):
        AlertCreate(symbol="AAPL", condition=AlertCondition.price_above)


def test_alert_create_price_below_requires_threshold():
    with pytest.raises(ValidationError, match="threshold_value"):
        AlertCreate(symbol="AAPL", condition=AlertCondition.price_below)


def test_alert_create_verdict_requires_threshold_verdict():
    with pytest.raises(ValidationError, match="threshold_verdict"):
        AlertCreate(symbol="AAPL", condition=AlertCondition.verdict_changes_to)


def test_alert_create_price_valid():
    a = AlertCreate(symbol="AAPL", condition=AlertCondition.price_above, threshold_value=200.0)
    assert a.threshold_value == 200.0
    assert a.symbol == "AAPL"


def test_alert_create_verdict_valid():
    a = AlertCreate(symbol="TSLA", condition=AlertCondition.verdict_changes_to, threshold_verdict="options")
    assert a.threshold_verdict == "options"


def test_alert_condition_enum_values():
    assert set(AlertCondition) == {
        AlertCondition.price_above,
        AlertCondition.price_below,
        AlertCondition.verdict_changes_to,
    }


# ---------------------------------------------------------------------------
# Watchlist schema
# ---------------------------------------------------------------------------


def test_watchlist_create_name_required():
    with pytest.raises(ValidationError):
        WatchlistCreate()


def test_watchlist_create_description_optional():
    wl = WatchlistCreate(name="earnings plays")
    assert wl.name == "earnings plays"
    assert wl.description is None
