from datetime import datetime, timedelta
from typing import Any, Dict, List


def demo_repositories() -> List[Dict[str, Any]]:
    base = datetime.utcnow()
    return [
        {
            "id": 1,
            "name": "payments-core",
            "url": "https://github.com/example/payments-core",
            "default_branch": "main",
            "created_at": (base - timedelta(days=180)).isoformat(),
            "updated_at": base.isoformat(),
        },
        {
            "id": 2,
            "name": "identity-gateway",
            "url": "https://github.com/example/identity-gateway",
            "default_branch": "main",
            "created_at": (base - timedelta(days=300)).isoformat(),
            "updated_at": base.isoformat(),
        },
        {
            "id": 3,
            "name": "cloud-orchestrator",
            "url": "https://github.com/example/cloud-orchestrator",
            "default_branch": "release",
            "created_at": (base - timedelta(days=90)).isoformat(),
            "updated_at": base.isoformat(),
        },
    ]


def demo_vulnerabilities() -> List[Dict[str, Any]]:
    base = datetime.utcnow()
    severities = ["CRITICAL", "HIGH", "HIGH", "MEDIUM", "LOW", "CRITICAL", "MEDIUM"]
    return [
        {
            "id": index + 1,
            "cve_id": "CVE-2026-{0:04d}".format(1000 + index),
            "source": "NVD",
            "severity": severity,
            "cvss_score": {"CRITICAL": 9.4, "HIGH": 8.1, "MEDIUM": 5.8, "LOW": 2.7}[severity],
            "summary": "Synthetic demo CVE showing enterprise vulnerability intelligence workflow.",
            "cwe": "CWE-79" if index % 2 == 0 else "CWE-89",
            "published_at": (base - timedelta(days=index * 2)).isoformat(),
            "modified_at": (base - timedelta(days=index)).isoformat(),
            "ingested_at": base.isoformat(),
        }
        for index, severity in enumerate(severities)
    ]


def demo_metrics() -> List[Dict[str, Any]]:
    values = {
        1: {
            "commit_count": 420,
            "code_churn": 14800,
            "contributor_count": 9,
            "dependency_change_commits": 16,
            "weekend_commit_ratio": 0.22,
            "off_hours_commit_ratio": 0.31,
            "health_score": 68,
        },
        2: {
            "commit_count": 280,
            "code_churn": 8400,
            "contributor_count": 6,
            "dependency_change_commits": 9,
            "weekend_commit_ratio": 0.12,
            "off_hours_commit_ratio": 0.18,
            "health_score": 82,
        },
        3: {
            "commit_count": 190,
            "code_churn": 22300,
            "contributor_count": 3,
            "dependency_change_commits": 24,
            "weekend_commit_ratio": 0.41,
            "off_hours_commit_ratio": 0.52,
            "health_score": 44,
        },
    }
    rows = []
    row_id = 1
    for repository_id, metrics in values.items():
        for name, value in metrics.items():
            rows.append(
                {
                    "id": row_id,
                    "repository_id": repository_id,
                    "metric_name": name,
                    "metric_value": value,
                    "scope": "repository",
                    "measured_at": datetime.utcnow().isoformat(),
                    "metric_metadata": None,
                }
            )
            row_id += 1
    return rows


def demo_risk_scores() -> List[Dict[str, Any]]:
    return [
        {
            "id": 1,
            "repository_id": 1,
            "model_run_id": 7,
            "risk_score": 0.68,
            "risk_level": "medium",
            "confidence": 0.72,
            "summary_json": {
                "recommendation": "Require security review before deployment.",
                "top_drivers": [{"name": "code_churn", "value": 14800}],
            },
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": 2,
            "repository_id": 2,
            "model_run_id": 7,
            "risk_score": 0.31,
            "risk_level": "low",
            "confidence": 0.81,
            "summary_json": {"recommendation": "Proceed with standard controls.", "top_drivers": []},
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": 3,
            "repository_id": 3,
            "model_run_id": 7,
            "risk_score": 0.87,
            "risk_level": "high",
            "confidence": 0.9,
            "summary_json": {
                "recommendation": "Block deployment until critical drivers are reviewed.",
                "top_drivers": [{"name": "dependency_change_commits", "value": 24}],
            },
            "created_at": datetime.utcnow().isoformat(),
        },
    ]


def demo_model_metrics() -> List[Dict[str, Any]]:
    return [
        {
            "id": 7,
            "model_name": "repository_risk_model",
            "model_type": "random_forest",
            "artifact_path": "artifacts/models/repository_risk_model_random_forest.joblib",
            "precision": 0.91,
            "recall": 0.87,
            "f1_score": 0.89,
            "roc_auc": 0.94,
            "training_rows": 240,
            "feature_columns": {"columns": []},
            "metrics_json": {
                "candidates": [
                    {"model_type": "random_forest", "precision": 0.91, "recall": 0.87, "f1_score": 0.89, "roc_auc": 0.94},
                    {"model_type": "xgboost", "precision": 0.9, "recall": 0.85, "f1_score": 0.87, "roc_auc": 0.93},
                ],
                "skipped": [],
            },
            "created_at": datetime.utcnow().isoformat(),
        }
    ]

