from django.db import transaction

from apps.agentic.runtime.base import BasePlaybook
from apps.enrichments.models import Enrichment, EnrichmentProvider, EnrichmentType
from integrations.cmdb.service import lookup_artifact_context


class Playbook(BasePlaybook):
    NAME = "CMDB Enrichment"
    DESC = "Query CMDB context for all Artifacts linked to the Case."
    TAGS = ["Custom", "CMDB", "Enrichment"]

    def run(self):
        if self.case is None:
            raise ValueError("CMDB Enrichment playbook requires a linked case.")

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
            output = lookup_artifact_context(artifact.type, artifact.value)
            if output.errors and not output.results:
                stats["errors"] += len(output.errors)
                continue
            for result in output.results:
                if not result.supported:
                    stats["unsupported"] += 1
                    continue
                try:
                    _upsert_artifact_enrichment(artifact, result)
                    stats["enriched"] += 1
                except Exception:
                    stats["errors"] += 1

        return (
            "CMDB enrichment completed. "
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
    uid = f"cmdb:{result.provider}:{artifact.artifact_id}"
    enrichment = (
        Enrichment.objects.select_for_update()
        .filter(
            artifact=artifact,
            provider=EnrichmentProvider.INTERNAL_CMDB,
            type=EnrichmentType.CMDB,
            uid=uid,
        )
        .first()
    )
    if enrichment is None:
        enrichment = Enrichment(
            artifact=artifact,
            provider=EnrichmentProvider.INTERNAL_CMDB,
            type=EnrichmentType.CMDB,
            uid=uid,
        )
    enrichment.name = "CMDB Context"
    enrichment.value = artifact.value
    enrichment.desc = _description(result)
    enrichment.data = result.model_dump()
    enrichment.full_clean()
    enrichment.save()
    return enrichment


def _description(result):
    service_name = result.business.get("service_name", "unknown service")
    criticality = result.business.get("business_criticality", "unknown criticality")
    if result.record_type:
        return f"{result.provider} returned {result.record_type} context for {service_name} ({criticality})."
    return f"{result.provider} returned CMDB context for {service_name} ({criticality})."
