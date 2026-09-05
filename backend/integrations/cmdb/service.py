import logging

from integrations.cmdb.models import CMDBQueryOutput
from integrations.cmdb.providers import get_providers

logger = logging.getLogger(__name__)


def list_providers():
    return list(get_providers().keys())


def lookup_artifact_context(artifact_type, artifact_value, provider=None):
    artifact_type = artifact_type.value if hasattr(artifact_type, "value") else str(artifact_type)
    artifact_value = str(artifact_value or "").strip()
    active_providers = get_providers()
    if provider is not None:
        if provider not in active_providers:
            raise ValueError(f"Unknown CMDB provider: {provider}")
        providers = {provider: active_providers[provider]}
    else:
        providers = active_providers

    results = []
    errors = []
    for provider_name, provider_instance in providers.items():
        try:
            result = provider_instance.lookup(artifact_type, artifact_value)
            results.append(result)
            if result.error:
                errors.append(f"[{provider_name}] {result.error}")
        except Exception:
            logger.exception("CMDB provider lookup failed: %s", provider_name)
            errors.append(f"[{provider_name}] Provider lookup failed.")

    return CMDBQueryOutput(
        artifact_type=artifact_type,
        artifact_value=artifact_value,
        results=results,
        errors=errors,
    )
