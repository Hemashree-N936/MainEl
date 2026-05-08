from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from platform_core.db.session import get_db
from platform_core.schemas.ml import (
    FeatureColumnsResponse,
    ModelRunRead,
    PredictionResponse,
    RepositoryRiskScoreRead,
    TrainingResponse,
)
from platform_core.services.ml.constants import FEATURE_COLUMNS
from platform_core.services.ml.model_service import ModelTrainingService
from platform_core.services.ml.prediction_service import PredictionService

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/train", response_model=TrainingResponse)
def train_model(db: Session = Depends(get_db)) -> TrainingResponse:
    return TrainingResponse(**ModelTrainingService(db).train_and_compare())


@router.post("/predict/repositories/{repository_id}", response_model=PredictionResponse)
def predict_repository(repository_id: int, db: Session = Depends(get_db)) -> PredictionResponse:
    return PredictionResponse(**PredictionService(db).predict_repository(repository_id))


@router.get("/model-metrics", response_model=List[ModelRunRead])
def get_model_metrics(db: Session = Depends(get_db)) -> List[ModelRunRead]:
    return ModelTrainingService(db).list_model_metrics()


@router.get("/risk-scores", response_model=List[RepositoryRiskScoreRead])
def get_risk_scores(
    repository_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[RepositoryRiskScoreRead]:
    return PredictionService(db).list_risk_scores(repository_id=repository_id)


@router.get("/features", response_model=FeatureColumnsResponse)
def get_feature_columns() -> FeatureColumnsResponse:
    return FeatureColumnsResponse(columns=FEATURE_COLUMNS)
