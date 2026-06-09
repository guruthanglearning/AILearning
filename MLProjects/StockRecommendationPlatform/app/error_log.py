from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from threading import Lock
from typing import Any

_MAX_ENTRIES = 500
_lock = Lock()
_buffer: deque[dict[str, Any]] = deque(maxlen=_MAX_ENTRIES)


def record(*, symbol: str, agent: str, status: str, message: str, detail: str | None = None) -> None:
    entry: dict[str, Any] = {
        "ts": datetime.now(tz=UTC).isoformat(),
        "symbol": symbol.upper(),
        "agent": agent,
        "status": status,
        "message": message,
    }
    if detail is not None:
        entry["detail"] = detail
    with _lock:
        _buffer.appendleft(entry)


def get_recent(limit: int = 200) -> list[dict[str, Any]]:
    with _lock:
        return list(_buffer)[:limit]


def clear() -> None:
    with _lock:
        _buffer.clear()
