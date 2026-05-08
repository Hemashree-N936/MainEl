from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PLOTLY_TEMPLATE = "plotly_dark"
SEVERITY_COLORS = {
    "CRITICAL": "#fb7185",
    "HIGH": "#f97316",
    "MEDIUM": "#fbbf24",
    "LOW": "#86C232",
    "UNKNOWN": "#6B6E70",
}
RISK_COLORS = {"high": "#fb7185", "medium": "#fbbf24", "low": "#86C232"}
SIGNAL_LABELS = {
    "code_churn": "Code Stability",
    "dependency_change_commits": "Package Risk Activity",
    "weekend_commit_ratio": "Unusual Development Timing",
    "off_hours_commit_ratio": "After-Hours Development Timing",
    "contributor_count": "Team Activity",
    "known_vulnerability_count": "Known Security Exposure",
    "high_vulnerability_count": "Known Security Exposure",
    "critical_vulnerability_count": "Known Security Exposure",
    "commit_count": "Development Activity",
    "commit_frequency_per_week": "Development Activity",
    "health_score": "Security Health",
}


def apply_chart_style(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f4f7f1", "family": "Inter"},
        margin={"l": 20, "r": 20, "t": 50, "b": 24},
        legend={"orientation": "h", "y": -0.18},
    )
    fig.update_xaxes(gridcolor="rgba(107,110,112,0.22)")
    fig.update_yaxes(gridcolor="rgba(107,110,112,0.22)")
    return fig


def vulnerability_severity_chart(vulnerabilities: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(vulnerabilities)
    if frame.empty:
        frame = pd.DataFrame({"severity": ["UNKNOWN"], "count": [0]})
    else:
        frame["severity"] = frame["severity"].fillna("UNKNOWN")
        frame = frame.groupby("severity").size().reset_index(name="count")
    fig = px.bar(
        frame,
        x="severity",
        y="count",
        color="severity",
        color_discrete_map=SEVERITY_COLORS,
        title="Known Security Exposure",
    )
    return apply_chart_style(fig)


def cve_timeline(vulnerabilities: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(vulnerabilities)
    if frame.empty or "modified_at" not in frame:
        frame = pd.DataFrame({"date": pd.date_range(end=pd.Timestamp.utcnow(), periods=7), "count": [0] * 7})
    else:
        frame["date"] = pd.to_datetime(frame["modified_at"], errors="coerce").dt.date
        frame = frame.dropna(subset=["date"]).groupby("date").size().reset_index(name="count")
    fig = px.area(frame, x="date", y="count", title="Known Security Threat Activity")
    fig.update_traces(line_color="#86C232", fillcolor="rgba(134,194,50,0.22)")
    return apply_chart_style(fig)


def risk_distribution(risk_scores: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(risk_scores)
    if frame.empty:
        frame = pd.DataFrame({"risk_level": ["low", "medium", "high"], "count": [0, 0, 0]})
    else:
        frame = frame.groupby("risk_level").size().reset_index(name="count")
    fig = px.pie(
        frame,
        names="risk_level",
        values="count",
        hole=0.58,
        color="risk_level",
        color_discrete_map=RISK_COLORS,
        title="AI Security Risk Distribution",
    )
    return apply_chart_style(fig)


def confidence_gauge(score: float, title: str = "Prediction Confidence") -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=round(score * 100, 1),
            number={"suffix": "%"},
            title={"text": title},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#86C232"},
                "steps": [
                    {"range": [0, 40], "color": "rgba(251,113,133,0.24)"},
                    {"range": [40, 70], "color": "rgba(251,191,36,0.24)"},
                    {"range": [70, 100], "color": "rgba(134,194,50,0.24)"},
                ],
            },
        )
    )
    return apply_chart_style(fig, height=300)


