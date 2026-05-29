from __future__ import annotations

import uuid
from datetime import date

from app.domain.enums import BloodType
from app.domain.forecasting.models import DonationCampaign
from app.domain.forecasting.repositories import CampaignRepository


class CampaignService:
    def __init__(self, campaign_repo: CampaignRepository) -> None:
        self._repo = campaign_repo

    async def create_campaign(
        self,
        hospital_id: uuid.UUID,
        title: str,
        description: str,
        target_blood_types: list[BloodType],
        target_units: int,
        start_date: date,
        end_date: date,
    ) -> DonationCampaign:
        if end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        campaign = DonationCampaign.create(
            hospital_id=hospital_id,
            title=title,
            description=description,
            target_blood_types=target_blood_types,
            target_units=target_units,
            start_date=start_date,
            end_date=end_date,
        )
        return await self._repo.save(campaign)

    async def activate_campaign(self, campaign_id: uuid.UUID) -> DonationCampaign:
        campaign = await self._repo.get_by_id(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        campaign.activate()
        return await self._repo.save(campaign)

    async def record_donation(self, campaign_id: uuid.UUID, units: int) -> DonationCampaign:
        campaign = await self._repo.get_by_id(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        campaign.record_donation(units)
        return await self._repo.save(campaign)

    async def cancel_campaign(self, campaign_id: uuid.UUID) -> DonationCampaign:
        campaign = await self._repo.get_by_id(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        campaign.cancel()
        return await self._repo.save(campaign)

    async def get_active_campaigns(self) -> list[DonationCampaign]:
        return await self._repo.get_active()

    async def get_hospital_campaigns(self, hospital_id: uuid.UUID) -> list[DonationCampaign]:
        return await self._repo.get_by_hospital(hospital_id)
