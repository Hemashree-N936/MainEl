from fastapi.testclient import TestClient

from platform_core.api.app import create_app
from platform_core.core.config import get_settings
from platform_core.db.init_db import init_db
from platform_core.services import (
    GitAnalysisService,
    MetricsService,
    ModelTrainingService,
    NvdClient,
    PredictionService,
    RepositoryMiningService,
    RepositoryService,
    RiskScoringEngine,
    VulnerabilityIntelligenceService,
    VulnerabilityService,
)


def test_core_imports() -> None:
    assert get_settings().app_name
    assert RepositoryService
    assert GitAnalysisService
    assert MetricsService
    assert ModelTrainingService
    assert NvdClient
    assert PredictionService
    assert RepositoryMiningService
    assert VulnerabilityIntelligenceService
    assert RiskScoringEngine
    assert VulnerabilityService


def test_fastapi_health() -> None:
    init_db()
    client = TestClient(create_app())
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
