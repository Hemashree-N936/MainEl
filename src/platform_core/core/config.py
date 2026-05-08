from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Predictive Cloud Security Intelligence Platform"
    environment: Literal["local", "dev", "test", "staging", "prod"] = "local"
    log_level: str = "INFO"
    log_json: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = Field(default="sqlite:///./data/sqlite/platform.db")
    repository_storage_path: Path = Path("./data/repositories")
    model_artifact_path: Path = Path("./artifacts/models")
    active_model_name: str = "repository_risk_model"
    minimum_training_rows: int = 50

    nvd_base_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    nvd_api_key: Optional[str] = None
    nvd_timeout_seconds: float = 20.0
    nvd_max_retries: int = 3
    nvd_retry_backoff_seconds: float = 1.5
    nvd_results_per_page: int = 2000
    nvd_cache_ttl_seconds: int = 3600

    github_api_base_url: str = "https://api.github.com"
    github_api_token: Optional[str] = None
    github_timeout_seconds: float = 15.0
    github_max_retries: int = 3
    github_retry_backoff_seconds: float = 1.2


@lru_cache
def get_settings() -> Settings:
    return Settings()
