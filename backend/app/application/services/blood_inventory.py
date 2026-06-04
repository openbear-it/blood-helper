from __future__ import annotations

import uuid
from datetime import date, timedelta

from app.domain.blood_inventory.models import BloodConsumptionRecord, BloodUnit, WastageRecord
from app.domain.blood_inventory.repositories import (
    BloodInventoryRepository,
    ConsumptionRepository,
    WastageRepository,
)
from app.domain.enums import BloodType, WastageReason
from app.infrastructure.cache.redis_client import redis_client


class BloodInventoryService:
    CRITICAL_THRESHOLD = 5
    LOW_THRESHOLD = 10

    def __init__(
        self,
        inventory_repo: BloodInventoryRepository,
        consumption_repo: ConsumptionRepository,
        wastage_repo: WastageRepository,
    ) -> None:
        self._inventory = inventory_repo
        self._consumption = consumption_repo
        self._wastage = wastage_repo

    async def add_blood_units(
        self,
        hospital_id: uuid.UUID,
        blood_type: BloodType,
        units: int,
        expiry_date: date,
    ) -> BloodUnit:
        unit = BloodUnit.create(
            hospital_id=hospital_id,
            blood_type=blood_type,
            units_available=units,
            expiry_date=expiry_date,
        )
        saved = await self._inventory.save(unit)
        await self._invalidate_inventory_cache(hospital_id)
        return saved

    async def consume_blood(
        self,
        hospital_id: uuid.UUID,
        department_id: uuid.UUID,
        blood_type: BloodType,
        units: int,
        consumption_date: date,
    ) -> BloodConsumptionRecord:
        units_available = await self._inventory.get_by_hospital_and_type(hospital_id, blood_type)
        remaining = units
        for unit in sorted(units_available, key=lambda u: u.expiry_date):
            if remaining <= 0:
                break
            if unit.units_usable > 0:
                to_consume = min(remaining, unit.units_usable)
                unit.consume(to_consume)
                await self._inventory.save(unit)
                remaining -= to_consume

        if remaining > 0:
            raise ValueError(f"Insufficient {blood_type.value} blood: {remaining} units short")

        record = BloodConsumptionRecord.create(
            hospital_id=hospital_id,
            department_id=department_id,
            blood_type=blood_type,
            units_consumed=units,
            consumption_date=consumption_date,
        )
        saved = await self._consumption.save(record)
        await self._invalidate_inventory_cache(hospital_id)
        return saved

    async def record_wastage(
        self,
        hospital_id: uuid.UUID,
        blood_type: BloodType,
        units: int,
        reason: WastageReason,
        wastage_date: date,
        notes: str = "",
    ) -> WastageRecord:
        record = WastageRecord.create(
            hospital_id=hospital_id,
            blood_type=blood_type,
            units_wasted=units,
            reason=reason,
            wastage_date=wastage_date,
            notes=notes,
        )
        return await self._wastage.save(record)

    async def get_inventory_summary(self, hospital_id: uuid.UUID) -> dict:
        cache_key = f"inventory:summary:{hospital_id}"
        cached = await redis_client.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        units = await self._inventory.get_by_hospital(hospital_id)
        summary: dict[str, dict] = {}
        for unit in units:
            bt = unit.blood_type.value
            if bt not in summary:
                summary[bt] = {"available": 0, "reserved": 0, "expiring_soon": 0}
            summary[bt]["available"] += unit.units_usable
            summary[bt]["reserved"] += unit.units_reserved
            if unit.expiry_date <= date.today() + timedelta(days=3):
                summary[bt]["expiring_soon"] += unit.units_usable

        result = {
            "hospital_id": str(hospital_id),
            "blood_types": summary,
            "critical_types": [
                bt for bt, data in summary.items()
                if data["available"] < self.CRITICAL_THRESHOLD
            ],
        }
        import json
        await redis_client.setex(cache_key, 300, json.dumps(result))
        return result

    async def get_expiring_units(self, hospital_id: uuid.UUID, days: int = 3) -> list[BloodUnit]:
        return await self._inventory.get_expiring_soon(hospital_id, days)

    async def get_wastage_analysis(
        self, hospital_id: uuid.UUID, start_date: date, end_date: date
    ) -> dict:
        records = await self._wastage.get_by_hospital(hospital_id, start_date, end_date)
        by_type: dict[str, dict] = {}
        by_reason: dict[str, int] = {}
        total_units = 0
        total_cost = 0

        for r in records:
            bt = r.blood_type.value
            if bt not in by_type:
                by_type[bt] = {"units": 0, "cost": 0}
            by_type[bt]["units"] += r.units_wasted
            by_type[bt]["cost"] += float(r.estimated_cost)

            rn = r.reason.value
            by_reason[rn] = by_reason.get(rn, 0) + r.units_wasted

            total_units += r.units_wasted
            total_cost += float(r.estimated_cost)

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_units_wasted": total_units,
            "total_estimated_cost": total_cost,
            "by_blood_type": by_type,
            "by_reason": by_reason,
        }

    async def get_history(
        self,
        hospital_id: uuid.UUID,
        start_date: date,
        end_date: date,
        blood_type: BloodType | None = None,
    ) -> dict:
        from collections import defaultdict

        consumption_records = await self._consumption.get_by_hospital(hospital_id, start_date, end_date)
        wastage_records = await self._wastage.get_by_hospital(hospital_id, start_date, end_date)

        if blood_type is not None:
            consumption_records = [r for r in consumption_records if r.blood_type == blood_type]
            wastage_records = [r for r in wastage_records if r.blood_type == blood_type]

        daily: dict[tuple[str, str], dict] = defaultdict(
            lambda: {"units_consumed": 0, "units_wasted": 0, "wastage_cost": 0.0}
        )

        for r in consumption_records:
            key = (r.consumption_date.isoformat(), r.blood_type.value)
            daily[key]["units_consumed"] += r.units_consumed

        for r in wastage_records:
            key = (r.wastage_date.isoformat(), r.blood_type.value)
            daily[key]["units_wasted"] += r.units_wasted
            daily[key]["wastage_cost"] += float(r.estimated_cost)

        data = [
            {
                "date": k[0],
                "blood_type": k[1],
                "units_consumed": v["units_consumed"],
                "units_wasted": v["units_wasted"],
                "wastage_cost": v["wastage_cost"],
            }
            for k, v in sorted(daily.items())
        ]

        by_type: dict[str, dict] = {}
        for r in consumption_records:
            bt = r.blood_type.value
            if bt not in by_type:
                by_type[bt] = {"consumed": 0, "wasted": 0, "wastage_cost": 0.0}
            by_type[bt]["consumed"] += r.units_consumed
        for r in wastage_records:
            bt = r.blood_type.value
            if bt not in by_type:
                by_type[bt] = {"consumed": 0, "wasted": 0, "wastage_cost": 0.0}
            by_type[bt]["wasted"] += r.units_wasted
            by_type[bt]["wastage_cost"] += float(r.estimated_cost)

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "data": data,
            "summary": {
                "total_consumed": sum(r.units_consumed for r in consumption_records),
                "total_wasted": sum(r.units_wasted for r in wastage_records),
                "total_wastage_cost": sum(float(r.estimated_cost) for r in wastage_records),
                "by_blood_type": by_type,
            },
        }

    async def _invalidate_inventory_cache(self, hospital_id: uuid.UUID) -> None:
        await redis_client.delete(f"inventory:summary:{hospital_id}")
