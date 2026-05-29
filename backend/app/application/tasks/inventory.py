import asyncio

from app.infrastructure.messaging.celery_app import celery_app


@celery_app.task(name="app.application.tasks.inventory.check_expiring_blood_units", bind=True)
def check_expiring_blood_units(self) -> dict:
    """Check for blood units expiring within 3 days and cache alerts."""

    async def _run():
        from app.infrastructure.database.session import AsyncSessionLocal
        from app.infrastructure.repositories.hospital import SQLHospitalRepository
        from app.infrastructure.repositories.blood_inventory import SQLBloodInventoryRepository
        from app.infrastructure.cache.redis_client import redis_client
        import json

        async with AsyncSessionLocal() as session:
            hospital_repo = SQLHospitalRepository(session)
            hospitals = await hospital_repo.get_all()
            all_alerts = []

            for hospital in hospitals:
                inv_repo = SQLBloodInventoryRepository(session)
                expiring = await inv_repo.get_expiring_soon(hospital.id, days=3)
                for unit in expiring:
                    alert = {
                        "hospital_id": str(hospital.id),
                        "hospital_name": hospital.name,
                        "blood_type": unit.blood_type.value,
                        "units": unit.units_usable,
                        "expiry_date": unit.expiry_date.isoformat(),
                    }
                    all_alerts.append(alert)

            if all_alerts:
                await redis_client.setex(
                    "alerts:expiring_units",
                    3600,
                    json.dumps(all_alerts),
                )

            return {"expiring_alerts": len(all_alerts)}

    return asyncio.run(_run())


@celery_app.task(name="app.application.tasks.inventory.check_critical_levels", bind=True)
def check_critical_levels(self) -> dict:
    """Check for critically low blood inventory levels."""

    async def _run():
        from app.infrastructure.database.session import AsyncSessionLocal
        from app.infrastructure.repositories.hospital import SQLHospitalRepository
        from app.infrastructure.repositories.blood_inventory import SQLBloodInventoryRepository
        from app.infrastructure.cache.redis_client import redis_client
        from app.domain.enums import InventoryStatus
        import json

        async with AsyncSessionLocal() as session:
            hospital_repo = SQLHospitalRepository(session)
            hospitals = await hospital_repo.get_all()
            critical_alerts = []

            for hospital in hospitals:
                inv_repo = SQLBloodInventoryRepository(session)
                units = await inv_repo.get_by_hospital(hospital.id)
                for unit in units:
                    if unit.status in (InventoryStatus.CRITICAL, InventoryStatus.LOW):
                        critical_alerts.append({
                            "hospital_id": str(hospital.id),
                            "hospital_name": hospital.name,
                            "blood_type": unit.blood_type.value,
                            "units_available": unit.units_usable,
                            "status": unit.status.value,
                        })

            if critical_alerts:
                await redis_client.setex(
                    "alerts:critical_levels",
                    1800,
                    json.dumps(critical_alerts),
                )

            return {"critical_alerts": len(critical_alerts)}

    return asyncio.run(_run())
