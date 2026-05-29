from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    CampaignCreate,
    CampaignDonationRequest,
    CampaignResponse,
)
from app.application.services.campaign import CampaignService
from app.domain.forecasting.models import DonationCampaign
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.forecasting import SQLCampaignRepository

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def get_campaign_service(session: AsyncSession = Depends(get_session)) -> CampaignService:
    return CampaignService(SQLCampaignRepository(session))


def _to_response(c: DonationCampaign) -> CampaignResponse:
    return CampaignResponse(
        id=c.id,
        hospital_id=c.hospital_id,
        title=c.title,
        description=c.description,
        target_blood_types=c.target_blood_types,
        target_units=c.target_units,
        collected_units=c.collected_units,
        progress_percentage=c.progress_percentage,
        start_date=c.start_date,
        end_date=c.end_date,
        status=c.status,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("/", response_model=list[CampaignResponse])
async def list_active_campaigns(
    svc: CampaignService = Depends(get_campaign_service),
) -> list[CampaignResponse]:
    campaigns = await svc.get_active_campaigns()
    return [_to_response(c) for c in campaigns]


@router.post("/hospitals/{hospital_id}", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    hospital_id: UUID,
    payload: CampaignCreate,
    svc: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    try:
        campaign = await svc.create_campaign(
            hospital_id=hospital_id,
            title=payload.title,
            description=payload.description,
            target_blood_types=payload.target_blood_types,
            target_units=payload.target_units,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_response(campaign)


@router.get("/hospitals/{hospital_id}", response_model=list[CampaignResponse])
async def list_hospital_campaigns(
    hospital_id: UUID,
    svc: CampaignService = Depends(get_campaign_service),
) -> list[CampaignResponse]:
    campaigns = await svc.get_hospital_campaigns(hospital_id)
    return [_to_response(c) for c in campaigns]


@router.post("/{campaign_id}/activate", response_model=CampaignResponse)
async def activate_campaign(
    campaign_id: UUID,
    svc: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    try:
        campaign = await svc.activate_campaign(campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_response(campaign)


@router.post("/{campaign_id}/donate", response_model=CampaignResponse)
async def record_donation(
    campaign_id: UUID,
    payload: CampaignDonationRequest,
    svc: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    try:
        campaign = await svc.record_donation(campaign_id, payload.units)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_response(campaign)


@router.post("/{campaign_id}/cancel", response_model=CampaignResponse)
async def cancel_campaign(
    campaign_id: UUID,
    svc: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    try:
        campaign = await svc.cancel_campaign(campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_response(campaign)
