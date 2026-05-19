"""Tests for alert router logic: _evaluate_alert, _refresh_alerts, and CRUD endpoints."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.routers.alerts import (
    _alert_to_response,
    _evaluate_alert,
    _refresh_alerts,
    create_alert,
    delete_alert,
    list_alerts,
    list_triggered_alerts,
)
from app.schemas.user import AlertCondition, AlertCreate, AlertResponse


def _alert(
    condition: str,
    threshold_value: float | None = None,
    threshold_verdict: str | None = None,
    is_active: bool = True,
    triggered_at: datetime | None = None,
    symbol: str = "AAPL",
) -> MagicMock:
    a = MagicMock()
    a.id = uuid.uuid4()
    a.symbol = symbol
    a.condition = condition
    a.threshold_value = threshold_value
    a.threshold_verdict = threshold_verdict
    a.is_active = is_active
    a.triggered_at = triggered_at
    return a


def _session(last_price: float | None, verdict: str | None) -> AsyncMock:
    mock_result = MagicMock()
    mock_result.first.return_value = (last_price, verdict) if last_price is not None or verdict is not None else None
    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)
    session.commit = AsyncMock()
    return session


def _session_no_run() -> AsyncMock:
    mock_result = MagicMock()
    mock_result.first.return_value = None
    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)
    session.commit = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# _evaluate_alert tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_price_above_triggers_when_price_exceeds_threshold():
    alert = _alert("price_above", threshold_value=140.0)
    session = _session(last_price=150.0, verdict=None)
    assert await _evaluate_alert(alert, session) is True


@pytest.mark.asyncio
async def test_price_above_does_not_trigger_when_price_below():
    alert = _alert("price_above", threshold_value=160.0)
    session = _session(last_price=150.0, verdict=None)
    assert await _evaluate_alert(alert, session) is False


@pytest.mark.asyncio
async def test_price_below_triggers_when_price_below_threshold():
    alert = _alert("price_below", threshold_value=160.0)
    session = _session(last_price=150.0, verdict=None)
    assert await _evaluate_alert(alert, session) is True


@pytest.mark.asyncio
async def test_price_below_does_not_trigger_when_price_above():
    alert = _alert("price_below", threshold_value=140.0)
    session = _session(last_price=150.0, verdict=None)
    assert await _evaluate_alert(alert, session) is False


@pytest.mark.asyncio
async def test_verdict_changes_to_triggers_on_match():
    alert = _alert("verdict_changes_to", threshold_verdict="stock")
    session = _session(last_price=150.0, verdict="stock")
    assert await _evaluate_alert(alert, session) is True


@pytest.mark.asyncio
async def test_verdict_changes_to_no_trigger_on_mismatch():
    alert = _alert("verdict_changes_to", threshold_verdict="stock")
    session = _session(last_price=150.0, verdict="options")
    assert await _evaluate_alert(alert, session) is False


@pytest.mark.asyncio
async def test_evaluate_returns_false_when_no_analysis_run_exists():
    alert = _alert("price_above", threshold_value=100.0)
    session = _session_no_run()
    assert await _evaluate_alert(alert, session) is False


# ---------------------------------------------------------------------------
# _refresh_alerts tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_sets_triggered_at_on_matching_alert():
    alert = _alert("price_above", threshold_value=140.0, is_active=True)
    session = _session(last_price=150.0, verdict=None)
    await _refresh_alerts([alert], session)
    assert alert.triggered_at is not None
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_skips_already_triggered_alert():
    already = datetime(2025, 1, 1, tzinfo=UTC)
    alert = _alert("price_above", threshold_value=140.0, is_active=True, triggered_at=already)
    session = _session(last_price=150.0, verdict=None)
    await _refresh_alerts([alert], session)
    # triggered_at must not change
    assert alert.triggered_at == already


@pytest.mark.asyncio
async def test_refresh_skips_inactive_alert():
    alert = _alert("price_above", threshold_value=140.0, is_active=False)
    session = _session(last_price=150.0, verdict=None)
    await _refresh_alerts([alert], session)
    assert alert.triggered_at is None


@pytest.mark.asyncio
async def test_evaluate_unknown_condition_returns_false():
    alert = _alert("unknown_condition", threshold_value=100.0)
    session = _session(last_price=150.0, verdict="stock")
    assert await _evaluate_alert(alert, session) is False


# ---------------------------------------------------------------------------
# _alert_to_response helper
# ---------------------------------------------------------------------------


def test_alert_to_response_price_above():
    row = _alert("price_above", threshold_value=150.0)
    row.id = uuid.uuid4()
    row.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    resp = _alert_to_response(row)
    assert resp.symbol == "AAPL"
    assert resp.condition == AlertCondition.price_above
    assert resp.threshold_value == 150.0


def test_alert_to_response_verdict():
    row = _alert("verdict_changes_to", threshold_verdict="stock")
    row.id = uuid.uuid4()
    row.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    resp = _alert_to_response(row)
    assert resp.condition == AlertCondition.verdict_changes_to
    assert resp.threshold_verdict == "stock"


# ---------------------------------------------------------------------------
# Alert CRUD router functions (direct call, no HTTP layer)
# ---------------------------------------------------------------------------


def _orm_alert(symbol: str = "AAPL", condition: str = "price_above", threshold_value: float = 150.0) -> MagicMock:
    row = MagicMock()
    row.id = uuid.uuid4()
    row.symbol = symbol
    row.condition = condition
    row.threshold_value = threshold_value
    row.threshold_verdict = None
    row.is_active = True
    row.triggered_at = None
    row.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    row.api_key_id = uuid.uuid4()
    return row


@pytest.mark.asyncio
async def test_list_alerts_returns_alerts():
    key = MagicMock()
    key.id = uuid.uuid4()
    row = _orm_alert()

    # session.execute for list query returns rows
    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = [row]

    # session.execute for _evaluate_alert returns no run
    eval_result = MagicMock()
    eval_result.first.return_value = None

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=[list_result, eval_result])
    session.commit = AsyncMock()

    result = await list_alerts(current_key=key, session=session)
    assert len(result) == 1
    assert result[0].symbol == "AAPL"


@pytest.mark.asyncio
async def test_list_triggered_alerts_returns_triggered():
    key = MagicMock()
    key.id = uuid.uuid4()
    triggered_at = datetime(2025, 5, 1, tzinfo=UTC)
    row = _orm_alert()
    row.triggered_at = triggered_at

    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = [row]

    eval_result = MagicMock()
    eval_result.first.return_value = None

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=[list_result, eval_result])
    session.commit = AsyncMock()

    result = await list_triggered_alerts(current_key=key, session=session)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_delete_alert_success():
    key = MagicMock()
    key.id = uuid.uuid4()
    row = _orm_alert()
    row.api_key_id = key.id

    session = AsyncMock()
    session.get = AsyncMock(return_value=row)
    session.delete = AsyncMock()
    session.commit = AsyncMock()

    await delete_alert(alert_id=row.id, current_key=key, session=session)
    session.delete.assert_awaited_once_with(row)


@pytest.mark.asyncio
async def test_delete_alert_not_found():
    key = MagicMock()
    key.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await delete_alert(alert_id=uuid.uuid4(), current_key=key, session=session)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_alert_endpoint():
    from datetime import datetime

    key = MagicMock()
    key.id = uuid.uuid4()

    req = AlertCreate(
        symbol="AAPL",
        condition=AlertCondition.price_above,
        threshold_value=150.0,
    )

    async def _refresh(row):
        row.id = uuid.uuid4()
        row.is_active = True
        row.triggered_at = None
        row.created_at = datetime(2025, 1, 1, tzinfo=UTC)

    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock(side_effect=_refresh)

    result = await create_alert(req=req, current_key=key, session=session)
    assert isinstance(result, AlertResponse)
    assert result.symbol == "AAPL"
    assert result.condition == AlertCondition.price_above
