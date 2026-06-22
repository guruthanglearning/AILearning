from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_key
from app.db.models import ApiKey, PortfolioPosition
from app.db.session import get_session
from app.schemas.user import (
    PortfolioPositionCreate,
    PortfolioPositionResponse,
    PortfolioPositionUpdate,
)

router = APIRouter()


def _to_response(row: PortfolioPosition) -> PortfolioPositionResponse:
    return PortfolioPositionResponse(
        id=row.id,
        symbol=row.symbol,
        shares=row.shares,
        cost_basis=row.cost_basis,
        entry_date=row.entry_date,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[PortfolioPositionResponse])
async def list_positions(
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> list[PortfolioPositionResponse]:
    rows = (
        await session.execute(
            select(PortfolioPosition)
            .where(PortfolioPosition.api_key_id == current_key.id)
            .order_by(PortfolioPosition.created_at)
        )
    ).scalars().all()
    return [_to_response(r) for r in rows]


@router.post("", response_model=PortfolioPositionResponse, status_code=201)
async def create_position(
    req: PortfolioPositionCreate,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> PortfolioPositionResponse:
    row = PortfolioPosition(
        api_key_id=current_key.id,
        symbol=req.symbol.upper().strip(),
        shares=req.shares,
        cost_basis=req.cost_basis,
        entry_date=req.entry_date,
        notes=req.notes,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.put("/{position_id}", response_model=PortfolioPositionResponse)
async def update_position(
    position_id: uuid.UUID,
    req: PortfolioPositionUpdate,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> PortfolioPositionResponse:
    row = await session.get(PortfolioPosition, position_id)
    if row is None or row.api_key_id != current_key.id:
        raise HTTPException(status_code=404, detail="Position not found")
    if req.shares is not None:
        row.shares = req.shares
    if req.cost_basis is not None:
        row.cost_basis = req.cost_basis
    if req.entry_date is not None:
        row.entry_date = req.entry_date
    if req.notes is not None:
        row.notes = req.notes
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.delete("/{position_id}", status_code=204)
async def delete_position(
    position_id: uuid.UUID,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> None:
    row = await session.get(PortfolioPosition, position_id)
    if row is None or row.api_key_id != current_key.id:
        raise HTTPException(status_code=404, detail="Position not found")
    await session.delete(row)
    await session.commit()
