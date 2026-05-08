from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

from apps.dashboard import charts
from apps.dashboard.components import (
    assistant_note,
    empty_state,
    github_repository_card,
    metric_card,
    section_title,
    security_health_card,
)


def normalize_data(
    repositories: List[Dict[str, Any]],
    vulnerabilities: List[Dict[str, Any]],
    metrics: List[Dict[str, Any]],
    risk_scores: List[Dict[str, Any]],
    model_metrics: List[Dict[str, Any]],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return (
        pd.DataFrame(repositories),
        pd.DataFrame(vulnerabilities),
        pd.DataFrame(metrics),
        pd.DataFrame(risk_scores),
        pd.DataFrame(model_metrics),
    )


def executive_overview(repositories, vulnerabilities, metrics, risk_scores, model_metrics) -> None:
    repo_df, vuln_df, metric_df, risk_df, model_df = normalize_data(
        repositories,
        vulnerabilities,
        metrics,
        risk_scores,
        model_metrics,
    )
    critical_count = _severity_count(vuln_df, "CRITICAL")
    high_risk_count = _risk_level_count(risk_df, "high")
    latest_model = "Ready" if not model_df.empty and "model_type" in model_df else "Not trained"

    cols = st.columns(4)
    with cols[0]:
        metric_card("Protected Repositories", str(len(repo_df)), "Projects watched")
    with cols[1]:
        metric_card("Known Security Exposure", str(len(vuln_df)), "Threat signals")
    with cols[2]:
        metric_card("Critical Exposure", str(critical_count), "Needs attention", "high" if critical_count else None)
    with cols[3]:
        metric_card("High Risk Projects", str(high_risk_count), "AI engine {0}".format(latest_model), "high" if high_risk_count else None)

    left, right = st.columns([1.4, 1])
    with left:
        section_title("Security Overview")
        st.plotly_chart(charts.metric_heatmap(metrics, repositories), use_container_width=True)
    with right:
        section_title("Risk Distribution")
        st.plotly_chart(charts.risk_distribution(risk_scores), use_container_width=True)

    lower_left, lower_right = st.columns(2)
    with lower_left:
        st.plotly_chart(charts.cve_timeline(vulnerabilities), use_container_width=True)
    with lower_right:
        st.plotly_chart(charts.contributor_activity_chart(metrics, repositories), use_container_width=True)
    assistant_note("Paste a GitHub URL in AI Security Analysis to get a plain-English risk briefing without cloning the repository.")


def vulnerability_intelligence(vulnerabilities: List[Dict[str, Any]]) -> None:
    section_title("Known Security Threats")
    frame = pd.DataFrame(vulnerabilities)
    controls = st.columns([1, 1, 2])
    severity = controls[0].selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    search = controls[1].text_input("Search CVE")
    if not frame.empty:
        if severity != "All" and "severity" in frame:
            frame = frame[frame["severity"] == severity]
        if search and "cve_id" in frame:
            frame = frame[frame["cve_id"].str.contains(search, case=False, na=False)]

    left, right = st.columns([1, 1])
    with left:
        st.plotly_chart(charts.vulnerability_severity_chart(frame.to_dict("records")), use_container_width=True)
    with right:
        st.plotly_chart(charts.cve_timeline(frame.to_dict("records")), use_container_width=True)

    if frame.empty:
        empty_state("No known security exposure found", "Run NVD ingestion or adjust filters. The assistant will show matching threats here.")
        return

    for _, row in frame.head(20).iterrows():
        severity_value = row.get("severity", "UNKNOWN")
        title = "{0} - {1} - CVSS {2}".format(
            row.get("cve_id", "Unknown CVE"),
            severity_value,
            row.get("cvss_score", "n/a"),
        )
        with st.expander(title):
            assistant_note(row.get("summary", "No summary available."))
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "CWE": row.get("cwe"),
                            "Published": row.get("published_at"),
                            "Modified": row.get("modified_at"),
                            "Source": row.get("source"),
                        }
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )


