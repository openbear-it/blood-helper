from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.infrastructure.cache.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active_connections:
            self.active_connections.remove(ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/alerts")
async def alerts_websocket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            # Push cached alerts every 30 seconds
            expiring = await redis_client.get("alerts:expiring_units")
            critical = await redis_client.get("alerts:critical_levels")

            if expiring or critical:
                payload: dict[str, Any] = {"type": "alerts"}
                if expiring:
                    payload["expiring_units"] = json.loads(expiring)
                if critical:
                    payload["critical_levels"] = json.loads(critical)
                await websocket.send_json(payload)

            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        manager.disconnect(websocket)


@router.websocket("/inventory/{hospital_id}")
async def inventory_websocket(websocket: WebSocket, hospital_id: str) -> None:
    await manager.connect(websocket)
    try:
        while True:
            cache_key = f"inventory:summary:{hospital_id}"
            cached = await redis_client.get(cache_key)
            if cached:
                await websocket.send_json({
                    "type": "inventory_update",
                    "data": json.loads(cached),
                })
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error("Inventory WebSocket error: %s", exc)
        manager.disconnect(websocket)
