"""Service package with lazy exports to keep imports lightweight."""

from importlib import import_module
from typing import Any

_EXPORTS = {
    "ApiCacheService": "platform_core.services.cache_service",
    "DatasetService": "platform_core.services.ml.dataset_service",
    "FeatureEngineeringService": "platform_core.services.ml.feature_engineering",
    "GitAnalysisService": "platform_core.services.git_analysis_service",
    "GitHubApiService": "platform_core.services.github_api_service",
    "MetricsService": "platform_core.services.metrics_service",
    "ModelTrainingService": "platform_core.services.ml.model_service",
    "NvdClient": "platform_core.services.nvd_client",
    "PredictionService": "platform_core.services.ml.prediction_service",
    "RepositoryMiningService": "platform_core.services.repository_mining_service",
    "RepositoryIntelligenceService": "platform_core.services.repository_intelligence_service",
    "RepositoryService": "platform_core.services.repository_service",
    "RiskScoringEngine": "platform_core.services.ml.risk_scoring",
    "VulnerabilityIntelligenceService": "platform_core.services.vulnerability_intelligence_service",
    "VulnerabilityService": "platform_core.services.vulnerability_service",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError("module {0!r} has no attribute {1!r}".format(__name__, name))
    module = import_module(_EXPORTS[name])
    return getattr(module, name)
