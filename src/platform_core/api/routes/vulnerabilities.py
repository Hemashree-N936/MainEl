from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from platform_core.db.session import get_db
from platform_core.schemas.vulnerability import (
    CveIngestionRequest,
    CveIngestionResponse,
    VulnerabilityRead,
)
from platform_core.services.vulnerability_service import VulnerabilityService

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


@router.get("", response_model=List[VulnerabilityRead])
def list_vulnerabilities(
    limit: int = Query(default=100, ge=1, le=1000),
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[VulnerabilityRead]:
    return VulnerabilityService(db).list_vulnerabilities(limit=limit, severity=severity)


@router.get("/{cve_id}", response_model=VulnerabilityRead)
def get_vulnerability(cve_id: str, db: Session = Depends(get_db)) -> VulnerabilityRead:
    return VulnerabilityService(db).get_vulnerability(cve_id)


@router.post("/ingest/nvd", response_model=CveIngestionResponse)
def ingest_nvd(payload: CveIngestionRequest, db: Session = Depends(get_db)) -> CveIngestionResponse:
    result = VulnerabilityService(db).ingest_nvd(
        modified_start=payload.modified_start,
        modified_end=payload.modified_end,
        keyword=payload.keyword,
        limit=payload.limit,
    )
    return CveIngestionResponse(**result)
