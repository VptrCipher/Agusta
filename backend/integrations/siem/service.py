from integrations.siem.backends import ELKQueryBackend, SplunkQueryBackend
from integrations.siem.models import (
    KeywordSearchInput,
    SchemaIndexSummary,
)
from integrations.siem.registry import get_backend_type, get_default_agg_fields, get_index_info, list_indices
from integrations.siem.response import build_query_output, build_raw_query_output


def explore_schema(input_data):
    if not input_data.target_index:
        return [
            SchemaIndexSummary(
                name=index_info.name,
                backend=index_info.backend,
                description=index_info.description,
                default_aggregation_fields=get_default_agg_fields(index_info.name),
            )
            for index_info in list_indices()
        ]
    return get_index_info(input_data.target_index)


def execute_adaptive_query(input_data):
    backend = get_backend_type(input_data.index_name)
    query_backend = _get_query_backend(backend)
    backend_result = query_backend.execute_structured_query(input_data)
    return build_query_output(input_data, backend_result)


def keyword_search(input_data):
    if input_data.index_name:
        backend = get_backend_type(input_data.index_name)
        backend_result = _get_query_backend(backend).execute_keyword_query(input_data)
        return [build_query_output(input_data, backend_result, index_distribution=backend_result.index_distribution)]

    results = []
    indices_by_backend = get_indices_by_backend()
    for backend_name, indices in indices_by_backend.items():
        query_backend = _get_query_backend(backend_name)
        for index_name in query_backend.discover_keyword_hit_indices(input_data, indices):
            per_index_input = KeywordSearchInput(
                keyword=input_data.keyword,
                time_range_start=input_data.time_range_start,
                time_range_end=input_data.time_range_end,
                time_field=input_data.time_field,
                index_name=index_name,
            )
            backend_result = query_backend.execute_keyword_query(per_index_input)
            results.append(
                build_query_output(
                    per_index_input,
                    backend_result,
                    index_distribution=backend_result.index_distribution,
                )
            )
    return results


def execute_spl(input_data):
    backend_result = SplunkQueryBackend.execute_spl_query(input_data)
    return build_raw_query_output(input_data, backend_result, limit=input_data.limit)


def execute_esql(input_data):
    backend_result = ELKQueryBackend.execute_esql_query(input_data)
    return build_raw_query_output(input_data, backend_result, limit=input_data.limit)


def discover_index_fields(input_data):
    return _get_query_backend(input_data.backend).discover_index_fields(
        input_data.index_name,
        time_start=input_data.time_range_start,
        time_end=input_data.time_range_end,
        doc_limit=input_data.doc_limit,
        max_samples=input_data.max_samples_per_field,
    )


def _get_query_backend(backend):
    if backend == "ELK":
        return ELKQueryBackend
    if backend == "Splunk":
        return SplunkQueryBackend
    raise ValueError(f"Unsupported backend: {backend}")


def get_indices_by_backend():
    result = {"ELK": [], "Splunk": []}
    for index_info in list_indices():
        result.setdefault(index_info.backend, []).append(index_info.name)
    return result
