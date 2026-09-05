#!/bin/sh
set -eu

if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi

required_services="
agusta-frontend
agusta-web
agusta-asgi
agusta-worker-module
agusta-worker-case-analysis
agusta-worker-playbook
agusta-worker-elk-action
agusta-worker-dashboard-cache
postgres
redis-stack
rustfs
"

service_ready() {
    service="$1"
    container_ids="$(docker compose ps --all -q "$service" 2>/dev/null || true)"
    if [ -z "$container_ids" ]; then
        return 1
    fi

    managed_found=false
    for container_id in $container_ids; do
        oneoff="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.oneoff"}}' "$container_id" 2>/dev/null || true)"
        if [ "$oneoff" = "True" ] || [ "$oneoff" = "true" ]; then
            continue
        fi
        managed_found=true

        status="$(docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)"
        if [ "$status" != "running" ]; then
            return 1
        fi

        health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_id" 2>/dev/null || true)"
        if [ "$health" != "none" ] && [ "$health" != "healthy" ]; then
            return 1
        fi
    done
    [ "$managed_found" = "true" ]
}

service_summary() {
    service="$1"
    container_ids="$(docker compose ps --all -q "$service" 2>/dev/null || true)"
    if [ -z "$container_ids" ]; then
        printf '%s: missing\n' "$service"
        return
    fi

    managed_found=false
    for container_id in $container_ids; do
        oneoff="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.oneoff"}}' "$container_id" 2>/dev/null || true)"
        if [ "$oneoff" = "True" ] || [ "$oneoff" = "true" ]; then
            printf '%s/%s: ignored one-off container\n' "$service" "$container_id"
            continue
        fi
        managed_found=true

        status="$(docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)"
        health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_id" 2>/dev/null || true)"
        printf '%s/%s: status=%s health=%s\n' "$service" "$container_id" "${status:-unknown}" "${health:-unknown}"
    done
    if [ "$managed_found" = "false" ]; then
        printf '%s: no managed service containers\n' "$service"
    fi
}

wait_seconds="${AGUSTA_DOCTOR_WAIT_SECONDS:-180}"
case "$wait_seconds" in
    ''|*[!0-9]*)
        echo "AGUSTA_DOCTOR_WAIT_SECONDS must be a non-negative integer." >&2
        exit 1
        ;;
esac

deadline="$(( $(date +%s) + wait_seconds ))"
while :; do
    pending=""
    for service in $required_services; do
        if ! service_ready "$service"; then
            pending="$pending $service"
        fi
    done

    if [ -z "$pending" ]; then
        break
    fi

    if [ "$(date +%s)" -ge "$deadline" ]; then
        echo "AGUSTA services did not become ready within ${wait_seconds}s:" >&2
        for service in $required_services; do
            service_summary "$service" >&2
        done
        exit 1
    fi
    sleep 5
done

docker compose ps
echo "All managed AGUSTA services are running and healthy."
docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-agusta}"
docker compose exec -T redis-stack redis-cli -a "${REDIS_PASSWORD}" ping
docker compose exec -T agusta-web python manage.py check
docker compose exec -T agusta-web python manage.py shell -c "from apps.agentic.services.custom import list_module_definitions_with_health, list_playbook_definition_records, list_siem_definition_records; results = (list_module_definitions_with_health(), list_playbook_definition_records(), list_siem_definition_records(reload=True)); print({result['section']: result['counts'] for result in results}); raise SystemExit(0 if all(result['success'] for result in results) else 1)"
docker compose exec -T agusta-web python - <<'PY'
import boto3
from django.conf import settings

client = boto3.client(
    "s3",
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
    config=settings.AWS_S3_CLIENT_CONFIG,
)
client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
PY

echo "AGUSTA deployment checks passed."
