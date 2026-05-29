import asyncio
from datetime import date

from app.infrastructure.messaging.celery_app import celery_app


@celery_app.task(name="app.application.tasks.campaigns.auto_activate_campaigns", bind=True)
def auto_activate_campaigns(self) -> dict:
    """Auto-activate campaigns whose start date has arrived."""

    async def _run():
        from app.infrastructure.database.session import AsyncSessionLocal
        from app.infrastructure.repositories.forecasting import SQLCampaignRepository
        from app.application.services.campaign import CampaignService
        from app.domain.enums import CampaignStatus

        async with AsyncSessionLocal() as session:
            repo = SQLCampaignRepository(session)
            # get all draft campaigns whose start date <= today
            from sqlalchemy import select
            from app.infrastructure.database.models import DonationCampaignORM

            stmt = select(DonationCampaignORM).where(
                DonationCampaignORM.status == CampaignStatus.DRAFT,
                DonationCampaignORM.start_date <= date.today(),
            )
            result = await session.execute(stmt)
            campaigns_to_activate = result.scalars().all()

            activated = 0
            svc = CampaignService(repo)
            for orm in campaigns_to_activate:
                try:
                    await svc.activate_campaign(orm.id)
                    activated += 1
                except Exception:
                    pass

            await session.commit()
            return {"activated": activated}

    return asyncio.run(_run())
