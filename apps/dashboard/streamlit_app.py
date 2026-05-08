from typing import Any, Dict, List

import streamlit as st

from apps.dashboard import demo_data, pages
from apps.dashboard.api_client import DashboardApiClient
from apps.dashboard.components import hero
from apps.dashboard.config import configure_dashboard_logging, get_dashboard_settings
from apps.dashboard.styles import apply_enterprise_theme

logger = configure_dashboard_logging()


NAVIGATION = [
    "Overview",
    "AI Security Analysis",
    "Known Security Threats",
    "Analyzed Projects",
    "System Status",
]


def main() -> None:
    settings = get_dashboard_settings()
    st.set_page_config(
        page_title="Predictive Cloud Security Intelligence Platform",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_enterprise_theme()

    client = DashboardApiClient(settings)
    with st.sidebar:
        st.markdown("### PCSI Platform")
        st.caption("AI-powered software security")
        selected_page = st.radio("Navigation", NAVIGATION, label_visibility="collapsed")
        st.divider()
        use_demo_fallback = st.toggle("Demo fallback", value=settings.demo_mode_enabled)
        refresh = st.button("Refresh Intelligence", use_container_width=True)
        st.caption("API: {0}".format(settings.api_base_url))

    if refresh:
        st.cache_data.clear()
        st.success("Dashboard data refreshed.")

    data = load_dashboard_data(settings.api_base_url, use_demo_fallback)
    backend_status = "LIVE API CONNECTED" if data["health"].get("status") == "ok" else "API FALLBACK MODE"
    hero(
        "Predictive Cloud Security Intelligence Platform",
        "Paste a GitHub repository URL to get fast AI-powered security analysis without manual cloning.",
        backend_status,
    )

    route_page(selected_page, client, data)
    logger.info("dashboard_rendered page=%s", selected_page)


@st.cache_data(ttl=30, show_spinner=False)
def load_dashboard_data(api_base_url: str, use_demo_fallback: bool) -> Dict[str, Any]:
    settings = get_dashboard_settings()
    client = DashboardApiClient(settings)

    health = client.health()
    repositories = client.repositories()
    vulnerabilities = client.vulnerabilities()
    metrics = client.metrics()
    risk_scores = client.risk_scores()
    model_metrics = client.model_metrics()

    if use_demo_fallback:
        repositories = repositories or demo_data.demo_repositories()
        vulnerabilities = vulnerabilities or demo_data.demo_vulnerabilities()
        metrics = metrics or demo_data.demo_metrics()
        risk_scores = risk_scores or demo_data.demo_risk_scores()
        model_metrics = model_metrics or demo_data.demo_model_metrics()

    return {
        "api_base_url": api_base_url,
        "health": health,
        "repositories": repositories,
        "vulnerabilities": vulnerabilities,
        "metrics": metrics,
        "risk_scores": _newest_first(risk_scores),
        "model_metrics": _newest_first(model_metrics),
    }


def route_page(selected_page: str, client: DashboardApiClient, data: Dict[str, Any]) -> None:
    repositories: List[Dict[str, Any]] = data["repositories"]
    vulnerabilities: List[Dict[str, Any]] = data["vulnerabilities"]
    metrics: List[Dict[str, Any]] = data["metrics"]
    risk_scores: List[Dict[str, Any]] = data["risk_scores"]
    model_metrics: List[Dict[str, Any]] = data["model_metrics"]

    if selected_page == "Overview":
        pages.executive_overview(repositories, vulnerabilities, metrics, risk_scores, model_metrics)
    elif selected_page == "Known Security Threats":
        pages.vulnerability_intelligence(vulnerabilities)
    elif selected_page == "AI Security Analysis":
        pages.ai_security_analysis(client, repositories, metrics, risk_scores, model_metrics)
    elif selected_page == "Analyzed Projects":
        pages.repository_explorer(repositories, metrics)
    elif selected_page == "System Status":
        pages.system_health(data["health"], data["api_base_url"])


def _newest_first(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda row: row.get("created_at", ""), reverse=True)


if __name__ == "__main__":
    main()
