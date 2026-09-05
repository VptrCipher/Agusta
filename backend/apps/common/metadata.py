from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.apps import apps
from django.db import models
from django.utils.module_loading import import_string

from apps.accounts.permissions import is_admin_user

SENSITIVE_FIELD_DENYLIST = {"password", "is_staff", "is_superuser", "groups", "user_permissions"}


@dataclass(frozen=True)
class ResourceConfig:
    key: str
    label: str
    model_label: str
    endpoint: str
    viewset_path: str
    admin_only: bool = False


RESOURCE_CONFIGS: tuple[ResourceConfig, ...] = (
    ResourceConfig("cases", "Cases", "cases.Case", "/cases/", "apps.cases.views.CaseViewSet"),
    ResourceConfig("alerts", "Alerts", "alerts.Alert", "/alerts/", "apps.alerts.views.AlertViewSet"),
    ResourceConfig("artifacts", "Artifacts", "artifacts.Artifact", "/artifacts/", "apps.artifacts.views.ArtifactViewSet"),
    ResourceConfig("enrichments", "Enrichments", "enrichments.Enrichment", "/enrichments/", "apps.enrichments.views.EnrichmentViewSet"),
    ResourceConfig("playbooks", "Playbooks", "playbooks.Playbook", "/playbooks/", "apps.playbooks.views.PlaybookViewSet"),
    ResourceConfig("knowledge", "Knowledge", "knowledge.Knowledge", "/knowledge/", "apps.knowledge.views.KnowledgeViewSet"),
    ResourceConfig("users", "Users", "accounts.User", "/auth/users/", "apps.accounts.views.UserViewSet", admin_only=True),
)


def _choices_for_field(field: models.Field) -> list[dict[str, str]]:
    return [{"label": str(label), "value": str(value)} for value, label in field.choices]


def _viewset_options(viewset: type) -> dict[str, list[str]]:
    return {
        "search": list(getattr(viewset, "search_fields", ()) or ()),
        "filters": list(getattr(viewset, "filterset_fields", ()) or ()),
    }


def _field_metadata(model: type[models.Model]) -> dict[str, dict[str, str | bool]]:
    result: dict[str, dict[str, str | bool]] = {}
    for field in model._meta.get_fields():
        if field.name in SENSITIVE_FIELD_DENYLIST:
            continue
        if not getattr(field, "concrete", False) and not getattr(field, "many_to_many", False):
            continue
        result[field.name] = {
            "label": getattr(field, "verbose_name", field.name).replace("_", " ").title(),
            "type": field.__class__.__name__,
            "has_choices": bool(getattr(field, "choices", None)),
            "help_text": str(getattr(field, "help_text", "") or ""),
        }
    return result


def _ordering_fields(viewset: type, model: type[models.Model]) -> list[str]:
    ordering_fields = getattr(viewset, "ordering_fields", None)
    if ordering_fields:
        return list(ordering_fields)
    return [
        field.name
        for field in model._meta.concrete_fields
        if field.name not in SENSITIVE_FIELD_DENYLIST
    ]


def _resource_visible(config: ResourceConfig, user: object | None) -> bool:
    if not config.admin_only:
        return True
    return is_admin_user(user)


def build_resource_metadata(
    user: object | None = None,
    configs: Iterable[ResourceConfig] = RESOURCE_CONFIGS,
) -> dict[str, dict[str, object]]:
    resources: dict[str, dict[str, object]] = {}
    for config in configs:
        if not _resource_visible(config, user):
            continue

        model = apps.get_model(config.model_label)
        viewset = import_string(config.viewset_path)
        viewset_options = _viewset_options(viewset)
        ordering = _ordering_fields(viewset, model)
        fields = _field_metadata(model)
        choices: dict[str, list[dict[str, str]]] = {}
        for filter_name in viewset_options["filters"]:
            field_name = filter_name.split("__", 1)[0]
            try:
                field = model._meta.get_field(field_name)
            except Exception:
                continue
            if getattr(field, "choices", None):
                choices[filter_name] = _choices_for_field(field)

        resources[config.key] = {
            "label": config.label,
            "endpoint": config.endpoint,
            "fields": fields,
            "choices": choices,
            "search": viewset_options["search"],
            "filters": viewset_options["filters"],
            "ordering": ordering,
        }
    return resources
