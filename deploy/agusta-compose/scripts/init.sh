#!/bin/sh
set -eu

if [ "$#" -ne 0 ]; then
    echo "init.sh does not accept arguments. Install custom Python dependencies with agusta-custom-deps." >&2
    exit 2
fi

# Operator overlay directories. These start empty on purpose: AGUSTA ships its
# own Modules, Playbooks and SIEM index definitions inside the backend image.
# Anything you drop in here is layered on top, and a file with the same name as
# a shipped one overrides it.
mkdir -p \
    certs \
    custom/data/modules \
    custom/data/playbooks \
    custom/data/siem \
    custom/modules \
    custom/playbooks \
    logs/nginx

if [ ! -e custom/requirements.txt ]; then
    cat > custom/requirements.txt <<'EOF'
# Add Python packages required by custom Module or Playbook scripts.
# Example:
# requests==2.32.5
EOF
fi

generate_secret() {
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex 32
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 -c 'import secrets; print(secrets.token_hex(32))'
        return
    fi
    od -An -N32 -tx1 /dev/urandom | tr -d ' \n'
}

set_env_value() {
    key="$1"
    value="$2"
    if grep -q "^${key}=" .env; then
        sed -i "s|^${key}=.*|${key}=${value}|" .env
    else
        printf '%s=%s\n' "$key" "$value" >> .env
    fi
}

if [ ! -e compose.override.yaml ]; then
    cat > compose.override.yaml <<'EOF'
# User-managed Docker Compose overrides.
# AGUSTA upgrades never overwrite this file.
# Keep supported passwords, ports, and image settings in .env.
# Replace the empty services mapping below when service-level overrides are needed.
#
# services:
#   agusta-web:
#     environment:
#       EXAMPLE_SETTING: value
services: {}
EOF
fi

if [ ! -f .env ]; then
    cp .env.example .env
    postgres_password="$(generate_secret)"
    redis_password="$(generate_secret)"
    rustfs_secret="$(generate_secret)"

    set_env_value DJANGO_SECRET_KEY "$(generate_secret)"
    set_env_value POSTGRES_PASSWORD "$postgres_password"
    set_env_value REDIS_PASSWORD "$redis_password"
    set_env_value RUSTFS_SECRET_KEY "$rustfs_secret"
    echo "Generated .env with random service secrets. Review .env before exposing the deployment."
fi

if grep -Eq '^(DJANGO_SECRET_KEY|POSTGRES_PASSWORD|REDIS_PASSWORD|RUSTFS_SECRET_KEY)=change-me' .env; then
    echo "Refusing to initialize with placeholder secrets in .env. Delete .env to regenerate or update the values manually."
    exit 1
fi

docker compose pull

docker compose run --rm agusta-migrate
docker compose up -d

echo "AGUSTA is starting. Run ./scripts/doctor.sh to verify the deployment."
echo "Create an administrator when needed:"
echo "  docker compose exec agusta-web python manage.py createsuperuser"
