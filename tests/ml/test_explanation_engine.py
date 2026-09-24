"""
Test Suite: Explanation Engine & Dual-Thesis Report Generation
==============================================================
Verifies:
1. Dual-thesis presence: every generated report includes both a distinct Bull and Bear case.
2. Uncertainty section: transparent analysis of model certainty, horizons, and risk regimes.
3. Zero numerical invention: output numbers match XGBoost scores and graph metrics bit-for-bit.
4. SHAP driver grounding: top catalysts and headwinds accurately reflect positive/negative SHAP values.
5. Graph source provenance citation: transmission narrative cites edge types and source tags.
6. Numerical mutation protection: ExplanationEngine rejects any altered numbers.
7. End-to-end ExplanationService pipeline and Prediction ORM generation.
"""

from datetime import datetime, timezone
import pytest

from backend.app.models.events import Event, EventArchetype
from backend.app.services.explanation_service import ExplanationService
from ml.explanation.schemas import DriverSummary, ExplanationReportSchema
from ml.explanation.thesis_generator import (
    BaseThesisGenerator,
    ExplanationEngine,
    MockRuleBasedThesisGenerator,
)
from ml.graph.propagation import RipplePropagationEngine
from ml.graph.schemas import HopEdgeProof, PathProof, TargetNodeImpact
from ml.scoring.feature_builder import FeatureBuilder
from ml.scoring.model_trainer import CompanyScoringModelTrainer
from ml.scoring.schemas import (
    CompanyPredictionOutput,
    CompanyScoringFeatures,
    FeatureAttribution,
    PredictionDirection,
    RiskLabel,
)


@pytest.fixture
def mock_prediction_output() -> CompanyPredictionOutput:
    """Create a realistic sample prediction output from Phase 3.5."""
    return CompanyPredictionOutput(
        prediction_id="pred_test_1234",
        ticker="TATAMOTORS.NS",
        as_of_timestamp="2022-05-22T00:00:00Z",
        horizon_days=7,
        predicted_impact_score=-0.2850,
        predicted_direction=PredictionDirection.BEARISH,
        confidence_score=0.8400,
        risk_label=RiskLabel.HIGH,
        base_value=0.0050,
        feature_attributions=[
            FeatureAttribution(
                feature_name="net_ripple_score",
                feature_value=-0.5500,
                shap_value=-0.1450,
                rank=1,
                direction_influence="BEARISH"
            ),
            FeatureAttribution(
                feature_name="consumed_commodity_30d_pct",
                feature_value=0.1200,
                shap_value=-0.0920,
                rank=2,
                direction_influence="BEARISH"
            ),
            FeatureAttribution(
                feature_name="return_20d",
                feature_value=0.0450,
                shap_value=0.0520,
                rank=3,
                direction_influence="BULLISH"
            ),
            FeatureAttribution(
                feature_name="operating_margin_proxy",
                feature_value=0.1200,
                shap_value=0.0180,
                rank=4,
                direction_influence="BULLISH"
            ),
        ],
        top_bullish_drivers=[
            FeatureAttribution(
                feature_name="return_20d",
                feature_value=0.0450,
                shap_value=0.0520,
                rank=3,
                direction_influence="BULLISH"
            ),
            FeatureAttribution(
                feature_name="operating_margin_proxy",
                feature_value=0.1200,
                shap_value=0.0180,
                rank=4,
                direction_influence="BULLISH"
            ),
        ],
        top_bearish_drivers=[
            FeatureAttribution(
                feature_name="net_ripple_score",
                feature_value=-0.5500,
                shap_value=-0.1450,
                rank=1,
                direction_influence="BEARISH"
            ),
            FeatureAttribution(
                feature_name="consumed_commodity_30d_pct",
                feature_value=0.1200,
                shap_value=-0.0920,
                rank=2,
                direction_influence="BEARISH"
            ),
        ],
        model_version="xgboost_v1.0"
    )


