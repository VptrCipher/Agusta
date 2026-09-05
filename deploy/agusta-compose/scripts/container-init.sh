#!/bin/sh
set -eu

python manage.py migrate
python manage.py collectstatic --noinput

# ---------------------------------------------------------------------------
# Demonstration environment.
#
#   auto (default) - seed only when the deployment has no cases at all, so a
#                    fresh install is immediately explorable while an existing
#                    deployment with real data is never touched.
#   on             - always ensure the demo environment is present (idempotent).
#   off            - never seed.
#
# AGUSTA_DEMO_REPLAY=on additionally replays the bundled sample payloads through
# the real detection Modules, so some cases are produced by the live pipeline.
# ---------------------------------------------------------------------------
demo_mode="$(printf '%s' "${AGUSTA_DEMO_DATA:-auto}" | tr '[:upper:]' '[:lower:]')"
demo_replay="$(printf '%s' "${AGUSTA_DEMO_REPLAY:-off}" | tr '[:upper:]' '[:lower:]')"

demo_args=""
case "$demo_mode" in
    auto) demo_args="--if-empty" ;;
    on)   demo_args="" ;;
    off)  demo_args="" ;;
    *)
        echo "AGUSTA_DEMO_DATA must be auto, on or off. Got: ${AGUSTA_DEMO_DATA:-}" >&2
        exit 2
        ;;
esac

if [ "$demo_replay" = "on" ]; then
    demo_args="$demo_args --replay-modules"
fi

if [ "$demo_mode" = "off" ]; then
    echo "AGUSTA_DEMO_DATA=off, skipping demonstration data."
else
    # Demonstration data is never allowed to block the deployment. Migrations and
    # static files have already succeeded above and the platform is fully
    # functional without sample data, so a failure here is a warning, not a
    # fatal error. `if ! cmd` also suspends `set -e` for this call.
    # shellcheck disable=SC2086
    if ! python manage.py seed_demo_data $demo_args; then
        echo "WARNING: demonstration data seeding failed. The deployment is still usable." >&2
        echo "         Retry manually with: python manage.py seed_demo_data" >&2
    fi
fi

python - <<'PY'
import time

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

bucket = settings.AWS_STORAGE_BUCKET_NAME

for attempt in range(1, 31):
    client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=settings.AWS_S3_CLIENT_CONFIG,
    )
    try:
        client.head_bucket(Bucket=bucket)
        break
    except ClientError as exc:
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status in {403, 404}:
            client.create_bucket(Bucket=bucket)
            break
        if attempt == 30:
            raise
    except Exception:
        if attempt == 30:
            raise
        time.sleep(2)
else:
    raise RuntimeError(f"Cannot initialize S3 bucket: {bucket}")
PY
