import pytest
from datetime import date, timedelta
from httpx import AsyncClient


async def _create_hospital(client: AsyncClient) -> dict:
    resp = await client.post("/api/v1/hospitals/", json={
        "name": "Blood Test Hospital",
        "code": "BTH",
        "city": "Florence",
        "region": "Tuscany",
        "capacity_beds": 400,
    })
    return resp.json()


async def _create_department(client: AsyncClient, hospital_id: str) -> dict:
    resp = await client.post(f"/api/v1/hospitals/{hospital_id}/departments", json={
        "name": "Surgery",
        "code": "SRG",
    })
    return resp.json()


@pytest.mark.asyncio
async def test_add_blood_units(client: AsyncClient):
    hospital = await _create_hospital(client)
    hospital_id = hospital["id"]

    response = await client.post(
        f"/api/v1/hospitals/{hospital_id}/inventory/units",
        json={
            "blood_type": "O+",
            "units_available": 25,
            "expiry_date": (date.today() + timedelta(days=14)).isoformat(),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["blood_type"] == "O+"
    assert data["units_available"] == 25


@pytest.mark.asyncio
async def test_inventory_summary(client: AsyncClient):
    hospital = await _create_hospital(client)
    hospital_id = hospital["id"]

    await client.post(
        f"/api/v1/hospitals/{hospital_id}/inventory/units",
        json={
            "blood_type": "A+",
            "units_available": 10,
            "expiry_date": (date.today() + timedelta(days=10)).isoformat(),
        },
    )

    response = await client.get(f"/api/v1/hospitals/{hospital_id}/inventory/summary")
    assert response.status_code == 200
    data = response.json()
    assert "blood_types" in data
    assert "A+" in data["blood_types"]


@pytest.mark.asyncio
async def test_consume_blood(client: AsyncClient):
    hospital = await _create_hospital(client)
    hospital_id = hospital["id"]
    dept = await _create_department(client, hospital_id)
    dept_id = dept["id"]

    await client.post(
        f"/api/v1/hospitals/{hospital_id}/inventory/units",
        json={
            "blood_type": "B+",
            "units_available": 15,
            "expiry_date": (date.today() + timedelta(days=10)).isoformat(),
        },
    )

    response = await client.post(
        f"/api/v1/hospitals/{hospital_id}/inventory/consume",
        json={
            "department_id": dept_id,
            "blood_type": "B+",
            "units": 5,
            "consumption_date": date.today().isoformat(),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["units_consumed"] == 5


@pytest.mark.asyncio
async def test_consume_insufficient_raises(client: AsyncClient):
    hospital = await _create_hospital(client)
    hospital_id = hospital["id"]
    dept = await _create_department(client, hospital_id)

    response = await client.post(
        f"/api/v1/hospitals/{hospital_id}/inventory/consume",
        json={
            "department_id": dept["id"],
            "blood_type": "AB-",
            "units": 100,
            "consumption_date": date.today().isoformat(),
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_record_wastage(client: AsyncClient):
    hospital = await _create_hospital(client)
    hospital_id = hospital["id"]

    response = await client.post(
        f"/api/v1/hospitals/{hospital_id}/inventory/wastage",
        json={
            "blood_type": "O-",
            "units_wasted": 3,
            "reason": "expired",
            "wastage_date": date.today().isoformat(),
            "notes": "Past expiry date",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["units_wasted"] == 3
    assert float(data["estimated_cost"]) == 750.0
