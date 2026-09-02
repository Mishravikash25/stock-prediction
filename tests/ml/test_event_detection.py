"""
Unit & Integration Tests for Event Detection (NLP) Layer
========================================================
Validates entity resolution, sentiment polarization, swappable LLM classification,
and benchmark accuracy against labeled test fixtures.
"""

import json
from pathlib import Path
from typing import List
import pytest

from backend.app.models.events import Event, EventArchetype as DBEventArchetype
from ml.nlp.entity_linker import EntityLinker
from ml.nlp.event_detector import EventDetector
from ml.nlp.llm_client import BaseLLMClient, MockRuleBasedLLMClient
from ml.nlp.schemas import EventArchetype, ExtractedEntity, LLMEventExtractionSchema
from ml.nlp.sentiment import SentimentAnalyzer

FIXTURES_PATH = Path(__file__).parent.parent / "fixtures" / "labeled_events.json"


@pytest.fixture
def labeled_events_data() -> list:
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_entity_linker_resolution() -> None:
    """Verify that EntityLinker accurately maps company, commodity, and sector text to graph node IDs."""
    linker = EntityLinker()
    text = "Tata Motors and JLR announce higher procurement from Tata Steel and JSW Steel for hot rolled coil."
    entities = linker.extract_entities(text)

    entity_ids = {e.matched_node_id for e in entities}
    assert "TATAMOTORS.NS" in entity_ids
    assert "TATASTEEL.NS" in entity_ids
    assert "JSWSTEEL.NS" in entity_ids
    assert "COMM_HRC_STEEL" in entity_ids

    # Check confidence bounds
    for e in entities:
        assert 0.80 <= e.confidence <= 1.0


def test_sentiment_analyzer_polarity() -> None:
    """Verify that sentiment analyzer returns correctly polarized values in [-1.0, 1.0]."""
    analyzer = SentimentAnalyzer(use_transformers=False)

    pos_text = "Tata Motors reports surging quarterly profit, expansion in EV margins, and strong dividend."
    neg_text = "Severe crude oil plunge and coking coal shortage trigger industrial slump and margin contraction."

    pos_score = analyzer.score(pos_text)
    neg_score = analyzer.score(neg_text)

    assert pos_score > 0.3
    assert neg_score < -0.3
    assert -1.0 <= pos_score <= 1.0
    assert -1.0 <= neg_score <= 1.0


def test_event_detector_on_labeled_fixtures(labeled_events_data: list) -> None:
    """Verify EventDetector against the labeled ground-truth fixture set across all 4 archetypes."""
    detector = EventDetector()

    for item in labeled_events_data:
        raw_text = item["raw_text"]
        expected_archetype = item["expected_archetype"]
        expected_origin = item["expected_origin_id"]
        expected_direction = item["expected_shock_direction"]

        event: Event = detector.detect(raw_text, source_channel="TEST_SUITE")

        # 1. Assert Event ORM structure
        assert isinstance(event, Event)
        assert event.event_id.startswith("evt_")
        assert event.archetype.value == expected_archetype
        assert event.origin_entity_id == expected_origin

        # 2. Assert Magnitude Direction
        if expected_direction == "NEGATIVE":
            assert event.shock_magnitude < 0
        else:
            assert event.shock_magnitude > 0

        # 3. Assert Linked Entities Presence
        linked_ids = {link.entity_id for link in event.entity_links}
        assert expected_origin in linked_ids

        # 4. Assert Confidence & Metadata Bounds
        assert 0.0 <= event.nlp_confidence <= 1.0
        assert -1.0 <= event.finbert_sentiment <= 1.0
        assert "direct_mechanism" in event.llm_classification_metadata


def test_swappable_llm_client() -> None:
    """Verify that EventDetector seamlessly accepts a swappable custom LLM backend."""
    class CustomMockLLM(BaseLLMClient):
        def extract_event(
            self,
            text: str,
            detected_entities: List[ExtractedEntity],
            sentiment_score: float
        ) -> LLMEventExtractionSchema:
            return LLMEventExtractionSchema(
                event_title="Custom Swapped Model Headline",
                archetype=EventArchetype.POLICY_TAX_CHANGE,
                origin_node_id="SEC_AUTO",
                origin_node_type="SECTOR",
                shock_magnitude=0.55,
                confidence=0.99,
                direct_transmission_mechanism="Custom test policy mechanism.",
                touched_sectors=["SEC_AUTO"]
            )

    custom_detector = EventDetector(llm_client=CustomMockLLM())
    event = custom_detector.detect("Arbitrary news article about auto components.")

    assert event.headline == "Custom Swapped Model Headline"
    assert event.archetype == DBEventArchetype.POLICY_TAX_CHANGE
    assert event.origin_entity_id == "SEC_AUTO"
    assert event.shock_magnitude == 0.55
    assert event.nlp_confidence == 0.99


def test_event_detector_validation_error() -> None:
    """Assert ValueError when passing empty string."""
    detector = EventDetector()
    with pytest.raises(ValueError):
        detector.detect("   ")
