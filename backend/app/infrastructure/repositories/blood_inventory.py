from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.blood_inventory.models import BloodConsumptionRecord, BloodUnit, WastageRecord
from app.domain.blood_inventory.repositories import (
    BloodInventoryRepository,
    ConsumptionRepository,
    WastageRepository,
)
from app.domain.enums import BloodType
from app.infrastructure.database.models import BloodConsumptionORM, BloodUnitORM, WastageORM


class SQLBloodInventoryRepository(BloodInventoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: BloodUnitORM) -> BloodUnit:
        return BloodUnit(
            id=orm.id,
            hospital_id=orm.hospital_id,
            blood_type=orm.blood_type,
            units_available=orm.units_available,
            units_reserved=orm.units_reserved,
            expiry_date=orm.expiry_date,
            last_updated=orm.last_updated,
        )

    def _to_orm(self, unit: BloodUnit) -> BloodUnitORM:
        return BloodUnitORM(
            id=unit.id,
            hospital_id=unit.hospital_id,
            blood_type=unit.blood_type,
            units_available=unit.units_available,
            units_reserved=unit.units_reserved,
            expiry_date=unit.expiry_date,
            last_updated=unit.last_updated,
        )

    async def get_by_id(self, unit_id: uuid.UUID) -> BloodUnit | None:
        result = await self._session.get(BloodUnitORM, unit_id)
        return self._to_domain(result) if result else None

    async def get_by_hospital(self, hospital_id: uuid.UUID) -> list[BloodUnit]:
        stmt = select(BloodUnitORM).where(BloodUnitORM.hospital_id == hospital_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]

    async def get_by_hospital_and_type(
        self, hospital_id: uuid.UUID, blood_type: BloodType
    ) -> list[BloodUnit]:
        stmt = select(BloodUnitORM).where(
            BloodUnitORM.hospital_id == hospital_id,
            BloodUnitORM.blood_type == blood_type,
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]

    async def save(self, unit: BloodUnit) -> BloodUnit:
        existing = await self._session.get(BloodUnitORM, unit.id)
        if existing:
            existing.units_available = unit.units_available
            existing.units_reserved = unit.units_reserved
            existing.expiry_date = unit.expiry_date
            existing.last_updated = unit.last_updated
        else:
            self._session.add(self._to_orm(unit))
        return unit

    async def delete(self, unit_id: uuid.UUID) -> None:
        existing = await self._session.get(BloodUnitORM, unit_id)
        if existing:
            await self._session.delete(existing)

    async def get_expiring_soon(self, hospital_id: uuid.UUID, days: int = 3) -> list[BloodUnit]:
        from datetime import timedelta
        cutoff = date.today() + timedelta(days=days)
        stmt = select(BloodUnitORM).where(
            BloodUnitORM.hospital_id == hospital_id,
            BloodUnitORM.expiry_date <= cutoff,
            BloodUnitORM.expiry_date >= date.today(),
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]


class SQLConsumptionRepository(ConsumptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: BloodConsumptionORM) -> BloodConsumptionRecord:
        return BloodConsumptionRecord(
            id=orm.id,
            hospital_id=orm.hospital_id,
            department_id=orm.department_id,
            blood_type=orm.blood_type,
            units_consumed=orm.units_consumed,
            consumption_date=orm.consumption_date,
            created_at=orm.created_at,
        )

    async def save(self, record: BloodConsumptionRecord) -> BloodConsumptionRecord:
        orm = BloodConsumptionORM(
            id=record.id,
            hospital_id=record.hospital_id,
            department_id=record.department_id,
            blood_type=record.blood_type,
            units_consumed=record.units_consumed,
            consumption_date=record.consumption_date,
            created_at=record.created_at,
        )
        self._session.add(orm)
        return record

    async def get_by_hospital(
        self, hospital_id: uuid.UUID, start_date: date, end_date: date
    ) -> list[BloodConsumptionRecord]:
        stmt = select(BloodConsumptionORM).where(
            BloodConsumptionORM.hospital_id == hospital_id,
            BloodConsumptionORM.consumption_date >= start_date,
            BloodConsumptionORM.consumption_date <= end_date,
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]

    async def get_by_department(
        self, department_id: uuid.UUID, start_date: date, end_date: date
    ) -> list[BloodConsumptionRecord]:
        stmt = select(BloodConsumptionORM).where(
            BloodConsumptionORM.department_id == department_id,
            BloodConsumptionORM.consumption_date >= start_date,
            BloodConsumptionORM.consumption_date <= end_date,
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]

    async def get_by_blood_type(
        self,
        hospital_id: uuid.UUID,
        blood_type: BloodType,
        start_date: date,
        end_date: date,
    ) -> list[BloodConsumptionRecord]:
        stmt = select(BloodConsumptionORM).where(
            BloodConsumptionORM.hospital_id == hospital_id,
            BloodConsumptionORM.blood_type == blood_type,
            BloodConsumptionORM.consumption_date >= start_date,
            BloodConsumptionORM.consumption_date <= end_date,
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]


class SQLWastageRepository(WastageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: WastageORM) -> WastageRecord:
        return WastageRecord(
            id=orm.id,
            hospital_id=orm.hospital_id,
            blood_type=orm.blood_type,
            units_wasted=orm.units_wasted,
            reason=orm.reason,
            wastage_date=orm.wastage_date,
            notes=orm.notes,
            estimated_cost=orm.estimated_cost,
            created_at=orm.created_at,
        )

    async def save(self, record: WastageRecord) -> WastageRecord:
        orm = WastageORM(
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
        self._session.add(orm)
        return record

    async def get_by_hospital(
        self, hospital_id: uuid.UUID, start_date: date, end_date: date
    ) -> list[WastageRecord]:
        stmt = select(WastageORM).where(
            WastageORM.hospital_id == hospital_id,
            WastageORM.wastage_date >= start_date,
            WastageORM.wastage_date <= end_date,
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]
