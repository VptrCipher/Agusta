FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    DJANGO_SETTINGS_MODULE=agusta.settings \
    PYTHONPATH=/opt/agusta/custom-packages:/app/custom

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Operator overlay directories. These are bind-mounted in a deployment; creating
# them here keeps the overlay lookups happy when no volume is mounted. Official
# content lives in /app/{modules,playbooks,data} and is copied above.
RUN mkdir -p \
    /app/custom/modules \
    /app/custom/playbooks \
    /app/custom/data/siem \
    /app/custom/data/modules \
    /app/custom/data/playbooks \
    /opt/agusta/custom-packages

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000 8001

CMD ["gunicorn", "agusta.wsgi:application", "--bind", "0.0.0.0:8000"]
