from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.enums import BloodType, ForecastHorizon
from app.domain.forecasting.models import DonationCampaign, ForecastResult


class ForecastRepository(ABC):
    @abstractmethod
    async def save(self, result: ForecastResult) -> ForecastResult: ...

    @abstractmethod
    async def get_latest(
        self,
        hospital_id: UUID,
        blood_type: BloodType,
        horizon: ForecastHorizon,
    ) -> list[ForecastResult]: ...

    @abstractmethod
    async def get_by_department(
        self,
        department_id: UUID,
        blood_type: BloodType,
        horizon: ForecastHorizon,
    ) -> list[ForecastResult]: ...


class CampaignRepository(ABC):
    @abstractmethod
    async def get_by_id(self, campaign_id: UUID) -> DonationCampaign | None: ...

    @abstractmethod
    async def get_by_hospital(self, hospital_id: UUID) -> list[DonationCampaign]: ...

    @abstractmethod
    async def get_active(self) -> list[DonationCampaign]: ...

    @abstractmethod
    async def save(self, campaign: DonationCampaign) -> DonationCampaign: ...

    @abstractmethod
    async def delete(self, campaign_id: UUID) -> None: ...
