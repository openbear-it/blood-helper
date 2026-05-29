from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import ForecastRequest, ForecastResultResponse
from app.application.services.forecasting import ForecastingService
from app.domain.forecasting.models import ForecastResult
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.blood_inventory import SQLConsumptionRepository
from app.infrastructure.repositories.forecasting import SQLForecastRepository

router = APIRouter(prefix="/hospitals/{hospital_id}/forecasts", tags=["forecasting"])


def get_forecasting_service(session: AsyncSession = Depends(get_session)) -> ForecastingService:
    return ForecastingService(
        consumption_repo=SQLConsumptionRepository(session),
        forecast_repo=SQLForecastRepository(session),
    )


def _to_response(r: ForecastResult) -> ForecastResultResponse:
    return ForecastResultResponse(
        id=r.id,
        hospital_id=r.hospital_id,
        department_id=r.department_id,
        blood_type=r.blood_type,
        horizon=r.horizon,
        forecast_date=r.forecast_date,
        predicted_units=r.predicted_units,
        lower_bound=r.lower_bound,
        upper_bound=r.upper_bound,
        model_name=r.model_name,
        confidence=r.confidence,
        created_at=r.created_at,
    )


@router.post("/run", response_model=list[ForecastResultResponse], status_code=status.HTTP_201_CREATED)
async def run_forecast(
    hospital_id: UUID,
    payload: ForecastRequest,
    svc: ForecastingService = Depends(get_forecasting_service),
) -> list[ForecastResultResponse]:
    results = await svc.run_forecast(
        hospital_id=hospital_id,
        blood_type=payload.blood_type,
        horizon=payload.horizon,
        department_id=payload.department_id,
    )
    return [_to_response(r) for r in results]


@router.get("/", response_model=list[ForecastResultResponse])
async def get_forecasts(
    hospital_id: UUID,
    blood_type: str,
    horizon: str,
    svc: ForecastingService = Depends(get_forecasting_service),
) -> list[ForecastResultResponse]:
    from app.domain.enums import BloodType, ForecastHorizon
    try:
        bt = BloodType(blood_type)
        h = ForecastHorizon(horizon)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    results = await svc.get_forecasts(hospital_id, bt, h)
    return [_to_response(r) for r in results]
