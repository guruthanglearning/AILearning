"""Tests for PolygonWsManager: subscribe, unsubscribe, _send_raw, _dispatch.
No real WebSocket connection required."""
from __future__ import annotations

import json

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.polygon_ws import PolygonWsManager, get_ws_manager, init_ws_manager


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


def test_init_and_get_ws_manager():
    mgr = init_ws_manager("test-key")
    assert get_ws_manager() is mgr
    assert isinstance(mgr, PolygonWsManager)


# ---------------------------------------------------------------------------
# subscribe
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscribe_adds_client_and_starts_runner():
    mgr = PolygonWsManager("fake-key")
    mgr._ensure_running = AsyncMock()
    client = AsyncMock()
    await mgr.subscribe("AAPL", client)
    assert client in mgr._subs["AAPL"]
    mgr._ensure_running.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_sends_upstream_subscription_when_ws_ready():
    mgr = PolygonWsManager("fake-key")
    mgr._ensure_running = AsyncMock()
    mock_ws = AsyncMock()
    mgr._ws = mock_ws
    client = AsyncMock()
    await mgr.subscribe("AAPL", client)
    mock_ws.send.assert_awaited_once()
    sent = json.loads(mock_ws.send.call_args[0][0])
    assert sent["action"] == "subscribe"
    assert "A.AAPL" in sent["params"]


@pytest.mark.asyncio
async def test_subscribe_second_client_does_not_resend_upstream():
    """Second subscriber for the same symbol must not send another upstream subscribe."""
    mgr = PolygonWsManager("fake-key")
    mgr._ensure_running = AsyncMock()
    mock_ws = AsyncMock()
    mgr._ws = mock_ws
    c1, c2 = AsyncMock(), AsyncMock()
    mgr._subs["AAPL"].add(c1)  # symbol already known
    await mgr.subscribe("AAPL", c2)
    mock_ws.send.assert_not_awaited()


# ---------------------------------------------------------------------------
# unsubscribe
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unsubscribe_removes_client_and_cleans_key():
    mgr = PolygonWsManager("fake-key")
    client = AsyncMock()
    mgr._subs["AAPL"].add(client)
    await mgr.unsubscribe("AAPL", client)
    assert "AAPL" not in mgr._subs


@pytest.mark.asyncio
async def test_unsubscribe_sends_upstream_when_last_client():
    mgr = PolygonWsManager("fake-key")
    mock_ws = AsyncMock()
    mgr._ws = mock_ws
    client = AsyncMock()
    mgr._subs["AAPL"].add(client)
    await mgr.unsubscribe("AAPL", client)
    mock_ws.send.assert_awaited_once()
    sent = json.loads(mock_ws.send.call_args[0][0])
    assert sent["action"] == "unsubscribe"
    assert "A.AAPL" in sent["params"]


@pytest.mark.asyncio
async def test_unsubscribe_with_remaining_clients_no_upstream_send():
    mgr = PolygonWsManager("fake-key")
    mock_ws = AsyncMock()
    mgr._ws = mock_ws
    c1, c2 = AsyncMock(), AsyncMock()
    mgr._subs["AAPL"].update({c1, c2})
    await mgr.unsubscribe("AAPL", c1)
    mock_ws.send.assert_not_awaited()
    assert c2 in mgr._subs["AAPL"]


# ---------------------------------------------------------------------------
# _send_raw
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_raw_sends_json_when_ws_ready():
    mgr = PolygonWsManager("fake-key")
    mock_ws = AsyncMock()
    mgr._ws = mock_ws
    await mgr._send_raw({"action": "subscribe", "params": "A.AAPL"})
    mock_ws.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_raw_no_op_when_ws_is_none():
    mgr = PolygonWsManager("fake-key")
    # _ws defaults to None — must not raise
    await mgr._send_raw({"action": "subscribe", "params": "A.AAPL"})


@pytest.mark.asyncio
async def test_send_raw_suppresses_send_exception():
    mgr = PolygonWsManager("fake-key")
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock(side_effect=RuntimeError("connection closed"))
    mgr._ws = mock_ws
    await mgr._send_raw({"action": "ping"})  # must not raise


# ---------------------------------------------------------------------------
# _dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_bad_json_does_not_raise():
    mgr = PolygonWsManager("fake-key")
    await mgr._dispatch("not-valid-json")


@pytest.mark.asyncio
async def test_dispatch_status_message_does_not_fan_out(monkeypatch):
    import app.polygon_ws as ws_module
    monkeypatch.setattr(ws_module, "log", MagicMock())
    mgr = PolygonWsManager("fake-key")
    client = AsyncMock()
    mgr._subs["AAPL"].add(client)
    await mgr._dispatch('[{"ev":"status","status":"connected","message":"OK"}]')
    client.send_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_dispatch_price_event_sends_payload_to_subscriber():
    mgr = PolygonWsManager("fake-key")
    client = AsyncMock()
    mgr._subs["AAPL"].add(client)
    event = json.dumps([{
        "ev": "A", "sym": "AAPL",
        "c": 150.0, "o": 149.0, "h": 151.0, "l": 148.0,
        "av": 1_000_000, "vw": 150.2, "e": 1_700_000_000_000,
    }])
    await mgr._dispatch(event)
    client.send_text.assert_awaited_once()
    payload = json.loads(client.send_text.call_args[0][0])
    assert payload["type"] == "price"
    assert payload["symbol"] == "AAPL"
    assert payload["price"] == pytest.approx(150.0)


@pytest.mark.asyncio
async def test_dispatch_price_event_no_subscribers_is_noop():
    mgr = PolygonWsManager("fake-key")
    event = json.dumps([{"ev": "A", "sym": "TSLA", "c": 200.0}])
    await mgr._dispatch(event)  # must not raise


@pytest.mark.asyncio
async def test_dispatch_dead_client_removed_from_subs():
    mgr = PolygonWsManager("fake-key")
    dead = AsyncMock()
    dead.send_text = AsyncMock(side_effect=RuntimeError("disconnected"))
    mgr._subs["AAPL"].add(dead)
    event = json.dumps([{"ev": "A", "sym": "AAPL", "c": 150.0}])
    await mgr._dispatch(event)
    assert dead not in mgr._subs.get("AAPL", set())


@pytest.mark.asyncio
async def test_dispatch_unknown_event_type_ignored():
    mgr = PolygonWsManager("fake-key")
    client = AsyncMock()
    mgr._subs["AAPL"].add(client)
    event = json.dumps([{"ev": "XT", "sym": "AAPL", "data": 42}])
    await mgr._dispatch(event)
    client.send_text.assert_not_awaited()
