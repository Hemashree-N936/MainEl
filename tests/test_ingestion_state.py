from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from platform_core.db.base import Base
from platform_core.models.api_cache import IngestionState
from platform_core.services.vulnerability_service import VulnerabilityService


def test_update_state_handles_null_records_ingested() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        state = IngestionState(provider="NVD", records_ingested=None)
        db.add(state)
        db.commit()

        VulnerabilityService(db)._update_state(datetime.utcnow(), 3)

        refreshed = db.query(IngestionState).filter(IngestionState.provider == "NVD").one()
        assert refreshed.records_ingested == 3
    finally:
        db.close()

