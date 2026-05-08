from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from platform_core.db.base import Base


class EngineeredMetric(Base):
    __tablename__ = "engineered_metrics"
    __table_args__ = (
        UniqueConstraint("repository_id", "metric_name", "scope", name="uq_metric_repo_name_scope"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    scope: Mapped[str] = mapped_column(String(128), default="repository", nullable=False)
    metric_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    repository = relationship("Repository", back_populates="engineered_metrics")

