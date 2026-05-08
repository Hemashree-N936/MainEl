from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.models.ml import RepositoryRiskScore
from platform_core.services.ml.dataset_service import DatasetService
from platform_core.services.ml.constants import FEATURE_COLUMNS
from platform_core.services.ml.feature_engineering import FeatureEngineeringService
from platform_core.services.ml.model_service import ModelTrainingService
from platform_core.services.ml.risk_scoring import RiskScoringEngine
from platform_core.utils.exceptions import PlatformError
from platform_core.core.logging import get_logger

logger = get_logger(__name__)


class PredictionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.dataset = DatasetService(db)
        self.features = FeatureEngineeringService(db)
        self.training = ModelTrainingService(db)

    def predict_repository(self, repository_id: int) -> Dict[str, object]:
        model_run = self._latest_or_train_model()
        bundle = self._load_bundle(model_run.artifact_path)
        frame = self.dataset.prepare_prediction_features(repository_id)
        feature_columns = bundle.get("feature_columns", FEATURE_COLUMNS)
        probability = self._positive_probability(bundle["model"], frame[feature_columns])
        feature_map = self.features.build_repository_features(repository_id)
        summary = RiskScoringEngine.summarize(repository_id, probability, feature_map)
        risk_score = RepositoryRiskScore(
            repository_id=repository_id,
            model_run_id=model_run.id,
            risk_score=summary["risk_score"],
            risk_level=summary["risk_level"],
            confidence=summary["confidence"],
            summary_json=summary,
        )
        self.db.add(risk_score)
        self.db.commit()
        self.db.refresh(risk_score)
        return {
            "repository_id": repository_id,
            "model_run_id": model_run.id,
            "risk_score": risk_score.risk_score,
            "risk_level": risk_score.risk_level,
            "confidence": risk_score.confidence,
            "summary": risk_score.summary_json,
        }

    def list_risk_scores(self, repository_id: Optional[int] = None) -> List[RepositoryRiskScore]:
        statement = select(RepositoryRiskScore).order_by(RepositoryRiskScore.created_at.desc())
        if repository_id is not None:
            statement = statement.where(RepositoryRiskScore.repository_id == repository_id)
        return list(self.db.scalars(statement).all())

    def _latest_or_train_model(self):
        try:
            return self.training.latest_model_run()
        except PlatformError:
            logger.warning("model_missing_training_before_prediction")
            self.training.train_and_compare()
            return self.training.latest_model_run()

    @staticmethod
    def _positive_probability(model, frame) -> float:
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(frame)
            if probabilities.shape[1] > 1:
                return float(probabilities[:, 1][0])
            return float(probabilities[:, 0][0])
        if hasattr(model, "decision_function"):
            import math

            score = float(model.decision_function(frame)[0])
            return 1.0 / (1.0 + math.exp(-score))
        return float(model.predict(frame)[0])

    @staticmethod
    def _load_bundle(artifact_path: str):
        try:
            import joblib
        except ImportError as exc:
            raise PlatformError("joblib is not installed. Run pip install -r requirements.txt.") from exc
        try:
            return joblib.load(artifact_path)
        except FileNotFoundError as exc:
            raise PlatformError("Model artifact not found: {0}".format(artifact_path)) from exc
