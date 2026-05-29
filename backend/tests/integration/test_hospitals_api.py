import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_hospital(client: AsyncClient):
    payload = {
        "name": "Ospedale San Raffaele",
        "code": "OSR",
        "city": "Milan",
        "region": "Lombardia",
        "capacity_beds": 1200,
    }
    response = await client.post("/api/v1/hospitals/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ospedale San Raffaele"
    assert data["code"] == "OSR"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_hospitals(client: AsyncClient):
    for i in range(3):
        await client.post("/api/v1/hospitals/", json={
            "name": f"Hospital {i}",
            "code": f"H{i:03d}",
            "city": "Rome",
            "region": "Lazio",
            "capacity_beds": 500,
        })
    response = await client.get("/api/v1/hospitals/")
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_get_hospital_not_found(client: AsyncClient):
    from uuid import uuid4
    response = await client.get(f"/api/v1/hospitals/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_department(client: AsyncClient):
    hospital_resp = await client.post("/api/v1/hospitals/", json={
        "name": "Test Hospital",
        "code": "TH001",
        "city": "Rome",
        "region": "Lazio",
        "capacity_beds": 300,
    })
    hospital_id = hospital_resp.json()["id"]

    dept_resp = await client.post(f"/api/v1/hospitals/{hospital_id}/departments", json={
        "name": "Emergency",
        "code": "EM",
    })
    assert dept_resp.status_code == 201
    assert dept_resp.json()["name"] == "Emergency"
