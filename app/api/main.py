"""
FastAPI dashboard for REDS — Real Estate AI Domination System.
Exposes lead data, campaign metrics, and system health endpoints.
"""

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.utils.logger import setup_logging
from app.utils.config import settings

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    log.info("reds_api_starting", env=settings.APP_ENV)
    yield
    log.info("reds_api_stopped")


app = FastAPI(
    title="REDS — Real Estate AI Domination System",
    description="Automated motivated seller lead generation and outreach pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.routes import leads, metrics, health

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(leads.router, prefix="/leads", tags=["Leads"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])