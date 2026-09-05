import hashlib

from django.db import connection, transaction

from apps.artifacts.models import Artifact, ArtifactType


def _choice_value(value):
    return value.value if hasattr(value, "value") else str(value)


def normalize_artifact_value(artifact_type, value):
    if value is None:
        return ""

    normalized = str(value).strip()
    artifact_type_value = _choice_value(artifact_type)

    if artifact_type_value in {ArtifactType.EMAIL_ADDRESS, ArtifactType.EMAIL, ArtifactType.HASH}:
        return normalized.lower()
    if artifact_type_value == ArtifactType.HOSTNAME:
        return normalized.lower().rstrip(".")
    if artifact_type_value == ArtifactType.MAC_ADDRESS:
        return normalized.lower().replace("-", ":")
    return normalized


def _artifact_identity_lock_id(*, name, type, role, value):
    raw_key = "|".join([name, type, role, value])
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False) & ((1 << 63) - 1)


def _lock_artifact_identity(*, name, type, role, value):
    lock_id = _artifact_identity_lock_id(name=name, type=type, role=role, value=value)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])


def get_or_create_artifact(*, name, type, role, value):
    normalized_name = _choice_value(name)
    normalized_type = _choice_value(type)
    normalized_role = _choice_value(role)
    normalized_value = normalize_artifact_value(type, value)

    with transaction.atomic():
        _lock_artifact_identity(
            name=normalized_name,
            type=normalized_type,
            role=normalized_role,
            value=normalized_value,
        )
        candidates = Artifact.objects.filter(
            name=normalized_name, type=normalized_type, role=normalized_role
        ).order_by("created_at")
        for artifact in candidates:
            if normalize_artifact_value(type, artifact.value) == normalized_value:
                if artifact.value != normalized_value:
                    artifact.value = normalized_value
                    artifact.full_clean()
                    artifact.save(update_fields=["value"])
                return artifact

        artifact = Artifact(
            name=normalized_name,
            type=normalized_type,
            role=normalized_role,
            value=normalized_value,
        )
        artifact.full_clean()
        artifact.save()
        return artifact
