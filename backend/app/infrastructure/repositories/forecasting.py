from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import BloodType, ForecastHorizon
from app.domain.forecasting.models import DonationCampaign, ForecastResult
from app.domain.forecasting.repositories import CampaignRepository, ForecastRepository
from app.infrastructure.database.models import DonationCampaignORM, ForecastResultORM


class SQLForecastRepository(ForecastRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: ForecastResultORM) -> ForecastResult:
        return ForecastResult(
            id=orm.id,
            hospital_id=orm.hospital_id,
            department_id=orm.department_id,
            blood_type=orm.blood_type,
            horizon=orm.horizon,
            forecast_date=orm.forecast_date,
            predicted_units=float(orm.predicted_units),
            lower_bound=float(orm.lower_bound),
            upper_bound=float(orm.upper_bound),
            model_name=orm.model_name,
            confidence=float(orm.confidence),
            created_at=orm.created_at,
        )

    async def save(self, result: ForecastResult) -> ForecastResult:
        orm = ForecastResultORM(
            id=result.id,
            hospital_id=result.hospital_id,
            department_id=result.department_id,
            blood_type=result.blood_type,
            horizon=result.horizon,
            forecast_date=result.forecast_date,
            predicted_units=result.predicted_units,
            lower_bound=result.lower_bound,
            upper_bound=result.upper_bound,
            model_name=result.model_name,
            confidence=result.confidence,
            created_at=result.created_at,
        )
        self._session.add(orm)
        return result

    async def get_latest(
        self,
        hospital_id: uuid.UUID,
        blood_type: BloodType,
        horizon: ForecastHorizon,
    ) -> list[ForecastResult]:
        latest_created_at = (
            select(func.max(ForecastResultORM.created_at))
            .where(
                ForecastResultORM.hospital_id == hospital_id,
                ForecastResultORM.blood_type == blood_type,
                ForecastResultORM.horizon == horizon,
            )
            .scalar_subquery()
        )
        stmt = (
            select(ForecastResultORM)
            .where(
                ForecastResultORM.hospital_id == hospital_id,
                ForecastResultORM.blood_type == blood_type,
                ForecastResultORM.horizon == horizon,
                ForecastResultORM.created_at == latest_created_at,
            )
            .order_by(ForecastResultORM.forecast_date.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]

    async def get_by_department(
        self,
        department_id: uuid.UUID,
        blood_type: BloodType,
        horizon: ForecastHorizon,
    ) -> list[ForecastResult]:
        latest_created_at = (
            select(func.max(ForecastResultORM.created_at))
            .where(
                ForecastResultORM.department_id == department_id,
                ForecastResultORM.blood_type == blood_type,
                ForecastResultORM.horizon == horizon,
            )
            .scalar_subquery()
        )
        stmt = (
            select(ForecastResultORM)
            .where(
                ForecastResultORM.department_id == department_id,
                ForecastResultORM.blood_type == blood_type,
                ForecastResultORM.horizon == horizon,
                ForecastResultORM.created_at == latest_created_at,
            )
            .order_by(ForecastResultORM.forecast_date.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]


class SQLCampaignRepository(CampaignRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: DonationCampaignORM) -> DonationCampaign:
        from app.domain.enums import BloodType
        return DonationCampaign(
            id=orm.id,
            hospital_id=orm.hospital_id,
            title=orm.title,
            description=orm.description,
            target_blood_types=[BloodType(bt) for bt in orm.target_blood_types],
            target_units=orm.target_units,
            collected_units=orm.collected_units,
            start_date=orm.start_date,
            end_date=orm.end_date,
            status=orm.status,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, campaign: DonationCampaign) -> DonationCampaignORM:
        return DonationCampaignORM(
            id=campaign.id,
            hospital_id=campaign.hospital_id,
            title=campaign.title,
            description=campaign.description,
            target_blood_types=[bt.value for bt in campaign.target_blood_types],
            target_units=campaign.target_units,
            collected_units=campaign.collected_units,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            status=campaign.status,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )

    async def get_by_id(self, campaign_id: uuid.UUID) -> DonationCampaign | None:
        result = await self._session.get(DonationCampaignORM, campaign_id)
        return self._to_domain(result) if result else None

    async def get_by_hospital(self, hospital_id: uuid.UUID) -> list[DonationCampaign]:
        stmt = select(DonationCampaignORM).where(DonationCampaignORM.hospital_id == hospital_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]

    async def get_active(self) -> list[DonationCampaign]:
        from app.domain.enums import CampaignStatus
        stmt = select(DonationCampaignORM).where(
            DonationCampaignORM.status == CampaignStatus.ACTIVE
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars()]

    async def save(self, campaign: DonationCampaign) -> DonationCampaign:
        existing = await self._session.get(DonationCampaignORM, campaign.id)
        if existing:
            existing.title = campaign.title
            existing.description = campaign.description
            existing.target_blood_types = [bt.value for bt in campaign.target_blood_types]
            existing.target_units = campaign.target_units
            existing.collected_units = campaign.collected_units
            existing.start_date = campaign.start_date
            existing.end_date = campaign.end_date
            existing.status = campaign.status
            existing.updated_at = campaign.updated_at
        else:
            self._session.add(self._to_orm(campaign))
        return campaign

    async def delete(self, campaign_id: uuid.UUID) -> None:
        existing = await self._session.get(DonationCampaignORM, campaign_id)
        if existing:
            await self._session.delete(existing)
