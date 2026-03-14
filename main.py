"""
REDS application entry point.
Run with: uvicorn main:app --reload --port 8080
"""

import uvicorn
from app.api.main import app
from app.utils.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.APP_ENV == "development",
    )