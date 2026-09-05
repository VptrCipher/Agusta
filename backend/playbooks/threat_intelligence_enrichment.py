from django.db import transaction

from apps.agentic.runtime.base import BasePlaybook
from apps.enrichments.models import Enrichment, EnrichmentType
from integrations.threat_intel.service import query_indicator


class Playbook(BasePlaybook):
    NAME = "Threat Intelligence Enrichment"
    DESC = "Query threat intelligence for all Artifacts linked to the Case."
    TAGS = ["System", "Threat Intel", "Enrichment"]

    def run(self):
        if self.case is None:
            raise ValueError("Threat Intelligence Enrichment playbook requires a linked case.")

        stats = {
            "alerts": 0,
            "artifacts": 0,
            "unique": 0,
            "enriched": 0,
            "unsupported": 0,
            "errors": 0,
        }
        artifacts = _collect_unique_artifacts(self.case)
        stats["unique"] = len(artifacts)
        stats["alerts"] = self.case.alerts.count()
        stats["artifacts"] = sum(alert.artifacts.count() for alert in self.case.alerts.all())

        for artifact in artifacts:
            if not artifact.value:
                stats["unsupported"] += 1
                continue
            output = query_indicator(artifact.value, artifact_type=artifact.type)
            if output.errors and not any(result.risk_level for result in output.results):
                stats["unsupported"] += 1
                continue
            for result in output.results:
                if result.error:
                    stats["unsupported"] += 1
                    continue
                try:
                    _upsert_artifact_enrichment(artifact, result)
                    stats["enriched"] += 1
                except Exception:
                    stats["errors"] += 1

        return (
            "Threat intelligence enrichment completed. "
            f"alerts={stats['alerts']}, artifacts={stats['artifacts']}, unique={stats['unique']}, "
            f"enriched={stats['enriched']}, unsupported={stats['unsupported']}, errors={stats['errors']}"
        )


def _collect_unique_artifacts(case):
    artifacts = {}
    for alert in case.alerts.prefetch_related("artifacts"):
        for artifact in alert.artifacts.all():
            artifacts[artifact.id] = artifact
    return list(artifacts.values())


@transaction.atomic
def _upsert_artifact_enrichment(artifact, result):
    uid = f"ti:{result.provider}:{artifact.artifact_id}"
    enrichment = (
        Enrichment.objects.select_for_update()
        .filter(
            artifact=artifact,
            provider=result.provider,
            type=EnrichmentType.THREAT_INTELLIGENCE,
            uid=uid,
        )
        .first()
    )
    if enrichment is None:
        enrichment = Enrichment(
            artifact=artifact,
            provider=result.provider,
            type=EnrichmentType.THREAT_INTELLIGENCE,
            uid=uid,
        )
    enrichment.name = "Threat Intelligence"
    enrichment.value = artifact.value
    enrichment.desc = _description(result)
    enrichment.data = result.model_dump()
    enrichment.full_clean()
    enrichment.save()
    return enrichment


def _description(result):
    malicious_text = "malicious" if result.is_malicious else "not malicious"
    risk = result.risk_level or "unknown"
    return f"{result.provider} assessed indicator as {malicious_text} with {risk} risk."
