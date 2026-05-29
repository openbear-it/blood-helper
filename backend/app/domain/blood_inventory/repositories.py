from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.blood_inventory.models import BloodConsumptionRecord, BloodUnit, WastageRecord
from app.domain.enums import BloodType


class BloodInventoryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, unit_id: UUID) -> BloodUnit | None: ...

    @abstractmethod
    async def get_by_hospital(self, hospital_id: UUID) -> list[BloodUnit]: ...

    @abstractmethod
    async def get_by_hospital_and_type(
        self, hospital_id: UUID, blood_type: BloodType
    ) -> list[BloodUnit]: ...

    @abstractmethod
    async def save(self, unit: BloodUnit) -> BloodUnit: ...

    @abstractmethod
    async def delete(self, unit_id: UUID) -> None: ...

    @abstractmethod
    async def get_expiring_soon(self, hospital_id: UUID, days: int = 3) -> list[BloodUnit]: ...


class ConsumptionRepository(ABC):
    @abstractmethod
    async def save(self, record: BloodConsumptionRecord) -> BloodConsumptionRecord: ...

    @abstractmethod
    async def get_by_hospital(
        self,
        hospital_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[BloodConsumptionRecord]: ...

    @abstractmethod
    async def get_by_department(
        self,
        department_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[BloodConsumptionRecord]: ...

    @abstractmethod
    async def get_by_blood_type(
        self,
        hospital_id: UUID,
        blood_type: BloodType,
        start_date: date,
        end_date: date,
    ) -> list[BloodConsumptionRecord]: ...


class WastageRepository(ABC):
    @abstractmethod
    async def save(self, record: WastageRecord) -> WastageRecord: ...

    @abstractmethod
    async def get_by_hospital(
        self, hospital_id: UUID, start_date: date, end_date: date
    ) -> list[WastageRecord]: ...
