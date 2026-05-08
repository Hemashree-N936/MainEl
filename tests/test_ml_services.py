from platform_core.services.ml.dataset_service import DatasetService
from platform_core.services.ml.constants import FEATURE_COLUMNS
from platform_core.services.ml.risk_scoring import RiskScoringEngine


def test_synthetic_training_data_has_required_features() -> None:
    rows = DatasetService.generate_synthetic_training_data(5)

    assert len(rows) == 5
    assert set(FEATURE_COLUMNS).issubset(rows[0].keys())


def test_risk_scoring_levels_and_confidence() -> None:
    assert RiskScoringEngine.level_for_score(0.2) == "low"
    assert RiskScoringEngine.level_for_score(0.5) == "medium"
    assert RiskScoringEngine.level_for_score(0.8) == "high"
    assert RiskScoringEngine.confidence_for_probability(0.8) == 0.8
    assert RiskScoringEngine.confidence_for_probability(0.1) == 0.9