@pytest.fixture
def mock_target_impact() -> TargetNodeImpact:
    """Create a realistic sample graph target impact from Phase 3.4."""
    hop1 = HopEdgeProof(
        source_node_id="COMM_COKING_COAL",
        target_node_id="TATASTEEL.NS",
        relationship_type="CONSUMES_COMMODITY",
        strength=0.85,
        source_tag="manual_seed",
        confidence=0.95,
        cost_share_pct=0.35
    )
    hop2 = HopEdgeProof(
        source_node_id="TATASTEEL.NS",
        target_node_id="TATAMOTORS.NS",
        relationship_type="SUPPLIES_TO",
        strength=0.70,
        source_tag="manual_seed",
        confidence=0.95,
        lead_time_days=14
    )
    proof = PathProof(
        path_id="COMM_COKING_COAL->TATASTEEL.NS->TATAMOTORS.NS",
        node_sequence=["COMM_COKING_COAL", "TATASTEEL.NS", "TATAMOTORS.NS"],
        edge_sequence=[hop1, hop2],
        hop_count=2,
        raw_path_strength=0.5950,
        alpha_attenuation=0.4225,
        attenuated_impact=-0.2138,
        source_tags=["manual_seed", "manual_seed"],
        all_sources_manual=True,
        explanation_narrative="Transmits negative commodity shock downstream."
    )
    return TargetNodeImpact(
        target_node_id="TATAMOTORS.NS",
        target_node_type="COMPANY",
        target_node_name="Tata Motors Limited",
        net_ripple_score=-0.5500,
        total_paths_count=1,
        shortest_hop_distance=2,
        strongest_path_impact=-0.2138,
        path_proofs=[proof],
        edge_source_tags_present=["manual_seed"]
    )


# =========================================================================
# 1. Dual-Thesis & Uncertainty Completeness Tests
# =========================================================================

def test_dual_thesis_presence_bull_and_bear(
    mock_prediction_output: CompanyPredictionOutput,
    mock_target_impact: TargetNodeImpact
):
    """Assert every generated report contains non-empty, detailed Bull and Bear cases."""
    engine = ExplanationEngine()
    report: ExplanationReportSchema = engine.explain(
        prediction=mock_prediction_output,
        target_impact=mock_target_impact
    )

    assert isinstance(report, ExplanationReportSchema)
    assert len(report.bull_case.strip()) >= 50
    assert len(report.bear_case.strip()) >= 50
    assert report.bull_case != report.bear_case
    assert "Tata Motors" in report.bull_case or "TATAMOTORS" in report.bull_case
    assert "Tata Motors" in report.bear_case or "TATAMOTORS" in report.bear_case


def test_uncertainty_section_presence(
    mock_prediction_output: CompanyPredictionOutput,
    mock_target_impact: TargetNodeImpact
):
    """Assert every report contains a detailed uncertainty analysis."""
    engine = ExplanationEngine()
    report = engine.explain(
        prediction=mock_prediction_output,
        target_impact=mock_target_impact
    )

    assert len(report.uncertainty_section.strip()) >= 50
    assert "84.0%" in report.uncertainty_section or "confidence" in report.uncertainty_section.lower()
    assert "HIGH" in report.uncertainty_section
    assert "7-day" in report.uncertainty_section


# =========================================================================
# 2. Zero Numerical Invention / Mutation Tests
# =========================================================================

def test_zero_numerical_invention(
    mock_prediction_output: CompanyPredictionOutput,
    mock_target_impact: TargetNodeImpact
):
    """
    Verify all numeric outputs in the report match upstream models bit-for-bit.
    The explanation layer must NEVER invent or modify numbers.
    """
    engine = ExplanationEngine()
    report = engine.explain(
        prediction=mock_prediction_output,
        target_impact=mock_target_impact
    )

    assert report.predicted_impact_score == mock_prediction_output.predicted_impact_score
    assert report.predicted_direction == mock_prediction_output.predicted_direction.value
    assert report.confidence_score == mock_prediction_output.confidence_score
    assert report.risk_label == mock_prediction_output.risk_label.value
    assert report.net_ripple_score == mock_target_impact.net_ripple_score
    assert report.shortest_hop_distance == mock_target_impact.shortest_hop_distance
    assert report.horizon_days == mock_prediction_output.horizon_days


def test_numerical_mutation_protection(
    mock_prediction_output: CompanyPredictionOutput,
    mock_target_impact: TargetNodeImpact
):
    """Assert ExplanationEngine detects and raises ValueError if a generator mutates a score."""
    class MutatingThesisGenerator(BaseThesisGenerator):
        def generate_report(self, prediction, target_impact=None, event=None, company_info=None):
            normal_gen = MockRuleBasedThesisGenerator()
            rep = normal_gen.generate_report(prediction, target_impact, event, company_info)
            # Malicious / erroneous numerical hallucination
            rep.predicted_impact_score = 0.9999
            return rep

    bad_engine = ExplanationEngine(generator=MutatingThesisGenerator())
    with pytest.raises(ValueError, match="Numerical mutation detected"):
        bad_engine.explain(mock_prediction_output, mock_target_impact)


