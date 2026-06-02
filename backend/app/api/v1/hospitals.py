from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import HospitalCreate, HospitalResponse, DepartmentCreate, DepartmentResponse
from app.domain.blood_inventory.models import Hospital, Department
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.hospital import SQLHospitalRepository, SQLDepartmentRepository

router = APIRouter(prefix="/hospitals", tags=["hospitals"])


@router.get("/", response_model=list[HospitalResponse])
async def list_hospitals(session: AsyncSession = Depends(get_session)) -> list[Hospital]:
    repo = SQLHospitalRepository(session)
    return await repo.get_all()


@router.post("/", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED)
async def create_hospital(
    payload: HospitalCreate,
    session: AsyncSession = Depends(get_session),
) -> Hospital:
    repo = SQLHospitalRepository(session)
    hospital = Hospital.create(
        name=payload.name,
        code=payload.code,
        city=payload.city,
        region=payload.region,
        capacity_beds=payload.capacity_beds,
    )
    return await repo.save(hospital)


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Hospital:
    repo = SQLHospitalRepository(session)
    hospital = await repo.get_by_id(hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital


@router.delete("/{hospital_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hospital(
    hospital_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    repo = SQLHospitalRepository(session)
    await repo.delete(hospital_id)


# ── Departments ──────────────────────────────────────────────────────────────

@router.get("/{hospital_id}/departments", response_model=list[DepartmentResponse])
async def list_departments(
    hospital_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[Department]:
    repo = SQLDepartmentRepository(session)
    return await repo.get_by_hospital(hospital_id)


@router.post(
    "/{hospital_id}/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    hospital_id: UUID,
    payload: DepartmentCreate,
    session: AsyncSession = Depends(get_session),
) -> Department:
    hospital_repo = SQLHospitalRepository(session)
    if not await hospital_repo.get_by_id(hospital_id):
        raise HTTPException(status_code=404, detail="Hospital not found")

    dept = Department.create(
        hospital_id=hospital_id,
        name=payload.name,
        code=payload.code,
    )
    repo = SQLDepartmentRepository(session)
    return await repo.save(dept)
