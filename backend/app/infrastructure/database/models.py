from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain.enums import (
    BloodType,
    CampaignStatus,
    ForecastHorizon,
    InventoryStatus,
    WastageReason,
)


class Base(DeclarativeBase):
    pass


class HospitalORM(Base):
    __tablename__ = "hospitals"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity_beds: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    departments: Mapped[list["DepartmentORM"]] = relationship(back_populates="hospital")
    blood_units: Mapped[list["BloodUnitORM"]] = relationship(back_populates="hospital")
    consumption_records: Mapped[list["BloodConsumptionORM"]] = relationship(back_populates="hospital")
    wastage_records: Mapped[list["WastageORM"]] = relationship(back_populates="hospital")
    campaigns: Mapped[list["DonationCampaignORM"]] = relationship(back_populates="hospital")


class DepartmentORM(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hospitals.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("hospital_id", "code", name="uq_dept_hospital_code"),)

    hospital: Mapped["HospitalORM"] = relationship(back_populates="departments")
    consumption_records: Mapped[list["BloodConsumptionORM"]] = relationship(back_populates="department")
    forecasts: Mapped[list["ForecastResultORM"]] = relationship(back_populates="department")


class BloodUnitORM(Base):
    __tablename__ = "blood_units"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hospitals.id"), nullable=False)
    blood_type: Mapped[BloodType] = mapped_column(SAEnum(BloodType), nullable=False)
    units_available: Mapped[int] = mapped_column(Integer, nullable=False)
    units_reserved: Mapped[int] = mapped_column(Integer, default=0)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hospital: Mapped["HospitalORM"] = relationship(back_populates="blood_units")


class BloodConsumptionORM(Base):
    __tablename__ = "blood_consumption_records"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hospitals.id"), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"), nullable=False)
    blood_type: Mapped[BloodType] = mapped_column(SAEnum(BloodType), nullable=False)
    units_consumed: Mapped[int] = mapped_column(Integer, nullable=False)
    consumption_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hospital: Mapped["HospitalORM"] = relationship(back_populates="consumption_records")
    department: Mapped["DepartmentORM"] = relationship(back_populates="consumption_records")


class WastageORM(Base):
    __tablename__ = "wastage_records"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hospitals.id"), nullable=False)
    blood_type: Mapped[BloodType] = mapped_column(SAEnum(BloodType), nullable=False)
    units_wasted: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[WastageReason] = mapped_column(SAEnum(WastageReason), nullable=False)
    wastage_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hospital: Mapped["HospitalORM"] = relationship(back_populates="wastage_records")


class ForecastResultORM(Base):
    __tablename__ = "forecast_results"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hospitals.id"), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    blood_type: Mapped[BloodType] = mapped_column(SAEnum(BloodType), nullable=False)
    horizon: Mapped[ForecastHorizon] = mapped_column(SAEnum(ForecastHorizon), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_units: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    lower_bound: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    upper_bound: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    department: Mapped["DepartmentORM | None"] = relationship(back_populates="forecasts")


class DonationCampaignORM(Base):
    __tablename__ = "donation_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hospitals.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    target_blood_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    target_units: Mapped[int] = mapped_column(Integer, nullable=False)
    collected_units: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(SAEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hospital: Mapped["HospitalORM"] = relationship(back_populates="campaigns")
