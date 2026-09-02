"""
Event Detector Service
======================
Main interface for ingesting raw financial news / filings and outputting
validated Event ORM instances with entity links and transmission metadata.
"""

from datetime import datetime, timezone
import hashlib
import logging
from typing import List, Optional
import uuid

from backend.app.models.events import Event, EventArchetype as DBEventArchetype, EventEntityLink
from ml.nlp.entity_linker import EntityLinker
from ml.nlp.llm_client import BaseLLMClient, MockRuleBasedLLMClient
from ml.nlp.schemas import ExtractedEntity, LLMEventExtractionSchema
from ml.nlp.sentiment import SentimentAnalyzer

logger = logging.getLogger(__name__)


class EventDetector:
    """End-to-end swappable Event Detection and Classification engine."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        entity_linker: Optional[EntityLinker] = None,
        sentiment_analyzer: Optional[SentimentAnalyzer] = None
    ) -> None:
        self.llm_client = llm_client or MockRuleBasedLLMClient()
        self.entity_linker = entity_linker or EntityLinker()
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()

    def detect(
        self,
        text: str,
        occurred_at: Optional[datetime] = None,
        source_channel: str = "NEWS_RSS",
        source_url: Optional[str] = None
    ) -> Event:
        """
        Transform raw text into a fully validated Event ORM instance with linked entities.
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Input text cannot be empty")

        event_timestamp = occurred_at or datetime.now(timezone.utc)
        if event_timestamp.tzinfo is None:
            event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)

        # 1. Extract and Link Entities
        detected_entities: List[ExtractedEntity] = self.entity_linker.extract_entities(clean_text)

        # 2. Polarize Sentiment
        sentiment_score: float = self.sentiment_analyzer.score(clean_text)

        # 3. LLM Structured Extraction (Schema-Constrained)
        extraction: LLMEventExtractionSchema = self.llm_client.extract_event(
            clean_text,
            detected_entities,
            sentiment_score
        )

        # 4. Generate deterministic / traceable event ID
        hash_digest = hashlib.sha256(f"{extraction.origin_node_id}_{event_timestamp.isoformat()}_{clean_text[:60]}".encode()).hexdigest()[:8]
        event_id = f"evt_{hash_digest}"

        # 5. Assemble Event ORM model
        event = Event(
            event_id=event_id,
            occurred_at=event_timestamp,
            headline=extraction.event_title,
            raw_source_text=clean_text,
            source_channel=source_channel,
            source_url=source_url,
            archetype=DBEventArchetype(extraction.archetype.value),
            origin_entity_id=extraction.origin_node_id,
            origin_entity_type=extraction.origin_node_type,
            shock_magnitude=extraction.shock_magnitude,
            nlp_confidence=extraction.confidence,
            finbert_sentiment=sentiment_score,
            llm_classification_metadata={
                "direct_mechanism": extraction.direct_transmission_mechanism,
                "touched_sectors": extraction.touched_sectors,
                "touched_commodities": extraction.touched_commodities,
                "touched_companies": extraction.touched_companies,
                "extra": extraction.extra_metadata
            }
        )

        # 6. Assemble EventEntityLink models
        seen_entities = set()
        links: List[EventEntityLink] = []

        # Add explicitly detected entities
        for ent in detected_entities:
            if ent.matched_node_id not in seen_entities:
                seen_entities.add(ent.matched_node_id)
                role = "PRIMARY_SOURCE" if ent.matched_node_id == extraction.origin_node_id else ent.mention_role
                link = EventEntityLink(
                    event_id=event_id,
                    entity_id=ent.matched_node_id,
                    entity_type=ent.entity_type,
                    mention_role=role,
                    resolution_confidence=ent.confidence
                )
                links.append(link)

        # Add origin entity if missing from detected
        if extraction.origin_node_id not in seen_entities:
            seen_entities.add(extraction.origin_node_id)
            links.append(
                EventEntityLink(
                    event_id=event_id,
                    entity_id=extraction.origin_node_id,
                    entity_type=extraction.origin_node_type,
                    mention_role="PRIMARY_SOURCE",
                    resolution_confidence=extraction.confidence
                )
            )

        event.entity_links = links
        logger.info(
            "Detected event %s: [%s] on origin %s with magnitude %.2f (%d entities linked)",
            event.event_id,
            event.archetype.value,
            event.origin_entity_id,
            event.shock_magnitude,
            len(event.entity_links)
        )
        return event
