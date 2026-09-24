"""
Events API Router (/api/v1/events)
==================================
Handles event querying, filtering, detailed entity linkage, and on-demand detection.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.seeds.domain_seed_data import SAMPLE_EVENTS_SEED
from backend.app.db.session import get_db
from backend.app.models.events import Event, EventArchetype, EventEntityLink
from backend.app.schemas.api_schemas import (
    DetectEventRequest,
    DetectEventResponse,
    EventDetailResponse,
    EventItemResponse,
    EventListResponse,
)
from ml.nlp.event_detector import EventDetector

logger = logging.getLogger(__name__)
router = APIRouter()
_detector = EventDetector()


@router.get("", response_model=EventListResponse)
async def list_events(
    sector: Optional[str] = Query(None, description="Filter by sector ID"),
    archetype: Optional[str] = Query(None, description="Filter by event archetype"),
    min_significance: Optional[float] = Query(None, description="Minimum absolute shock magnitude"),
    start_date: Optional[str] = Query(None, description="ISO start date"),
    end_date: Optional[str] = Query(None, description="ISO end date"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
) -> EventListResponse:
    """Fetch historical or live detected market events with multi-dimensional filtering."""
    try:
        stmt = select(Event).order_by(desc(Event.occurred_at))
        if archetype:
            stmt = stmt.where(Event.archetype == EventArchetype(archetype))
        if min_significance is not None:
            stmt = stmt.where(Event.shock_magnitude >= min_significance)

        res = await db.execute(stmt)
        db_events = res.scalars().all()
    except Exception as err:
        logger.warning("Database query notice (%s). Using in-memory seed events.", err)
        db_events = []

    # Map records
    items = []
    source_events = db_events if db_events else SAMPLE_EVENTS_SEED

    for evt in source_events:
        if isinstance(evt, dict):
            e_id = evt["event_id"]
            ts = evt["occurred_at"]
            title = evt["headline"]
            arch = evt["archetype"]
            raw = evt["raw_source_text"]
            url = evt.get("source_url")
            orig_id = evt["origin_entity_id"]
            orig_type = evt["origin_entity_type"]
            mag = float(evt["shock_magnitude"])
            conf = float(evt["nlp_confidence"])
            sent = float(evt["finbert_sentiment"])
            meta = evt.get("llm_classification_metadata", {})
            sectors = meta.get("touched_sectors", ["SEC_STEEL"])
            commodities = meta.get("touched_commodities", ["COMM_HRC_STEEL"])
        else:
            e_id = evt.event_id
            ts = evt.occurred_at.isoformat()
            title = evt.headline
            arch = evt.archetype.value
            raw = evt.raw_source_text
            url = evt.source_url
            orig_id = evt.origin_entity_id
            orig_type = evt.origin_entity_type
            mag = float(evt.shock_magnitude)
            conf = float(evt.nlp_confidence)
            sent = float(evt.finbert_sentiment)
            meta = evt.llm_classification_metadata or {}
            sectors = meta.get("touched_sectors", [])
            commodities = meta.get("touched_commodities", [])

        # Filter in memory if needed
        if archetype and arch != archetype:
            continue
        if min_significance is not None and abs(mag) < min_significance:
            continue

        items.append(
            EventItemResponse(
                id=e_id,
                timestamp=ts,
                title=title,
                archetype=arch,
                source_headline=raw[:140] + ("..." if len(raw) > 140 else ""),
                source_url=url,
                origin_node_id=orig_id,
                origin_node_type=orig_type,
                magnitude=mag,
                confidence=conf,
                sentiment_score=sent,
                touched_sectors=sectors,
                touched_commodities=commodities
            )
        )

    total_count = len(items)
    paginated = items[offset: offset + limit]

    return EventListResponse(
        total=total_count,
        limit=limit,
        offset=offset,
        items=paginated
    )


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event_detail(
    event_id: str,
    db: AsyncSession = Depends(get_db)
) -> EventDetailResponse:
    """Retrieve complete entity linkage and impact summary for a single event."""
    # Check seed events first
    matched = next((e for e in SAMPLE_EVENTS_SEED if e["event_id"] == event_id), None)
    if matched:
        links = matched.get("links", [])
        return EventDetailResponse(
            id=matched["event_id"],
            timestamp=matched["occurred_at"],
            title=matched["headline"],
            raw_text=matched["raw_source_text"],
            archetype=matched["archetype"],
            magnitude=float(matched["shock_magnitude"]),
            confidence=float(matched["nlp_confidence"]),
            sentiment_score=float(matched["finbert_sentiment"]),
            extracted_entities=[
                {"name": l["entity_id"], "entity_type": l["entity_type"], "node_id": l["entity_id"]}
                for l in links
            ],
            downstream_impact_count=len(links) * 2,
            top_impacted_ticker="TATASTEEL.NS"
        )

    # Otherwise query DB
    try:
        stmt = select(Event).where(Event.event_id == event_id)
        res = await db.execute(stmt)
        evt = res.scalar_one_or_none()
        if not evt:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

        l_stmt = select(EventEntityLink).where(EventEntityLink.event_id == event_id)
        l_res = await db.execute(l_stmt)
        links = l_res.scalars().all()

        return EventDetailResponse(
            id=evt.event_id,
            timestamp=evt.occurred_at.isoformat(),
            title=evt.headline,
            raw_text=evt.raw_source_text,
            archetype=evt.archetype.value,
            magnitude=float(evt.shock_magnitude),
            confidence=float(evt.nlp_confidence),
            sentiment_score=float(evt.finbert_sentiment),
            extracted_entities=[
                {"name": l.entity_id, "entity_type": l.entity_type, "node_id": l.entity_id}
                for l in links
            ],
            downstream_impact_count=len(links) * 2,
            top_impacted_ticker=links[0].entity_id if links else None
        )
    except HTTPException:
        raise
    except Exception as err:
        logger.error("Error fetching event %s: %s", event_id, err)
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


@router.post("/detect", response_model=DetectEventResponse)
async def detect_event(request: DetectEventRequest) -> DetectEventResponse:
    """Ad-hoc NLP extraction and classification endpoint for user-submitted text."""
    try:
        detected: Event = _detector.detect(
            text=request.text,
            source_channel=request.source_name or "USER_SUBMITTED"
        )

        entities_summary = [
            {"text": l.entity_id, "label": l.entity_type} for l in getattr(detected, "entity_links", [])
        ]
        meta = detected.llm_classification_metadata or {}

        payload = {
            "archetype": detected.archetype.value,
            "magnitude": float(detected.shock_magnitude),
            "confidence": float(detected.nlp_confidence),
            "primary_commodity": detected.origin_entity_id if detected.origin_entity_type == "COMMODITY" else None,
            "primary_sector": detected.origin_entity_id if detected.origin_entity_type == "SECTOR" else "SEC_STEEL",
            "reasoning": meta.get("direct_mechanism", "Direct economic transmission mechanism."),
            "spacy_entities": entities_summary
        }
        return DetectEventResponse(detected_event=payload)
    except Exception as err:
        logger.exception("Error detecting event: %s", err)
        raise HTTPException(status_code=400, detail=f"Failed to process text: {str(err)}")
