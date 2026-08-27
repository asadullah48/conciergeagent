import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from conciergeagent.core.models import (
    CustomerProfile, ServiceInteraction, ConciergeSessionResponse, WealthTier
)
from conciergeagent.orchestration.concierge_engine import ConciergeEngine

app = FastAPI(
    title="ConciergeAgent Platform Gateway",
    version="1.0.0",
    description="Hyperpersonalized Customer Service & Financial Concierge Multi-Agent Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ConciergeEngine()

# Mount Static UI Files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"service": "ConciergeAgent", "status": "active", "docs": "/docs"}

@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "ConciergeAgent", "version": "1.0.0"}

@app.get("/readyz")
def readyz():
    return {"status": "ready", "concierge_agents_active": 3}

@app.post("/api/v1/concierge/interact", response_model=ConciergeSessionResponse)
def interact_concierge(interaction: ServiceInteraction):
    return engine.process_interaction(interaction)