def repository_risk_analysis(repositories, metrics, risk_scores) -> None:
    section_title("AI Security Analysis")
    st.plotly_chart(charts.metric_heatmap(metrics, repositories), use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts.code_churn_chart(metrics, repositories), use_container_width=True)
    with right:
        st.plotly_chart(charts.temporal_activity_chart(metrics, repositories), use_container_width=True)

    risk_df = _risk_with_names(risk_scores, repositories)
    if risk_df.empty:
        empty_state("No AI security scores", "Paste a GitHub repository URL or run a prediction.")
    else:
        st.dataframe(risk_df, use_container_width=True, hide_index=True)


def ml_prediction_center(client, repositories, risk_scores) -> None:
    section_title("AI Security Analysis")
    repo_names = {repo["name"]: repo["id"] for repo in repositories}
    if not repo_names:
        empty_state("No repositories", "Register repositories before running predictions.")
        return

    selected_name = st.selectbox("Repository", list(repo_names.keys()))
    selected_id = repo_names[selected_name]

    actions = st.columns([1, 1, 2])
    if actions[0].button("Run Prediction", use_container_width=True):
        with st.spinner("Generating repository risk prediction..."):
            result = client.trigger_prediction(selected_id)
        if result:
            st.success("AI security analysis completed.")
            st.json(result)
        else:
            st.error("Analysis failed. Check API logs and ML runtime dependencies.")

    if actions[1].button("Train Model", use_container_width=True):
        with st.spinner("Training model candidates..."):
            result = client.trigger_training()
        if result:
            st.success("Training completed and model artifact persisted.")
            st.json(result)
        else:
            st.error("Training failed. Check API logs and ML runtime dependencies.")

    selected_scores = [score for score in risk_scores if score.get("repository_id") == selected_id]
    latest = selected_scores[0] if selected_scores else None
    left, right = st.columns([1, 1])
    with left:
        st.plotly_chart(
            charts.confidence_gauge(float(latest.get("confidence", 0)) if latest else 0),
            use_container_width=True,
        )
    with right:
        if latest:
            metric_card("AI Risk Score", "{0:.0%}".format(float(latest.get("risk_score", 0))), latest.get("risk_level"), latest.get("risk_level"))
            summary = latest.get("summary_json") or {}
            st.info(summary.get("recommendation", "No recommendation available."))
        else:
            empty_state("No analysis yet", "Run analysis for the selected repository.")


def ai_security_analysis(client, repositories, metrics, risk_scores, model_metrics) -> None:
    section_title("AI Security Analysis")
    st.caption("Paste a public GitHub repository URL. Quick Analysis uses the GitHub API only; Deep Scan uses your existing local repository mining pipeline.")
    assistant_note("Quick Analysis checks repository activity, team signals, release cadence, issue pressure, and freshness, then runs the existing AI risk model.")

    with st.container():
        cols = st.columns([2.2, 1, 1])
        github_url = cols[0].text_input(
            "GitHub repository URL",
            placeholder="https://github.com/owner/repository",
            help="Quick Analysis does not clone the repository.",
        )
        mode_label = cols[1].selectbox("Analysis mode", ["Quick Analysis", "Deep Scan Mode"])
        repository_path = ""
        if mode_label == "Deep Scan Mode":
            repository_path = cols[2].text_input("Local repo path", placeholder="C:\\path\\to\\repo")
        else:
            cols[2].markdown("")
            cols[2].caption("No cloning required")

    run_analysis = st.button("Analyze Repository", use_container_width=True)
    if run_analysis:
        if not github_url.strip():
            st.error("Paste a GitHub repository URL to start analysis.")
        elif mode_label == "Deep Scan Mode" and not repository_path.strip():
            st.error("Deep Scan Mode requires a local repository path.")
        else:
            progress = st.progress(0, text="Checking the GitHub URL...")
            with st.spinner("Gathering repository intelligence..."):
                progress.progress(25, text="Reading repository profile and activity signals...")
                result = client.analyze_github_repository(
                    github_url.strip(),
                    "deep" if mode_label == "Deep Scan Mode" else "quick",
                    repository_path.strip() if repository_path.strip() else None,
                )
                progress.progress(75, text="Asking the AI model for a security assessment...")
            if result:
                if result.get("error"):
                    progress.empty()
                    st.error(result["error"])
                else:
                    progress.progress(100, text="Security briefing ready.")
                    st.success("Security briefing ready.")
                    st.session_state["latest_github_analysis"] = result
                    st.cache_data.clear()
            else:
                progress.empty()
                st.error("The assistant could not complete the analysis. Check the URL, API status, or GitHub rate limits.")

    latest = st.session_state.get("latest_github_analysis")
    if latest:
        _render_github_analysis_result(latest)
    else:
        empty_state(
            "Ready for analysis",
            "Start with Quick Analysis for a fast AI briefing. Use Deep Scan Mode only when you want full local repository inspection.",
        )

    st.divider()
    _render_existing_security_analysis(client, repositories, metrics, risk_scores)

    with st.expander("Developer Mode: advanced model diagnostics", expanded=False):
        model_metrics_page(model_metrics)


