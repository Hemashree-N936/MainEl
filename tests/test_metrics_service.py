from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from platform_core.db.base import Base
from platform_core.models import Repository
from platform_core.services.metrics_service import MetricsService


def test_metric_upsert_updates_existing_metric() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        repository = Repository(name="demo", url="https://example.test/demo", default_branch="main")
        db.add(repository)
        db.commit()
        db.refresh(repository)

        service = MetricsService(db)
        service.upsert_metric(repository.id, "commit_count", 1)
        metric = service.upsert_metric(repository.id, "commit_count", 2)

        assert metric.metric_value == 2
        assert len(service.list_metrics(repository.id)) == 1
    finally:
        db.close()

