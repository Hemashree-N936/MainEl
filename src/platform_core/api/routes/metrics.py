from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from platform_core.db.session import get_db
from platform_core.schemas.metrics import (
    EngineeredMetricRead,
    RepositoryAnalysisRequest,
    RepositoryAnalysisResponse,
)
from platform_core.services.metrics_service import MetricsService
from platform_core.services.repository_mining_service import RepositoryMiningService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=List[EngineeredMetricRead])
def list_metrics(
    repository_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[EngineeredMetricRead]:
    return MetricsService(db).list_metrics(repository_id=repository_id)


@router.post("/repository-analysis", response_model=RepositoryAnalysisResponse)
def analyze_repository(
    payload: RepositoryAnalysisRequest,
    db: Session = Depends(get_db),
) -> RepositoryAnalysisResponse:
    metrics = RepositoryMiningService(db).analyze_repository(
        payload.repository_id,
        payload.repository_path,
    )
    return RepositoryAnalysisResponse(repository_id=payload.repository_id, metrics=metrics)

