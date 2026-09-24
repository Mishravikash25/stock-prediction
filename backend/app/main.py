"""
FastAPI Application Entry Point
===============================
Configures CORS middleware, health check endpoint, exception handlers,
and mounts API v1 sub-routers.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_v1_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("market_ripple_api")

app = FastAPI(
    title="Explainable AI Market Ripple Engine API",
    description="Cross-tier economic supply chain shock propagation, XGBoost multi-factor scoring, and SHAP dual-theses.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1
app.include_router(api_v1_router)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for container orchestrators and load balancers."""
    return {
        "status": "HEALTHY",
        "service": "market_ripple_backend",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception fallback handler."""
    logger.exception("Unhandled error processing %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again later."}
    )
