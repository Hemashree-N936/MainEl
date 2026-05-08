from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.models.repository import Repository
from platform_core.schemas.repository import RepositoryCreate


class RepositoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_repositories(self) -> List[Repository]:
        return list(self.db.scalars(select(Repository).order_by(Repository.created_at.desc())).all())

    def create_repository(self, payload: RepositoryCreate) -> Repository:
        repository = Repository(
            name=payload.name,
            url=str(payload.url),
            default_branch=payload.default_branch,
        )
        self.db.add(repository)
        self.db.commit()
        self.db.refresh(repository)
        return repository

    def get_or_create_repository(self, payload: RepositoryCreate) -> Repository:
        existing = self.db.scalar(select(Repository).where(Repository.url == str(payload.url)))
        if existing is not None:
            return existing
        return self.create_repository(payload)
