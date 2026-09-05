#!/bin/sh
set -eu
umask 077

APPLICATION_SERVICES="
agusta-frontend
agusta-web
agusta-asgi
agusta-worker-module
agusta-worker-case-analysis
agusta-worker-playbook
agusta-worker-elk-action
agusta-worker-dashboard-cache
"

usage() {
    cat <<'EOF'
Usage: ./scripts/upgrade.sh

Applies the target release already extracted over this AGUSTA Compose deployment:
updates image settings, pulls images, runs migrations, starts services, and
checks the deployment.
EOF
}

if [ "$#" -ne 0 ]; then
    case "${1:-}" in
        -h|--help)
            usage
            exit 0
            ;;
    esac
    usage >&2
    exit 1
fi

for command_name in awk chmod cut docker grep mktemp mv rm stat; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Required command is not available: $command_name" >&2
        exit 1
    fi
done

deployment_dir="$(pwd -P)"
if [ ! -f "$deployment_dir/compose.yaml" ] ||
   [ ! -f "$deployment_dir/.env" ] ||
   [ ! -f "$deployment_dir/.env.example" ]; then
    echo "Run this script from an initialized AGUSTA Compose deployment directory." >&2
    exit 1
fi

env_value() {
    file="$1"
    key="$2"
    line_count="$(grep -c "^${key}=" "$file" || true)"
    if [ "$line_count" -ne 1 ]; then
        echo "$file must contain exactly one ${key}= entry." >&2
        return 1
    fi

    value="$(grep "^${key}=" "$file" | cut -d= -f2-)"
    if [ -z "$value" ]; then
        echo "$file contains an empty ${key}= entry." >&2
        return 1
    fi
    printf '%s\n' "$value"
}

backend_image="$(env_value "$deployment_dir/.env.example" AGUSTA_BACKEND_IMAGE)"
frontend_image="$(env_value "$deployment_dir/.env.example" AGUSTA_FRONTEND_IMAGE)"
current_backend_image="$(env_value "$deployment_dir/.env" AGUSTA_BACKEND_IMAGE)"
current_frontend_image="$(env_value "$deployment_dir/.env" AGUSTA_FRONTEND_IMAGE)"

temporary_env=""
cleanup() {
    if [ -n "$temporary_env" ]; then
        rm -f "$temporary_env"
    fi
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

update_image_settings() {
    temporary_env="$(mktemp "$deployment_dir/.env.upgrade.XXXXXX")"
    env_mode="$(stat -c '%a' "$deployment_dir/.env" 2>/dev/null || stat -f '%Lp' "$deployment_dir/.env")"

    awk \
        -v backend_image="$backend_image" \
        -v frontend_image="$frontend_image" '
        index($0, "AGUSTA_BACKEND_IMAGE=") == 1 {
            print "AGUSTA_BACKEND_IMAGE=" backend_image
            next
        }
        index($0, "AGUSTA_FRONTEND_IMAGE=") == 1 {
            print "AGUSTA_FRONTEND_IMAGE=" frontend_image
            next
        }
        { print }
    ' "$deployment_dir/.env" > "$temporary_env"
    chmod "$env_mode" "$temporary_env"
    mv "$temporary_env" "$deployment_dir/.env"
    temporary_env=""
}

run_pre_migration_steps() {
    :
}

run_post_migration_steps() {
    :
}

echo "Updating backend image: $current_backend_image -> $backend_image"
echo "Updating frontend image: $current_frontend_image -> $frontend_image"
update_image_settings

docker compose config --quiet
docker compose pull

echo "Stopping the current AGUSTA application services..."
docker compose stop $APPLICATION_SERVICES

run_pre_migration_steps
docker compose run --rm agusta-migrate
run_post_migration_steps

docker compose up -d
./scripts/doctor.sh

echo "AGUSTA upgrade completed."
