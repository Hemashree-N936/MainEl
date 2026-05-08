import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_core.db.init_db import init_db
from platform_core.db.session import SessionLocal
from platform_core.services.vulnerability_service import VulnerabilityService
from platform_core.utils.datetime import parse_datetime


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest CVE data from the NVD API.")
    parser.add_argument("--modified-start", help="ISO datetime, for example 2026-05-01T00:00:00")
    parser.add_argument("--modified-end", help="ISO datetime, defaults to now")
    parser.add_argument("--keyword", help="Optional NVD keyword search")
    parser.add_argument("--limit", type=int, help="Optional cap for demos/tests")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        result = VulnerabilityService(db).ingest_nvd(
            modified_start=_parse_arg_datetime(args.modified_start),
            modified_end=_parse_arg_datetime(args.modified_end) or datetime.utcnow(),
            keyword=args.keyword,
            limit=args.limit,
        )
        print(result)
    finally:
        db.close()


def _parse_arg_datetime(value: Optional[str]) -> Optional[datetime]:
    return parse_datetime(value) if value else None


if __name__ == "__main__":
    main()

