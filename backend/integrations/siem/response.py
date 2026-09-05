from __future__ import annotations

from typing import Any, Optional

from integrations.siem.backends import BackendQueryResult
from integrations.siem.models import (
    AdaptiveQueryInput,
    ESQLQueryInput,
    KeywordSearchInput,
    QueryOutput,
    SAMPLE_COUNT,
    SAMPLE_THRESHOLD,
    SPLQueryInput,
)
from integrations.siem.registry import get_default_agg_fields


def build_query_output(
        input_data: AdaptiveQueryInput | KeywordSearchInput,
        result: BackendQueryResult,
        *,
        index_distribution: Optional[dict[str, int]] = None,
) -> QueryOutput:
    status = "records" if result.total_hits <= SAMPLE_THRESHOLD else "summary"
    record_limit = SAMPLE_THRESHOLD if status == "records" else SAMPLE_COUNT

    if isinstance(input_data, AdaptiveQueryInput):
        explicit_fields = list(input_data.filters.keys()) + result.aggregation_fields
    else:
        explicit_fields = result.aggregation_fields

    fields_to_project = list(dict.fromkeys(
        [input_data.time_field, *explicit_fields, *get_default_agg_fields(result.index_name)]
    ))

    records = [
        project_record(r, fields_to_project)
        for r in result.raw_records[:record_limit]
    ]

    return QueryOutput(
        backend=result.backend,
        index_name=result.index_name,
        status=status,
        total_hits=result.total_hits,
        returned_records=len(records),
        truncated=result.total_hits > len(records),
        message=f"Matched {result.total_hits} events in {result.index_name} ({result.backend}). "
                + ("Returning projected records." if status == "records" else "Returning statistics and samples."),
        index_distribution=index_distribution,
        statistics=result.statistics,
        records=records,
    )


def project_record(record: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    projected: dict[str, Any] = {}
    for field_path in fields:
        value = _get_nested(record, field_path)
        if value is not _MISSING:
            projected[field_path] = value
    if "_index" in record:
        projected["_index"] = record["_index"]
    return projected


_MISSING = object()


def _get_nested(record: dict[str, Any], field_path: str) -> Any:
    if field_path in record:
        return record[field_path]
    current: Any = record
    for segment in field_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return _MISSING
        current = current[segment]
    return current


def build_raw_query_output(
        input_data: SPLQueryInput | ESQLQueryInput,
        result: BackendQueryResult,
        *,
        limit: int = 100,
) -> QueryOutput:
    records = result.raw_records
    return QueryOutput(
        backend=result.backend,
        index_name=result.index_name,
        status="records",
        total_hits=result.total_hits,
        returned_records=len(records),
        truncated=len(records) >= limit,
        message=f"Executed raw {result.backend} query against {result.index_name}. Returned {len(records)} records.",
        statistics=[],
        records=records,
    )
