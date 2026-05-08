from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class RepositoryAnalysisRequest(BaseModel):
    repository_id: int
    repository_path: Path


class RepositoryAnalysisResponse(BaseModel):
    repository_id: int
    metrics: Dict[str, float]


class EngineeredMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    metric_name: str
    metric_value: float
    scope: str
    measured_at: datetime
    metric_metadata: Optional[dict] = None

