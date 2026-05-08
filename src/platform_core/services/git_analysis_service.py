from pathlib import Path
from typing import Any, Dict

from git import Repo


class GitAnalysisService:
    """Phase 1 repository access wrapper; feature extraction is added later."""

    def open_repository(self, path: Path) -> Repo:
        return Repo(path)

    def summarize_repository(self, path: Path) -> Dict[str, Any]:
        repo = self.open_repository(path)
        return {
            "active_branch": repo.active_branch.name if not repo.head.is_detached else "detached",
            "commit_count": sum(1 for _ in repo.iter_commits()),
        }
