# Predictive Cloud Security Intelligence Platform

Enterprise-grade AI-powered DevSecOps platform for predicting software vulnerability risk before deployment.

Phase 1 establishes the production-style foundation only. ML models, CVE ingestion pipelines, CI/CD workflows, and full frontend workflows are intentionally deferred.

## Architecture Overview

```text
apps/
  api/                  FastAPI entrypoint
  dashboard/            Streamlit dashboard shell
src/platform_core/
  api/                  FastAPI app factory and route modules
  core/                 environment config and structured logging
  db/                   SQLAlchemy engine, session, and database initialization
  models/               SQLAlchemy domain models
  schemas/              Pydantic request/response schemas
  services/             reusable business/service boundaries
  utils/                common utilities and platform exceptions
tests/                  import and API smoke tests
data/                   local repository and SQLite storage
```

## Phase 1 Capabilities

- Modular FastAPI backend with `/api/v1/health` and repository registration endpoints.
- SQLAlchemy database layer using SQLite by default.
- Initial domain models for repositories, commits, dependencies, and vulnerabilities.
- Pydantic schemas for API contracts.
- Structured JSON logging and environment-driven configuration.
- Reusable service boundaries for repository management, Git analysis, and vulnerability intelligence.
- Streamlit dashboard base with Plotly readiness visualization.
- Docker and docker-compose support for API and dashboard services.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Run the API:

```bash
set PYTHONPATH=src
uvicorn apps.api.main:app --reload
```

Run the dashboard:

```bash
set PYTHONPATH=src
streamlit run apps/dashboard/streamlit_app.py
```

Run tests:

```bash
set PYTHONPATH=src
pytest
```

## Docker

```bash
copy .env.example .env
docker compose up --build
```

Services:

- API: <http://localhost:8000/docs>
- Dashboard: <http://localhost:8501>

## Phase 4 Dashboard

The Streamlit dashboard provides a dark enterprise cybersecurity command center with:

- Executive overview, vulnerability intelligence, repository risk analysis, ML prediction center, threat analytics, repository explorer, model metrics, and system health.
- Live API integration for vulnerabilities, repository metrics, model metrics, predictions, risk scores, and health.
- Demo fallback data controlled by `DASHBOARD_DEMO_MODE=true` for evaluator presentations when the backend has limited data.
- Interactive filters, repository selection, prediction and training buttons, expandable CVE details, risk recommendations, and live refresh.

## Phase 5 Product Intelligence And GitHub API Analysis

The dashboard now supports a product-style GitHub repository workflow:

- Paste `https://github.com/owner/repository` into **AI Security Analysis**.
- **Quick Analysis** uses the GitHub REST API only and does not clone repositories.
- **Deep Scan Mode** remains available for advanced local GitPython mining when a local repository path is provided.
- GitHub metadata, activity, contributors, releases, issues, branches, freshness, and repository age are converted into existing platform metrics.
- The existing ML prediction pipeline generates an AI risk result, Security Health Score, plain-English explanations, and recommended actions.
- Advanced ROC-AUC, precision, recall, and candidate model diagnostics are kept under Developer Mode.

Optional GitHub API configuration:

```bash
set GITHUB_API_TOKEN=your_token_here
```

API endpoint:

- `POST /api/v1/repositories/analyze-github`

Launch locally:

```bash
set PYTHONPATH=.
set API_BASE_URL=http://localhost:8000/api/v1
streamlit run apps/dashboard/streamlit_app.py
```

For Docker:

```bash
docker compose up --build
```

## API Endpoints

- `GET /api/v1/health`
- `GET /api/v1/repositories`
- `POST /api/v1/repositories`
- `GET /api/v1/vulnerabilities`
- `GET /api/v1/vulnerabilities/{cve_id}`
- `POST /api/v1/vulnerabilities/ingest/nvd`
- `GET /api/v1/metrics`
- `POST /api/v1/metrics/repository-analysis`
- `POST /api/v1/ml/train`
- `POST /api/v1/ml/predict/repositories/{repository_id}`
- `GET /api/v1/ml/model-metrics`
- `GET /api/v1/ml/risk-scores`
- `GET /api/v1/ml/features`

Example repository payload:

```json
{
  "name": "example-service",
  "url": "https://github.com/example/example-service",
  "default_branch": "main"
}
```

## Next Phases

- Repository evolution feature extraction.
- Commit history and contributor behavior analytics.
- Dependency diffing and package ecosystem parsers.
- CVE/NVD ingestion and vulnerability enrichment.
- Model training with scikit-learn, XGBoost, and SHAP explanations.
- GitHub Actions CI/CD and security checks.

## Phase 2 Ingestion And Mining

Seed local demo data:

```bash
set PYTHONPATH=src
python scripts/seed_demo_data.py
```

Ingest recent NVD CVEs:

```bash
set PYTHONPATH=src
python scripts/ingest_nvd.py --modified-start 2026-05-01T00:00:00 --limit 50
```

Analyze a local Git repository:

```bash
set PYTHONPATH=src
python scripts/analyze_repository.py --path C:\path\to\repo --name demo-service --url https://github.com/example/demo-service
```

## Phase 3 Training And Prediction

Train and compare Random Forest and XGBoost models:

```bash
set PYTHONPATH=src
python scripts/train_model.py
```

Generate a repository prediction after training:

```bash
set PYTHONPATH=src
python scripts/predict_repository_risk.py --repository-id 1
```

The training pipeline uses mined repository metrics, commit aggregates, dependency counts, vulnerability aggregates, and repository health indicators. If there are not enough repository rows yet, it generates realistic synthetic training rows so the pipeline can be exercised before production labels exist.
