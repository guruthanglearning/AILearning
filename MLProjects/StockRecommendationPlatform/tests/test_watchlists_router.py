"""Watchlists router — direct handler call tests, no DB, no HTTP stack."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.routers.watchlists import (
    add_symbol,
    create_watchlist,
    delete_watchlist,
    list_symbols,
    list_watchlists,
    remove_symbol,
)
from app.schemas.user import WatchlistCreate, WatchlistSymbolAdd

# ── Helpers ───────────────────────────────────────────────────────────────────

def _key():
    k = MagicMock()
    k.id = uuid.uuid4()
    return k


def _wl(name: str = "my-list", owner_id: uuid.UUID | None = None) -> MagicMock:
    w = MagicMock()
    w.id = uuid.uuid4()
    w.name = name
    w.description = None
    w.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    w.api_key_id = owner_id or uuid.uuid4()
    w.symbols = []
    return w


def _sym(symbol: str = "AAPL", note: str | None = None) -> MagicMock:
    s = MagicMock()
    s.symbol = symbol
    s.note = note
    s.added_at = datetime(2025, 1, 1, tzinfo=UTC)
    s.watchlist_id = uuid.uuid4()
    return s


def _session_with_execute(*rows_per_call) -> AsyncMock:
    """Build a mock session whose .execute returns successive result mocks."""
    session = AsyncMock()
    results = []
    for rows in rows_per_call:
        r = MagicMock()
        if isinstance(rows, list):
            r.scalars.return_value.all.return_value = rows
            r.scalar_one_or_none.return_value = rows[0] if rows else None
        else:
            r.scalar_one_or_none.return_value = rows
        results.append(r)
    session.execute = AsyncMock(side_effect=results)
    return session


# ── create_watchlist ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_watchlist_success(monkeypatch):
    key = _key()
    new_wl = _wl("earnings plays", key.id)
    monkeypatch.setattr("app.routers.watchlists.Watchlist", lambda **kw: new_wl)

    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    result = await create_watchlist(req=WatchlistCreate(name="earnings plays"), current_key=key, session=session)
    assert result.name == "earnings plays"
    assert result.symbol_count == 0
    session.commit.assert_awaited_once()


# ── list_watchlists ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_watchlists_empty():
    key = _key()
    session = _session_with_execute([])
    result = await list_watchlists(current_key=key, session=session)
    assert result == []


@pytest.mark.asyncio
async def test_list_watchlists_with_items():
    key = _key()
    wl = _wl("p1", key.id)
    # First execute → watchlist rows; second execute → symbol rows for that watchlist
    session = AsyncMock()
    call_count = 0

    async def _execute(stmt):
        nonlocal call_count
        r = MagicMock()
        if call_count == 0:
            r.scalars.return_value.all.return_value = [wl]
        else:
            r.scalars.return_value.all.return_value = [_sym(), _sym("MSFT")]
        call_count += 1
        return r

    session.execute = _execute
    result = await list_watchlists(current_key=key, session=session)
    assert len(result) == 1
    assert result[0].name == "p1"
    assert result[0].symbol_count == 2


# ── delete_watchlist ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_watchlist_success():
    key = _key()
    wl = _wl(owner_id=key.id)
    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)
    session.delete = AsyncMock()
    session.commit = AsyncMock()

    await delete_watchlist(wid=wl.id, current_key=key, session=session)
    session.delete.assert_awaited_once_with(wl)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_watchlist_not_found_raises_404():
    from fastapi import HTTPException
    key = _key()
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await delete_watchlist(wid=uuid.uuid4(), current_key=key, session=session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_watchlist_wrong_owner_raises_404():
    from fastapi import HTTPException
    key = _key()
    wl = _wl(owner_id=uuid.uuid4())  # different owner
    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)

    with pytest.raises(HTTPException) as exc:
        await delete_watchlist(wid=wl.id, current_key=key, session=session)
    assert exc.value.status_code == 404


# ── add_symbol ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_symbol_success():

    key = _key()
    wl = _wl(owner_id=key.id)

    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)
    no_dup = MagicMock()
    no_dup.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=no_dup)
    session.add = MagicMock()
    session.commit = AsyncMock()

    async def _refresh(row):
        row.added_at = datetime(2025, 1, 1, tzinfo=UTC)
    session.refresh = AsyncMock(side_effect=_refresh)

    result = await add_symbol(wid=wl.id, req=WatchlistSymbolAdd(symbol="aapl"), current_key=key, session=session)
    assert result.symbol == "AAPL"
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_symbol_uppercases_symbol():
    from app.db.models import WatchlistSymbol as WS  # noqa: F401 — forces real class in scope

    key = _key()
    wl = _wl(owner_id=key.id)

    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)
    no_dup = MagicMock()
    no_dup.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=no_dup)
    session.add = MagicMock()
    session.commit = AsyncMock()

    async def _refresh(row):
        row.added_at = datetime(2025, 1, 1, tzinfo=UTC)
    session.refresh = AsyncMock(side_effect=_refresh)

    result = await add_symbol(wid=wl.id, req=WatchlistSymbolAdd(symbol="tsla"), current_key=key, session=session)
    assert result.symbol == "TSLA"


@pytest.mark.asyncio
async def test_add_symbol_duplicate_raises_409():
    from fastapi import HTTPException
    key = _key()
    wl = _wl(owner_id=key.id)

    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)
    dup = MagicMock()
    dup.scalar_one_or_none.return_value = _sym("AAPL")
    session.execute = AsyncMock(return_value=dup)

    with pytest.raises(HTTPException) as exc:
        await add_symbol(wid=wl.id, req=WatchlistSymbolAdd(symbol="AAPL"), current_key=key, session=session)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_add_symbol_watchlist_not_found_raises_404():
    from fastapi import HTTPException
    key = _key()
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await add_symbol(wid=uuid.uuid4(), req=WatchlistSymbolAdd(symbol="AAPL"), current_key=key, session=session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_add_symbol_wrong_owner_raises_404():
    from fastapi import HTTPException
    key = _key()
    wl = _wl(owner_id=uuid.uuid4())  # wrong owner
    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)

    with pytest.raises(HTTPException) as exc:
        await add_symbol(wid=wl.id, req=WatchlistSymbolAdd(symbol="AAPL"), current_key=key, session=session)
    assert exc.value.status_code == 404


# ── list_symbols ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_symbols_success():
    key = _key()
    wl = _wl(owner_id=key.id)
    syms = [_sym("AAPL"), _sym("MSFT"), _sym("NVDA")]

    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)
    r = MagicMock()
    r.scalars.return_value.all.return_value = syms
    session.execute = AsyncMock(return_value=r)

    results = await list_symbols(wid=wl.id, current_key=key, session=session)
    assert len(results) == 3
    assert results[0].symbol == "AAPL"


@pytest.mark.asyncio
async def test_list_symbols_empty():
    key = _key()
    wl = _wl(owner_id=key.id)

    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)
    r = MagicMock()
    r.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=r)

    results = await list_symbols(wid=wl.id, current_key=key, session=session)
    assert results == []


@pytest.mark.asyncio
async def test_list_symbols_not_found_raises_404():
    from fastapi import HTTPException
    key = _key()
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await list_symbols(wid=uuid.uuid4(), current_key=key, session=session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_symbols_wrong_owner_raises_404():
    from fastapi import HTTPException
    key = _key()
    wl = _wl(owner_id=uuid.uuid4())
    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)

    with pytest.raises(HTTPException) as exc:
        await list_symbols(wid=wl.id, current_key=key, session=session)
    assert exc.value.status_code == 404


# ── remove_symbol ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remove_symbol_success():
    key = _key()
    wl = _wl(owner_id=key.id)
    sym = _sym("AAPL")

    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)
    r = MagicMock()
    r.scalar_one_or_none.return_value = sym
    session.execute = AsyncMock(return_value=r)
    session.delete = AsyncMock()
    session.commit = AsyncMock()

    await remove_symbol(wid=wl.id, symbol="AAPL", current_key=key, session=session)
    session.delete.assert_awaited_once_with(sym)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_symbol_watchlist_not_found_raises_404():
    from fastapi import HTTPException
    key = _key()
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await remove_symbol(wid=uuid.uuid4(), symbol="AAPL", current_key=key, session=session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_remove_symbol_wrong_owner_raises_404():
    from fastapi import HTTPException
    key = _key()
    wl = _wl(owner_id=uuid.uuid4())
    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)

    with pytest.raises(HTTPException) as exc:
        await remove_symbol(wid=wl.id, symbol="AAPL", current_key=key, session=session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_remove_symbol_not_in_watchlist_raises_404():
    from fastapi import HTTPException
    key = _key()
    wl = _wl(owner_id=key.id)

    session = AsyncMock()
    session.get = AsyncMock(return_value=wl)
    r = MagicMock()
    r.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=r)

    with pytest.raises(HTTPException) as exc:
        await remove_symbol(wid=wl.id, symbol="NVDA", current_key=key, session=session)
    assert exc.value.status_code == 404
