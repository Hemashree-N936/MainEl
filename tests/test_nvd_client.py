from types import SimpleNamespace

from platform_core.services.nvd_client import NvdClient


class FakeResponse:
    status_code = 200
    text = "ok"

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class FakeHttp:
    def __init__(self):
        self.calls = []

    def get(self, url, params, headers, timeout):
        self.calls.append(params)
        start = params["startIndex"]
        if start == 0:
            return FakeResponse(
                {
                    "totalResults": 3,
                    "vulnerabilities": [{"cve": {"id": "CVE-1"}}, {"cve": {"id": "CVE-2"}}],
                }
            )
        return FakeResponse({"totalResults": 3, "vulnerabilities": [{"cve": {"id": "CVE-3"}}]})


def test_iter_cves_uses_start_index_pagination() -> None:
    settings = SimpleNamespace(
        nvd_base_url="https://example.test",
        nvd_api_key=None,
        nvd_timeout_seconds=1,
        nvd_max_retries=1,
        nvd_retry_backoff_seconds=0,
        nvd_results_per_page=2,
        nvd_cache_ttl_seconds=60,
    )
    http = FakeHttp()
    client = NvdClient(settings=settings, http_session=http)

    cves = list(client.iter_cves({}))

    assert [item["cve"]["id"] for item in cves] == ["CVE-1", "CVE-2", "CVE-3"]
    assert [call["startIndex"] for call in http.calls] == [0, 2]

