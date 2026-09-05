#!/bin/sh
set -eu
umask 077

PROJECT_NAME="agusta-compose"
ARCHIVE_IMAGE="alpine:3.22"
FORMAT_VERSION="agusta-full-backup-v1"

usage() {
    cat <<'EOF'
Usage: ./scripts/backup.sh [backup-root]

Creates a stopped full backup under:
  <backup-root>/agusta-full-<timestamp>/

The default backup root is ./backups.
EOF
}

if [ "$#" -gt 1 ]; then
    usage >&2
    exit 1
fi

case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
esac

for command_name in basename date docker grep mkdir sha256sum tar; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Required command is not available: $command_name" >&2
        exit 1
    fi
done

deployment_dir="$(pwd -P)"
if [ "$(basename "$deployment_dir")" != "$PROJECT_NAME" ]; then
    echo "Run this script from a deployment directory named $PROJECT_NAME." >&2
    exit 1
fi
if [ ! -f compose.yaml ] || [ ! -f .env ]; then
    echo "Run this script from an initialized AGUSTA Compose deployment directory." >&2
    exit 1
fi
if [ -n "${COMPOSE_PROJECT_NAME:-}" ] || grep -q '^COMPOSE_PROJECT_NAME=' .env; then
    echo "Custom COMPOSE_PROJECT_NAME values are not supported by this backup script." >&2
    exit 1
fi
if grep -q '^name:' compose.yaml ||
   { [ -f compose.override.yaml ] && grep -q '^name:' compose.override.yaml; }; then
    echo "Custom top-level Compose project names are not supported by this backup script." >&2
    exit 1
fi

docker compose config --quiet

for volume_name in \
    "${PROJECT_NAME}_postgres-data" \
    "${PROJECT_NAME}_redis-data" \
    "${PROJECT_NAME}_rustfs-data" \
    "${PROJECT_NAME}_custom-python-packages" \
    "${PROJECT_NAME}_static-files"
do
    if ! docker volume inspect "$volume_name" >/dev/null 2>&1; then
        echo "Required Docker volume does not exist: $volume_name" >&2
        exit 1
    fi
done

if ! docker image inspect "$ARCHIVE_IMAGE" >/dev/null 2>&1; then
    docker pull "$ARCHIVE_IMAGE"
fi

backup_root="${1:-$deployment_dir/backups}"
mkdir -p "$backup_root"
backup_root="$(cd "$backup_root" && pwd -P)"

case "$backup_root/" in
    "$deployment_dir/backups/"*)
        ;;
    "$deployment_dir/"*)
        echo "A backup root inside the deployment directory must be under $deployment_dir/backups." >&2
        exit 1
        ;;
esac

timestamp="$(date +%Y%m%d%H%M%S)"
backup_dir="$backup_root/agusta-full-$timestamp"
mkdir "$backup_dir"

services_stopped=false
backup_complete=false

finish() {
    status="$?"
    trap - EXIT HUP INT TERM

    if [ "$services_stopped" = "true" ]; then
        echo "Starting AGUSTA services..."
        if docker compose up -d; then
            if [ "$backup_complete" = "true" ]; then
                if ./scripts/doctor.sh; then
                    echo "Backup created: $backup_dir"
                else
                    echo "Backup was created, but the deployment health check failed: $backup_dir" >&2
                    status=1
                fi
            fi
        else
            echo "Failed to restart AGUSTA services." >&2
            status=1
        fi
    fi

    if [ "$backup_complete" != "true" ]; then
        echo "Backup did not complete: $backup_dir" >&2
    fi
    exit "$status"
}

trap finish EXIT
trap 'exit 1' HUP INT TERM

services_stopped=true
docker compose stop

set -- .env .env.example compose.yaml scripts custom certs logs
if [ -f compose.override.yaml ]; then
    set -- "$@" compose.override.yaml
fi
if [ -f README.md ]; then
    set -- "$@" README.md
fi
if [ -f README.zh.md ]; then
    set -- "$@" README.zh.md
fi

tar -czf "$backup_dir/files.tar.gz" "$@"

docker run --rm \
    -v "${PROJECT_NAME}_postgres-data:/volumes/postgres-data:ro" \
    -v "${PROJECT_NAME}_redis-data:/volumes/redis-data:ro" \
    -v "${PROJECT_NAME}_rustfs-data:/volumes/rustfs-data:ro" \
    -v "${PROJECT_NAME}_custom-python-packages:/volumes/custom-python-packages:ro" \
    -v "${PROJECT_NAME}_static-files:/volumes/static-files:ro" \
    -v "$backup_dir:/backup" \
    "$ARCHIVE_IMAGE" \
    sh -euc 'cd /volumes && tar -czf /backup/volumes.tar.gz postgres-data redis-data rustfs-data custom-python-packages static-files'

tar -tzf "$backup_dir/files.tar.gz" >/dev/null
tar -tzf "$backup_dir/volumes.tar.gz" >/dev/null

cat > "$backup_dir/manifest.txt" <<EOF
format=$FORMAT_VERSION
created_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
project_name=$PROJECT_NAME
files_archive=files.tar.gz
volumes_archive=volumes.tar.gz
EOF

(
    cd "$backup_dir"
    sha256sum files.tar.gz volumes.tar.gz > SHA256SUMS
)

backup_complete=true
