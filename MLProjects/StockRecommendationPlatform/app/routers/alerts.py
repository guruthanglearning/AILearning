from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_key
from app.db.models import Alert, AnalysisRun, ApiKey
from app.db.session import get_session
from app.schemas.user import AlertCondition, AlertCreate, AlertResponse

router = APIRouter()


def _alert_to_response(row: Alert) -> AlertResponse:
    return AlertResponse(
        id=row.id,
        symbol=row.symbol,
        condition=AlertCondition(row.condition),
        threshold_value=row.threshold_value,
        threshold_verdict=row.threshold_verdict,
        is_active=row.is_active,
        triggered_at=row.triggered_at,
        created_at=row.created_at,
    )


async def _evaluate_alert(alert: Alert, session: AsyncSession) -> bool:
    """Check if alert condition is met against the latest analysis_run for the symbol."""
    result = await session.execute(
        select(AnalysisRun.last_price, AnalysisRun.instrument_recommendation)
        .where(AnalysisRun.symbol == alert.symbol)
        .order_by(AnalysisRun.started_at.desc())
        .limit(1)
    )
    row = result.first()
    if row is None:
        return False
    last_price, verdict = row
    cond = alert.condition
    if cond == AlertCondition.price_above:
        return last_price is not None and alert.threshold_value is not None and last_price > alert.threshold_value
    if cond == AlertCondition.price_below:
        return last_price is not None and alert.threshold_value is not None and last_price < alert.threshold_value
    if cond == AlertCondition.verdict_changes_to:
        return verdict is not None and verdict == alert.threshold_verdict
    return False


async def _refresh_alerts(alerts: list[Alert], session: AsyncSession) -> None:
    """Evaluate all active alerts and mark triggered ones."""
    for alert in alerts:
        if not alert.is_active or alert.triggered_at is not None:
            continue
        if await _evaluate_alert(alert, session):
            alert.triggered_at = datetime.now(tz=UTC)
    await session.commit()


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    req: AlertCreate,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> AlertResponse:
    row = Alert(
        api_key_id=current_key.id,
        symbol=req.symbol.upper().strip(),
        condition=req.condition.value,
        threshold_value=req.threshold_value,
        threshold_verdict=req.threshold_verdict,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _alert_to_response(row)


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> list[AlertResponse]:
    rows = (
        await session.execute(
            select(Alert).where(Alert.api_key_id == current_key.id)
        )
    ).scalars().all()
    await _refresh_alerts(list(rows), session)
    return [_alert_to_response(r) for r in rows]


@router.get("/triggered", response_model=list[AlertResponse])
async def list_triggered_alerts(
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> list[AlertResponse]:
    rows = (
        await session.execute(
            select(Alert).where(
                Alert.api_key_id == current_key.id,
                Alert.is_active == True,  # noqa: E712
            )
        )
    ).scalars().all()
    await _refresh_alerts(list(rows), session)
    triggered = [r for r in rows if r.triggered_at is not None]
    return [_alert_to_response(r) for r in triggered]


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: uuid.UUID,
    current_key: ApiKey = Depends(get_current_key),
    session: AsyncSession = Depends(get_session),
) -> None:
    row = await session.get(Alert, alert_id)
    if row is None or row.api_key_id != current_key.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    await session.delete(row)
    await session.commit()
