"""
NLP Event Extraction & Entity Resolution Schemas (Pydantic v2)
==============================================================
Strict Pydantic v2 validation models for NLP entity resolution,
sentiment analysis, and schema-constrained LLM event classification.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class EventArchetype(str, Enum):
    """The 4 core event archetypes approved in project constraints."""
    COMMODITY_SHOCK = "COMMODITY_SHOCK"
    POLICY_TAX_CHANGE = "POLICY_TAX_CHANGE"
    SUPPLY_DISRUPTION = "SUPPLY_DISRUPTION"
    MACRO_RATE_SHIFT = "MACRO_RATE_SHIFT"


class ExtractedEntity(BaseModel):
    """An entity detected in text and resolved to a knowledge graph node ID."""
    name: str = Field(description="Exact entity text mentioned in article")
    matched_node_id: str = Field(description="Canonical node ID from Neo4j (e.g., 'TATASTEEL.NS', 'COMM_COKING_COAL')")
    entity_type: str = Field(description="'COMPANY', 'COMMODITY', 'SECTOR', or 'MACRO'")
    confidence: float = Field(ge=0.0, le=1.0, description="Entity resolution certainty")
    mention_role: str = Field(default="DIRECT_TARGET", description="'PRIMARY_SOURCE', 'DIRECT_TARGET', or 'MENTIONED_PEER'")


class LLMEventExtractionSchema(BaseModel):
    """Strict JSON schema passed to LLM for event classification and reasoning."""
    event_title: str = Field(description="Concise 1-line professional headline of the market event")
    archetype: EventArchetype = Field(description="Primary archetype from the 4 approved categories")
    origin_node_id: str = Field(description="Root graph node triggering the shock (e.g., 'COMM_COKING_COAL', 'SEC_STEEL')")
    origin_node_type: str = Field(description="'SECTOR', 'COMMODITY', 'COMPANY', or 'MACRO'")
    shock_magnitude: float = Field(
        ge=-1.0, le=1.0,
        description="Estimated immediate direction and scale of shock (-1.0 severe negative, +1.0 severe positive)"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence score")
    direct_transmission_mechanism: str = Field(
        description="Specific economic transmission mechanism explaining immediate propagation"
    )
    touched_sectors: List[str] = Field(default_factory=list, description="List of sector IDs affected")
    touched_commodities: List[str] = Field(default_factory=list, description="List of commodity IDs affected")
    touched_companies: List[str] = Field(default_factory=list, description="List of company tickers affected")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
