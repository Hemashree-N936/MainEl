from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class RepositoryCreate(BaseModel):
    name: str
    url: HttpUrl
    default_branch: str = "main"


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    default_branch: str
    created_at: datetime
    updated_at: datetime


class GitHubRepositoryAnalysisRequest(BaseModel):
    github_url: str
    analysis_mode: str = "quick"
    repository_path: Optional[Path] = None


class GitHubRepositoryAnalysisResponse(BaseModel):
    analysis_mode: str
    repository: Dict[str, Any]
    github: Dict[str, Any]
    metrics: Dict[str, float]
    prediction: Dict[str, Any]
    security_health_score: int
    health_label: str
    explanations: List[str]
    recommendations: List[str]
