from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.enums import BloodType, InventoryStatus, WastageReason


@dataclass
class Hospital:
    id: UUID
    name: str
    code: str
    city: str
    region: str
    capacity_beds: int
    created_at: datetime

    @staticmethod
    def create(name: str, code: str, city: str, region: str, capacity_beds: int) -> "Hospital":
        return Hospital(
            id=uuid4(),
            name=name,
            code=code,
            city=city,
            region=region,
            capacity_beds=capacity_beds,
            created_at=datetime.utcnow(),
        )


@dataclass
class Department:
    id: UUID
    hospital_id: UUID
    name: str
    code: str
    created_at: datetime

    @staticmethod
    def create(hospital_id: UUID, name: str, code: str) -> "Department":
        return Department(
            id=uuid4(),
            hospital_id=hospital_id,
            name=name,
            code=code,
            created_at=datetime.utcnow(),
        )


@dataclass
class BloodUnit:
    id: UUID
    hospital_id: UUID
    blood_type: BloodType
    units_available: int
    units_reserved: int
    expiry_date: date
    last_updated: datetime

    @property
    def units_usable(self) -> int:
        return max(0, self.units_available - self.units_reserved)

    @property
    def status(self) -> InventoryStatus:
        if self.units_usable == 0:
            return InventoryStatus.CRITICAL
        if self.units_usable < 5:
            return InventoryStatus.LOW
        if self.units_usable > 50:
            return InventoryStatus.SURPLUS
        return InventoryStatus.ADEQUATE

    @property
    def is_expired(self) -> bool:
        return self.expiry_date < date.today()

    def reserve(self, units: int) -> None:
        if units > self.units_usable:
            raise ValueError(f"Cannot reserve {units} units, only {self.units_usable} usable")
        self.units_reserved += units
        self.last_updated = datetime.utcnow()

    def release(self, units: int) -> None:
        self.units_reserved = max(0, self.units_reserved - units)
        self.last_updated = datetime.utcnow()

    def consume(self, units: int) -> None:
        if units > self.units_usable:
            raise ValueError(f"Cannot consume {units} units, only {self.units_usable} usable")
        self.units_available -= units
        self.last_updated = datetime.utcnow()

    @staticmethod
    def create(
        hospital_id: UUID,
        blood_type: BloodType,
        units_available: int,
        expiry_date: date,
    ) -> "BloodUnit":
        return BloodUnit(
            id=uuid4(),
            hospital_id=hospital_id,
            blood_type=blood_type,
            units_available=units_available,
            units_reserved=0,
            expiry_date=expiry_date,
            last_updated=datetime.utcnow(),
        )


@dataclass
class BloodConsumptionRecord:
    id: UUID
    hospital_id: UUID
    department_id: UUID
    blood_type: BloodType
    units_consumed: int
    consumption_date: date
    created_at: datetime

    @staticmethod
    def create(
        hospital_id: UUID,
        department_id: UUID,
        blood_type: BloodType,
        units_consumed: int,
        consumption_date: date,
    ) -> "BloodConsumptionRecord":
        return BloodConsumptionRecord(
            id=uuid4(),
            hospital_id=hospital_id,
            department_id=department_id,
            blood_type=blood_type,
            units_consumed=units_consumed,
            consumption_date=consumption_date,
            created_at=datetime.utcnow(),
        )


@dataclass
class WastageRecord:
    id: UUID
    hospital_id: UUID
    blood_type: BloodType
    units_wasted: int
    reason: WastageReason
    wastage_date: date
    notes: str
    created_at: datetime
    estimated_cost: Decimal = field(default=Decimal("0"))

    COST_PER_UNIT = Decimal("250.00")  # EUR per unit

    def __post_init__(self) -> None:
        self.estimated_cost = Decimal(self.units_wasted) * self.COST_PER_UNIT

    @staticmethod
    def create(
        hospital_id: UUID,
        blood_type: BloodType,
        units_wasted: int,
        reason: WastageReason,
        wastage_date: date,
        notes: str = "",
    ) -> "WastageRecord":
        return WastageRecord(
            id=uuid4(),
            hospital_id=hospital_id,
            blood_type=blood_type,
            units_wasted=units_wasted,
            reason=reason,
            wastage_date=wastage_date,
            notes=notes,
            created_at=datetime.utcnow(),
        )
