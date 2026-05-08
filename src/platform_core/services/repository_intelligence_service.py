from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from platform_core.core.logging import get_logger
from platform_core.schemas.repository import RepositoryCreate
from platform_core.services.github_api_service import GitHubApiService
from platform_core.services.metrics_service import MetricsService
from platform_core.services.ml.prediction_service import PredictionService
from platform_core.services.repository_mining_service import RepositoryMiningService
from platform_core.services.repository_service import RepositoryService
from platform_core.utils.exceptions import PlatformError

logger = get_logger(__name__)


class RepositoryIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.github = GitHubApiService()
        self.repositories = RepositoryService(db)
        self.metrics = MetricsService(db)
        self.predictions = PredictionService(db)
        self.mining = RepositoryMiningService(db)

    def analyze_github_repository(
        self,
        github_url: str,
        analysis_mode: str = "quick",
        repository_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        mode = analysis_mode.lower()
        if mode not in {"quick", "deep"}:
            raise PlatformError("Analysis mode must be quick or deep.")

        logger.info("repository_intelligence_started mode=%s url=%s", mode, github_url)
        profile = self.github.fetch_repository_intelligence(github_url)
        repository = self.repositories.get_or_create_repository(
            RepositoryCreate(
                name=profile["name"],
                url=profile["url"],
                default_branch=profile["default_branch"],
            )
        )
        quick_metrics = self._persist_quick_metrics(repository.id, profile)
        deep_metrics: Dict[str, float] = {}
        if mode == "deep":
            if repository_path is None:
                raise PlatformError("Deep Scan Mode requires a local repository path.")
            deep_metrics = self.mining.analyze_repository(repository.id, repository_path)

        try:
            prediction = self.predictions.predict_repository(repository.id)
        except Exception as exc:
            logger.exception("repository_prediction_failed repository_id=%s", repository.id)
            raise PlatformError("GitHub data was collected, but AI prediction failed: {0}".format(exc)) from exc
        health_score = self._security_health_score(prediction["risk_score"], quick_metrics)
        result = {
            "analysis_mode": mode,
            "repository": {
                "id": repository.id,
                "name": repository.name,
                "url": repository.url,
                "default_branch": repository.default_branch,
            },
            "github": profile,
            "metrics": {**quick_metrics, **deep_metrics},
            "prediction": prediction,
            "security_health_score": health_score,
            "health_label": self._health_label(health_score),
            "explanations": self._plain_english_explanations(quick_metrics, prediction),
            "recommendations": self._recommendations(quick_metrics, prediction),
        }
        logger.info(
            "repository_intelligence_completed repository_id=%s mode=%s health_score=%s",
            repository.id,
            mode,
            health_score,
        )
        return result

    def _persist_quick_metrics(self, repository_id: int, profile: Dict[str, Any]) -> Dict[str, float]:
        dependency_pressure = min(float(profile["recent_release_count"] + profile["recent_issue_count"]), 30.0)
        stale_penalty = min(float(profile["days_since_update"]) / 30.0, 12.0)
        code_stability = max(0.0, 100.0 - (float(profile["recent_commit_count"]) * 1.8) - dependency_pressure - stale_penalty)
        metrics = {
            "commit_count": float(profile["commit_sample_count"]),
            "commit_frequency_per_week": float(profile["commit_frequency_per_week"]),
            "code_churn": float(profile["recent_commit_count"] * 120),
            "contributor_count": float(profile["contributors"]),
            "dependency_change_commits": dependency_pressure,
            "branch_count": float(profile["branch_count"]),
            "active_days": min(float(profile["repository_age_days"]), 365.0),
            "weekend_commit_ratio": 0.0,
            "off_hours_commit_ratio": 0.0,
            "max_branch_commits": float(profile["recent_commit_count"]),
            "repository_age_days": float(profile["repository_age_days"]),
            "health_score": code_stability,
            "github_stars": float(profile["stars"]),
            "github_forks": float(profile["forks"]),
            "github_open_issues": float(profile["open_issues"]),
            "github_recent_issues": float(profile["recent_issue_count"]),
            "github_days_since_update": float(profile["days_since_update"]),
            "github_release_activity": float(profile["recent_release_count"]),
        }
        for name, value in metrics.items():
            self.metrics.upsert_metric(
                repository_id,
                name,
                value,
                metric_metadata={"source": "github_api", "analysis_mode": "quick"},
            )
        return metrics

    @staticmethod
    def _security_health_score(risk_score: float, metrics: Dict[str, float]) -> int:
        model_component = 100.0 - (float(risk_score) * 100.0)
        stability_component = float(metrics.get("health_score", 70.0))
        freshness_penalty = min(float(metrics.get("github_days_since_update", 0.0)) / 4.0, 25.0)
        score = (model_component * 0.62) + (stability_component * 0.38) - freshness_penalty
        return int(max(0, min(100, round(score))))

    @staticmethod
    def _health_label(score: int) -> str:
        if score >= 75:
            return "Stable"
        if score >= 45:
            return "Moderate Risk"
        return "High Risk"

    @staticmethod
    def _plain_english_explanations(metrics: Dict[str, float], prediction: Dict[str, Any]) -> list[str]:
        explanations = []
        if metrics.get("dependency_change_commits", 0) >= 8:
            explanations.append("Frequent package or release changes may introduce security risks.")
        if metrics.get("commit_frequency_per_week", 0) >= 10:
            explanations.append("Rapid development activity increases the chance of unstable code.")
        if metrics.get("github_days_since_update", 0) >= 60:
            explanations.append("Low maintenance activity may indicate outdated dependencies or delayed fixes.")
        if metrics.get("github_open_issues", 0) >= 50:
            explanations.append("A high number of open issues can signal maintenance pressure.")
        if not explanations:
            explanations.append("The repository shows a balanced activity profile based on available GitHub data.")
        risk_level = prediction.get("risk_level", "low")
        explanations.append("The AI model currently classifies this repository as {0} risk.".format(risk_level))
        return explanations

    @staticmethod
    def _recommendations(metrics: Dict[str, float], prediction: Dict[str, Any]) -> list[str]:
        recommendations = [
            "Scan dependencies before release.",
            "Review recent package updates for security impact.",
        ]
        if metrics.get("commit_frequency_per_week", 0) >= 10:
            recommendations.append("Monitor unstable development activity during active release windows.")
        if metrics.get("github_days_since_update", 0) >= 60:
            recommendations.append("Improve maintenance consistency and review overdue security updates.")
        if prediction.get("risk_level") == "high":
            recommendations.append("Audit authentication and access-control paths before deployment.")
        return recommendations
