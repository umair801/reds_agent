"""Health check endpoint."""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(redirect_slashes=False)


@router.get("/")
@router.get("")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "REDS",
        "timestamp": datetime.utcnow().isoformat(),
    }