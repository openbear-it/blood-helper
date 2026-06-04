from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    BloodUnitCreate,
    BloodUnitResponse,
    ConsumeBloodRequest,
    ConsumptionResponse,
    HistoricalDataResponse,
    InventorySummaryResponse,
    PSIResponse,
    PSIBloodTypeResponse,
    WastageAnalysisResponse,
    WastageCreate,
    WastageResponse,
)
from app.application.services.blood_inventory import BloodInventoryService
from app.application.services.psi import PSIService, ScenarioMethod
from app.domain.blood_inventory.models import BloodUnit
from app.domain.enums import BloodType
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.blood_inventory import (
    SQLBloodInventoryRepository,
    SQLConsumptionRepository,
    SQLWastageRepository,
)

router = APIRouter(prefix="/hospitals/{hospital_id}/inventory", tags=["inventory"])


def get_inventory_service(session: AsyncSession = Depends(get_session)) -> BloodInventoryService:
    return BloodInventoryService(
        inventory_repo=SQLBloodInventoryRepository(session),
        consumption_repo=SQLConsumptionRepository(session),
        wastage_repo=SQLWastageRepository(session),
    )


def _unit_to_response(unit: BloodUnit) -> BloodUnitResponse:
    return BloodUnitResponse(
        id=unit.id,
        hospital_id=unit.hospital_id,
        blood_type=unit.blood_type,
        units_available=unit.units_available,
        units_reserved=unit.units_reserved,
        units_usable=unit.units_usable,
        expiry_date=unit.expiry_date,
        status=unit.status,
        last_updated=unit.last_updated,
    )


@router.get("/summary", response_model=InventorySummaryResponse)
async def get_inventory_summary(
    hospital_id: UUID,
    svc: BloodInventoryService = Depends(get_inventory_service),
) -> InventorySummaryResponse:
    data = await svc.get_inventory_summary(hospital_id)
    return InventorySummaryResponse(**data)


@router.post("/units", response_model=BloodUnitResponse, status_code=status.HTTP_201_CREATED)
async def add_blood_units(
    hospital_id: UUID,
    payload: BloodUnitCreate,
    svc: BloodInventoryService = Depends(get_inventory_service),
) -> BloodUnitResponse:
    unit = await svc.add_blood_units(
        hospital_id=hospital_id,
        blood_type=payload.blood_type,
        units=payload.units_available,
        expiry_date=payload.expiry_date,
    )
    return _unit_to_response(unit)


@router.post("/consume", response_model=ConsumptionResponse, status_code=status.HTTP_201_CREATED)
async def consume_blood(
    hospital_id: UUID,
    payload: ConsumeBloodRequest,
    svc: BloodInventoryService = Depends(get_inventory_service),
) -> ConsumptionResponse:
    try:
        record = await svc.consume_blood(
            hospital_id=hospital_id,
            department_id=payload.department_id,
            blood_type=payload.blood_type,
            units=payload.units,
            consumption_date=payload.consumption_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ConsumptionResponse(
        id=record.id,
        hospital_id=record.hospital_id,
        department_id=record.department_id,
        blood_type=record.blood_type,
        units_consumed=record.units_consumed,
        consumption_date=record.consumption_date,
        created_at=record.created_at,
    )


@router.post("/wastage", response_model=WastageResponse, status_code=status.HTTP_201_CREATED)
async def record_wastage(
    hospital_id: UUID,
    payload: WastageCreate,
    svc: BloodInventoryService = Depends(get_inventory_service),
) -> WastageResponse:
    record = await svc.record_wastage(
        hospital_id=hospital_id,
        blood_type=payload.blood_type,
        units=payload.units_wasted,
        reason=payload.reason,
        wastage_date=payload.wastage_date,
        notes=payload.notes,
    )
    return WastageResponse(
        id=record.id,
        hospital_id=record.hospital_id,
        blood_type=record.blood_type,
        units_wasted=record.units_wasted,
        reason=record.reason,
        wastage_date=record.wastage_date,
        notes=record.notes,
        estimated_cost=record.estimated_cost,
        created_at=record.created_at,
    )


@router.get("/wastage/analysis", response_model=WastageAnalysisResponse)
async def get_wastage_analysis(
    hospital_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    svc: BloodInventoryService = Depends(get_inventory_service),
) -> WastageAnalysisResponse:
    data = await svc.get_wastage_analysis(hospital_id, start_date, end_date)
    return WastageAnalysisResponse(**data)


@router.get("/expiring", response_model=list[BloodUnitResponse])
async def get_expiring_units(
    hospital_id: UUID,
    days: int = Query(default=3, ge=1, le=30),
    svc: BloodInventoryService = Depends(get_inventory_service),
) -> list[BloodUnitResponse]:
    units = await svc.get_expiring_units(hospital_id, days)
    return [_unit_to_response(u) for u in units]


@router.get("/psi", response_model=PSIResponse)
async def get_psi(
    hospital_id: UUID,
    horizon_days: int = Query(default=7, ge=1, le=30),
    percentile: int = Query(default=95, ge=1, le=99),
    method: ScenarioMethod = Query(default=ScenarioMethod.STATIC),
    history_days: int = Query(default=90, ge=14, le=365),
    friction: float = Query(default=0.05, ge=0.0, le=0.5),
    session: AsyncSession = Depends(get_session),
) -> PSIResponse:
    svc = PSIService(session)
    result = await svc.compute(
        hospital_id=hospital_id,
        horizon_days=horizon_days,
        percentile=percentile,
        method=method,
        history_days=history_days,
        friction=friction,
    )
    return PSIResponse(
        hospital_id=result.hospital_id,
        horizon_days=result.horizon_days,
        percentile=result.percentile,
        method=result.method.value,
        overall_psi=result.overall_psi,
        critical_types=result.critical_types,
        by_blood_type=[
            PSIBloodTypeResponse(
                blood_type=r.blood_type,
                psi=r.psi,
                stock_total=r.stock_total,
                stock_net_valid=r.stock_net_valid,
                expected_demand=r.expected_demand,
                expected_inflows=r.expected_inflows,
                at_risk_units=r.at_risk_units,
                horizon_days=r.horizon_days,
                percentile=r.percentile,
                method=r.method.value,
            )
            for r in result.by_blood_type
        ],
    )


@router.get("/history", response_model=HistoricalDataResponse)
async def get_inventory_history(
    hospital_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    blood_type: BloodType | None = Query(default=None),
    svc: BloodInventoryService = Depends(get_inventory_service),
) -> HistoricalDataResponse:
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must be >= start_date")
    data = await svc.get_history(
        hospital_id=hospital_id,
        start_date=start_date,
        end_date=end_date,
        blood_type=blood_type,
    )
    return HistoricalDataResponse(**data)
