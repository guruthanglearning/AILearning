from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_key
from app.db.models import ApiKey, Watchlist, WatchlistSymbol
from app.db.session import get_session
from app.schemas.user import WatchlistCreate, WatchlistResponse, WatchlistSymbolAdd, WatchlistSymbolResponse

router = APIRouter()


def _wl_to_response(row: Watchlist) -> WatchlistResponse:
    return WatchlistResponse(
        id=row.id,
        name=row.name,
        description=row.description,
        created_at=row.created_at,
        symbol_count=len(row.symbols) if row.symbols is not None else 0,
    )


@router.post("", response_model=WatchlistResponse, status_code=201)
async def create_watchlist(
    req: WatchlistCreate,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> WatchlistResponse:
    row = Watchlist(api_key_id=current_key.id, name=req.name, description=req.description)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return WatchlistResponse(id=row.id, name=row.name, description=row.description,
                             created_at=row.created_at, symbol_count=0)


@router.get("", response_model=list[WatchlistResponse])
async def list_watchlists(
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> list[WatchlistResponse]:
    rows = (
        await session.execute(
            select(Watchlist).where(Watchlist.api_key_id == current_key.id)
        )
    ).scalars().all()
    result = []
    for row in rows:
        syms = (
            await session.execute(
                select(WatchlistSymbol).where(WatchlistSymbol.watchlist_id == row.id)
            )
        ).scalars().all()
        result.append(WatchlistResponse(id=row.id, name=row.name, description=row.description,
                                        created_at=row.created_at, symbol_count=len(syms)))
    return result


@router.delete("/{wid}", status_code=204)
async def delete_watchlist(
    wid: uuid.UUID,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> None:
    row = await session.get(Watchlist, wid)
    if row is None or row.api_key_id != current_key.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    await session.delete(row)
    await session.commit()


@router.post("/{wid}/symbols", response_model=WatchlistSymbolResponse, status_code=201)
async def add_symbol(
    wid: uuid.UUID,
    req: WatchlistSymbolAdd,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> WatchlistSymbolResponse:
    wl = await session.get(Watchlist, wid)
    if wl is None or wl.api_key_id != current_key.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    symbol = req.symbol.upper().strip()
    existing = (
        await session.execute(
            select(WatchlistSymbol).where(
                WatchlistSymbol.watchlist_id == wid,
                WatchlistSymbol.symbol == symbol,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"{symbol} already in watchlist")
    row = WatchlistSymbol(watchlist_id=wid, symbol=symbol, note=req.note)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return WatchlistSymbolResponse(symbol=row.symbol, note=row.note, added_at=row.added_at)


@router.get("/{wid}/symbols", response_model=list[WatchlistSymbolResponse])
async def list_symbols(
    wid: uuid.UUID,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> list[WatchlistSymbolResponse]:
    wl = await session.get(Watchlist, wid)
    if wl is None or wl.api_key_id != current_key.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    rows = (
        await session.execute(
            select(WatchlistSymbol).where(WatchlistSymbol.watchlist_id == wid)
        )
    ).scalars().all()
    return [WatchlistSymbolResponse(symbol=r.symbol, note=r.note, added_at=r.added_at) for r in rows]


@router.delete("/{wid}/symbols/{symbol}", status_code=204)
async def remove_symbol(
    wid: uuid.UUID,
    symbol: str,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> None:
    wl = await session.get(Watchlist, wid)
    if wl is None or wl.api_key_id != current_key.id:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    row = (
        await session.execute(
            select(WatchlistSymbol).where(
                WatchlistSymbol.watchlist_id == wid,
                WatchlistSymbol.symbol == symbol.upper().strip(),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Symbol not in watchlist")
    await session.delete(row)
    await session.commit()
