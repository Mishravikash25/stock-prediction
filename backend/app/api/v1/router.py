"""
API v1 Router
=============
Aggregates and mounts all v1 sub-routers for Events, Ripple Graph, Companies, and Predictions.
"""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import companies, events, predictions, ripple

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(events.router, prefix="/events", tags=["Events"])
api_v1_router.include_router(ripple.router, prefix="/ripple", tags=["Ripple Graph"])
api_v1_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_v1_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions & Backtesting"])
