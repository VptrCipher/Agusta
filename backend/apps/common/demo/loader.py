"""Builds the AGUSTA demonstration environment from ``catalog.py``.

Design rules
------------
* **Idempotent.** Every record carries the ``agusta-demo`` tag / marker. If the
  environment is already present the loader is a no-op, so it is safe to call on
  every container start.
* **Scoped.** ``purge()`` only ever deletes records carrying the demo marker, so
  it can never remove operator data.
* **Honest.** Records are tagged and their provenance is stated. Nothing claims
  to be real observed telemetry.
* **Back-dated.** ``created_at`` is rewritten after insert so dashboards, MTTD /
  MTTA / MTTR charts and the activity feed have realistic history.
"""

import json
import logging

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from apps.agentic.services.artifacts import get_or_create_artifact
from apps.alerts.models import Alert, AlertAnalyticState, AlertAnalyticType
from apps.artifacts.models import Artifact
from apps.audit.context import audit_actor, suppress_audit
from apps.cases.models import Case, CaseRelationship, CaseRelationshipType
from apps.comments.models import Comment
from apps.comments.services import create_record_comment
from apps.common.demo import DEMO_DATA_VERSION, catalog
from apps.common.demo import provenance as prov
from apps.enrichments.models import Enrichment, EnrichmentProvider, EnrichmentType
from apps.inbox.models import InboxMessage
from apps.knowledge.models import Knowledge, KnowledgeSource
from apps.playbooks.models import Playbook, PlaybookJobStatus, PlaybookRunMessage

logger = logging.getLogger(__name__)

User = None  # resolved lazily so the module imports without app loading


def _user_model():
    global User
    if User is None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
    return User


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _backdate(instance, created_at, updated_at=None):
    """Rewrite auto_now timestamps, which ``save()`` always overwrites."""
    type(instance).objects.filter(pk=instance.pk).update(
        created_at=created_at,
        updated_at=updated_at or created_at,
    )
    instance.created_at = created_at
    instance.updated_at = updated_at or created_at


