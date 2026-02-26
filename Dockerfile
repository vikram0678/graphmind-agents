# ─────────────────────────────────────────
# Base stage — shared dependencies
# ─────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY migrations/ ./migrations/

RUN mkdir -p /app/logs

# ─────────────────────────────────────────
# API stage
# ─────────────────────────────────────────
FROM base AS api

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ─────────────────────────────────────────
# Worker stage
# ─────────────────────────────────────────
FROM base AS worker

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "--concurrency=2"]