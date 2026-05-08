from datetime import datetime, timedelta
from typing import Optional


NVD_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed


def format_nvd_datetime(value: datetime) -> str:
    return value.strftime(NVD_DATETIME_FORMAT)[:-3]


def chunk_date_range(start: datetime, end: datetime, max_days: int = 120):
    current = start
    while current < end:
        chunk_end = min(current + timedelta(days=max_days), end)
        yield current, chunk_end
        current = chunk_end
