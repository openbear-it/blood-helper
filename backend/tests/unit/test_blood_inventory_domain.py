import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.domain.blood_inventory.models import BloodUnit, BloodConsumptionRecord, WastageRecord
from app.domain.enums import BloodType, InventoryStatus, WastageReason


class TestBloodUnit:
    def test_create_blood_unit(self):
        unit = BloodUnit.create(
            hospital_id=uuid4(),
            blood_type=BloodType.O_POSITIVE,
            units_available=20,
            expiry_date=date.today() + timedelta(days=14),
        )
        assert unit.units_available == 20
        assert unit.units_reserved == 0
        assert unit.units_usable == 20
        assert unit.blood_type == BloodType.O_POSITIVE

    def test_status_adequate(self):
        unit = BloodUnit.create(uuid4(), BloodType.A_POSITIVE, 15, date.today() + timedelta(days=10))
        assert unit.status == InventoryStatus.ADEQUATE

    def test_status_low(self):
        unit = BloodUnit.create(uuid4(), BloodType.A_POSITIVE, 3, date.today() + timedelta(days=10))
        assert unit.status == InventoryStatus.LOW

    def test_status_critical(self):
        unit = BloodUnit.create(uuid4(), BloodType.A_POSITIVE, 0, date.today() + timedelta(days=10))
        assert unit.status == InventoryStatus.CRITICAL

    def test_status_surplus(self):
        unit = BloodUnit.create(uuid4(), BloodType.A_POSITIVE, 60, date.today() + timedelta(days=10))
        assert unit.status == InventoryStatus.SURPLUS

    def test_consume_blood(self):
        unit = BloodUnit.create(uuid4(), BloodType.O_NEGATIVE, 10, date.today() + timedelta(days=7))
        unit.consume(3)
        assert unit.units_available == 7

    def test_consume_raises_when_insufficient(self):
        unit = BloodUnit.create(uuid4(), BloodType.O_NEGATIVE, 2, date.today() + timedelta(days=7))
        with pytest.raises(ValueError):
            unit.consume(5)

    def test_reserve_and_release(self):
        unit = BloodUnit.create(uuid4(), BloodType.B_POSITIVE, 10, date.today() + timedelta(days=7))
        unit.reserve(3)
        assert unit.units_reserved == 3
        assert unit.units_usable == 7
        unit.release(3)
        assert unit.units_reserved == 0

    def test_is_expired(self):
        unit = BloodUnit.create(uuid4(), BloodType.AB_POSITIVE, 5, date.today() - timedelta(days=1))
        assert unit.is_expired is True


class TestWastageRecord:
    def test_estimated_cost(self):
        record = WastageRecord.create(
            hospital_id=uuid4(),
            blood_type=BloodType.O_POSITIVE,
            units_wasted=4,
            reason=WastageReason.EXPIRED,
            wastage_date=date.today(),
        )
        from decimal import Decimal
        assert record.estimated_cost == Decimal("1000.00")
