import pytest
from datetime import date, timedelta
from httpx import AsyncClient


async def _create_hospital(client: AsyncClient, code: str = "CH001") -> dict:
    resp = await client.post("/api/v1/hospitals/", json={
        "name": "Campaign Hospital",
        "code": code,
        "city": "Naples",
        "region": "Campania",
        "capacity_beds": 600,
    })
    return resp.json()


@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient):
    hospital = await _create_hospital(client)
    hospital_id = hospital["id"]

    response = await client.post(f"/api/v1/campaigns/hospitals/{hospital_id}", json={
        "title": "Summer Blood Drive",
        "description": "Help save lives",
        "target_blood_types": ["O+", "O-"],
        "target_units": 200,
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=30)).isoformat(),
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Summer Blood Drive"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_activate_campaign(client: AsyncClient):
    hospital = await _create_hospital(client, "CH002")
    hospital_id = hospital["id"]

    create_resp = await client.post(f"/api/v1/campaigns/hospitals/{hospital_id}", json={
        "title": "Test Campaign",
        "description": "",
        "target_blood_types": ["A+"],
        "target_units": 50,
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=7)).isoformat(),
    })
    campaign_id = create_resp.json()["id"]

    activate_resp = await client.post(f"/api/v1/campaigns/{campaign_id}/activate")
    assert activate_resp.status_code == 200
    assert activate_resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_donate_to_campaign(client: AsyncClient):
    hospital = await _create_hospital(client, "CH003")
    hospital_id = hospital["id"]

    create_resp = await client.post(f"/api/v1/campaigns/hospitals/{hospital_id}", json={
        "title": "Donate Campaign",
        "description": "",
        "target_blood_types": ["B+"],
        "target_units": 100,
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=14)).isoformat(),
    })
    campaign_id = create_resp.json()["id"]
    await client.post(f"/api/v1/campaigns/{campaign_id}/activate")

    donate_resp = await client.post(f"/api/v1/campaigns/{campaign_id}/donate", json={"units": 30})
    assert donate_resp.status_code == 200
    assert donate_resp.json()["collected_units"] == 30
    assert donate_resp.json()["progress_percentage"] == 30.0


@pytest.mark.asyncio
async def test_list_active_campaigns(client: AsyncClient):
    hospital = await _create_hospital(client, "CH004")
    hospital_id = hospital["id"]

    create_resp = await client.post(f"/api/v1/campaigns/hospitals/{hospital_id}", json={
        "title": "Active Campaign",
        "description": "",
        "target_blood_types": ["AB+"],
        "target_units": 50,
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=7)).isoformat(),
    })
    campaign_id = create_resp.json()["id"]
    await client.post(f"/api/v1/campaigns/{campaign_id}/activate")

    list_resp = await client.get("/api/v1/campaigns/")
    assert list_resp.status_code == 200
    ids = [c["id"] for c in list_resp.json()]
    assert campaign_id in ids
