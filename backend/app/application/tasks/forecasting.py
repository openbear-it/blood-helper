from celery import shared_task

from app.infrastructure.messaging.celery_app import celery_app


@celery_app.task(name="app.application.tasks.forecasting.run_all_forecasts", bind=True, max_retries=3)
def run_all_forecasts(self) -> dict:
    """Run daily forecasts for all hospitals and blood types."""
    import asyncio
    from app.domain.enums import BloodType, ForecastHorizon

    async def _run():
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.infrastructure.database.session import AsyncSessionLocal
        from app.infrastructure.repositories.hospital import SQLHospitalRepository
        from app.infrastructure.repositories.blood_inventory import SQLConsumptionRepository
        from app.infrastructure.repositories.forecasting import SQLForecastRepository
        from app.application.services.forecasting import ForecastingService

        async with AsyncSessionLocal() as session:
            hospital_repo = SQLHospitalRepository(session)
            hospitals = await hospital_repo.get_all()
            total = 0
            for hospital in hospitals:
                consumption_repo = SQLConsumptionRepository(session)
                forecast_repo = SQLForecastRepository(session)
                svc = ForecastingService(consumption_repo, forecast_repo)
                for blood_type in BloodType:
                    for horizon in ForecastHorizon:
                        try:
                            results = await svc.run_forecast(
                                hospital.id, blood_type, horizon
                            )
                            total += len(results)
                        except Exception as e:
                            pass
            await session.commit()
            return {"forecasts_generated": total, "hospitals": len(hospitals)}

    return asyncio.run(_run())


@celery_app.task(name="app.application.tasks.forecasting.run_hospital_forecast", bind=True)
def run_hospital_forecast(self, hospital_id: str, blood_type: str, horizon: str) -> dict:
    import asyncio
    from uuid import UUID
    from app.domain.enums import BloodType, ForecastHorizon

    async def _run():
        from app.infrastructure.database.session import AsyncSessionLocal
        from app.infrastructure.repositories.blood_inventory import SQLConsumptionRepository
        from app.infrastructure.repositories.forecasting import SQLForecastRepository
        from app.application.services.forecasting import ForecastingService

        async with AsyncSessionLocal() as session:
            svc = ForecastingService(
                SQLConsumptionRepository(session),
                SQLForecastRepository(session),
            )
            results = await svc.run_forecast(
                UUID(hospital_id),
                BloodType(blood_type),
                ForecastHorizon(horizon),
            )
            await session.commit()
            return {"forecasts_generated": len(results)}

    return asyncio.run(_run())
