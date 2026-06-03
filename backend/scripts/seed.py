"""
Seed script — populates the database with realistic Italian hospital data.

Usage (from backend/ directory):
    python -m scripts.seed
"""
from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.enums import BloodType, CampaignStatus, ForecastHorizon, WastageReason
from app.infrastructure.database.models import (
    Base,
    BloodConsumptionORM,
    BloodUnitORM,
    DepartmentORM,
    DonationCampaignORM,
    ForecastResultORM,
    HospitalORM,
    WastageORM,
)

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

TODAY = date.today()

# ---------------------------------------------------------------------------
# Master data
# ---------------------------------------------------------------------------

HOSPITALS = [
    {"name": "Ospedale Policlinico Umberto I", "code": "RM001", "city": "Roma", "region": "Lazio", "capacity_beds": 1500},
    {"name": "Ospedale San Raffaele", "code": "MI001", "city": "Milano", "region": "Lombardia", "capacity_beds": 1350},
    {"name": "Azienda Ospedaliera di Padova", "code": "PD001", "city": "Padova", "region": "Veneto", "capacity_beds": 950},
    {"name": "Ospedale Civile SS. Giovanni e Paolo", "code": "VE001", "city": "Venezia", "region": "Veneto", "capacity_beds": 600},
    {"name": "Ospedale Maggiore di Bologna", "code": "BO001", "city": "Bologna", "region": "Emilia-Romagna", "capacity_beds": 780},
]

DEPARTMENTS_PER_HOSPITAL = [
    {"name": "Cardiologia", "code": "CARD"},
    {"name": "Chirurgia Generale", "code": "CHIR"},
    {"name": "Ematologia", "code": "EMAT"},
    {"name": "Terapia Intensiva", "code": "ICU"},
    {"name": "Ortopedia", "code": "ORTO"},
    {"name": "Oncologia", "code": "ONCO"},
]

# Blood type distribution (approximate Italian population distribution)
BLOOD_TYPE_WEIGHTS = {
    BloodType.A_POSITIVE: 36,
    BloodType.A_NEGATIVE: 7,
    BloodType.B_POSITIVE: 8,
    BloodType.B_NEGATIVE: 2,
    BloodType.AB_POSITIVE: 4,
    BloodType.AB_NEGATIVE: 1,
    BloodType.O_POSITIVE: 38,
    BloodType.O_NEGATIVE: 7,
}

BLOOD_TYPES = list(BLOOD_TYPE_WEIGHTS.keys())
BT_WEIGHTS_LIST = list(BLOOD_TYPE_WEIGHTS.values())


def weighted_blood_type() -> BloodType:
    return random.choices(BLOOD_TYPES, weights=BT_WEIGHTS_LIST, k=1)[0]


def rand_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Seeding helpers
# ---------------------------------------------------------------------------

def seed_hospitals(session: Session) -> list[HospitalORM]:
    hospitals = []
    for h in HOSPITALS:
        orm = HospitalORM(id=rand_uuid(), **h)
        session.add(orm)
        hospitals.append(orm)
    session.flush()
    return hospitals


def seed_departments(session: Session, hospitals: list[HospitalORM]) -> list[DepartmentORM]:
    departments: list[DepartmentORM] = []
    for hospital in hospitals:
        for dept in DEPARTMENTS_PER_HOSPITAL:
            orm = DepartmentORM(
                id=rand_uuid(),
                hospital_id=hospital.id,
                name=dept["name"],
                code=dept["code"],
            )
            session.add(orm)
            departments.append(orm)
    session.flush()
    return departments


