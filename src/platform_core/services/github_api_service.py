import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from platform_core.core.config import get_settings
from platform_core.core.logging import get_logger
from platform_core.utils.exceptions import PlatformError

logger = get_logger(__name__)


class GitHubApiService:
    """Small GitHub REST API client for repository intelligence gathering."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def parse_repository_url(url: str) -> Tuple[str, str]:
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
            raise PlatformError("Enter a valid GitHub repository URL like https://github.com/owner/repository.")
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) < 2:
            raise PlatformError("GitHub URL must include both owner and repository name.")
        owner, repository = parts[0], parts[1].removesuffix(".git")
        if not owner or not repository:
            raise PlatformError("GitHub URL must include both owner and repository name.")
        return owner, repository

    def fetch_repository_intelligence(self, url: str) -> Dict[str, Any]:
        owner, repository = self.parse_repository_url(url)
        logger.info("github_repository_analysis_started owner=%s repository=%s", owner, repository)
        repo = self._get("/repos/{0}/{1}".format(owner, repository))
        contributors = self._get_optional_list("/repos/{0}/{1}/contributors".format(owner, repository), {"per_page": 100})
        releases = self._get_optional_list("/repos/{0}/{1}/releases".format(owner, repository), {"per_page": 30})
        commits = self._get_optional_list("/repos/{0}/{1}/commits".format(owner, repository), {"per_page": 100})
        issues = self._get_optional_list(
            "/repos/{0}/{1}/issues".format(owner, repository),
            {"state": "all", "per_page": 100},
        )
        branches = self._get_optional_list("/repos/{0}/{1}/branches".format(owner, repository), {"per_page": 100})

        now = datetime.now(timezone.utc)
        created_at = self._parse_datetime(repo.get("created_at"))
        pushed_at = self._parse_datetime(repo.get("pushed_at") or repo.get("updated_at"))
        commit_dates = [
            self._parse_datetime(
                commit.get("commit", {}).get("committer", {}).get("date")
                or commit.get("commit", {}).get("author", {}).get("date")
            )
            for commit in commits
        ]
        commit_dates = [date for date in commit_dates if date is not None]
        recent_commits = [date for date in commit_dates if (now - date).days <= 30]
        release_dates = [self._parse_datetime(release.get("published_at")) for release in releases]
        release_dates = [date for date in release_dates if date is not None]
        issue_dates = [self._parse_datetime(issue.get("created_at")) for issue in issues if "pull_request" not in issue]
        issue_dates = [date for date in issue_dates if date is not None]

        age_days = max((now - created_at).days, 0) if created_at else 0
        commit_frequency = len(recent_commits) / max(30.0 / 7.0, 1.0)
        contributor_count = int(repo.get("subscribers_count") or 0)
        if contributors:
            contributor_count = len(contributors)

        profile = {
            "owner": owner,
            "name": repo.get("name") or repository,
            "full_name": repo.get("full_name") or "{0}/{1}".format(owner, repository),
            "url": repo.get("html_url") or url,
            "description": repo.get("description"),
            "avatar_url": repo.get("owner", {}).get("avatar_url"),
            "default_branch": repo.get("default_branch") or "main",
            "stars": int(repo.get("stargazers_count") or 0),
            "forks": int(repo.get("forks_count") or 0),
            "open_issues": int(repo.get("open_issues_count") or 0),
            "contributors": contributor_count,
            "release_count": len(releases),
            "recent_release_count": sum(1 for date in release_dates if (now - date).days <= 180),
            "branch_count": len(branches),
            "commit_sample_count": len(commits),
            "recent_commit_count": len(recent_commits),
            "commit_frequency_per_week": round(commit_frequency, 4),
            "repository_age_days": age_days,
            "days_since_update": max((now - pushed_at).days, 0) if pushed_at else 0,
            "last_updated": pushed_at.isoformat() if pushed_at else repo.get("updated_at"),
            "issue_sample_count": len(issue_dates),
            "recent_issue_count": sum(1 for date in issue_dates if (now - date).days <= 30),
            "archived": bool(repo.get("archived")),
            "disabled": bool(repo.get("disabled")),
            "private": bool(repo.get("private")),
            "language": repo.get("language"),
        }
        logger.info(
            "github_repository_analysis_completed owner=%s repository=%s commits=%s contributors=%s branches=%s",
            owner,
            repository,
            len(commits),
            contributor_count,
            len(branches),
        )
        return profile

    def _get_list(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        data = self._get(path, params=params)
        if isinstance(data, list):
            return data
        return []

    def _get_optional_list(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        try:
            return self._get_list(path, params=params)
        except PlatformError as exc:
            if "rate limit" in str(exc).lower():
                raise
            logger.warning("github_optional_endpoint_skipped path=%s error=%s", path, exc)
            return []

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = self.settings.github_api_base_url.rstrip("/") + path
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "pcsi-platform",
        }
        if self.settings.github_api_token:
            headers["Authorization"] = "Bearer {0}".format(self.settings.github_api_token)

        last_error: Optional[Exception] = None
        for attempt in range(1, self.settings.github_max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.settings.github_timeout_seconds,
                )
                if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                    reset_at = self._rate_limit_reset(response)
                    raise PlatformError(
                        "GitHub API rate limit reached. Try again after {0} or configure GITHUB_API_TOKEN.".format(
                            reset_at
                        )
                    )
                if response.status_code == 404:
                    raise PlatformError("GitHub repository was not found or is not accessible.")
                if response.status_code in {409, 422}:
                    raise PlatformError("GitHub could not provide this repository signal right now.")
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.settings.github_max_retries:
                    logger.warning("github_api_retry path=%s status=%s attempt=%s", path, response.status_code, attempt)
                    time.sleep(self.settings.github_retry_backoff_seconds * attempt)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("github_api_request_failed path=%s attempt=%s error=%s", path, attempt, exc)
                if attempt < self.settings.github_max_retries:
                    time.sleep(self.settings.github_retry_backoff_seconds * attempt)

        if last_error is not None:
            raise PlatformError("GitHub API request failed: {0}".format(last_error)) from last_error
        raise PlatformError("GitHub API request failed.")

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    @staticmethod
    def _rate_limit_reset(response: requests.Response) -> str:
        reset_value = response.headers.get("X-RateLimit-Reset")
        if reset_value:
            try:
                return datetime.fromtimestamp(int(reset_value), tz=timezone.utc).isoformat()
            except ValueError:
                pass
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return parsedate_to_datetime(retry_after).isoformat()
            except (TypeError, ValueError):
                return "the retry window"
        return "the next GitHub rate-limit window"
