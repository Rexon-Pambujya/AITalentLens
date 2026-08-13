# Shared image for both the FastAPI API and the Celery worker (infra/docker-compose.yml
# overrides CMD per-service). Kept single-stage since the backend has no
# build step - just installed Python packages.
FROM python:3.12-slim

WORKDIR /app

# System deps: libpq for psycopg2, build tools for any package needing
# compilation, and poppler/libmupdf runtime deps used transitively by PyMuPDF.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
