from typing import Any, List, Tuple
from sqlalchemy.orm import Session

from platform_core.services.ml.constants import FEATURE_COLUMNS


class DatasetService:
    def __init__(self, db: Session) -> None:
        from platform_core.core.config import get_settings
        from platform_core.services.ml.feature_engineering import FeatureEngineeringService

        self.db = db
        self.settings = get_settings()
        self.features = FeatureEngineeringService(db)

    def prepare_training_dataset(self) -> Tuple[Any, Any]:
        import pandas as pd

        rows = self.features.build_repository_feature_matrix()
        if len(rows) < self.settings.minimum_training_rows:
            rows.extend(self.generate_synthetic_training_data(self.settings.minimum_training_rows - len(rows)))

        frame = pd.DataFrame(rows)
        if frame.empty:
            frame = pd.DataFrame(self.generate_synthetic_training_data(self.settings.minimum_training_rows))

        for column in FEATURE_COLUMNS:
            if column not in frame:
                frame[column] = 0.0
        frame = frame.fillna(0.0)
        labels = frame.apply(self._derive_label, axis=1).astype(int)
        return frame[FEATURE_COLUMNS], labels

    def prepare_prediction_features(self, repository_id: int) -> Any:
        import pandas as pd

        row = self.features.build_repository_features(repository_id)
        frame = pd.DataFrame([row])
        for column in FEATURE_COLUMNS:
            if column not in frame:
                frame[column] = 0.0
        return frame[FEATURE_COLUMNS].fillna(0.0)

    @staticmethod
    def generate_synthetic_training_data(count: int) -> List[dict]:
        rows = []
        for index in range(max(count, 0)):
            high_risk = index % 3 == 0
            rows.append(
                {
                    "commit_count": 20 + index * 3,
                    "commit_frequency_per_week": 2.0 + (index % 10),
                    "code_churn": 2500 + index * 180 if high_risk else 300 + index * 20,
                    "contributor_count": 1 + (index % 8),
                    "dependency_change_commits": 12 + (index % 12) if high_risk else index % 4,
                    "branch_count": 1 + (index % 6),
                    "active_days": 7 + index,
                    "weekend_commit_ratio": 0.45 if high_risk else 0.08,
                    "off_hours_commit_ratio": 0.55 if high_risk else 0.12,
                    "max_branch_commits": 10 + index,
                    "dependency_count": 30 + (index % 40) if high_risk else 4 + (index % 8),
                    "commit_files_changed_avg": 18.0 if high_risk else 3.0,
                    "commit_insertions_avg": 250.0 if high_risk else 35.0,
                    "commit_deletions_avg": 180.0 if high_risk else 20.0,
                    "critical_vulnerability_count": 2 if high_risk else 0,
                    "high_vulnerability_count": 5 if high_risk else 1,
                    "known_vulnerability_count": 25 if high_risk else 3,
                    "repository_age_days": 30 + index,
                    "health_score": 42.0 if high_risk else 86.0,
                }
            )
        return rows

    @staticmethod
    def _derive_label(row) -> int:
        score = 0
        score += 2 if row["critical_vulnerability_count"] >= 1 else 0
        score += 2 if row["high_vulnerability_count"] >= 3 else 0
        score += 1 if row["code_churn"] >= 5000 else 0
        score += 1 if row["dependency_change_commits"] >= 8 else 0
        score += 1 if row["weekend_commit_ratio"] >= 0.35 else 0
        score += 1 if row["off_hours_commit_ratio"] >= 0.45 else 0
        score += 1 if row["health_score"] < 60 else 0
        return 1 if score >= 3 else 0
