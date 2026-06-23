from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_key
from app.db.models import ApiKey, UserSettings
from app.db.session import get_session
from app.schemas.user import UserSettingsPayload, UserSettingsResponse

router = APIRouter()

_FIELDS = [
    "default_symbol",
    "default_portfolio_value",
    "default_max_risk_pct",
    "preferred_claude_model",
    "market_grid_refresh_secs",
    "market_grid_symbols",
]


def _to_response(row: UserSettings | None) -> UserSettingsResponse:
    if row is None:
        return UserSettingsResponse()
    blob = row.settings_json or {}
    return UserSettingsResponse(
        **{k: blob.get(k) for k in _FIELDS},
        updated_at=row.updated_at,
    )


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> UserSettingsResponse:
    row = (
        await session.execute(
            select(UserSettings).where(UserSettings.api_key_id == current_key.id)
        )
    ).scalar_one_or_none()
    return _to_response(row)


@router.put("", response_model=UserSettingsResponse)
async def upsert_settings(
    payload: UserSettingsPayload,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> UserSettingsResponse:
    row = (
        await session.execute(
            select(UserSettings).where(UserSettings.api_key_id == current_key.id)
        )
    ).scalar_one_or_none()

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}

    if row is None:
        row = UserSettings(api_key_id=current_key.id, settings_json=updates)
        session.add(row)
    else:
        merged = {**row.settings_json, **updates}
        row.settings_json = merged

    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.delete("/{key}", status_code=204)
async def delete_setting(
    key: str,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove a single setting key (resets it to the default / unset state)."""
    if key not in _FIELDS:
        return
    row = (
        await session.execute(
            select(UserSettings).where(UserSettings.api_key_id == current_key.id)
        )
    ).scalar_one_or_none()
    if row and key in row.settings_json:
        blob = dict(row.settings_json)
        del blob[key]
        row.settings_json = blob
        await session.commit()
