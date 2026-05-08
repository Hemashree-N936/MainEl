import streamlit as st


def apply_enterprise_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #222629;
            --panel: rgba(34, 38, 41, 0.88);
            --panel-solid: #2b3033;
            --border: rgba(107, 110, 112, 0.42);
            --text: #f4f7f1;
            --muted: #b8bdb5;
            --cyan: #86C232;
            --blue: #61892F;
            --green: #86C232;
            --yellow: #fbbf24;
            --red: #fb7185;
            --steel: #474B4F;
            --ash: #6B6E70;
        }

        html, body, [class*="css"] {
            font-family: "Inter", sans-serif;
        }

        .stApp {
            color: var(--text);
            background:
                radial-gradient(circle at 18% 12%, rgba(134, 194, 50, 0.13), transparent 28%),
                radial-gradient(circle at 88% 18%, rgba(97, 137, 47, 0.12), transparent 26%),
                linear-gradient(135deg, #222629 0%, #1b1f21 48%, #222629 100%);
            animation: gradientFlow 18s ease-in-out infinite alternate;
        }

        @keyframes gradientFlow {
            from { background-position: 0% 0%; }
            to { background-position: 100% 60%; }
        }

        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 2rem;
            max-width: 1480px;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(34, 38, 41, 0.99), rgba(27, 31, 33, 0.98));
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text);
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
        }

        .pcsi-hero {
            border: 1px solid rgba(134, 194, 50, 0.28);
            background: linear-gradient(135deg, rgba(34, 38, 41, 0.94), rgba(71, 75, 79, 0.62));
            box-shadow: 0 22px 70px rgba(0, 0, 0, 0.38), inset 0 0 48px rgba(134, 194, 50, 0.06);
            border-radius: 12px;
            padding: 26px 30px;
            margin-bottom: 22px;
            position: relative;
            overflow: hidden;
        }

        .pcsi-hero:after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, transparent, rgba(134, 194, 50, 0.10), transparent);
            transform: translateX(-100%);
            animation: scanLine 5.5s ease-in-out infinite;
        }

        @keyframes scanLine {
            0% { transform: translateX(-100%); }
            55% { transform: translateX(100%); }
            100% { transform: translateX(100%); }
        }

        .pcsi-title {
            font-size: 34px;
            font-weight: 800;
            letter-spacing: 0;
            margin: 0;
        }

        .pcsi-subtitle {
            color: var(--muted);
            font-size: 15px;
            margin-top: 8px;
        }

        .pcsi-card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.24);
            transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
            min-height: 118px;
        }

        .pcsi-card:hover {
            transform: translateY(-2px);
            border-color: rgba(134, 194, 50, 0.54);
            box-shadow: 0 20px 55px rgba(134, 194, 50, 0.10);
        }

        .pcsi-health-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .health-badge {
            border: 1px solid var(--border);
            border-radius: 999px;
            padding: 7px 10px;
            color: var(--cyan);
            font-size: 12px;
            font-weight: 800;
            background: rgba(34, 38, 41, 0.78);
        }

        .health-meter {
            height: 9px;
            margin-top: 14px;
            border-radius: 999px;
            background: rgba(107, 110, 112, 0.26);
            overflow: hidden;
        }

        .health-meter span {
            display: block;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--red), var(--yellow), var(--green));
        }

        .repo-card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.24);
        }

        .repo-card-top {
            display: grid;
            grid-template-columns: 52px 1fr auto;
            gap: 12px;
            align-items: center;
        }

        .repo-avatar {
            width: 48px;
            height: 48px;
            border-radius: 10px;
            border: 1px solid var(--border);
        }

        .repo-name {
            font-size: 18px;
            font-weight: 800;
        }

        .repo-url {
            color: var(--muted);
            font-size: 12px;
            word-break: break-all;
        }

        .repo-card-score {
            color: var(--green);
            font-size: 22px;
            font-weight: 800;
        }

        .repo-stats {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 8px;
            margin-top: 14px;
        }

        .repo-stats span {
            border: 1px solid rgba(107, 110, 112, 0.30);
            background: rgba(71, 75, 79, 0.38);
            border-radius: 8px;
            padding: 11px;
            color: var(--muted);
            font-size: 12px;
        }

        .repo-stats b {
            display: block;
            color: var(--text);
            margin-top: 3px;
        }

        .assistant-note {
            display: flex;
            gap: 12px;
            align-items: flex-start;
            border: 1px solid rgba(134, 194, 50, 0.22);
            background: rgba(71, 75, 79, 0.30);
            border-radius: 10px;
            padding: 13px 14px;
            margin-bottom: 10px;
            color: var(--text);
            line-height: 1.45;
        }

        .assistant-note b {
            color: var(--green);
            min-width: 58px;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.08em;
        }

        .assistant-action {
            border-color: rgba(134, 194, 50, 0.34);
            background: rgba(97, 137, 47, 0.22);
        }

        .empty-state {
            border: 1px dashed rgba(134, 194, 50, 0.34);
            background: rgba(71, 75, 79, 0.24);
            border-radius: 10px;
            padding: 18px;
            margin: 12px 0;
        }

        .empty-title {
            font-weight: 800;
            font-size: 15px;
            color: var(--text);
        }

        .empty-body {
            color: var(--muted);
            margin-top: 5px;
            line-height: 1.45;
        }

        @media (max-width: 900px) {
            .repo-stats {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        .pcsi-metric-label {
            color: var(--muted);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .pcsi-metric-value {
            font-size: 30px;
            font-weight: 800;
            margin-top: 10px;
        }

        .pcsi-metric-delta {
            color: var(--cyan);
            font-size: 13px;
            margin-top: 4px;
        }

        .risk-high {
            color: var(--red);
            text-shadow: 0 0 18px rgba(251, 113, 133, 0.6);
            animation: pulseRisk 2s ease-in-out infinite;
        }

        @keyframes pulseRisk {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.72; }
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: rgba(71, 75, 79, 0.42);
            font-weight: 700;
            font-size: 12px;
            text-transform: uppercase;
        }

        .section-title {
            font-size: 20px;
            font-weight: 800;
            margin: 14px 0 12px 0;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }

        .stButton > button {
            border-radius: 8px;
            border: 1px solid rgba(134, 194, 50, 0.42);
            background: linear-gradient(135deg, rgba(134, 194, 50, 0.22), rgba(97, 137, 47, 0.20));
            color: var(--text);
            font-weight: 800;
            transition: transform 160ms ease, box-shadow 160ms ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 28px rgba(134, 194, 50, 0.20);
            border-color: rgba(134, 194, 50, 0.72);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            background: rgba(71, 75, 79, 0.44);
            border: 1px solid var(--border);
            padding: 8px 14px;
        }

        div[data-testid="stAlert"] {
            border-radius: 10px;
            border: 1px solid rgba(134, 194, 50, 0.22);
        }

        .stProgress > div > div > div > div {
            background-color: var(--green);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
