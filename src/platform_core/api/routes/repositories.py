from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from platform_core.db.session import get_db
from platform_core.schemas.repository import (
    GitHubRepositoryAnalysisRequest,
    GitHubRepositoryAnalysisResponse,
    RepositoryCreate,
    RepositoryRead,
)
from platform_core.services.repository_intelligence_service import RepositoryIntelligenceService
from platform_core.services.repository_service import RepositoryService

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=List[RepositoryRead])
def list_repositories(db: Session = Depends(get_db)) -> List[RepositoryRead]:
    return RepositoryService(db).list_repositories()


@router.post("", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
def create_repository(payload: RepositoryCreate, db: Session = Depends(get_db)) -> RepositoryRead:
    try:
        return RepositoryService(db).create_repository(payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository URL already exists.",
        ) from exc


@router.post("/analyze-github", response_model=GitHubRepositoryAnalysisResponse)
def analyze_github_repository(
    payload: GitHubRepositoryAnalysisRequest,
    db: Session = Depends(get_db),
) -> GitHubRepositoryAnalysisResponse:
    return GitHubRepositoryAnalysisResponse(
        **RepositoryIntelligenceService(db).analyze_github_repository(
            github_url=payload.github_url,
            analysis_mode=payload.analysis_mode,
            repository_path=payload.repository_path,
        )
    )
