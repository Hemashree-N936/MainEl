import logging
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardSettings:
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    request_timeout_seconds: float = float(os.getenv("DASHBOARD_REQUEST_TIMEOUT_SECONDS", "8"))
    demo_mode_enabled: bool = os.getenv("DASHBOARD_DEMO_MODE", "true").lower() == "true"
    log_level: str = os.getenv("DASHBOARD_LOG_LEVEL", "INFO")


def get_dashboard_settings() -> DashboardSettings:
    return DashboardSettings()


def configure_dashboard_logging() -> logging.Logger:
    settings = get_dashboard_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    return logging.getLogger("pcsi.dashboard")
