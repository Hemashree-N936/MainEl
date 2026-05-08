from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.models.engineered_metric import EngineeredMetric


class MetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_metrics(self, repository_id: Optional[int] = None) -> List[EngineeredMetric]:
        statement = select(EngineeredMetric).order_by(EngineeredMetric.measured_at.desc())
        if repository_id is not None:
            statement = statement.where(EngineeredMetric.repository_id == repository_id)
        return list(self.db.scalars(statement).all())

    def upsert_metric(
        self,
        repository_id: int,
        metric_name: str,
        metric_value: float,
        scope: str = "repository",
        metric_metadata: Optional[Dict[str, Any]] = None,
    ) -> EngineeredMetric:
        metric = self.db.scalar(
            select(EngineeredMetric).where(
                EngineeredMetric.repository_id == repository_id,
                EngineeredMetric.metric_name == metric_name,
                EngineeredMetric.scope == scope,
            )
        )
        if metric is None:
            metric = EngineeredMetric(
                repository_id=repository_id,
                metric_name=metric_name,
                metric_value=metric_value,
                scope=scope,
                metric_metadata=metric_metadata,
            )
            self.db.add(metric)
        else:
            metric.metric_value = metric_value
            metric.metric_metadata = metric_metadata
            metric.measured_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(metric)
        return metric