def _render_github_analysis_result(result: Dict[str, Any]) -> None:
    github = result.get("github", {})
    prediction = result.get("prediction", {})
    score = int(result.get("security_health_score", 0))
    label = result.get("health_label", "Unknown")
    github_repository_card(github, score)

    cols = st.columns(4)
    with cols[0]:
        security_health_card(score, label)
    with cols[1]:
        metric_card("AI Risk", "{0:.0%}".format(float(prediction.get("risk_score", 0))), prediction.get("risk_level"), prediction.get("risk_level"))
    with cols[2]:
        metric_card("Development Activity", str(github.get("recent_commit_count", 0)), "Recent commits")
    with cols[3]:
        metric_card("Package Risk Activity", str(github.get("recent_release_count", 0)), "Recent releases")

    left, right = st.columns([1, 1])
    with left:
        section_title("Plain-English Explanation")
        for explanation in result.get("explanations", []):
            assistant_note(explanation)
    with right:
        section_title("Recommended Actions")
        for recommendation in result.get("recommendations", []):
            assistant_note(recommendation, tone="action")


def _render_existing_security_analysis(client, repositories, metrics, risk_scores) -> None:
    section_title("Assistant Signal Review")
    st.plotly_chart(charts.metric_heatmap(metrics, repositories), use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts.code_churn_chart(metrics, repositories), use_container_width=True)
    with right:
        st.plotly_chart(charts.temporal_activity_chart(metrics, repositories), use_container_width=True)

    repo_names = {repo["name"]: repo["id"] for repo in repositories}
    if repo_names:
        with st.expander("Run analysis for an already registered project", expanded=False):
            selected_name = st.selectbox("Project", list(repo_names.keys()))
            selected_id = repo_names[selected_name]
            if st.button("Run AI Prediction", use_container_width=True):
                with st.spinner("Running AI prediction..."):
                    result = client.trigger_prediction(selected_id)
                if result:
                    st.success("AI prediction completed.")
                    st.json(_friendly_prediction(result))
                else:
                    st.error("Prediction failed. Check API logs and ML runtime dependencies.")

    risk_df = _risk_with_names(risk_scores, repositories)
    if risk_df.empty:
        empty_state("No previous analysis", "Completed GitHub analyses will appear here with risk labels, confidence, and assistant recommendations.")
    else:
        st.dataframe(risk_df, use_container_width=True, hide_index=True)


def threat_analytics(vulnerabilities, metrics, risk_scores, repositories) -> None:
    section_title("Threat Analytics")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts.vulnerability_severity_chart(vulnerabilities), use_container_width=True)
    with right:
        st.plotly_chart(charts.contributor_activity_chart(metrics, repositories), use_container_width=True)
    st.plotly_chart(charts.risk_distribution(risk_scores), use_container_width=True)