def metric_heatmap(metrics: List[Dict[str, Any]], repositories: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(metrics)
    if frame.empty and repositories:
        frame = pd.DataFrame(
            {
                "repository_id": [repo["id"] for repo in repositories],
                "metric_name": ["health_score"] * len(repositories),
                "metric_value": [0] * len(repositories),
            }
        )
    if frame.empty:
        frame = pd.DataFrame(
            {"repository": ["No data"], "metric_name": ["health_score"], "metric_value": [0]}
        )
        pivot = frame.pivot_table(
            index="repository",
            columns="metric_name",
            values="metric_value",
            aggfunc="mean",
            fill_value=0,
        )
        fig = px.imshow(
            pivot[["health_score"]],
            aspect="auto",
            color_continuous_scale=["#222629", "#61892F", "#86C232"],
            title="AI Security Signals",
        )
        return apply_chart_style(fig)
    repo_names = {repo["id"]: repo["name"] for repo in repositories}
    frame["repository"] = frame["repository_id"].map(repo_names).fillna(frame["repository_id"].astype(str))
    pivot = frame.pivot_table(
        index="repository",
        columns="metric_name",
        values="metric_value",
        aggfunc="mean",
        fill_value=0,
    )
    preferred = [
        "health_score",
        "code_churn",
        "dependency_change_commits",
        "weekend_commit_ratio",
        "off_hours_commit_ratio",
    ]
    columns = [column for column in preferred if column in pivot.columns]
    if not columns:
        columns = list(pivot.columns[:5])
    display = pivot[columns].rename(columns=SIGNAL_LABELS)
    fig = px.imshow(
        display,
        aspect="auto",
        color_continuous_scale=["#222629", "#61892F", "#86C232"],
        title="AI Security Signals",
    )
    return apply_chart_style(fig)


def code_churn_chart(metrics: List[Dict[str, Any]], repositories: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(metrics)
    repo_names = {repo["id"]: repo["name"] for repo in repositories}
    if frame.empty:
        frame = pd.DataFrame({"repository_id": [], "metric_name": [], "metric_value": []})
    frame = frame[frame.get("metric_name", pd.Series(dtype=str)).isin(["code_churn", "commit_count"])]
    if frame.empty:
        frame = pd.DataFrame({"repository": ["No data"], "metric_name": ["Code Stability"], "metric_value": [0]})
    else:
        frame["repository"] = frame["repository_id"].map(repo_names).fillna(frame["repository_id"].astype(str))
        frame["metric_name"] = frame["metric_name"].map(SIGNAL_LABELS).fillna(frame["metric_name"])
    fig = px.bar(
        frame,
        x="repository",
        y="metric_value",
        color="metric_name",
        barmode="group",
        title="Code Stability And Development Activity",
        labels={"metric_value": "Signal strength", "metric_name": "Signal", "repository": "Repository"},
        color_discrete_sequence=["#86C232", "#61892F"],
    )
    return apply_chart_style(fig)


def contributor_activity_chart(metrics: List[Dict[str, Any]], repositories: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(metrics)
    repo_names = {repo["id"]: repo["name"] for repo in repositories}
    if frame.empty:
        frame = pd.DataFrame({"repository": ["No data"], "Team Activity": [0], "Package Risk Activity": [0]})
    else:
        pivot = frame.pivot_table(
            index="repository_id",
            columns="metric_name",
            values="metric_value",
            aggfunc="mean",
            fill_value=0,
        ).reset_index()
        pivot["repository"] = pivot["repository_id"].map(repo_names).fillna(pivot["repository_id"].astype(str))
        frame = pd.DataFrame(
            {
                "repository": pivot["repository"],
                "Team Activity": pivot.get("contributor_count", 0),
                "Package Risk Activity": pivot.get("dependency_change_commits", 0),
            }
        )
    fig = px.scatter(
        frame,
        x="Team Activity",
        y="Package Risk Activity",
        text="repository",
        size="Package Risk Activity",
        title="Team Activity And Package Risk Activity",
        color="Package Risk Activity",
        color_continuous_scale=["#474B4F", "#61892F", "#86C232"],
    )
    fig.update_traces(textposition="top center")
    return apply_chart_style(fig)


def model_comparison_chart(model_metrics: List[Dict[str, Any]]) -> go.Figure:
    rows = []
    for run in model_metrics:
        for candidate in run.get("metrics_json", {}).get("candidates", []):
            for metric_name in ["precision", "recall", "f1_score", "roc_auc"]:
                rows.append(
                    {
                        "model": candidate.get("model_type", run.get("model_type")),
                        "metric": metric_name,
                        "value": candidate.get(metric_name, 0),
                    }
                )
    frame = pd.DataFrame(rows)
    if frame.empty:
        frame = pd.DataFrame({"model": ["No model"], "metric": ["f1_score"], "value": [0]})
    fig = px.bar(
        frame,
        x="metric",
        y="value",
        color="model",
        barmode="group",
        range_y=[0, 1],
        title="Advanced Model Metrics",
        color_discrete_sequence=["#86C232", "#61892F", "#6B6E70"],
    )
    return apply_chart_style(fig)


def temporal_activity_chart(metrics: List[Dict[str, Any]], repositories: List[Dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(metrics)
    repo_names = {repo["id"]: repo["name"] for repo in repositories}
    if frame.empty:
        frame = pd.DataFrame({"repository": ["No data"], "pattern": ["Unusual Development Timing"], "value": [0]})
    else:
        frame = frame[frame["metric_name"].isin(["weekend_commit_ratio", "off_hours_commit_ratio"])]
        frame["repository"] = frame["repository_id"].map(repo_names).fillna(frame["repository_id"].astype(str))
        frame = frame.rename(columns={"metric_name": "pattern", "metric_value": "value"})
        frame["pattern"] = frame["pattern"].map(SIGNAL_LABELS).fillna(frame["pattern"])
    fig = px.line(
        frame,
        x="repository",
        y="value",
        color="pattern",
        markers=True,
        title="Development Activity Patterns",
        labels={"value": "Signal strength", "pattern": "Signal", "repository": "Repository"},
        color_discrete_sequence=["#86C232", "#6B6E70"],
    )
    return apply_chart_style(fig)
