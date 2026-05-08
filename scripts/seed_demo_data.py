import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_core.db.init_db import init_db
from platform_core.db.session import SessionLocal
from platform_core.models.vulnerability import Vulnerability
from platform_core.schemas.repository import RepositoryCreate
from platform_core.services.metrics_service import MetricsService
from platform_core.services.repository_service import RepositoryService
from platform_core.services.vulnerability_service import VulnerabilityService


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        repository = RepositoryService(db).get_or_create_repository(
            RepositoryCreate(
                name="demo-service",
                url="https://github.com/example/demo-service",
                default_branch="main",
            )
        )
        MetricsService(db).upsert_metric(repository.id, "commit_count", 42)
        MetricsService(db).upsert_metric(repository.id, "code_churn", 1280)

        VulnerabilityService(db).upsert_vulnerability(
            {
                "cve_id": "CVE-2099-0001",
                "source": "NVD",
                "severity": "HIGH",
                "cvss_score": 8.1,
                "summary": "Demo vulnerability record for local development.",
                "published_at": datetime.utcnow(),
                "modified_at": datetime.utcnow(),
                "cwe": "CWE-79",
                "references_json": {"urls": ["https://nvd.nist.gov/"]},
                "raw_json": {"demo": True},
            }
        )
        print({"repository_id": repository.id, "seeded_vulnerabilities": 1})
    finally:
        db.close()


if __name__ == "__main__":
    main()

