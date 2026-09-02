"""
LLM Client Interface & Schema-Constrained Extraction
===================================================
Provides abstract swappable LLM clients, including a strict offline deterministic
rule-based extractor and an API-compatible structured JSON schema client.
"""

from abc import ABC, abstractmethod
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from ml.nlp.schemas import EventArchetype, ExtractedEntity, LLMEventExtractionSchema

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract interface for LLM event classification."""

    @abstractmethod
    def extract_event(
        self,
        text: str,
        detected_entities: List[ExtractedEntity],
        sentiment_score: float
    ) -> LLMEventExtractionSchema:
        """Extract structured event matching LLMEventExtractionSchema from text and entities."""
        pass


class MockRuleBasedLLMClient(BaseLLMClient):
    """
    Deterministic rule-based extractor implementing the exact Pydantic schema contract.
    Used for 100% offline testing, CI/CD, and zero-token deterministic classification.
    """

    def extract_event(
        self,
        text: str,
        detected_entities: List[ExtractedEntity],
        sentiment_score: float
    ) -> LLMEventExtractionSchema:
        text_lower = text.lower()

        # Archetype Decision Logic
        archetype = EventArchetype.COMMODITY_SHOCK
        origin_id = "COMM_BRENT_CRUDE"
        origin_type = "COMMODITY"
        mechanism = "Direct commodity market volatility impacting industrial input costs."

        # 1. Macro Rate Shift Checks
        if any(k in text_lower for k in ["repo rate", "monetary policy", "interest rate", "basis points", "rbi", "federal reserve"]):
            archetype = EventArchetype.MACRO_RATE_SHIFT
            origin_id = "MACRO_RBI_REPO"
            origin_type = "MACRO"
            mechanism = "Central bank rate adjustment alters borrowing costs and consumer financing demand."

        # 2. Policy Tax / Tariff Change Checks
        elif any(k in text_lower for k in ["duty", "tariff", "tax", "gst", "subsidy", "ministry of finance", "dgft", "export duty", "import duty"]):
            archetype = EventArchetype.POLICY_TAX_CHANGE
            if any(e.entity_type == "SECTOR" for e in detected_entities):
                sec = next(e for e in detected_entities if e.entity_type == "SECTOR")
                origin_id = sec.matched_node_id
                origin_type = "SECTOR"
            elif any("steel" in e.matched_node_id.lower() or "metal" in e.matched_node_id.lower() for e in detected_entities):
                origin_id = "SEC_STEEL"
                origin_type = "SECTOR"
            else:
                origin_id = "SEC_STEEL"
                origin_type = "SECTOR"
            mechanism = "Regulatory tax policy changes export realization and shifts domestic price equilibrium."

        # 3. Supply Disruption Checks
        elif any(k in text_lower for k in ["halt", "shut", "flood", "strike", "shortage", "disrupt", "port closure", "bottleneck", "drought"]):
            archetype = EventArchetype.SUPPLY_DISRUPTION
            comm_entities = [e for e in detected_entities if e.entity_type == "COMMODITY"]
            if comm_entities:
                origin_id = comm_entities[0].matched_node_id
                origin_type = "COMMODITY"
            else:
                origin_id = "COMM_COKING_COAL"
                origin_type = "COMMODITY"
            mechanism = "Physical supply or logistical disruption restricts raw material availability for downstream manufacturers."

        # 4. Commodity Shock Checks
        else:
            archetype = EventArchetype.COMMODITY_SHOCK
            comm_entities = [e for e in detected_entities if e.entity_type == "COMMODITY"]
            if comm_entities:
                origin_id = comm_entities[0].matched_node_id
                origin_type = "COMMODITY"
            else:
                origin_id = "COMM_BRENT_CRUDE"
                origin_type = "COMMODITY"
            mechanism = "Global commodity price shock propagates directly through input procurement and product pricing."

        # Shock magnitude derived from sentiment and severity terms
        magnitude = sentiment_score
        if "plunge" in text_lower or "collapse" in text_lower or "severe" in text_lower:
            magnitude = -0.80
        elif "surge" in text_lower or "spike" in text_lower or "jump" in text_lower:
            magnitude = 0.75 if "growth" in text_lower else -0.75

        # Touched entity collections
        touched_sectors = list({e.matched_node_id for e in detected_entities if e.entity_type == "SECTOR"})
        touched_commodities = list({e.matched_node_id for e in detected_entities if e.entity_type == "COMMODITY"})
        touched_companies = list({e.matched_node_id for e in detected_entities if e.entity_type == "COMPANY"})

        # If empty, infer defaults from origin
        if origin_id == "COMM_BRENT_CRUDE" and "SEC_ENERGY" not in touched_sectors:
            touched_sectors.append("SEC_ENERGY")
            if "COMM_BRENT_CRUDE" not in touched_commodities:
                touched_commodities.append("COMM_BRENT_CRUDE")
        elif (origin_id == "COMM_COKING_COAL" or origin_id == "SEC_STEEL") and "SEC_STEEL" not in touched_sectors:
            touched_sectors.append("SEC_STEEL")
        elif origin_id == "MACRO_RBI_REPO" and "SEC_AUTO" not in touched_sectors:
            touched_sectors.append("SEC_AUTO")

        # Generate professional 1-line headline
        first_sentence = text.split(".")[0].strip()
        headline = first_sentence if len(first_sentence) < 140 else f"{first_sentence[:137]}..."

        return LLMEventExtractionSchema(
            event_title=headline,
            archetype=archetype,
            origin_node_id=origin_id,
            origin_node_type=origin_type,
            shock_magnitude=round(float(magnitude), 4),
            confidence=0.92,
            direct_transmission_mechanism=mechanism,
            touched_sectors=touched_sectors,
            touched_commodities=touched_commodities,
            touched_companies=touched_companies
        )
