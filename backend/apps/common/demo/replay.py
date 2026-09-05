"""Replay the bundled sample alert payloads through AGUSTA's real detection path.

This is the most credible part of the demonstration environment: instead of
inserting rows that merely look like detections, it feeds the sample payloads
that ship in ``backend/data/modules/<module>/raw_alert_*.json`` into the actual
Module classes. Those Modules then call ``create_alert_with_context()``, which is
the same code the production ingestion pipeline uses.

That means the resulting Cases, Alerts and Artifacts were genuinely produced by
AGUSTA's own detection logic, including real ``correlation_uid`` computation, so
folding two payloads from the same rule into one Case is demonstrably the
platform's behaviour rather than something the seeder faked.

Two modes:

* direct (default) - instantiate the Module and call ``run(payload)``. Fully
  deterministic and needs no Redis, so it is safe for first-boot seeding.
* ``via_redis=True`` - publish onto the Module's Redis stream and let the running
  ``agusta-worker-module`` consume it. Better for showing the live pipeline, but
  asynchronous.
"""

import json
import logging
from pathlib import Path

from django.conf import settings

from apps.agentic.runtime.module import scan_module_definitions

logger = logging.getLogger(__name__)

SAMPLE_GLOB = "raw_alert_*.json"


def bundled_payload_dir():
    """Directory holding per-module sample payloads."""
    return Path(settings.BASE_DIR) / "data" / "modules"


def iter_sample_payloads():
    """Yield ``(module_slug, path, payload)`` for every bundled sample."""
    root = bundled_payload_dir()
    if not root.is_dir():
        return
    for module_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for path in sorted(module_dir.glob(SAMPLE_GLOB)):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                logger.exception("Unreadable bundled sample payload: %s", path)
                continue
            yield module_dir.name, path, payload


def _mark_as_demo(case, alert):
    """Tag pipeline-produced records so the scoped purge can reclaim them."""
    from apps.common.demo import provenance as prov

    if prov.DEMO_TAG not in (case.tags or []):
        case.tags = [*(case.tags or []), prov.DEMO_TAG]
        type(case).objects.filter(pk=case.pk).update(tags=case.tags)
    if alert is not None and prov.DEMO_TAG not in (alert.labels or []):
        alert.labels = [*(alert.labels or []), prov.DEMO_TAG]
        type(alert).objects.filter(pk=alert.pk).update(labels=alert.labels)


def _definitions_by_slug():
    definitions, errors = scan_module_definitions()
    for error in errors:
        logger.warning("Module definition failed to load during replay: %s", error)
    return {Path(definition.path).stem: definition for definition in definitions}


def replay_bundled_payloads(*, via_redis=False):
    """Feed every bundled sample payload through its Module.

    Returns ``{"replayed": int, "cases": [...], "errors": [...], "log": [...]}``.
    """
    definitions = _definitions_by_slug()
    log = []
    errors = []
    cases = []
    replayed = 0

    if not definitions:
        message = (
            "No detection Modules discovered. Expected official Modules in "
            f"{Path(settings.BASE_DIR) / 'modules'}."
        )
        log.append(message)
        errors.append({"error": message})
        return {"replayed": 0, "cases": [], "errors": errors, "log": log}

    samples = list(iter_sample_payloads())
    if not samples:
        message = f"No bundled sample payloads found in {bundled_payload_dir()}."
        log.append(message)
        return {"replayed": 0, "cases": [], "errors": errors, "log": log}

    client = None
    if via_redis:
        from apps.common.redis_stream import RedisStreamClient

        client = RedisStreamClient()

    for slug, path, payload in samples:
        definition = definitions.get(slug)
        if definition is None:
            log.append(f"skip {path.name}: no Module named {slug}")
            continue

        try:
            if via_redis:
                message_id = client.send_message(definition.stream_name, payload)
                replayed += 1
                log.append(
                    f"published {path.parent.name}/{path.name} -> stream "
                    f"{definition.stream_name} (id {message_id})"
                )
            else:
                result = definition.module_class().run(payload)
                replayed += 1
                case = getattr(result, "case", None)
                alert = getattr(result, "alert", None)
                if case is not None:
                    # The Module sets its own tags, so mark the output as demo
                    # data afterwards. Without this, --purge would leave these
                    # cases behind.
                    _mark_as_demo(case, alert)
                    cases.append(case)
                    log.append(
                        f"{path.parent.name}/{path.name} -> {definition.name}: "
                        f"case {case.case_id} / alert {getattr(alert, 'alert_id', '?')}"
                    )
                else:
                    log.append(f"{path.parent.name}/{path.name} -> {definition.name}: no case returned")
        except Exception as exc:  # a bad sample must not abort seeding
            logger.exception("Failed to replay bundled payload %s", path)
            errors.append({"path": str(path), "module": slug, "error": str(exc)})
            log.append(f"FAILED {path.parent.name}/{path.name}: {exc}")

    distinct_cases = {case.pk for case in cases}
    if cases:
        folded = len(cases) - len(distinct_cases)
        summary = f"{replayed} payload(s) produced {len(distinct_cases)} distinct case(s)"
        if folded:
            summary += (
                f"; {folded} alert(s) were folded into an existing case by matching "
                "correlation_uid, computed by the Module itself"
            )
        else:
            summary += "; each payload had a distinct correlation_uid so no folding occurred"
        log.append(summary)

    return {"replayed": replayed, "cases": cases, "errors": errors, "log": log}