def _fmt_delta(value):
    if value is None:
        return None
    total_minutes = int(value.total_seconds() // 60)
    days, remainder = divmod(total_minutes, 1440)
    hours, minutes = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return "".join(parts)


def is_seeded():
    """True when the demonstration environment is already present."""
    return Case.objects.filter(tags__contains=[prov.DEMO_TAG]).exists()


def summary_counts():
    return {
        "cases": Case.objects.filter(tags__contains=[prov.DEMO_TAG]).count(),
        "alerts": Alert.objects.filter(labels__contains=[prov.DEMO_TAG]).count(),
        "artifacts": Artifact.objects.filter(
            value__in=[value for value, *_ in catalog.ARTIFACTS.values()]
        ).count(),
        "enrichments": Enrichment.objects.filter(uid__startswith=f"{prov.DEMO_TAG}:").count(),
        "knowledge": Knowledge.objects.filter(tags__contains=[prov.DEMO_TAG]).count(),
        "playbooks": Playbook.objects.filter(job_id__startswith=prov.DEMO_PREFIX).count(),
        "case_relationships": CaseRelationship.objects.filter(
            note__startswith=prov.DEMO_PREFIX
        ).count(),
    }


# --------------------------------------------------------------------------- #
# People
# --------------------------------------------------------------------------- #


def ensure_analysts(*, password=None):
    """Create the demo SOC team.

    Passwords are UNUSABLE by default: these accounts exist so cases have
    realistic assignees, commenters and audit actors, not to be logged into.
    Sign in with the deployment's own superuser. ``password`` is only honoured
    when an operator explicitly opts in.
    """
    model = _user_model()
    users = {}
    for spec in catalog.ANALYSTS:
        user, _created = model.objects.get_or_create(username=spec["username"])
        user.first_name = spec["first_name"]
        user.last_name = spec["last_name"]
        user.email = f"{spec['username']}@{prov.ORG_DOMAIN}"
        user.is_active = True
        if password:
            user.set_password(password)
        elif not user.has_usable_password():
            user.set_unusable_password()
        user.save()
        users[spec["username"]] = user
    return users


# --------------------------------------------------------------------------- #
# Artifacts
# --------------------------------------------------------------------------- #


def ensure_artifacts():
    """Materialise the shared artifact registry, reusing existing rows."""
    artifacts = {}
    for key, (value, type_, role, name) in catalog.ARTIFACTS.items():
        artifacts[key] = get_or_create_artifact(value=value, type=type_, role=role, name=name)
    return artifacts


# --------------------------------------------------------------------------- #
# Enrichments / knowledge / playbooks
# --------------------------------------------------------------------------- #


def _enrichment_uid(case_key, index, value):
    return f"{prov.DEMO_TAG}:{case_key}:{index}:{value}"[:255]


def _create_enrichment(*, parent, spec, case_key, index, created_at):
    parent_field = parent._meta.model_name
    data = dict(spec.get("data") or {})
    data.setdefault("_provenance", prov.ATTRIBUTION)
    enrichment = Enrichment(
        **{parent_field: parent},
        name=spec["name"],
        type=EnrichmentType(spec["type"]),
        provider=EnrichmentProvider(spec["provider"]),
        uid=_enrichment_uid(case_key, index, spec["value"]),
        value=str(spec["value"])[:500],
        desc=spec.get("desc", ""),
        data=data,
    )
    enrichment.full_clean()
    enrichment.save()
    _backdate(enrichment, created_at)
    return enrichment


def _create_playbook(*, case, spec, users, case_key, index, case_created):
    status = PlaybookJobStatus(spec["status"])
    started_at = case_created + spec["started_offset"] if spec.get("started_offset") else None
    finished_at = started_at + spec["duration"] if started_at and spec.get("duration") else None

    playbook = Playbook(
        case=case,
        name=spec["name"],
        user=users.get(spec.get("user")) if spec.get("user") else None,
        user_input=spec.get("user_input", ""),
        job_status=status,
        job_id=f"{prov.DEMO_PREFIX}-{case_key}-{index:02d}",
        started_at=started_at,
        finished_at=finished_at,
        remark=spec.get("remark", ""),
    )
    playbook.full_clean()
    playbook.save()
    _backdate(playbook, started_at or case_created)

    for sequence, message in enumerate(spec.get("messages") or [], start=1):
        PlaybookRunMessage.objects.create(
            playbook_run=playbook,
            sequence=sequence,
            message=message,
        )
    return playbook


def _create_knowledge(*, case, spec, created_at):
    knowledge = Knowledge(
        title=spec["title"],
        body=spec["body"],
        source=KnowledgeSource.CASE,
        case=case,
        tags=[prov.DEMO_TAG, *spec.get("tags", [])],
    )
    knowledge.full_clean()
    knowledge.save()
    _backdate(knowledge, created_at)
    return knowledge


# --------------------------------------------------------------------------- #
# Cases and alerts
# --------------------------------------------------------------------------- #


def _case_from_stage(stage, *, users, now, story_key):
    first_seen = now - stage["first_seen"]
    detected_at = first_seen + stage["ttd"]
    acknowledged_at = detected_at + stage["tta"] if stage.get("tta") else None
    closed_at = acknowledged_at + stage["ttr"] if acknowledged_at and stage.get("ttr") else None

    report = dict(stage.get("ai") or {})
    report["metrics"] = {
        "time_to_detect": _fmt_delta(stage["ttd"]),
        "time_to_acknowledge": _fmt_delta(stage.get("tta")),
        "time_to_resolve": _fmt_delta(stage.get("ttr")),
    }
    report["_provenance"] = prov.ATTRIBUTION

    assignee_name = stage.get("assignee")
    case = Case(
        title=stage["title"],
        severity=stage["severity"],
        severity_ai=stage["severity"],
        confidence=stage["confidence"],
        confidence_ai=stage["confidence"],
        impact=stage["impact"],
        impact_ai=stage["impact"],
        priority=stage["priority"],
        priority_ai=stage["priority"],
        description=stage["description"],
        category=stage["category"],
        tags=[prov.DEMO_TAG, *stage.get("tags", [])],
        status=stage["status"],
        verdict=stage["verdict"],
        verdict_ai=stage["verdict"],
        summary=stage.get("summary", ""),
        assignee=users.get(assignee_name) if assignee_name else None,
        acknowledged_time=acknowledged_at,
        closed_time=closed_at,
        correlation_uid=f"{prov.DEMO_PREFIX}-{story_key.upper()}-{stage['key'].upper()}",
        investigation_report_ai_json=json.dumps(report, ensure_ascii=False, indent=2),
    )
    case.full_clean()
    case.save()
    _backdate(case, detected_at)
    return case, first_seen, detected_at


def _create_alert(*, case, spec, artifacts, first_seen, case_key, index):
    tactic, technique = prov.ATTACK[spec["attack"]]
    vendor, product, feature = catalog.VENDORS.get(
        spec["product"], ("AGUSTA", "Demonstration Telemetry", "Detection")
    )
    seen_at = first_seen + spec.get("offset", catalog.m(0))

    raw = dict(spec.get("raw") or {})
    raw.setdefault("_provenance", prov.ATTRIBUTION)

    alert = Alert(
        case=case,
        title=spec["title"],
        severity=spec["severity"],
        confidence=spec["confidence"],
        impact=spec["impact"],
        disposition=spec["disposition"],
        action=spec["action"],
        status=spec["status"],
        risk_level=spec["risk"],
        labels=[prov.DEMO_TAG, *spec.get("labels", [])],
        desc=spec.get("desc", ""),
        first_seen_time=seen_at,
        last_seen_time=seen_at,
        rule_id=spec.get("rule_id", ""),
        rule_name=spec.get("rule_name", ""),
        correlation_uid=case.correlation_uid,
        source_uid=f"{prov.DEMO_PREFIX}-{case_key}-{index:03d}",
        data_sources=[str(spec["product"])],
        analytic_name=spec.get("analytic_name", ""),
        analytic_type=spec.get("analytic_type", AlertAnalyticType.UNKNOWN),
        analytic_state=spec.get("analytic_state", AlertAnalyticState.ACTIVE),
        analytic_desc=spec.get("analytic_desc", ""),
        tactic=tactic,
        technique=technique,
        mitigation=spec.get("mitigation", ""),
        product_category=spec["product"],
        product_vendor=vendor,
        product_name=product,
        product_feature=feature,
        policy_type=spec.get("policy_type", ""),
        raw_data=raw,
        unmapped={"agusta_demo": True, "attack_reference": technique},
    )
    alert.full_clean()
    alert.save()
    _backdate(alert, seen_at)

    for artifact_key in spec.get("artifacts", []):
        artifact = artifacts.get(artifact_key)
        if artifact is None:
            logger.warning("Demo catalog references unknown artifact key: %s", artifact_key)
            continue
        alert.artifacts.add(artifact)
    return alert


def _apply_stage_extras(*, case, stage, users, artifacts, first_seen, case_created):
    for index, spec in enumerate(stage.get("alerts", []), start=1):
        _create_alert(
            case=case,
            spec=spec,
            artifacts=artifacts,
            first_seen=first_seen,
            case_key=stage["key"],
            index=index,
        )

    for index, spec in enumerate(stage.get("enrichments", []), start=1):
        _create_enrichment(
            parent=case,
            spec=spec,
            case_key=stage["key"],
            index=index,
            created_at=case_created,
        )

    for index, spec in enumerate(stage.get("playbooks", []), start=1):
        _create_playbook(
            case=case,
            spec=spec,
            users=users,
            case_key=stage["key"],
            index=index,
            case_created=case_created,
        )

    if stage.get("knowledge"):
        _create_knowledge(case=case, spec=stage["knowledge"], created_at=case_created)

    for offset, (author, body, mentions) in enumerate(stage.get("comments", []), start=1):
        comment_author = users.get(author)
        if comment_author is None:
            continue
        comment = create_record_comment(
            author=comment_author,
            content_object=case,
            body=body,
            mentions=[users[name] for name in mentions if name in users],
        )
        _backdate(comment, case_created + catalog.m(12 * offset))


def _link_cases(source, target, relationship_type, note, created_at):
    if source.pk == target.pk:
        return None
    pair_key = CaseRelationship.build_pair_key(source.pk, target.pk)
    if CaseRelationship.objects.filter(pair_key=pair_key).exists():
        return None
    relationship = CaseRelationship(
        source_case=source,
        target_case=target,
        relationship_type=relationship_type,
        note=f"{prov.DEMO_PREFIX} {note}"[:500],
    )
    relationship.save()
    _backdate(relationship, created_at)
    return relationship


# --------------------------------------------------------------------------- #
# Background queue
# --------------------------------------------------------------------------- #


def _create_routine_cases(*, users, artifacts, now):
    created = []
    for index, row in enumerate(catalog.ROUTINE, start=1):
        title, category, severity, status, verdict, assignee, days_ago, attack, tags = row
        stage = {
            "key": f"routine-{index:02d}",
            "title": title,
            "category": category,
            "severity": severity,
            "confidence": catalog.CaseConfidence.MEDIUM,
            "impact": catalog.CaseImpact.LOW,
            "priority": catalog.CasePriority.LOW
            if severity in {catalog.CaseSeverity.LOW, catalog.CaseSeverity.INFORMATIONAL}
            else catalog.CasePriority.MEDIUM,
            "status": status,
            "verdict": verdict,
            "assignee": assignee,
            "tags": ["routine", *tags],
            "first_seen": catalog.d(days_ago) + catalog.h(2),
            "ttd": catalog.m(6 + index),
            "tta": catalog.m(14 + index),
            "ttr": catalog.h(1) + catalog.m(9 * index)
            if status in {catalog.CaseStatus.RESOLVED, catalog.CaseStatus.CLOSED}
            else None,
            "description": f"{title}. Routine queue item retained for trend and workload context.",
            "summary": "Handled through standard triage." if status == catalog.CaseStatus.CLOSED else "",
            "ai": {"hypothesis": title, "confidence": "Medium", "routine": True},
            "alerts": [
                {
                    "title": title,
                    "attack": attack,
                    "product": catalog.ProductCategory(category)
                    if category in set(catalog.ProductCategory.values)
                    else catalog.ProductCategory.SIEM,
                    "severity": catalog.Severity(severity),
                    "confidence": catalog.Confidence.MEDIUM,
                    "impact": catalog.Impact.LOW,
                    "disposition": catalog.Disposition.DETECTED,
                    "action": catalog.AlertAction.OBSERVED,
                    "status": catalog.AlertStatus.RESOLVED
                    if status in {catalog.CaseStatus.RESOLVED, catalog.CaseStatus.CLOSED}
                    else catalog.AlertStatus.NEW,
                    "risk": catalog.AlertRiskLevel.LOW,
                    "rule_id": f"AGUSTA-ROUTINE-{index:04d}",
                    "rule_name": title,
                    "analytic_type": catalog.AlertAnalyticType.RULE,
                    "analytic_name": "Routine Detection",
                    "analytic_desc": "Standard detection content.",
                    "desc": title,
                    "mitigation": "Standard playbook applied.",
                    "labels": ["routine", *tags],
                    "artifacts": [],
                    "offset": catalog.m(0),
                    "raw": {"agusta.routine": True, "title": title},
                }
            ],
            "enrichments": [],
            "comments": [],
            "playbooks": [],
        }
        case, first_seen, case_created = _case_from_stage(
            stage, users=users, now=now, story_key="routine"
        )
        _apply_stage_extras(
            case=case,
            stage=stage,
            users=users,
            artifacts=artifacts,
            first_seen=first_seen,
            case_created=case_created,
        )
        created.append(case)
    return created


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #


@transaction.atomic
def seed(*, analyst_password=None, include_routine=True):
    """Create the demonstration environment. No-op when already present."""
    if is_seeded():
        logger.info("AGUSTA demo environment already present; skipping seed.")
        return {"created": False, **summary_counts()}

    now = timezone.now()
    users = ensure_analysts(password=analyst_password)
    automation = users[catalog.AUTOMATION_USER]
    artifacts = ensure_artifacts()
    cases_by_key = {}

    with audit_actor(automation):
        for story in catalog.STORIES:
            story_cases = []
            chain_keys = {stage["key"] for stage in story["stages"]}
            for stage in story["stages"] + story.get("extra_cases", []):
                case, first_seen, case_created = _case_from_stage(
                    stage, users=users, now=now, story_key=story["key"]
                )
                cases_by_key[stage["key"]] = case
                if stage["key"] in chain_keys:
                    story_cases.append((stage, case, case_created))
                _apply_stage_extras(
                    case=case,
                    stage=stage,
                    users=users,
                    artifacts=artifacts,
                    first_seen=first_seen,
                    case_created=case_created,
                )

            # Kill-chain lineage: stage N is the parent of stage N+1.
            if story.get("chain"):
                for (_prev_stage, parent, _pc), (_next_stage, child, created) in zip(
                    story_cases, story_cases[1:]
                ):
                    _link_cases(
                        parent,
                        child,
                        CaseRelationshipType.PARENT_OF,
                        f"{story['name']} - kill chain progression",
                        created,
                    )

            for source_key, target_key in story.get("related", []):
                source = cases_by_key.get(source_key)
                target = cases_by_key.get(target_key)
                if source and target:
                    _link_cases(
                        source,
                        target,
                        CaseRelationshipType.RELATED,
                        f"{story['name']} - shared infrastructure or identity",
                        max(source.created_at, target.created_at),
                    )

            _create_campaign_knowledge(story, cases_by_key, now)

        if include_routine:
            _create_routine_cases(users=users, artifacts=artifacts, now=now)

    counts = summary_counts()
    logger.info("Seeded AGUSTA demo environment v%s: %s", DEMO_DATA_VERSION, counts)
    return {"created": True, **counts}


def _create_campaign_knowledge(story, cases_by_key, now):
    """One campaign-level knowledge record per story, describing the narrative."""
    if story["key"] == "benign":
        return None
    stage_keys = [stage["key"] for stage in story["stages"]] + [
        stage["key"] for stage in story.get("extra_cases", [])
    ]
    linked = [cases_by_key[key] for key in stage_keys if key in cases_by_key]
    if not linked:
        return None
    body = (
        f"## Campaign\n{story['name']}\n\n"
        f"**Attributed to:** {story['actor']}\n\n"
        f"## Narrative\n{story['narrative']}\n\n"
        f"## Correlated cases\n"
        + "\n".join(f"- `{case.case_id}` {case.title}" for case in linked)
        + f"\n\n## Provenance\n{prov.ATTRIBUTION}\n"
    )
    knowledge = Knowledge(
        title=f"Campaign brief: {story['name']}",
        body=body,
        source=KnowledgeSource.MANUAL,
        tags=[prov.DEMO_TAG, "campaign", story["key"]],
    )
    knowledge.full_clean()
    knowledge.save()
    _backdate(knowledge, now - catalog.h(6))
    return knowledge


@transaction.atomic
def purge():
    """Delete only demo-marked records. Never touches operator data."""
    with suppress_audit():
        counts = {}
        counts["knowledge"] = Knowledge.objects.filter(tags__contains=[prov.DEMO_TAG]).delete()[0]
        demo_cases = Case.objects.filter(tags__contains=[prov.DEMO_TAG])

        # Comments and inbox messages attach through a GenericForeignKey, which
        # has no database constraint, so deleting the Case does NOT cascade to
        # them. Remove them explicitly or they accumulate on every reseed.
        case_ids = [str(pk) for pk in demo_cases.values_list("pk", flat=True)]
        case_type = ContentType.objects.get_for_model(Case, for_concrete_model=False)
        counts["comments"] = Comment.objects.filter(
            content_type=case_type, object_id__in=case_ids
        ).delete()[0]
        counts["inbox_messages"] = InboxMessage.objects.filter(
            content_type=case_type, object_id__in=case_ids
        ).delete()[0]

        counts["case_relationships"] = CaseRelationship.objects.filter(
            note__startswith=prov.DEMO_PREFIX
        ).delete()[0]
        counts["enrichments"] = Enrichment.objects.filter(
            uid__startswith=f"{prov.DEMO_TAG}:"
        ).delete()[0]
        counts["playbooks"] = Playbook.objects.filter(
            job_id__startswith=prov.DEMO_PREFIX
        ).delete()[0]
        # Cases cascade to their alerts.
        counts["cases"] = demo_cases.delete()[0]
        # Artifacts are shared, so only remove ones the demo introduced and
        # that no surviving alert still references.
        demo_values = [value for value, *_ in catalog.ARTIFACTS.values()]
        counts["artifacts"] = (
            Artifact.objects.filter(value__in=demo_values, alerts__isnull=True).delete()[0]
        )
    logger.info("Purged AGUSTA demo environment: %s", counts)
    return counts
