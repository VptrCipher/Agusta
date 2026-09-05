from django.contrib.contenttypes.models import ContentType

from .context import get_current_actor
from .models import AuditLog

RESOURCE_KEYS = {
    "case": "cases",
    "alert": "alerts",
    "artifact": "artifacts",
    "enrichment": "enrichments",
    "playbook": "playbooks",
    "knowledge": "knowledge",
    "user": "users",
}


def readable_label(obj):
    if hasattr(obj, "get_full_name"):
        return obj.get_full_name() or getattr(obj, "username", "") or str(obj.pk)
    model_name = obj._meta.model_name
    field_name = f"{model_name}_id"
    return str(getattr(obj, field_name, "") or getattr(obj, "username", "") or obj.pk)


def resource_key_for_model(model):
    return RESOURCE_KEYS.get(model._meta.model_name, f"{model._meta.model_name}s")


def write_relation_event(parent, action, relation, related_object, actor=None):
    return AuditLog.objects.create(
        content_type=ContentType.objects.get_for_model(type(parent)),
        object_id=str(parent.id),
        action=action,
        actor=actor if actor is not None else get_current_actor(),
        metadata={
            "relation": relation,
            "related_resource": resource_key_for_model(type(related_object)),
            "related_id": str(related_object.id),
            "related_label": readable_label(related_object),
        },
    )
