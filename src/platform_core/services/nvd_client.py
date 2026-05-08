from time import sleep
from typing import Any, Dict, Iterator, Optional

import requests
from requests import Response, Session as HttpSession

from platform_core.core.config import Settings, get_settings
from platform_core.core.logging import get_logger
from platform_core.services.cache_service import ApiCacheService
from platform_core.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)


class NvdClient:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        http_session: Optional[HttpSession] = None,
        cache: Optional[ApiCacheService] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.http = http_session or requests.Session()
        self.cache = cache

    def fetch_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        request_params = dict(params)
        headers = {}
        if self.settings.nvd_api_key:
            headers["apiKey"] = self.settings.nvd_api_key

        cached = self.cache.get("NVD", self.settings.nvd_base_url, request_params) if self.cache else None
        if cached is not None:
            logger.info("nvd_cache_hit", extra={"params": request_params})
            return cached

        response_json = self._request_with_retries(request_params, headers)
        if self.cache is not None:
            self.cache.set(
                "NVD",
                self.settings.nvd_base_url,
                request_params,
                response_json,
                self.settings.nvd_cache_ttl_seconds,
            )
        return response_json

    def iter_cves(self, params: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        start_index = int(params.get("startIndex", 0))
        results_per_page = int(params.get("resultsPerPage", self.settings.nvd_results_per_page))

        while True:
            page_params = dict(params)
            page_params["startIndex"] = start_index
            page_params["resultsPerPage"] = results_per_page
            page = self.fetch_page(page_params)
            vulnerabilities = page.get("vulnerabilities", [])
            for item in vulnerabilities:
                yield item

            total_results = int(page.get("totalResults", 0))
            returned = len(vulnerabilities)
            start_index += returned
            if returned == 0 or start_index >= total_results:
                break

    def _request_with_retries(self, params: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        last_error: Optional[Exception] = None
        for attempt in range(1, self.settings.nvd_max_retries + 1):
            try:
                response = self.http.get(
                    self.settings.nvd_base_url,
                    params=params,
                    headers=headers,
                    timeout=self.settings.nvd_timeout_seconds,
                )
                self._raise_for_status(response)
                logger.info("nvd_page_fetched", extra={"attempt": attempt, "params": params})
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                logger.warning("nvd_request_failed", extra={"attempt": attempt, "error": str(exc)})
                if attempt < self.settings.nvd_max_retries:
                    sleep(self.settings.nvd_retry_backoff_seconds * attempt)
        raise ExternalServiceError("NVD request failed after retries.") from last_error

    @staticmethod
    def _raise_for_status(response: Response) -> None:
        if response.status_code >= 400:
            raise requests.HTTPError(
                "NVD API returned HTTP {0}: {1}".format(response.status_code, response.text),
                response=response,
            )

