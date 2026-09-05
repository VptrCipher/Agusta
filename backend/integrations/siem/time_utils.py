from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from dateutil import parser as dateutil_parser

UTC_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def normalize_time_input(value: Any, relative_base: datetime) -> str:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = dateutil_parser.isoparse(str(value))
        except (ValueError, OverflowError):
            raise ValueError(f"Unable to parse ISO 8601 time value: {value}")

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Time values must include timezone, e.g. 2026-06-23T12:00:00Z or 2026-06-23T20:00:00+08:00")
    parsed = parsed.astimezone(timezone.utc)

    return parsed.strftime(UTC_TIME_FORMAT)


def normalize_time_range_inputs(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    normalized = dict(data)
    for field_name in ("time_range_start", "time_range_end"):
        if field_name in normalized and normalized[field_name] is not None:
            normalized[field_name] = normalize_time_input(normalized[field_name], datetime.now(timezone.utc))
    return normalized


def validate_time_range_order(start: str, end: str) -> None:
    start_dt = datetime.strptime(start, UTC_TIME_FORMAT).replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end, UTC_TIME_FORMAT).replace(tzinfo=timezone.utc)
    if end_dt <= start_dt:
        raise ValueError("time_range_end must be later than time_range_start")
