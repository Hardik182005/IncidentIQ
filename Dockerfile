# ── IncidentIQ — single Cloud Run service (FastAPI API + static UI) ──────────
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend application code
COPY backend/ /app/

# Static frontend bundled into /app/frontend (served by FastAPI at "/")
COPY index.html /app/frontend/
COPY screens/ /app/frontend/screens/
COPY components/ /app/frontend/components/

RUN mkdir -p /tmp/incidentiq_logs

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Cloud Run injects $PORT (defaults to 8080); shell form lets it expand.
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --log-level info
