# syntax=docker/dockerfile:1

# ---- Build stage: produce a wheel from pyproject, without dev extras ----
FROM python:3.12-slim AS builder

WORKDIR /build
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml README.md LICENSE ./
COPY conciergeagent ./conciergeagent
RUN python -m pip install --upgrade pip build \
    && python -m build --wheel --outdir /dist


# ---- Runtime stage: install only the wheel and its runtime dependencies ----
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="ConciergeAgent" \
      org.opencontainers.image.description="Hyperpersonalized customer service and financial concierge multi-agent platform" \
      org.opencontainers.image.source="https://github.com/asadullah48/conciergeagent" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production \
    LOG_LEVEL=info

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 concierge

WORKDIR /app
COPY --from=builder /dist/*.whl /tmp/
RUN python -m pip install /tmp/*.whl \
    && rm -f /tmp/*.whl

# Run unprivileged: nothing in this service needs root.
USER concierge
EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:8005/healthz || exit 1

CMD ["uvicorn", "conciergeagent.server:app", "--host", "0.0.0.0", "--port", "8005"]
