import asyncio
import logging
import subprocess
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)


def _run_alembic_upgrade() -> None:
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd="/app",
        capture_output=True,
        text=True,
    )
    if result.stdout:
        logger.info(result.stdout)
    if result.stderr:
        logger.info(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade failed (exit {result.returncode})")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Running database migrations...")
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        await loop.run_in_executor(pool, _run_alembic_upgrade)
    logger.info("Database migrations complete.")
    yield


app = FastAPI(
    title="blood-helper Intelligence Platform",
    description="Blood inventory monitoring, consumption forecasting, and donation campaign management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "healthy", "service": "blood-helper-api"}