def seed_blood_units(session: Session, hospitals: list[HospitalORM]) -> None:
    for hospital in hospitals:
        for blood_type in BLOOD_TYPES:
            # Each hospital has 1-3 batches per blood type with different expiry dates
            batches = random.randint(1, 3)
            for _ in range(batches):
                units = random.randint(5, 120)
                expiry = TODAY + timedelta(days=random.randint(3, 42))
                orm = BloodUnitORM(
                    id=rand_uuid(),
                    hospital_id=hospital.id,
                    blood_type=blood_type,
                    units_available=units,
                    units_reserved=random.randint(0, max(1, units // 5)),
                    expiry_date=expiry,
                )
                session.add(orm)
    session.flush()


def seed_consumption_records(
    session: Session,
    hospitals: list[HospitalORM],
    departments: list[DepartmentORM],
    days: int = 180,
) -> None:
    dept_by_hospital: dict[uuid.UUID, list[DepartmentORM]] = {}
    for dept in departments:
        dept_by_hospital.setdefault(dept.hospital_id, []).append(dept)

    for hospital in hospitals:
        hospital_depts = dept_by_hospital.get(hospital.id, [])
        if not hospital_depts:
            continue
        for i in range(days):
            record_date = TODAY - timedelta(days=days - i)
            # 3-6 consumption records per day per hospital
            for _ in range(random.randint(3, 6)):
                dept = random.choice(hospital_depts)
                orm = BloodConsumptionORM(
                    id=rand_uuid(),
                    hospital_id=hospital.id,
                    department_id=dept.id,
                    blood_type=weighted_blood_type(),
                    units_consumed=random.randint(1, 8),
                    consumption_date=record_date,
                )
                session.add(orm)
    session.flush()


def seed_wastage_records(
    session: Session,
    hospitals: list[HospitalORM],
    days: int = 90,
) -> None:
    reasons = list(WastageReason)
    reason_weights = [60, 15, 20, 5]  # expired dominates

    for hospital in hospitals:
        # ~2 wastage events per week per hospital
        for i in range(0, days, 3):
            if random.random() < 0.6:
                continue
            record_date = TODAY - timedelta(days=days - i)
            reason = random.choices(reasons, weights=reason_weights, k=1)[0]
            cost_per_unit = Decimal(str(round(random.uniform(150, 400), 2)))
            units = random.randint(1, 5)
            orm = WastageORM(
                id=rand_uuid(),
                hospital_id=hospital.id,
                blood_type=weighted_blood_type(),
                units_wasted=units,
                reason=reason,
                wastage_date=record_date,
                notes=f"Registrazione automatica — {reason.value}",
                estimated_cost=cost_per_unit * units,
            )
            session.add(orm)
    session.flush()


def seed_campaigns(session: Session, hospitals: list[HospitalORM]) -> None:
    campaign_templates = [
        {"title": "Campagna Emergenza Estate", "description": "Raccolta urgente per scorte estive"},
        {"title": "Donatori Solidali", "description": "Campagna mensile per gruppi rari"},
        {"title": "Maratona del Sangue", "description": "Evento annuale di raccolta sangue"},
    ]

    for hospital in hospitals:
        # 1 active campaign
        tmpl = random.choice(campaign_templates)
        active = DonationCampaignORM(
            id=rand_uuid(),
            hospital_id=hospital.id,
            title=f"{tmpl['title']} — {hospital.city}",
            description=tmpl["description"],
            target_blood_types=random.sample(
                [bt.value for bt in BLOOD_TYPES], k=random.randint(2, 4)
            ),
            target_units=random.randint(50, 200),
            collected_units=random.randint(10, 60),
            start_date=TODAY - timedelta(days=random.randint(5, 15)),
            end_date=TODAY + timedelta(days=random.randint(10, 30)),
            status=CampaignStatus.ACTIVE,
        )
        session.add(active)

        # 1 completed campaign
        completed = DonationCampaignORM(
            id=rand_uuid(),
            hospital_id=hospital.id,
            title=f"Campagna Primaverile — {hospital.city}",
            description="Raccolta completata con successo",
            target_blood_types=random.sample(
                [bt.value for bt in BLOOD_TYPES], k=random.randint(2, 4)
            ),
            target_units=random.randint(50, 150),
            collected_units=random.randint(60, 150),
            start_date=TODAY - timedelta(days=60),
            end_date=TODAY - timedelta(days=10),
            status=CampaignStatus.COMPLETED,
        )
        session.add(completed)

        # 1 draft campaign
        draft = DonationCampaignORM(
            id=rand_uuid(),
            hospital_id=hospital.id,
            title=f"Campagna Autunnale — {hospital.city}",
            description="In pianificazione",
            target_blood_types=random.sample(
                [bt.value for bt in BLOOD_TYPES], k=random.randint(2, 5)
            ),
            target_units=random.randint(80, 250),
            collected_units=0,
            start_date=TODAY + timedelta(days=30),
            end_date=TODAY + timedelta(days=90),
            status=CampaignStatus.DRAFT,
        )
        session.add(draft)

    session.flush()


def seed_forecast_results(
    session: Session,
    hospitals: list[HospitalORM],
    departments: list[DepartmentORM],
) -> None:
    dept_by_hospital: dict[uuid.UUID, list[DepartmentORM]] = {}
    for dept in departments:
        dept_by_hospital.setdefault(dept.hospital_id, []).append(dept)

    horizons = [ForecastHorizon.DAILY, ForecastHorizon.WEEKLY]
    models = ["prophet", "xgboost"]

    for hospital in hospitals:
        for blood_type in BLOOD_TYPES:
            for horizon in horizons:
                days = 30 if horizon == ForecastHorizon.DAILY else 12
                for day_offset in range(1, days + 1):
                    base = random.uniform(5, 30)
                    noise = random.uniform(0.8, 1.2)
                    predicted = round(base * noise, 2)
                    margin = round(predicted * random.uniform(0.1, 0.25), 2)
                    forecast_date = (
                        TODAY + timedelta(days=day_offset)
                        if horizon == ForecastHorizon.DAILY
                        else TODAY + timedelta(weeks=day_offset)
                    )
                    orm = ForecastResultORM(
                        id=rand_uuid(),
                        hospital_id=hospital.id,
                        department_id=None,
                        blood_type=blood_type,
                        horizon=horizon,
                        forecast_date=forecast_date,
                        predicted_units=Decimal(str(predicted)),
                        lower_bound=Decimal(str(round(predicted - margin, 2))),
                        upper_bound=Decimal(str(round(predicted + margin, 2))),
                        model_name=random.choice(models),
                        confidence=Decimal(str(round(random.uniform(0.75, 0.98), 4))),
                    )
                    session.add(orm)
    session.flush()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    engine = create_engine(settings.DATABASE_URL_SYNC, echo=False)

    print("Connecting to database…")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Connection OK.")

    with Session(engine) as session:
        # Check for existing data
        existing = session.query(HospitalORM).count()
        if existing > 0:
            print(f"Database already has {existing} hospital(s) — skipping seed.")
            return

        print("Seeding hospitals…")
        hospitals = seed_hospitals(session)

        print("Seeding departments…")
        departments = seed_departments(session, hospitals)

        print("Seeding blood units…")
        seed_blood_units(session, hospitals)

        print("Seeding consumption records (180 days)…")
        seed_consumption_records(session, hospitals, departments, days=180)

        print("Seeding wastage records (90 days)…")
        seed_wastage_records(session, hospitals, days=90)

        print("Seeding donation campaigns…")
        seed_campaigns(session, hospitals)

        print("Seeding forecast results…")
        seed_forecast_results(session, hospitals, departments)

        session.commit()
        print("Seed completed successfully.")
        print(f"  Hospitals : {len(hospitals)}")
        print(f"  Departments: {len(DEPARTMENTS_PER_HOSPITAL) * len(hospitals)}")


if __name__ == "__main__":
    main()
