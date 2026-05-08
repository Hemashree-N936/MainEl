from typing import Any, Dict, Optional
from html import escape

import streamlit as st


def hero(title: str, subtitle: str, status: str) -> None:
    st.markdown(
        """
        <div class="pcsi-hero">
            <div class="status-pill">{status}</div>
            <h1 class="pcsi-title">{title}</h1>
            <div class="pcsi-subtitle">{subtitle}</div>
        </div>
        """.format(title=escape(title), subtitle=escape(subtitle), status=escape(status)),
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, delta: Optional[str] = None, risk: Optional[str] = None) -> None:
    risk_class = "risk-high" if risk == "high" else ""
    st.markdown(
        """
        <div class="pcsi-card">
            <div class="pcsi-metric-label">{label}</div>
            <div class="pcsi-metric-value {risk_class}">{value}</div>
            <div class="pcsi-metric-delta">{delta}</div>
        </div>
        """.format(
            label=escape(label),
            value=escape(value),
            delta=escape(delta or "Live intelligence"),
            risk_class=risk_class,
        ),
        unsafe_allow_html=True,
    )


def security_health_card(score: int, label: str) -> None:
    risk = "high" if label == "High Risk" else None
    st.markdown(
        """
        <div class="pcsi-card health-card">
            <div class="pcsi-metric-label">Security Health Score</div>
            <div class="pcsi-health-row">
                <div class="pcsi-metric-value {risk_class}">{score}</div>
                <div class="health-badge">{label}</div>
            </div>
            <div class="health-meter"><span style="width: {score}%"></span></div>
        </div>
        """.format(score=score, label=escape(label), risk_class="risk-high" if risk else ""),
        unsafe_allow_html=True,
    )


def github_repository_card(github: Dict[str, Any], score: Optional[int] = None) -> None:
    avatar = github.get("avatar_url") or ""
    score_html = ""
    if score is not None:
        score_html = '<div class="repo-card-score">{0}/100</div>'.format(score)
    st.markdown(
        """
        <div class="repo-card">
            <div class="repo-card-top">
                <img src="{avatar}" class="repo-avatar" />
                <div>
                    <div class="repo-name">{name}</div>
                    <div class="repo-url">{url}</div>
                </div>
                {score_html}
            </div>
            <div class="repo-stats">
                <span>Stars <b>{stars}</b></span>
                <span>Forks <b>{forks}</b></span>
                <span>Team <b>{contributors}</b></span>
                <span>Issues <b>{issues}</b></span>
                <span>Branches <b>{branches}</b></span>
                <span>Updated <b>{updated}</b></span>
            </div>
        </div>
        """.format(
            avatar=escape(str(avatar)),
            name=escape(str(github.get("full_name") or github.get("name") or "Repository")),
            url=escape(str(github.get("url") or "")),
            stars=github.get("stars", 0),
            forks=github.get("forks", 0),
            contributors=github.get("contributors", 0),
            issues=github.get("open_issues", 0),
            branches=github.get("branch_count", 0),
            updated=escape(str(github.get("last_updated", "unknown"))),
            score_html=score_html,
        ),
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown('<div class="section-title">{0}</div>'.format(escape(text)), unsafe_allow_html=True)


def empty_state(title: str, body: str) -> None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-title">{title}</div>
            <div class="empty-body">{body}</div>
        </div>
        """.format(title=escape(title), body=escape(body)),
        unsafe_allow_html=True,
    )


def assistant_note(message: str, tone: str = "info") -> None:
    icon = "Action" if tone == "action" else "Insight"
    st.markdown(
        """
        <div class="assistant-note assistant-{tone}">
            <b>{icon}</b>
            <span>{message}</span>
        </div>
        """.format(tone=escape(tone), icon=icon, message=escape(message)),
        unsafe_allow_html=True,
    )


def error_state(message: str) -> None:
    st.error(message)
