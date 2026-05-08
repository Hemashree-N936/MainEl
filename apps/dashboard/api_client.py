from typing import Any, Dict, List, Optional

import requests

from apps.dashboard.config import DashboardSettings, configure_dashboard_logging

logger = configure_dashboard_logging()


class DashboardApiClient:
    def __init__(self, settings: DashboardSettings) -> None:
        self.settings = settings

    def health(self) -> Dict[str, Any]:
        return self._get("/health", default={})

    def repositories(self) -> List[Dict[str, Any]]:
        return self._get("/repositories", default=[])

    def vulnerabilities(self, limit: int = 500, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit}
        if severity and severity != "All":
            params["severity"] = severity
        return self._get("/vulnerabilities", params=params, default=[])

    def metrics(self, repository_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"repository_id": repository_id} if repository_id else None
        return self._get("/metrics", params=params, default=[])

    def model_metrics(self) -> List[Dict[str, Any]]:
        return self._get("/ml/model-metrics", default=[])

    def risk_scores(self, repository_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"repository_id": repository_id} if repository_id else None
        return self._get("/ml/risk-scores", params=params, default=[])

    def trigger_prediction(self, repository_id: int) -> Dict[str, Any]:
        return self._post("/ml/predict/repositories/{0}".format(repository_id), default={})

    def trigger_training(self) -> Dict[str, Any]:
        return self._post("/ml/train", default={})

    def analyze_github_repository(
        self,
        github_url: str,
        analysis_mode: str = "quick",
        repository_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"github_url": github_url, "analysis_mode": analysis_mode}
        if repository_path:
            payload["repository_path"] = repository_path
        return self._post("/repositories/analyze-github", json=payload, default={}, return_error=True)

    def _get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        default: Any = None,
    ) -> Any:
        try:
            response = requests.get(
                self.settings.api_base_url + path,
                params=params,
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.warning("dashboard_api_get_failed path=%s error=%s", path, exc)
            return default

    def _post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        default: Any = None,
        return_error: bool = False,
    ) -> Any:
        try:
            response = requests.post(
                self.settings.api_base_url + path,
                json=json,
                timeout=self.settings.request_timeout_seconds,
            )
            if return_error and response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except ValueError:
                    detail = response.text
                return {"error": detail}
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.warning("dashboard_api_post_failed path=%s error=%s", path, exc)
            return default
