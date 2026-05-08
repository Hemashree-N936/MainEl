from platform_core.api.routes.health import router as health_router
from platform_core.api.routes.metrics import router as metrics_router
from platform_core.api.routes.ml import router as ml_router
from platform_core.api.routes.repositories import router as repositories_router
from platform_core.api.routes.vulnerabilities import router as vulnerabilities_router

__all__ = [
    "health_router",
    "metrics_router",
    "ml_router",
    "repositories_router",
    "vulnerabilities_router",
]
