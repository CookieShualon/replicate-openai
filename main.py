from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import HOST, PORT
from app.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Replicate OpenAI Gateway",
    description=(
        "An OpenAI-compatible API gateway that routes requests to Replicate-hosted models. "
        "Point any OpenAI SDK client at this server using base_url='http://localhost:8000/v1'."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow all origins so browser-based OpenAI clients work out of the box.
# Tighten this in production.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount the OpenAI-compatible router under /v1
# ---------------------------------------------------------------------------
app.include_router(router, prefix="/v1")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/", tags=["health"])
async def health_check() -> dict:
    """Basic health check — returns service name and status."""
    return {
        "status": "ok",
        "service": "replicate-openai-gateway",
        "docs": "/docs",
        "openai_base_url": f"http://{HOST}:{PORT}/v1",
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting Replicate OpenAI Gateway on %s:%s", HOST, PORT)
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
