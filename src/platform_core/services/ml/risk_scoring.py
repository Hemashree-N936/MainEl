from typing import Dict


class RiskScoringEngine:
    @staticmethod
    def level_for_score(risk_score: float) -> str:
        if risk_score >= 0.70:
            return "high"
        if risk_score >= 0.40:
            return "medium"
        return "low"

    @staticmethod
    def confidence_for_probability(probability: float) -> float:
        return max(probability, 1.0 - probability)

    @staticmethod
    def summarize(repository_id: int, probability: float, features: Dict[str, float]) -> Dict[str, object]:
        level = RiskScoringEngine.level_for_score(probability)
        return {
            "repository_id": repository_id,
            "risk_level": level,
            "risk_score": round(probability, 4),
            "confidence": round(RiskScoringEngine.confidence_for_probability(probability), 4),
            "top_drivers": RiskScoringEngine._top_drivers(features),
            "recommendation": RiskScoringEngine._recommendation(level),
        }

    @staticmethod
    def _top_drivers(features: Dict[str, float]):
        candidates = {
            "code_churn": features.get("code_churn", 0.0),
            "dependency_change_commits": features.get("dependency_change_commits", 0.0) * 100.0,
            "off_hours_commit_ratio": features.get("off_hours_commit_ratio", 0.0) * 1000.0,
            "weekend_commit_ratio": features.get("weekend_commit_ratio", 0.0) * 1000.0,
            "high_vulnerability_count": features.get("high_vulnerability_count", 0.0) * 500.0,
            "critical_vulnerability_count": features.get("critical_vulnerability_count", 0.0) * 1000.0,
        }
        return [
            {"name": name, "value": features.get(name, 0.0)}
            for name, _ in sorted(candidates.items(), key=lambda item: item[1], reverse=True)[:3]
        ]

    @staticmethod
    def _recommendation(level: str) -> str:
        if level == "high":
            return "Block deployment until dependency, churn, and vulnerability drivers are reviewed."
        if level == "medium":
            return "Require security review and focused validation before deployment."
        return "Proceed with standard automated controls."

