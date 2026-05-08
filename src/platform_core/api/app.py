from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from platform_core.api.routes import (
    health_router,
    metrics_router,
    ml_router,
    repositories_router,
    vulnerabilities_router,
)
from platform_core.core.config import get_settings
from platform_core.core.logging import configure_logging, get_logger
from platform_core.db.init_db import init_db
from platform_core.utils.exceptions import PlatformError

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    logger.info("application_started")
    yield
    logger.info("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(repositories_router, prefix="/api/v1")
    app.include_router(vulnerabilities_router, prefix="/api/v1")
    app.include_router(metrics_router, prefix="/api/v1")
    app.include_router(ml_router, prefix="/api/v1")

    @app.exception_handler(PlatformError)
    async def platform_error_handler(request: Request, exc: PlatformError) -> JSONResponse:
        logger.error("platform_error", extra={"path": str(request.url.path), "error": str(exc)})
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    return app


app = create_app()
