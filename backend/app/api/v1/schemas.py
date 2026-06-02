from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    BloodType,
    CampaignStatus,
    ForecastHorizon,
    InventoryStatus,
    WastageReason,
)


# ── Hospital ────────────────────────────────────────────────────────────────

class HospitalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=20)
    city: str = Field(..., min_length=1, max_length=100)
    region: str = Field(..., min_length=1, max_length=100)
    capacity_beds: int = Field(..., gt=0)


class HospitalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    city: str
    region: str
    capacity_beds: int
    created_at: datetime


# ── Department ──────────────────────────────────────────────────────────────

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=20)


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hospital_id: UUID
    name: str
    code: str
    created_at: datetime


# ── Blood Inventory ─────────────────────────────────────────────────────────

class BloodUnitCreate(BaseModel):
    blood_type: BloodType
    units_available: int = Field(..., gt=0)
    expiry_date: date


class BloodUnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hospital_id: UUID
    blood_type: BloodType
    units_available: int
    units_reserved: int
    units_usable: int
    expiry_date: date
    status: InventoryStatus
    last_updated: datetime


class ConsumeBloodRequest(BaseModel):
    department_id: UUID
    blood_type: BloodType
    units: int = Field(..., gt=0)
    consumption_date: date = Field(default_factory=date.today)


class ConsumptionResponse(BaseModel):
    id: UUID
    hospital_id: UUID
    department_id: UUID
    blood_type: BloodType
    units_consumed: int
    consumption_date: date
    created_at: datetime


# ── Wastage ─────────────────────────────────────────────────────────────────

class WastageCreate(BaseModel):
    blood_type: BloodType
    units_wasted: int = Field(..., gt=0)
    reason: WastageReason
    wastage_date: date = Field(default_factory=date.today)
    notes: str = ""


class WastageResponse(BaseModel):
    id: UUID
    hospital_id: UUID
    blood_type: BloodType
    units_wasted: int
    reason: WastageReason
    wastage_date: date
    notes: str
    estimated_cost: Decimal
    created_at: datetime


# ── Forecasting ─────────────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    blood_type: BloodType
    horizon: ForecastHorizon
    department_id: UUID | None = None


class ForecastResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    hospital_id: UUID
    department_id: UUID | None
    blood_type: BloodType
    horizon: ForecastHorizon
    forecast_date: date
    predicted_units: float
    lower_bound: float
    upper_bound: float
    model_name: str
    confidence: float
    created_at: datetime


# ── Campaigns ───────────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    target_blood_types: list[BloodType] = Field(..., min_length=1)
    target_units: int = Field(..., gt=0)
    start_date: date
    end_date: date


class CampaignDonationRequest(BaseModel):
    units: int = Field(..., gt=0)


class CampaignResponse(BaseModel):
    id: UUID
    hospital_id: UUID
    title: str
    description: str
    target_blood_types: list[BloodType]
    target_units: int
    collected_units: int
    progress_percentage: float
    start_date: date
    end_date: date
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime


# ── Analytics ───────────────────────────────────────────────────────────────

class InventorySummaryResponse(BaseModel):
    hospital_id: str
    blood_types: dict[str, dict]
    critical_types: list[str]


class WastageAnalysisResponse(BaseModel):
    period: dict[str, str]
    total_units_wasted: int
    total_estimated_cost: float
    by_blood_type: dict[str, dict]
    by_reason: dict[str, int]