# =========================================================================
# 3. SHAP Feature Grounding & Provenance Tests
# =========================================================================

def test_shap_catalyst_and_headwind_grounding(
    mock_prediction_output: CompanyPredictionOutput,
    mock_target_impact: TargetNodeImpact
):
    """Assert SHAP drivers are accurately partitioned into catalysts and headwinds."""
    engine = ExplanationEngine()
    report = engine.explain(
        prediction=mock_prediction_output,
        target_impact=mock_target_impact
    )

    # Catalysts should contain positive SHAP drivers
    assert len(report.top_catalysts) == 2
    for cat in report.top_catalysts:
        assert cat.direction == "BULLISH"
        assert cat.impact_magnitude > 0.0

    # Headwinds should contain negative SHAP drivers
    assert len(report.top_headwinds) == 2
    for hw in report.top_headwinds:
        assert hw.direction == "BEARISH"
        assert hw.impact_magnitude > 0.0

    cat_names = [c.feature_name for c in report.top_catalysts]
    assert "return_20d" in cat_names
    assert "operating_margin_proxy" in cat_names

    hw_names = [h.feature_name for h in report.top_headwinds]
    assert "net_ripple_score" in hw_names
    assert "consumed_commodity_30d_pct" in hw_names


def test_edge_source_tag_citation_in_narrative(
    mock_prediction_output: CompanyPredictionOutput,
    mock_target_impact: TargetNodeImpact
):
    """Assert transmission narrative cites relationship type and source tags accurately."""
    engine = ExplanationEngine()
    report = engine.explain(
        prediction=mock_prediction_output,
        target_impact=mock_target_impact
    )

    narrative = report.transmission_narrative
    assert "COMM_COKING_COAL" in narrative
    assert "TATASTEEL.NS" in narrative
    assert "TATAMOTORS.NS" in narrative
    assert "CONSUMES_COMMODITY" in narrative
    assert "SUPPLIES_TO" in narrative
    assert "source: manual_seed" in narrative


# =========================================================================
# 4. End-to-End ExplanationService Integration Tests
# =========================================================================

def test_end_to_end_explanation_service_commodity_event():
    """Verify full explanation service pipeline on a live commodity shock event."""
    service = ExplanationService()
    
    event = Event(
        event_id="evt_coking_coal_spike_2022",
        occurred_at=datetime(2022, 4, 1, tzinfo=timezone.utc),
        headline="Metallurgical Coking Coal Surges to Record Highs",
        raw_source_text="Global supply shortages drove metallurgical coking coal prices higher.",
        source_channel="NEWS_RSS",
        archetype=EventArchetype.COMMODITY_SHOCK,
        origin_entity_id="COMM_COKING_COAL",
        origin_entity_type="COMMODITY",
        shock_magnitude=-0.85,
        nlp_confidence=0.95,
        finbert_sentiment=-0.75,
        llm_classification_metadata={"origin": "COMM_COKING_COAL"}
    )

    # Generate full report for Tata Steel
    report = service.generate_company_report(
        ticker="TATASTEEL.NS",
        as_of_date="2022-04-01",
        event=event,
        horizon_days=7
    )

    assert report.ticker == "TATASTEEL.NS"
    assert report.predicted_direction in ["BEARISH", "BULLISH", "NEUTRAL"]
    assert len(report.bull_case) > 50
    assert len(report.bear_case) > 50
    assert len(report.uncertainty_section) > 50
    assert len(report.transmission_narrative) > 20

    # Convert to database Prediction ORM record
    pred_output = service.scoring_service.score_company("TATASTEEL.NS", "2022-04-01", event=event)
    orm_pred = service.create_prediction_orm_model(
        report=report,
        prediction=pred_output,
        actual_price_at_prediction=110.50,
        split_id="SPLIT_TEST_V1"
    )

    assert orm_pred.prediction_id == pred_output.prediction_id
    assert orm_pred.ticker == "TATASTEEL.NS"
    assert orm_pred.bull_case_text == report.bull_case
    assert orm_pred.bear_case_text == report.bear_case
    assert orm_pred.uncertainty_text == report.uncertainty_section
    assert orm_pred.actual_price_at_prediction == 110.50
