from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from git import Commit as GitCommit
from git import Repo
from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.core.logging import get_logger
from platform_core.models.commit import Commit
from platform_core.models.dependency import Dependency
from platform_core.models.repository import Repository
from platform_core.services.metrics_service import MetricsService
from platform_core.utils.exceptions import ResourceNotFoundError

logger = get_logger(__name__)

DEPENDENCY_FILE_NAMES = {
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "package.json",
    "package-lock.json",
    "yarn.lock",
}


class RepositoryMiningService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.metrics = MetricsService(db)

    def analyze_repository(self, repository_id: int, repository_path: Path) -> Dict[str, float]:
        repository = self.db.get(Repository, repository_id)
        if repository is None:
            raise ResourceNotFoundError("Repository {0} not found.".format(repository_id))
        repo = Repo(repository_path)
        if repo.bare:
            raise ResourceNotFoundError("Repository path is bare or invalid: {0}".format(repository_path))

        commits = list(repo.iter_commits("--all"))
        self._persist_commits(repository.id, commits)
        self._persist_current_dependencies(repository.id, repository_path)

        metrics = self._calculate_metrics(repo, commits)
        for name, value in metrics.items():
            self.metrics.upsert_metric(repository.id, name, float(value))
        logger.info(
            "repository_analysis_completed",
            extra={"repository_id": repository_id, "commit_count": len(commits)},
        )
        return metrics

    def _persist_commits(self, repository_id: int, commits: Iterable[GitCommit]) -> None:
        for git_commit in commits:
            commit_hash = git_commit.hexsha
            existing = self.db.scalar(
                select(Commit).where(
                    Commit.repository_id == repository_id,
                    Commit.commit_hash == commit_hash,
                )
            )
            stats = git_commit.stats.total
            committed_at = datetime.utcfromtimestamp(git_commit.committed_date)
            if existing is None:
                self.db.add(
                    Commit(
                        repository_id=repository_id,
                        commit_hash=commit_hash,
                        author_name=git_commit.author.name,
                        author_email=git_commit.author.email,
                        message=git_commit.message.strip(),
                        committed_at=committed_at,
                        files_changed=stats.get("files", 0),
                        insertions=stats.get("insertions", 0),
                        deletions=stats.get("deletions", 0),
                    )
                )
            else:
                existing.author_name = git_commit.author.name
                existing.author_email = git_commit.author.email
                existing.message = git_commit.message.strip()
                existing.committed_at = committed_at
                existing.files_changed = stats.get("files", 0)
                existing.insertions = stats.get("insertions", 0)
                existing.deletions = stats.get("deletions", 0)
        self.db.commit()

    def _persist_current_dependencies(self, repository_id: int, repository_path: Path) -> None:
        discovered = self._discover_dependencies(repository_path)
        for package_name, package_version, ecosystem in discovered:
            existing = self.db.scalar(
                select(Dependency).where(
                    Dependency.repository_id == repository_id,
                    Dependency.package_name == package_name,
                    Dependency.ecosystem == ecosystem,
                )
            )
            if existing is None:
                self.db.add(
                    Dependency(
                        repository_id=repository_id,
                        package_name=package_name,
                        package_version=package_version,
                        ecosystem=ecosystem,
                    )
                )
            else:
                existing.package_version = package_version
        self.db.commit()

    def _calculate_metrics(self, repo: Repo, commits: List[GitCommit]) -> Dict[str, float]:
        if not commits:
            return {
                "commit_count": 0,
                "commit_frequency_per_week": 0,
                "code_churn": 0,
                "contributor_count": 0,
                "dependency_change_commits": 0,
                "branch_count": len(repo.branches),
                "active_days": 0,
                "weekend_commit_ratio": 0,
                "off_hours_commit_ratio": 0,
            }

        dates = [datetime.utcfromtimestamp(commit.committed_date) for commit in commits]
        min_date = min(dates)
        max_date = max(dates)
        active_days = max((max_date - min_date).days, 1)
        contributor_emails = {commit.author.email for commit in commits if commit.author.email}
        churn = sum(commit.stats.total.get("insertions", 0) + commit.stats.total.get("deletions", 0) for commit in commits)
        dependency_change_commits = sum(1 for commit in commits if self._commit_touches_dependencies(commit))
        weekend_commits = sum(1 for date in dates if date.weekday() >= 5)
        off_hours_commits = sum(1 for date in dates if date.hour < 8 or date.hour >= 18)
        branch_activity = self._branch_activity(repo)

        return {
            "commit_count": len(commits),
            "commit_frequency_per_week": len(commits) / max(active_days / 7.0, 1.0),
            "code_churn": churn,
            "contributor_count": len(contributor_emails),
            "dependency_change_commits": dependency_change_commits,
            "branch_count": len(repo.branches),
            "active_days": active_days,
            "weekend_commit_ratio": weekend_commits / len(commits),
            "off_hours_commit_ratio": off_hours_commits / len(commits),
            "max_branch_commits": max(branch_activity.values()) if branch_activity else 0,
        }

    @staticmethod
    def _commit_touches_dependencies(commit: GitCommit) -> bool:
        try:
            files = commit.stats.files.keys()
        except ValueError:
            return False
        return any(Path(path).name in DEPENDENCY_FILE_NAMES for path in files)

    @staticmethod
    def _branch_activity(repo: Repo) -> Dict[str, int]:
        activity: Dict[str, int] = {}
        for branch in repo.branches:
            activity[branch.name] = sum(1 for _ in repo.iter_commits(branch.name))
        return activity

    @staticmethod
    def _discover_dependencies(repository_path: Path) -> List[tuple[str, Optional[str], str]]:
        dependencies = []
        requirements = repository_path / "requirements.txt"
        if requirements.exists():
            for line in requirements.read_text(encoding="utf-8", errors="ignore").splitlines():
                parsed = RepositoryMiningService._parse_requirement_line(line)
                if parsed:
                    dependencies.append(parsed)
        package_json = repository_path / "package.json"
        if package_json.exists():
            dependencies.append(("package.json", None, "npm"))
        return dependencies

    @staticmethod
    def _parse_requirement_line(line: str) -> Optional[tuple[str, Optional[str], str]]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            return None
        for separator in ("==", ">=", "<=", "~=", ">", "<"):
            if separator in stripped:
                name, version = stripped.split(separator, 1)
                return name.strip(), version.strip(), "python"
        return stripped, None, "python"

