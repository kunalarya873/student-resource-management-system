import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.router import api_v1_router
from app.constants import API_DESCRIPTION, TAGS_METADATA
from app.core.config import settings
from app.core.database import engine
from app.core.telemetry import setup_telemetry, shutdown_telemetry

# Initialize OpenTelemetry logging bridge early
setup_telemetry()

logger = logging.getLogger("amu_backend")
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify DB connectivity on startup
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successfully established.")
    except (SQLAlchemyError, OSError) as exc:
        logger.warning(f"Database connection deferred or pending startup: {exc}")

    # Ensure MinIO/S3 object storage bucket exists
    try:
        from app.services.storage_service import storage_service

        await storage_service.ensure_bucket_exists()
        logger.info("S3 storage bucket verified.")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"S3 storage bucket check deferred: {exc}")

    yield

    # Clean up engine pool on shutdown
    logger.info("Disposing database engine connection pool...")
    await engine.dispose()
    shutdown_telemetry()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=API_DESCRIPTION,
    openapi_tags=TAGS_METADATA,
    contact={
        "name": "AMU Student Resource Management Engineering Team",
        "email": "support@amu.edu",
    },
    license_info={
        "name": "MIT / Academic License",
        "identifier": "MIT",
    },
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/healthz", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    db_healthy = False
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            db_healthy = res.scalar() == 1
    except (SQLAlchemyError, OSError) as exc:
        logger.error(f"Health check database query failed: {exc}")

    return {
        "status": "ok",
        "database": "connected" if db_healthy else "disconnected",
        "environment": settings.APP_ENV,
    }
