"""Health check endpoint."""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "REDS",
        "timestamp": datetime.utcnow().isoformat(),
    }