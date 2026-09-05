#!/bin/sh
set -eu
umask 077

PROJECT_NAME="agusta-compose"
ARCHIVE_IMAGE="alpine:3.22"
FORMAT_VERSION="agusta-full-backup-v1"

usage() {
    cat <<'EOF'
Usage: ./scripts/restore.sh <backup-directory>

Replaces the current AGUSTA deployment files and Docker named volumes with a
stopped full backup created by backup.sh.
EOF
}

if [ "$#" -ne 1 ]; then
    usage >&2
    exit 1
fi

case "$1" in
    -h|--help)
        usage
        exit 0
        ;;
esac

for command_name in awk basename cp docker grep mktemp rm sha256sum tar; do
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
if [ ! -f compose.yaml ]; then
    echo "Run this script from an AGUSTA Compose release directory." >&2
    exit 1
fi
if [ -n "${COMPOSE_PROJECT_NAME:-}" ] ||
   { [ -f .env ] && grep -q '^COMPOSE_PROJECT_NAME=' .env; }; then
    echo "Custom COMPOSE_PROJECT_NAME values are not supported by this restore script." >&2
    exit 1
fi
if grep -q '^name:' compose.yaml ||
   { [ -f compose.override.yaml ] && grep -q '^name:' compose.override.yaml; }; then
    echo "Custom top-level Compose project names are not supported by this restore script." >&2
    exit 1
fi

backup_dir="$1"
if [ ! -d "$backup_dir" ]; then
    echo "Backup directory does not exist: $backup_dir" >&2
    exit 1
fi
backup_dir="$(cd "$backup_dir" && pwd -P)"

for file_name in manifest.txt SHA256SUMS files.tar.gz volumes.tar.gz; do
    if [ ! -f "$backup_dir/$file_name" ]; then
        echo "Backup file is missing: $backup_dir/$file_name" >&2
        exit 1
    fi
done

if ! grep -qx "format=$FORMAT_VERSION" "$backup_dir/manifest.txt"; then
    echo "Unsupported or incomplete backup format." >&2
    exit 1
fi
if ! grep -qx "project_name=$PROJECT_NAME" "$backup_dir/manifest.txt"; then
    echo "The backup does not belong to the $PROJECT_NAME Compose project." >&2
    exit 1
fi

(
    cd "$backup_dir"
    sha256sum -c SHA256SUMS
)
tar -tzf "$backup_dir/files.tar.gz" >/dev/null
tar -tzf "$backup_dir/volumes.tar.gz" >/dev/null

if ! tar -tzf "$backup_dir/files.tar.gz" |
    awk '
        /^\// || /(^|\/)\.\.(\/|$)/ { invalid = 1 }
        END { exit invalid ? 1 : 0 }
    '
then
    echo "The files archive contains an unsafe path." >&2
    exit 1
fi

if ! tar -tzf "$backup_dir/volumes.tar.gz" |
    awk '
        /^\// || /(^|\/)\.\.(\/|$)/ { invalid = 1 }
        !/^(postgres-data|redis-data|rustfs-data|custom-python-packages|static-files)(\/|$)/ { invalid = 1 }
        END { exit invalid ? 1 : 0 }
    '
then
    echo "The volumes archive contains an unexpected or unsafe path." >&2
    exit 1
fi
for directory in postgres-data redis-data rustfs-data custom-python-packages static-files; do
    if ! tar -tzf "$backup_dir/volumes.tar.gz" | grep -Eq "^${directory}(/|$)"; then
        echo "The volumes archive is missing: $directory" >&2
        exit 1
    fi
done

stage_dir="$(mktemp -d)"
cleanup() {
    rm -rf "$stage_dir"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

tar -xzf "$backup_dir/files.tar.gz" -C "$stage_dir"

if [ ! -f "$stage_dir/.env" ] ||
   [ ! -f "$stage_dir/compose.yaml" ] ||
   [ ! -x "$stage_dir/scripts/doctor.sh" ]; then
    echo "The files archive is not a complete AGUSTA Compose deployment." >&2
    exit 1
fi
if grep -q '^COMPOSE_PROJECT_NAME=' "$stage_dir/.env"; then
    echo "The backup uses an unsupported custom COMPOSE_PROJECT_NAME." >&2
    exit 1
fi
if grep -q '^name:' "$stage_dir/compose.yaml" ||
   { [ -f "$stage_dir/compose.override.yaml" ] &&
     grep -q '^name:' "$stage_dir/compose.override.yaml"; }; then
    echo "The backup uses an unsupported custom top-level Compose project name." >&2
    exit 1
fi

(
    cd "$stage_dir"
    docker compose config --quiet
)

if ! docker image inspect "$ARCHIVE_IMAGE" >/dev/null 2>&1; then
    docker pull "$ARCHIVE_IMAGE"
fi

echo "Stopping the current AGUSTA deployment..."
if [ -f .env ]; then
    docker compose down --remove-orphans
fi

rm -f .env .env.example README.md README.zh.md compose.yaml compose.override.yaml
rm -rf scripts custom certs logs
cp -a "$stage_dir"/. "$deployment_dir"/

docker run --rm \
    -v "${PROJECT_NAME}_postgres-data:/volumes/postgres-data" \
    -v "${PROJECT_NAME}_redis-data:/volumes/redis-data" \
    -v "${PROJECT_NAME}_rustfs-data:/volumes/rustfs-data" \
    -v "${PROJECT_NAME}_custom-python-packages:/volumes/custom-python-packages" \
    -v "${PROJECT_NAME}_static-files:/volumes/static-files" \
    -v "$backup_dir:/backup:ro" \
    "$ARCHIVE_IMAGE" \
    sh -euc '
        for directory in postgres-data redis-data rustfs-data custom-python-packages static-files; do
            find "/volumes/$directory" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
        done
        tar -xzf /backup/volumes.tar.gz -C /volumes
    '

docker compose up -d
./scripts/doctor.sh

echo "AGUSTA restored from: $backup_dir"
