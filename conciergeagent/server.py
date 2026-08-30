"""FastAPI gateway for the ConciergeAgent platform."""
from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from conciergeagent import __version__
from conciergeagent.core.config import get_settings
from conciergeagent.core.models import ConciergeSessionResponse, ServiceInteraction
from conciergeagent.core.observability import METRICS, configure_logging
from conciergeagent.llm.client import LLMClient
from conciergeagent.orchestration.concierge_engine import ConciergeEngine

logger = logging.getLogger(__name__)
settings = get_settings()

# Narration is opt-in and credential-gated. Without LLM_API_KEY the gateway is
# fully deterministic, so a public demo costs nothing and cannot fail on a
# third-party outage.
engine = ConciergeEngine(LLMClient(settings) if settings.llm_active else None)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.log_level, settings.json_logs)
    logger.info(
        "conciergeagent gateway starting",
        extra={
            "version": __version__,
            "environment": settings.environment,
            "allowed_origins": settings.allowed_origins,
            "narration": settings.llm_model if settings.llm_active else "deterministic",
        },
    )
    yield
    logger.info("conciergeagent gateway stopped", extra={"version": __version__})


app = FastAPI(
    title="ConciergeAgent Platform Gateway",
    version=__version__,
    description=(
        "Hyperpersonalized customer service and financial concierge multi-agent platform. "
        "Routes each interaction through a sentiment/hospitality audit, then to a specialist "
        "advisory, support, or loyalty lane."
    ),
    license_info={"name": "Apache 2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
    lifespan=lifespan,
)

# An explicit allowlist: '*' combined with allow_credentials lets any origin
# make credentialed calls, which the CORS specification exists to prevent.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a structured error and record it, rather than leaking a traceback."""
    METRICS.increment("concierge_unhandled_errors_total", {"path": request.url.path})
    logger.exception("unhandled error", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred."},
    )


@app.get("/", include_in_schema=False)
def serve_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
    return JSONResponse(
        {"service": "ConciergeAgent", "version": __version__, "status": "active", "docs": "/docs"}
    )


@app.get("/healthz", tags=["operations"])
def healthz() -> dict:
    """Liveness probe: the process is running."""
    return {"status": "healthy", "service": "ConciergeAgent", "version": __version__}


@app.get("/readyz", tags=["operations"])
def readyz() -> dict:
    """Readiness probe: the agent graph is constructed and able to serve."""
    return {
        "status": "ready",
        "concierge_agents_active": 3,
        "agents": [
            engine.advisor_agent.name,
            engine.support_agent.name,
            engine.experience_agent.name,
        ],
        "narration_mode": "llm" if engine.llm_client else "deterministic",
        "narration_model": engine.llm_client.model if engine.llm_client else None,
    }


@app.get("/metrics", tags=["operations"], response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    """Prometheus text-format exposition of interaction counters and latency."""
    if not settings.metrics_enabled:
        return PlainTextResponse("metrics disabled\n", status_code=404)
    return PlainTextResponse(METRICS.render_prometheus(), media_type="text/plain; version=0.0.4")


@app.post(
    "/api/v1/concierge/interact",
    response_model=ConciergeSessionResponse,
    tags=["concierge"],
    summary="Process one customer interaction end to end",
)
def interact_concierge(interaction: ServiceInteraction) -> ConciergeSessionResponse:
    """Audit sentiment, route to the specialist lane, and return the reply."""
    return engine.process_interaction(interaction)
