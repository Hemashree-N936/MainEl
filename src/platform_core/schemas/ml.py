from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class TrainingResponse(BaseModel):
    model_run_id: int
    selected_model: str
    artifact_path: str
    training_rows: int
    metrics: Dict[str, Any]


class ModelRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_name: str
    model_type: str
    artifact_path: str
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    roc_auc: Optional[float] = None
    training_rows: int
    feature_columns: Dict[str, Any]
    metrics_json: Dict[str, Any]
    created_at: datetime


class PredictionResponse(BaseModel):
    repository_id: int
    model_run_id: int
    risk_score: float
    risk_level: str
    confidence: float
    summary: Dict[str, Any]


class RepositoryRiskScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    model_run_id: Optional[int] = None
    risk_score: float
    risk_level: str
    confidence: float
    summary_json: Dict[str, Any]
    created_at: datetime


class FeatureColumnsResponse(BaseModel):
    columns: List[str]

