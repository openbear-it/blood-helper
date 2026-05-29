from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

from app.domain.enums import BloodType, CampaignStatus, ForecastHorizon


@dataclass
class ForecastResult:
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

    @staticmethod
    def create(
        hospital_id: UUID,
        blood_type: BloodType,
        horizon: ForecastHorizon,
        forecast_date: date,
        predicted_units: float,
        lower_bound: float,
        upper_bound: float,
        model_name: str,
        confidence: float,
        department_id: UUID | None = None,
    ) -> "ForecastResult":
        return ForecastResult(
            id=uuid4(),
            hospital_id=hospital_id,
            department_id=department_id,
            blood_type=blood_type,
            horizon=horizon,
            forecast_date=forecast_date,
            predicted_units=predicted_units,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            model_name=model_name,
            confidence=confidence,
            created_at=datetime.utcnow(),
        )


@dataclass
class DonationCampaign:
    id: UUID
    hospital_id: UUID
    title: str
    description: str
    target_blood_types: list[BloodType]
    target_units: int
    collected_units: int
    start_date: date
    end_date: date
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime

    @property
    def progress_percentage(self) -> float:
        if self.target_units == 0:
            return 0.0
        return min(100.0, (self.collected_units / self.target_units) * 100)

    @property
    def is_active(self) -> bool:
        today = date.today()
        return (
            self.status == CampaignStatus.ACTIVE
            and self.start_date <= today <= self.end_date
        )

    def activate(self) -> None:
        if self.status != CampaignStatus.DRAFT:
            raise ValueError("Only draft campaigns can be activated")
        self.status = CampaignStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        self.status = CampaignStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        if self.status == CampaignStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed campaign")
        self.status = CampaignStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def record_donation(self, units: int) -> None:
        if not self.is_active:
            raise ValueError("Campaign is not active")
        self.collected_units += units
        self.updated_at = datetime.utcnow()
        if self.collected_units >= self.target_units:
            self.complete()

    @staticmethod
    def create(
        hospital_id: UUID,
        title: str,
        description: str,
        target_blood_types: list[BloodType],
        target_units: int,
        start_date: date,
        end_date: date,
    ) -> "DonationCampaign":
        now = datetime.utcnow()
        return DonationCampaign(
            id=uuid4(),
            hospital_id=hospital_id,
            title=title,
            description=description,
            target_blood_types=target_blood_types,
            target_units=target_units,
            collected_units=0,
            start_date=start_date,
            end_date=end_date,
            status=CampaignStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
