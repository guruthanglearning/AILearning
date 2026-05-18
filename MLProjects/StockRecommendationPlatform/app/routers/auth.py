from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import generate_key, get_current_key
from app.db.models import ApiKey
from app.db.session import get_session
from app.schemas.user import ApiKeyCreate, ApiKeyResponse

router = APIRouter()


@router.post("", response_model=ApiKeyResponse, status_code=201)
async def create_key(
    req: ApiKeyCreate,
    session: AsyncSession = Depends(get_session),
) -> ApiKeyResponse:
    """Create a new API key. The raw key is returned once — store it securely."""
    raw, prefix, key_hash = generate_key()
    row = ApiKey(name=req.name, key_prefix=prefix, key_hash=key_hash)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return ApiKeyResponse(
        id=row.id,
        name=row.name,
        key_prefix=row.key_prefix,
        is_active=row.is_active,
        created_at=row.created_at,
        key=raw,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_keys(
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> list[ApiKeyResponse]:
    """List all active keys that share the same key_prefix (owned by the caller)."""
    rows = (
        await session.execute(
            select(ApiKey).where(
                ApiKey.key_prefix == current_key.key_prefix,
                ApiKey.is_active == True,  # noqa: E712
            )
        )
    ).scalars().all()
    return [
        ApiKeyResponse(id=r.id, name=r.name, key_prefix=r.key_prefix,
                       is_active=r.is_active, created_at=r.created_at,
                       last_used_at=r.last_used_at)
        for r in rows
    ]


@router.delete("/{key_id}", status_code=204)
async def revoke_key(
    key_id: uuid.UUID,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Revoke an API key (must share same key_prefix as caller's key)."""
    row = await session.get(ApiKey, key_id)
    if row is None or row.key_prefix != current_key.key_prefix:
        raise HTTPException(status_code=404, detail="Key not found")
    row.is_active = False
    await session.commit()
