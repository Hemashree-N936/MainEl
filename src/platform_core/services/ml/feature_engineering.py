from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from platform_core.models.commit import Commit
from platform_core.models.dependency import Dependency
from platform_core.models.engineered_metric import EngineeredMetric
from platform_core.models.repository import Repository
from platform_core.models.vulnerability import Vulnerability
from platform_core.services.ml.constants import FEATURE_COLUMNS


class FeatureEngineeringService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build_repository_feature_matrix(self) -> List[Dict[str, float]]:
        repositories = list(self.db.scalars(select(Repository)).all())
        return [self.build_repository_features(repository.id) for repository in repositories]

    def build_repository_features(self, repository_id: int) -> Dict[str, float]:
        repository = self.db.get(Repository, repository_id)
        if repository is None:
            raise ValueError("Repository {0} not found.".format(repository_id))

        features = {column: 0.0 for column in FEATURE_COLUMNS}
        features["repository_id"] = float(repository_id)

        metrics = self.db.scalars(
            select(EngineeredMetric).where(EngineeredMetric.repository_id == repository_id)
        ).all()
        for metric in metrics:
            if metric.metric_name in features:
                features[metric.metric_name] = float(metric.metric_value or 0)

        commit_aggregates = self.db.execute(
            select(
                func.count(Commit.id),
                func.avg(Commit.files_changed),
                func.avg(Commit.insertions),
                func.avg(Commit.deletions),
            ).where(Commit.repository_id == repository_id)
        ).one()
        features["commit_count"] = max(features["commit_count"], float(commit_aggregates[0] or 0))
        features["commit_files_changed_avg"] = float(commit_aggregates[1] or 0)
        features["commit_insertions_avg"] = float(commit_aggregates[2] or 0)
        features["commit_deletions_avg"] = float(commit_aggregates[3] or 0)

        dependency_count = self.db.scalar(
            select(func.count(Dependency.id)).where(Dependency.repository_id == repository_id)
        )
        features["dependency_count"] = float(dependency_count or 0)

        features.update(self._vulnerability_correlation_features())
        features["repository_age_days"] = max((repository.updated_at - repository.created_at).days, 0)
        features["health_score"] = self._health_score(features)
        return features

    def _vulnerability_correlation_features(self) -> Dict[str, float]:
        known = self.db.scalar(select(func.count(Vulnerability.id))) or 0
        high = (
            self.db.scalar(
                select(func.count(Vulnerability.id)).where(Vulnerability.severity == "HIGH")
            )
            or 0
        )
        critical = (
            self.db.scalar(
                select(func.count(Vulnerability.id)).where(Vulnerability.severity == "CRITICAL")
            )
            or 0
        )
        return {
            "known_vulnerability_count": float(known),
            "high_vulnerability_count": float(high),
            "critical_vulnerability_count": float(critical),
        }

    @staticmethod
    def _health_score(features: Dict[str, float]) -> float:
        churn_penalty = min(features["code_churn"] / 10000.0, 1.0) * 25.0
        temporal_penalty = min(
            features["weekend_commit_ratio"] + features["off_hours_commit_ratio"],
            1.0,
        ) * 20.0
        dependency_penalty = min(features["dependency_change_commits"] / 20.0, 1.0) * 20.0
        contributor_bonus = min(features["contributor_count"], 10.0) * 2.0
        score = 100.0 - churn_penalty - temporal_penalty - dependency_penalty + contributor_bonus
        return max(0.0, min(score, 100.0))
