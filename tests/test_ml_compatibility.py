from platform_core.services.ml.model_service import ModelTrainingService
from platform_core.utils.runtime_checks import version_at_least


def test_version_comparison() -> None:
    assert version_at_least("2.1.4", (2, 1, 4))
    assert not version_at_least("2.1.3", (2, 1, 4))


def test_xgboost_sklearn_known_bad_combination() -> None:
    assert ModelTrainingService._version_at_least("1.6.0", (1, 6, 0))
    assert not ModelTrainingService._version_at_least("2.1.3", (2, 1, 4))

