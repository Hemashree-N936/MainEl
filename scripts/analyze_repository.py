import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_core.db.init_db import init_db
from platform_core.db.session import SessionLocal
from platform_core.schemas.repository import RepositoryCreate
from platform_core.services.repository_mining_service import RepositoryMiningService
from platform_core.services.repository_service import RepositoryService


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine a local Git repository and store metrics.")
    parser.add_argument("--path", required=True, help="Local Git repository path")
    parser.add_argument("--name", required=True, help="Repository display name")
    parser.add_argument("--url", required=True, help="Repository URL or local file URL")
    parser.add_argument("--branch", default="main", help="Default branch name")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        repository = RepositoryService(db).get_or_create_repository(
            RepositoryCreate(name=args.name, url=args.url, default_branch=args.branch)
        )
        metrics = RepositoryMiningService(db).analyze_repository(repository.id, Path(args.path))
        print({"repository_id": repository.id, "metrics": metrics})
    finally:
        db.close()


if __name__ == "__main__":
    main()

