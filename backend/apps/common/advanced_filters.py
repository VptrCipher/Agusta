from __future__ import annotations

import json
from functools import reduce
from operator import and_ as q_and

from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend

EMPTY_OPERATORS = {"is_empty", "is_not_empty"}
TEXT_OPERATORS = {"eq", "neq", "contains", "contains_all", "not_contains"} | EMPTY_OPERATORS
SELECT_OPERATORS = {"is", "is_not", "is_one_of", "is_not_any_of"} | EMPTY_OPERATORS
TAG_OPERATORS = {"contains_any", "not_contains_any", "contains_all"} | EMPTY_OPERATORS
DATE_NUMBER_OPERATORS = {"eq", "neq", "lt", "gt", "lte", "gte", "between", "not_between"} | EMPTY_OPERATORS
TYPE_OPERATORS = {
    "text": TEXT_OPERATORS,
    "select": SELECT_OPERATORS,
    "multi-select": SELECT_OPERATORS,
    "tag": TAG_OPERATORS,
    "user": SELECT_OPERATORS,
    "date": DATE_NUMBER_OPERATORS,
    "number": DATE_NUMBER_OPERATORS,
}


def _values(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item) != ""]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value)]


def _empty_q(field: str, value_type: str) -> Q:
    if value_type == "tag":
        return Q(**{field: []}) | Q(**{f"{field}__isnull": True})
    if value_type in {"user", "date", "number"}:
        return Q(**{f"{field}__isnull": True})
    return Q(**{field: ""}) | Q(**{f"{field}__isnull": True})


def _contains_all_q(field: str, values: list[str], value_type: str) -> Q:
    if not values:
        raise ValidationError("Filter value is required.")
    lookup = "contains" if value_type == "tag" else "icontains"
    return reduce(q_and, (Q(**{f"{field}__{lookup}": value}) for value in values))


def _condition_q(field: str, value_type: str, operator: str, value) -> Q:
    values = _values(value)

    if operator == "is_empty":
        return _empty_q(field, value_type)
    if operator == "is_not_empty":
        return ~_empty_q(field, value_type)

    if operator in {"eq", "is"}:
        if not values:
            raise ValidationError("Filter value is required.")
        return Q(**{field: values[0]})
    if operator in {"neq", "is_not"}:
        if not values:
            raise ValidationError("Filter value is required.")
        return ~Q(**{field: values[0]})
    if operator == "contains":
        if not values:
            raise ValidationError("Filter value is required.")
        return Q(**{f"{field}__icontains": values[0]})
    if operator == "not_contains":
        if not values:
            raise ValidationError("Filter value is required.")
        return ~Q(**{f"{field}__icontains": values[0]})
    if operator == "contains_all":
        return _contains_all_q(field, values, value_type)
    if operator == "contains_any":
        if not values:
            raise ValidationError("Filter value is required.")
        return reduce(lambda left, right: left | right, (Q(**{f"{field}__contains": value}) for value in values))
    if operator == "not_contains_any":
        if not values:
            raise ValidationError("Filter value is required.")
        return ~reduce(lambda left, right: left | right, (Q(**{f"{field}__contains": value}) for value in values))
    if operator == "is_one_of":
        if not values:
            raise ValidationError("Filter value is required.")
        return Q(**{f"{field}__in": values})
    if operator == "is_not_any_of":
        if not values:
            raise ValidationError("Filter value is required.")
        return ~Q(**{f"{field}__in": values})
    if operator == "lt":
        if not values:
            raise ValidationError("Filter value is required.")
        return Q(**{f"{field}__lt": values[0]})
    if operator == "gt":
        if not values:
            raise ValidationError("Filter value is required.")
        return Q(**{f"{field}__gt": values[0]})
    if operator == "lte":
        if not values:
            raise ValidationError("Filter value is required.")
        return Q(**{f"{field}__lte": values[0]})
    if operator == "gte":
        if not values:
            raise ValidationError("Filter value is required.")
        return Q(**{f"{field}__gte": values[0]})
    if operator in {"between", "not_between"}:
        if len(values) != 2:
            raise ValidationError("Range filters require two values.")
        query = Q(**{f"{field}__gte": values[0], f"{field}__lte": values[1]})
        return ~query if operator == "not_between" else query

    raise ValidationError(f"Unsupported filter operator: {operator}")


class AdvancedFilterBackend(BaseFilterBackend):
    query_param = "advanced_filters"

    def filter_queryset(self, request, queryset, view):
        raw_filters = request.query_params.get(self.query_param)
        if not raw_filters:
            return queryset

        try:
            filters = json.loads(raw_filters)
        except json.JSONDecodeError as exc:
            raise ValidationError("advanced_filters must be valid JSON.") from exc

        if not isinstance(filters, list):
            raise ValidationError("advanced_filters must be a list.")

        field_types = getattr(view, "advanced_filter_fields", {})
        if not isinstance(field_types, dict):
            field_types = {field: "text" for field in field_types}

        combined = Q()
        has_condition = False
        for item in filters:
            if not isinstance(item, dict):
                raise ValidationError("Each advanced filter must be an object.")
            field = str(item.get("field") or "")
            operator = str(item.get("operator") or "")
            connector = str(item.get("connector") or "and")
            if field not in field_types:
                raise ValidationError(f"Unsupported filter field: {field}")
            value_type = field_types[field]
            if operator not in TYPE_OPERATORS.get(value_type, TEXT_OPERATORS):
                raise ValidationError(f"Unsupported filter operator: {operator}")

            condition = _condition_q(field, value_type, operator, item.get("value"))
            if not has_condition:
                combined = condition
                has_condition = True
            elif connector == "or":
                combined |= condition
            else:
                combined &= condition

        return queryset.filter(combined).distinct() if has_condition else queryset
