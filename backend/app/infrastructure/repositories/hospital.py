from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.blood_inventory.models import Hospital, Department
from app.infrastructure.database.models import HospitalORM, DepartmentORM


class SQLHospitalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: HospitalORM) -> Hospital:
        return Hospital(
            id=orm.id,
            name=orm.name,
            code=orm.code,
            city=orm.city,
            region=orm.region,
            capacity_beds=orm.capacity_beds,
            created_at=orm.created_at,
        )

    async def get_all(self) -> list[Hospital]:
        result = await self._session.execute(select(HospitalORM))
        return [self._to_domain(row) for row in result.scalars()]

    async def get_by_id(self, hospital_id: uuid.UUID) -> Hospital | None:
        result = await self._session.get(HospitalORM, hospital_id)
        return self._to_domain(result) if result else None

    async def save(self, hospital: Hospital) -> Hospital:
        existing = await self._session.get(HospitalORM, hospital.id)
        if existing:
            existing.name = hospital.name
            existing.code = hospital.code
            existing.city = hospital.city
            existing.region = hospital.region
            existing.capacity_beds = hospital.capacity_beds
        else:
            self._session.add(HospitalORM(
                id=hospital.id,
                name=hospital.name,
                code=hospital.code,
                city=hospital.city,
                region=hospital.region,
                capacity_beds=hospital.capacity_beds,
                created_at=hospital.created_at,
            ))
        return hospital

    async def delete(self, hospital_id: uuid.UUID) -> None:
        existing = await self._session.get(HospitalORM, hospital_id)
        if existing:
            await self._session.delete(existing)


class SQLDepartmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: DepartmentORM) -> Department:
        return Department(
            id=orm.id,
            hospital_id=orm.hospital_id,
            name=orm.name,
            code=orm.code,
            created_at=orm.created_at,
        )

    async def get_by_hospital(self, hospital_id: uuid.UUID) -> list[Department]:
        stmt = select(DepartmentORM).where(DepartmentORM.hospital_id == hospital_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]

    async def get_by_id(self, dept_id: uuid.UUID) -> Department | None:
        result = await self._session.get(DepartmentORM, dept_id)
        return self._to_domain(result) if result else None

    async def save(self, dept: Department) -> Department:
        existing = await self._session.get(DepartmentORM, dept.id)
        if existing:
            existing.name = dept.name
            existing.code = dept.code
        else:
            self._session.add(DepartmentORM(
                id=dept.id,
                hospital_id=dept.hospital_id,
                name=dept.name,
                code=dept.code,
                created_at=dept.created_at,
            ))
        return dept
