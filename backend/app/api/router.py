from fastapi import APIRouter

from app.api.v1 import campaigns, forecasting, hospitals, inventory
from app.api.websocket import alerts

api_router = APIRouter()

api_router.include_router(hospitals.router)
api_router.include_router(inventory.router)
api_router.include_router(forecasting.router)
api_router.include_router(campaigns.router)
api_router.include_router(alerts.router)
