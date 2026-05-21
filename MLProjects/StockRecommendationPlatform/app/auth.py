from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiKey
from app.db.session import get_session

_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)


def generate_key() -> tuple[str, str, str]:
    """Return (raw_key, prefix, key_hash). raw_key must be shown once and never stored."""
    raw = "sk-" + secrets.token_hex(20)
    prefix = raw[:8]
    return raw, prefix, hash_key(raw)


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_current_key(
    raw_key: str = Security(_HEADER),
    session: AsyncSession = Depends(get_session),
) -> ApiKey:
    row = (
        await session.execute(
            select(ApiKey).where(
                ApiKey.key_hash == hash_key(raw_key),
                ApiKey.is_active == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    row.last_used_at = datetime.now(tz=UTC)
    await session.commit()
    return row
