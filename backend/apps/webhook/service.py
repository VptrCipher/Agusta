from apps.common.redis_stream import RedisStreamClient
from apps.settings.runtime_config import get_stream_maxlen
from apps.webhook.schemas import KibanaPayload, SplunkPayload, WebhookResult


class WebhookRedisError(RuntimeError):
    pass


def handle_splunk_webhook(payload, *, redis_client=None):
    parsed = SplunkPayload.model_validate(payload)
    stream = parsed.search_name.strip()
    if not stream:
        raise ValueError("search_name is required.")

    redis_client = redis_client or RedisStreamClient()
    try:
        message_id = redis_client.send_message(stream, parsed.result, maxlen=get_stream_maxlen())
    except Exception as exc:
        raise WebhookRedisError(f"Failed to write Redis stream {stream}: {type(exc).__name__}") from exc

    return WebhookResult(stream=stream, sent=1, skipped=0, message_ids=[message_id])


def handle_kibana_webhook(payload, *, redis_client=None):
    parsed = KibanaPayload.model_validate(payload)
    stream = parsed.rule.name.strip()
    if not stream:
        raise ValueError("rule.name is required.")

    redis_client = redis_client or RedisStreamClient()
    sent = 0
    skipped = 0
    message_ids = []
    for hit in parsed.context.hits:
        source = extract_source(hit)
        if not source:
            skipped += 1
            continue
        try:
            message_id = redis_client.send_message(stream, source, maxlen=get_stream_maxlen())
        except Exception as exc:
            raise WebhookRedisError(f"Failed to write Redis stream {stream}: {type(exc).__name__}") from exc
        sent += 1
        message_ids.append(message_id)

    return WebhookResult(stream=stream, sent=sent, skipped=skipped, message_ids=message_ids)


def normalize_hit_value(value):
    if isinstance(value, dict):
        if set(value.keys()) == {"keyword"}:
            return normalize_hit_value(value.get("keyword"))
        return {key: normalize_hit_value(item) for key, item in value.items() if not str(key).endswith(".keyword")}
    if isinstance(value, list):
        return [normalize_hit_value(item) for item in value]
    return value


def extract_source(hit):
    if not isinstance(hit, dict):
        return {}
    source = hit.get("_source") if isinstance(hit.get("_source"), dict) else hit
    source = normalize_hit_value(source)
    return source if isinstance(source, dict) else {}
