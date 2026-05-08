from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.core.config import get_settings
from platform_core.core.logging import get_logger
from platform_core.models.ml import ModelRun
from platform_core.services.ml.dataset_service import DatasetService
from platform_core.services.ml.constants import FEATURE_COLUMNS
from platform_core.utils.exceptions import PlatformError

logger = get_logger(__name__)


class ModelTrainingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.dataset = DatasetService(db)

    def train_and_compare(self) -> Dict[str, Any]:
        X, y = self.dataset.prepare_training_dataset()
        dependencies = self._load_ml_dependencies()

        train_test_split = dependencies["train_test_split"]
        StandardScaler = dependencies["StandardScaler"]
        RandomForestClassifier = dependencies["RandomForestClassifier"]
        Pipeline = dependencies["Pipeline"]
        metrics = dependencies["metrics"]
        joblib = dependencies["joblib"]

        stratify = y if len(set(y.tolist())) > 1 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
            stratify=stratify,
        )

        candidates = {
            "random_forest": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "classifier",
                        RandomForestClassifier(
                            n_estimators=120,
                            random_state=42,
                            class_weight="balanced",
                        ),
                    ),
                ]
            )
        }
        xgboost_classifier = self._build_xgboost_classifier(dependencies)
        if xgboost_classifier is not None:
            candidates["xgboost"] = Pipeline(
                [("scaler", StandardScaler()), ("classifier", xgboost_classifier)]
            )

        results = []
        skipped = []
        best_model = None
        best_result = None
        for model_type, model in candidates.items():
            try:
                model.fit(X_train, y_train)
                result = self._evaluate_model(model_type, model, X_test, y_test, metrics)
                results.append(result)
                if best_result is None or result["f1_score"] > best_result["f1_score"]:
                    best_result = result
                    best_model = model
            except Exception as exc:
                skipped.append({"model_type": model_type, "reason": str(exc)})
                logger.warning(
                    "model_candidate_skipped",
                    extra={"model_type": model_type, "error": str(exc)},
                )

        if best_model is None or best_result is None:
            raise PlatformError("No model candidates were trained.")

        artifact_path = self._artifact_path(best_result["model_type"])
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": best_model,
                "feature_columns": FEATURE_COLUMNS,
                "trained_at": datetime.utcnow().isoformat(),
            },
            artifact_path,
        )

        run = ModelRun(
            model_name=self.settings.active_model_name,
            model_type=best_result["model_type"],
            artifact_path=str(artifact_path),
            precision=best_result["precision"],
            recall=best_result["recall"],
            f1_score=best_result["f1_score"],
            roc_auc=best_result["roc_auc"],
            training_rows=len(X),
            feature_columns={"columns": FEATURE_COLUMNS},
            metrics_json={"candidates": results, "skipped": skipped},
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        logger.info(
            "model_training_completed",
            extra={"model_run_id": run.id, "model_type": run.model_type, "training_rows": len(X)},
        )
        return {
            "model_run_id": run.id,
            "selected_model": run.model_type,
            "artifact_path": run.artifact_path,
            "training_rows": run.training_rows,
            "metrics": run.metrics_json,
        }

    def latest_model_run(self) -> ModelRun:
        run = self.db.scalar(select(ModelRun).order_by(ModelRun.created_at.desc()))
        if run is None:
            raise PlatformError("No trained model is available. Trigger training first.")
        return run

    def list_model_metrics(self) -> List[ModelRun]:
        return list(self.db.scalars(select(ModelRun).order_by(ModelRun.created_at.desc())).all())

    def _evaluate_model(self, model_type: str, model: Any, X_test: Any, y_test: Any, metrics: Any) -> Dict[str, float]:
        predictions = model.predict(X_test)
        probabilities = self._positive_probabilities(model, X_test)
        return {
            "model_type": model_type,
            "precision": float(metrics.precision_score(y_test, predictions, zero_division=0)),
            "recall": float(metrics.recall_score(y_test, predictions, zero_division=0)),
            "f1_score": float(metrics.f1_score(y_test, predictions, zero_division=0)),
            "roc_auc": self._roc_auc(metrics, y_test, probabilities),
        }

    @staticmethod
    def _positive_probabilities(model: Any, X_test: Any):
        if hasattr(model, "predict_proba"):
            return model.predict_proba(X_test)[:, 1]
        return model.predict(X_test)

    @staticmethod
    def _roc_auc(metrics: Any, y_test: Any, probabilities: Any) -> float:
        try:
            return float(metrics.roc_auc_score(y_test, probabilities))
        except ValueError:
            return 0.0

    def _artifact_path(self, model_type: str) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return self.settings.model_artifact_path / "{0}_{1}_{2}.joblib".format(
            self.settings.active_model_name,
            model_type,
            timestamp,
        )

    @staticmethod
    def _build_xgboost_classifier(dependencies: Dict[str, Any]) -> Any:
        XGBClassifier = dependencies.get("XGBClassifier")
        if XGBClassifier is None:
            return None
        compatible, reason = ModelTrainingService._xgboost_is_compatible()
        if not compatible:
            logger.warning("xgboost_disabled", extra={"reason": reason})
            return None
        return XGBClassifier(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
        )

    @staticmethod
    def _xgboost_is_compatible() -> Tuple[bool, str]:
        sklearn_version = ModelTrainingService._package_version("scikit-learn")
        xgboost_version = ModelTrainingService._package_version("xgboost")
        if sklearn_version is None or xgboost_version is None:
            return False, "Unable to determine sklearn/xgboost versions."

        # XGBoost versions before 2.1.4 are known to fail with scikit-learn 1.6+
        # during estimator tag inspection, commonly as:
        # AttributeError: 'super' object has no attribute 'sklearn_tags'
        if ModelTrainingService._version_at_least(sklearn_version, (1, 6, 0)) and not ModelTrainingService._version_at_least(
            xgboost_version,
            (2, 1, 4),
        ):
            return (
                False,
                "xgboost {0} is incompatible with scikit-learn {1}; using RandomForest fallback.".format(
                    xgboost_version,
                    sklearn_version,
                ),
            )
        return True, "compatible"

    @staticmethod
    def _package_version(package_name: str) -> Optional[str]:
        try:
            return metadata.version(package_name)
        except metadata.PackageNotFoundError:
            return None

    @staticmethod
    def _version_at_least(version: str, minimum: Tuple[int, int, int]) -> bool:
        parts = []
        for token in version.replace("-", ".").split("."):
            if token.isdigit():
                parts.append(int(token))
            else:
                numeric = "".join(character for character in token if character.isdigit())
                parts.append(int(numeric) if numeric else 0)
            if len(parts) == 3:
                break
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3]) >= minimum

    @staticmethod
    def _load_ml_dependencies() -> Dict[str, Any]:
        try:
            import joblib
            from sklearn import metrics
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import StandardScaler
        except ImportError as exc:
            raise PlatformError("ML dependencies are not installed. Run pip install -r requirements.txt.") from exc

        try:
            from xgboost import XGBClassifier
        except ImportError:
            XGBClassifier = None

        return {
            "joblib": joblib,
            "metrics": metrics,
            "RandomForestClassifier": RandomForestClassifier,
            "StandardScaler": StandardScaler,
            "train_test_split": train_test_split,
            "Pipeline": Pipeline,
            "XGBClassifier": XGBClassifier,
        }
