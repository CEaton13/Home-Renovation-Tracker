# --- Build stage: install dependencies ---
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir --prefix=/install ".[dev]" \
    && PYTHONPATH=/install/lib/python3.11/site-packages \
       python -m opentelemetry.instrumentation.bootstrap -a requirements > /tmp/otel-requirements.txt \
    && pip install --no-cache-dir --prefix=/install -r /tmp/otel-requirements.txt

# --- Runtime stage: copy only what's needed to run ---
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY src/ ./src/

ENV PYTHONPATH=/app/src
ENV DB_PATH=/app/data/renovation_tracker.db

RUN mkdir -p /app/data

EXPOSE 5000

CMD ["opentelemetry-instrument", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "renovation_tracker.app:create_app()"]