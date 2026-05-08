"""Machine-learning service package with lazy exports."""

from importlib import import_module
from typing import Any

_EXPORTS = {
    "DatasetService": "platform_core.services.ml.dataset_service",
    "FeatureEngineeringService": "platform_core.services.ml.feature_engineering",
    "ModelTrainingService": "platform_core.services.ml.model_service",
    "PredictionService": "platform_core.services.ml.prediction_service",
    "RiskScoringEngine": "platform_core.services.ml.risk_scoring",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError("module {0!r} has no attribute {1!r}".format(__name__, name))
    module = import_module(_EXPORTS[name])
    return getattr(module, name)