def repository_explorer(repositories, metrics) -> None:
    section_title("Analyzed Projects")
    repo_df = pd.DataFrame(repositories)
    if repo_df.empty:
        empty_state("No repositories", "Use the API or seed script to register repositories.")
        return
    search = st.text_input("Filter repositories")
    if search:
        repo_df = repo_df[repo_df["name"].str.contains(search, case=False, na=False)]
    st.dataframe(repo_df, use_container_width=True, hide_index=True)
    st.plotly_chart(charts.code_churn_chart(metrics, repositories), use_container_width=True)


def model_metrics_page(model_metrics: List[Dict[str, Any]]) -> None:
    section_title("Developer Diagnostics")
    st.plotly_chart(charts.model_comparison_chart(model_metrics), use_container_width=True)
    frame = pd.DataFrame(model_metrics)
    if frame.empty:
        empty_state("No model runs", "Run model training to populate comparison metrics.")
    else:
        st.dataframe(frame, use_container_width=True, hide_index=True)
        skipped = []
        for run in model_metrics:
            skipped.extend(run.get("metrics_json", {}).get("skipped", []))
        if skipped:
            st.warning("Some model candidates were skipped for runtime compatibility.")
            st.dataframe(pd.DataFrame(skipped), use_container_width=True, hide_index=True)


def model_metrics(model_metrics: List[Dict[str, Any]]) -> None:
    model_metrics_page(model_metrics)


def system_health(health: Dict[str, Any], api_base_url: str) -> None:
    section_title("System Status")
    cols = st.columns(3)
    with cols[0]:
        metric_card("API Status", health.get("status", "unreachable"))
    with cols[1]:
        metric_card("Environment", health.get("environment", "unknown"))
    with cols[2]:
        metric_card("Backend URL", api_base_url)
    st.code(api_base_url, language="text")


def _severity_count(frame: pd.DataFrame, severity: str) -> int:
    if frame.empty or "severity" not in frame:
        return 0
    return int((frame["severity"] == severity).sum())


def _risk_level_count(frame: pd.DataFrame, level: str) -> int:
    if frame.empty or "risk_level" not in frame:
        return 0
    return int((frame["risk_level"] == level).sum())


def _risk_with_names(risk_scores: List[Dict[str, Any]], repositories: List[Dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(risk_scores)
    if frame.empty:
        return frame
    names = {repo["id"]: repo["name"] for repo in repositories}
    frame["repository"] = frame["repository_id"].map(names).fillna(frame["repository_id"].astype(str))
    columns = ["repository", "risk_level", "risk_score", "confidence", "created_at"]
    frame = frame[[column for column in columns if column in frame]]
    return frame.rename(
        columns={
            "repository": "Project",
            "risk_level": "Risk label",
            "risk_score": "AI risk score",
            "confidence": "Confidence",
            "created_at": "Analyzed at",
        }
    )


def _friendly_prediction(result: Dict[str, Any]) -> Dict[str, Any]:
    summary = result.get("summary", {})
    signals = [
        {"Signal": _friendly_signal(driver.get("name", "signal")), "Value": driver.get("value")}
        for driver in summary.get("top_drivers", [])
    ]
    return {
        "AI risk score": result.get("risk_score"),
        "Risk label": result.get("risk_level"),
        "Confidence": result.get("confidence"),
        "Recommendation": summary.get("recommendation"),
        "Main signals": signals,
    }


def _friendly_signal(name: str) -> str:
    labels = {
        "code_churn": "Code Stability",
        "dependency_change_commits": "Package Risk Activity",
        "weekend_commit_ratio": "Unusual Development Timing",
        "off_hours_commit_ratio": "After-Hours Development Timing",
        "contributor_count": "Team Activity",
        "known_vulnerability_count": "Known Security Exposure",
        "high_vulnerability_count": "Known Security Exposure",
        "critical_vulnerability_count": "Known Security Exposure",
    }
    return labels.get(name, name.replace("_", " ").title())
