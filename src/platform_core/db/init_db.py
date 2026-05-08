from platform_core.db.base import Base
from platform_core.db.session import engine
from platform_core.models import (
    api_cache,
    commit,
    dependency,
    engineered_metric,
    ml,
    repository,
    vulnerability,
)


def init_db() -> None:
    """Create database tables for local development and Phase 1 demos."""

    _ = (repository, commit, dependency, vulnerability, engineered_metric, api_cache, ml)
    Base.metadata.create_all(bind=engine)
    repair_sqlite_schema()


def repair_sqlite_schema() -> None:
    """Apply small SQLite-safe repairs for local databases created by earlier phases."""

    if not engine.url.drivername.startswith("sqlite"):
        return

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(ingestion_states)").fetchall()
        }
        if not columns:
            return
        if "records_ingested" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE ingestion_states "
                "ADD COLUMN records_ingested INTEGER NOT NULL DEFAULT 0"
            )
        else:
            connection.exec_driver_sql(
                "UPDATE ingestion_states SET records_ingested = 0 WHERE records_ingested IS NULL"
            )
