"""
Polygon.io WebSocket relay.

Maintains a single upstream connection to socket.polygon.io and fans out
per-second aggregate (A.*) events to every browser WebSocket that has
subscribed to that symbol.

Usage
-----
  from app.polygon_ws import init_ws_manager, get_ws_manager

  # In app lifespan (startup):
  init_ws_manager(settings.polygon_api_key)

  # In a FastAPI WebSocket endpoint:
  manager = get_ws_manager()
  await manager.subscribe("AAPL", websocket)
  try:
      while True:
          await websocket.receive_text()   # keep alive
  except WebSocketDisconnect:
      pass
  finally:
      await manager.unsubscribe("AAPL", websocket)
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import WebSocket

log = logging.getLogger(__name__)

_RECONNECT_DELAY_S = 5


class PolygonWsManager:
    def __init__(self, api_key: str, realtime: bool = False) -> None:
        self._api_key = api_key
        self._realtime = realtime
        self._subs: dict[str, set[WebSocket]] = defaultdict(set)
        self._ws = None
        self._lock = asyncio.Lock()
        self._runner: asyncio.Task | None = None
        self._ws_status: str = "offline"
        self._ws_status_code: str = "offline"

    # ------------------------------------------------------------------
    # Mode management
    # ------------------------------------------------------------------

    @property
    def realtime(self) -> bool:
        return self._realtime

    @property
    def ws_status(self) -> str:
        return self._ws_status

    @property
    def ws_status_code(self) -> str:
        return self._ws_status_code

    @property
    def ws_connected(self) -> bool:
        return self._ws_status_code in ("auth_success", "success")

    def ws_url(self) -> str:
        return (
            "wss://socket.polygon.io/stocks" if self._realtime
            else "wss://delayed.polygon.io/stocks"
        )

    async def set_mode(self, realtime: bool) -> None:
        """Switch between real-time and 15-min-delayed feed at runtime.

        Updates the URL flag then closes the current upstream connection so
        the reconnect loop re-opens it against the new endpoint.
        """
        self._realtime = realtime
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def subscribe(self, symbol: str, client: WebSocket) -> None:
        """Register *client* to receive price updates for *symbol*."""
        async with self._lock:
            is_new = symbol not in self._subs or not self._subs[symbol]
            self._subs[symbol].add(client)
            await self._ensure_running()
            if is_new and self._ws is not None:
                await self._send_raw({"action": "subscribe", "params": f"A.{symbol}"})

    async def unsubscribe(self, symbol: str, client: WebSocket) -> None:
        """Remove *client*; unsubscribe upstream when last client for *symbol* disconnects."""
        async with self._lock:
            self._subs[symbol].discard(client)
            if not self._subs[symbol]:
                if symbol in self._subs:
                    del self._subs[symbol]
                if self._ws is not None:
                    await self._send_raw({"action": "unsubscribe", "params": f"A.{symbol}"})

    # ------------------------------------------------------------------
    # Internal machinery
    # ------------------------------------------------------------------

    async def _ensure_running(self) -> None:
        if self._runner is None or self._runner.done():
            self._runner = asyncio.create_task(self._run())

    async def _send_raw(self, msg: dict) -> None:
        try:
            if self._ws is not None:
                await self._ws.send(json.dumps(msg))
        except Exception:
            pass

    async def _run(self) -> None:
        """Connect → auth → subscribe active symbols → relay messages.  Reconnects on failure."""
        import websockets

        while True:
            try:
                async with websockets.connect(self.ws_url()) as ws:
                    self._ws = ws
                    log.info("polygon_ws_connected url=%s", self.ws_url())

                    await ws.send(json.dumps({"action": "auth", "params": self._api_key}))

                    # Re-subscribe any symbols that were active before reconnect
                    async with self._lock:
                        for sym in list(self._subs):
                            if self._subs[sym]:
                                await ws.send(
                                    json.dumps({"action": "subscribe", "params": f"A.{sym}"})
                                )

                    async for raw in ws:
                        await self._dispatch(raw)

            except Exception as exc:
                log.warning("polygon_ws_disconnected: %s", exc)
                self._ws = None
                self._ws_status = "disconnected"
                self._ws_status_code = "disconnected"

            await asyncio.sleep(_RECONNECT_DELAY_S)

    async def _dispatch(self, raw: str) -> None:
        """Parse one Polygon message and push price updates to subscribed clients."""
        try:
            events = json.loads(raw)
        except Exception:
            return

        for ev in events:
            ev_type = ev.get("ev", "")
            sym     = ev.get("sym", "")

            if ev_type == "status":
                msg  = ev.get("message", "")
                code = ev.get("status", "")
                self._ws_status      = msg
                self._ws_status_code = code
                log.info("polygon_ws_status: %s (%s)", msg, code)
                if code == "auth_failed" and self._realtime:
                    log.warning("polygon_ws: real-time auth failed — plan doesn't include socket.polygon.io; reverting to 15-min delayed feed")
                    self._realtime       = False
                    self._ws_status_code = "auth_failed_reverted"
                    if self._ws is not None:
                        try:
                            await self._ws.close()
                        except Exception:
                            pass
                continue

            if ev_type == "A" and sym:
                payload = json.dumps({
                    "type":   "price",
                    "symbol": sym,
                    "price":  ev.get("c"),     # close of the 1-second aggregate
                    "open":   ev.get("o"),
                    "high":   ev.get("h"),
                    "low":    ev.get("l"),
                    "volume": ev.get("av"),    # accumulated day volume
                    "vwap":   ev.get("vw"),
                    "ts":     ev.get("e"),     # end of window timestamp (ms)
                })
                dead: list[tuple[str, WebSocket]] = []
                for client in list(self._subs.get(sym, set())):
                    try:
                        await client.send_text(payload)
                    except Exception:
                        dead.append((sym, client))
                for s, c in dead:
                    self._subs[s].discard(c)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_manager: PolygonWsManager | None = None


def init_ws_manager(api_key: str) -> PolygonWsManager:
    global _manager
    from app.config import settings
    _manager = PolygonWsManager(api_key, realtime=settings.polygon_realtime)
    return _manager


def get_ws_manager() -> PolygonWsManager | None:
    return _manager
