import logging
import re
import uuid
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.agentic.runtime.base import BasePlaybook
from apps.agentic.runtime.loader import discover_script_class, iter_overlaid_python_scripts
from apps.audit.context import suppress_audit
from apps.inbox.notifications import notify_playbook_completion
from apps.playbooks.models import Playbook, PlaybookJobStatus, PlaybookRunMessage

logger = logging.getLogger(__name__)

PLAYBOOK_RISK_LEVELS = {"Low", "Medium", "High", "Critical"}
MAX_RUN_MESSAGE_LENGTH = 1000
MAX_RUN_REMARK_LENGTH = 2000
ORPHANED_RUN_REMARK = "Playbook worker stopped before completion."
_AUTHORIZATION_RE = re.compile(r"(?i)\bauthorization\b(\s*[:=]\s*)[^\r\n]+")
_SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    \b(password|token|api[_-]?key|secret)\b
    (\s*[:=]\s*)
    ("[^"\r\n]*"|'[^'\r\n]*'|[^\s,;]+)
    """
)


def _sanitize_visible_text(value, *, max_length):
    text = str(value or "").strip()
    text = _AUTHORIZATION_RE.sub(lambda match: f"authorization{match.group(1)}***", text)
    text = _SENSITIVE_ASSIGNMENT_RE.sub(
        lambda match: f"{match.group(1)}{match.group(2)}***",
        text,
    )
    return text[:max_length]


def default_playbook_scripts_dir():
    return Path(settings.BASE_DIR) / "playbooks"


def default_custom_playbook_scripts_dir():
    return Path(settings.CUSTOM_DIR) / "playbooks"


def default_playbook_script_dirs():
    return [default_playbook_scripts_dir(), default_custom_playbook_scripts_dir()]


def _normalize_tags(value):
    if isinstance(value, str):
        raw_tags = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_tags = value
    else:
        raw_tags = []

    tags = []
    seen = set()
    for item in raw_tags:
        tag = str(item).strip()
        if tag and tag not in seen:
            tags.append(tag)
            seen.add(tag)
    return tags


def scan_playbook_definitions(*, scripts_dir=None, scripts_dirs=None):
    if scripts_dirs is not None and scripts_dir is not None:
        raise ValueError("Use scripts_dir or scripts_dirs, not both.")
    paths = (
        iter_overlaid_python_scripts(*(scripts_dirs or default_playbook_script_dirs()))
        if scripts_dir is None
        else iter_overlaid_python_scripts(scripts_dir)
    )
    definitions = []
    errors = []
    for path in paths:
        try:
            definition = discover_script_class(
                path,
                class_name="Playbook",
                base_class=BasePlaybook,
            )
        except Exception:
            logger.exception("Failed to load playbook definition from %s", path)
            errors.append({"path": str(path), "error": "Failed to load playbook definition."})
            continue
        if definition is not None:
            risk_level = getattr(definition.script_class, "RISK_LEVEL", "Low")
            if risk_level not in PLAYBOOK_RISK_LEVELS:
                logger.error(
                    "Invalid playbook risk level: path=%s risk_level=%r",
                    path,
                    risk_level,
                )
                errors.append({
                    "path": str(path),
                    "error": f"RISK_LEVEL must be one of: {', '.join(sorted(PLAYBOOK_RISK_LEVELS))}.",
                })
                continue
            definitions.append(definition)
    return definitions, errors


def _playbook_definitions(scripts_dir=None):
    definitions, _errors = scan_playbook_definitions(scripts_dir=scripts_dir)
    return definitions


def list_playbook_definitions(*, include_path=False, scripts_dir=None):
    definitions = []
    for item in _playbook_definitions(scripts_dir=scripts_dir):
        data = {
            "name": item.name,
            "description": getattr(item.script_class, "DESC", ""),
            "tags": _normalize_tags(getattr(item.script_class, "TAGS", [])),
            "risk_level": item.script_class.RISK_LEVEL,
        }
        if include_path:
            data["path"] = str(item.path)
        definitions.append(data)
    return definitions


def find_playbook_class(name, *, scripts_dir=None):
    for definition in _playbook_definitions(scripts_dir=scripts_dir):
        if definition.name == name:
            return definition.script_class
    raise LookupError(f"Playbook script not found: {name}")


@transaction.atomic
def create_pending_playbook_run(*, name, case, user=None, user_input=""):
    known_names = {item["name"] for item in list_playbook_definitions()}
    if name not in known_names:
        raise ValueError(f"Unknown playbook definition: {name}")

    playbook = Playbook(
        case=case,
        name=name,
        user=user if getattr(user, "is_authenticated", False) else None,
        user_input=user_input or "",
        job_status=PlaybookJobStatus.PENDING,
    )
    playbook.full_clean()
    playbook.save()
    return playbook


@transaction.atomic
def claim_pending_playbook_run():
    playbook = (
        Playbook.objects
        .select_for_update()
        .filter(job_status=PlaybookJobStatus.PENDING)
        .order_by("created_at", "id")
        .first()
    )
    if playbook is None:
        return None

    playbook.job_status = PlaybookJobStatus.RUNNING
    playbook.job_id = str(uuid.uuid4())
    playbook.started_at = timezone.now()
    playbook.finished_at = None
    playbook.remark = ""
    with suppress_audit():
        playbook.save(update_fields=[
            "job_status",
            "job_id",
            "started_at",
            "finished_at",
            "remark",
            "updated_at",
        ])
    return playbook


@transaction.atomic
def add_playbook_run_message(playbook, message):
    if not isinstance(message, str):
        raise TypeError("Run message must be a string.")
    sanitized = _sanitize_visible_text(message, max_length=MAX_RUN_MESSAGE_LENGTH)
    if not sanitized:
        raise ValueError("Run message must not be empty.")

    locked = Playbook.objects.select_for_update().get(pk=playbook.pk)
    if locked.job_status != PlaybookJobStatus.RUNNING:
        raise ValueError("Run messages can only be added while the playbook is Running.")
    last_sequence = (
        PlaybookRunMessage.objects
        .filter(playbook_run=locked)
        .aggregate(value=Max("sequence"))["value"]
        or 0
    )
    return PlaybookRunMessage.objects.create(
        playbook_run=locked,
        sequence=last_sequence + 1,
        message=sanitized,
    )


@transaction.atomic
def mark_playbook_success(playbook, remark):
    locked = Playbook.objects.select_for_update().get(pk=playbook.pk)
    if locked.job_status != PlaybookJobStatus.RUNNING:
        raise ValueError(f"Playbook must be Running before success, got {locked.job_status}")
    locked.job_status = PlaybookJobStatus.SUCCESS
    locked.finished_at = timezone.now()
    locked.remark = _sanitize_visible_text(remark, max_length=MAX_RUN_REMARK_LENGTH)
    with suppress_audit():
        locked.save(update_fields=["job_status", "finished_at", "remark", "updated_at"])
    notify_playbook_completion(locked)
    return locked


@transaction.atomic
def mark_playbook_failed(playbook, error):
    locked = Playbook.objects.select_for_update().get(pk=playbook.pk)
    if locked.job_status != PlaybookJobStatus.RUNNING:
        raise ValueError(f"Playbook must be Running before failure, got {locked.job_status}")
    locked.job_status = PlaybookJobStatus.FAILED
    locked.finished_at = timezone.now()
    logger.exception("Playbook execution failed", exc_info=error)
    locked.remark = "Playbook execution failed."
    with suppress_audit():
        locked.save(update_fields=["job_status", "finished_at", "remark", "updated_at"])
    notify_playbook_completion(locked)
    return locked


def recover_orphaned_playbook_runs():
    with transaction.atomic():
        # `of=("self",)` restricts the row lock to the playbook table. Without it
        # PostgreSQL rejects the query outright, because select_related("user")
        # produces a LEFT OUTER JOIN (Playbook.user is nullable) and
        # "FOR UPDATE cannot be applied to the nullable side of an outer join".
        # That aborted the worker before it reached its run loop.
        orphaned_runs = list(
            Playbook.objects
            .select_for_update(of=("self",))
            .select_related("user", "case")
            .filter(job_status=PlaybookJobStatus.RUNNING)
        )
        finished_at = timezone.now()
        for playbook in orphaned_runs:
            playbook.job_status = PlaybookJobStatus.FAILED
            playbook.finished_at = finished_at
            playbook.remark = ORPHANED_RUN_REMARK
            with suppress_audit():
                playbook.save(update_fields=["job_status", "finished_at", "remark", "updated_at"])

    for playbook in orphaned_runs:
        notify_playbook_completion(playbook)
    return len(orphaned_runs)
