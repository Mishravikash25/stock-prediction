"""
Test Suite: Company-Level Multi-Factor Scoring & Chronological Splits
=====================================================================
Verifies:
1. Shared Chronological Splitter (zero lookahead leakage, embargo window, purging).
2. Point-in-time multi-factor feature extraction.
3. XGBoost model training and LightGBM benchmark comparison.
4. SHAP TreeExplainer additive efficiency property and ranked attributions.
5. Calibrated confidence scoring, directional classification, and risk labeling.
6. End-to-end ScoringService integration.
"""

from datetime import datetime, timezone
import math
import numpy as np
import pandas as pd
import pytest

from backend.app.models.events import Event, EventArchetype
from backend.app.services.scoring_service import ScoringService
from ml.graph.propagation import RipplePropagationEngine
from ml.graph.schemas import RippleGraphResult
from ml.scoring.explainers import ShapExplainer
from ml.scoring.feature_builder import FeatureBuilder
from ml.scoring.model_trainer import CompanyScoringModelTrainer
from ml.scoring.schemas import (
    CompanyPredictionOutput,
    CompanyScoringFeatures,
    FeatureAttribution,
    ModelBenchmarkComparison,
    PredictionDirection,
    RiskLabel,
)
from ml.scoring.split_utils import ChronologicalSplitter, DataLeakageError


@pytest.fixture
def sample_feature_df() -> pd.DataFrame:
    """Generate deterministic synthetic feature dataset for testing."""
    builder = FeatureBuilder()
    return builder.build_synthetic_training_dataset(n_samples=600, random_state=42)


@pytest.fixture
def trained_model_trainer(sample_feature_df: pd.DataFrame) -> CompanyScoringModelTrainer:
    """Provide a fitted CompanyScoringModelTrainer instance."""
    trainer = CompanyScoringModelTrainer(random_state=42)
    trainer.train_and_benchmark(
        sample_feature_df,
        train_start="2020-01-01",
        train_end="2022-06-30",
        val_start="2022-07-01",
        val_end="2022-12-31",
        test_start="2023-01-01",
        test_end="2023-12-31",
        embargo_days=7
    )
    return trainer


# =========================================================================
# 1. Chronological Splitter Integrity Tests
# =========================================================================

def test_chronological_split_monotonic_and_embargo(sample_feature_df: pd.DataFrame):
    """Verify non-overlapping chronological splits with explicit embargo buffer."""
    splitter = ChronologicalSplitter(date_column="as_of_date", embargo_days=7)
    train_df, val_df, test_df = splitter.split_by_dates(
        sample_feature_df,
        train_start="2020-01-01",
        train_end="2022-06-30",
        val_start="2022-07-01",
        val_end="2022-12-31",
        test_start="2023-01-01",
        test_end="2023-12-31"
    )

    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0

    max_train = pd.to_datetime(train_df["as_of_date"]).max()
    min_val = pd.to_datetime(val_df["as_of_date"]).min()
    max_val = pd.to_datetime(val_df["as_of_date"]).max()
    min_test = pd.to_datetime(test_df["as_of_date"]).min()

    # Assert strict monotonicity
    assert max_train < min_val
    assert max_val < min_test

    # Assert embargo buffer (at least 7 days between train end and val min, val end and test min)
    assert (min_val - max_train).days >= 7
    assert (min_test - max_val).days >= 7


def test_chronological_split_leakage_error_on_overlap(sample_feature_df: pd.DataFrame):
    """Assert DataLeakageError is raised if dates overlap or are inverted."""
    splitter = ChronologicalSplitter(date_column="as_of_date", embargo_days=7)

    # Inverted train_start and train_end
    with pytest.raises(DataLeakageError, match="must be before train end"):
        splitter.split_by_dates(
            sample_feature_df,
            train_start="2022-06-30",
            train_end="2020-01-01",
            val_start="2022-07-01",
            val_end="2022-12-31",
            test_start="2023-01-01",
            test_end="2023-12-31"
        )

    # Overlapping train_end and val_start
    with pytest.raises(DataLeakageError, match="overlaps with validation start"):
        splitter.split_by_dates(
            sample_feature_df,
            train_start="2020-01-01",
            train_end="2022-08-01",
            val_start="2022-07-01",
            val_end="2022-12-31",
            test_start="2023-01-01",
            test_end="2023-12-31"
        )


def test_walk_forward_splits_generation(sample_feature_df: pd.DataFrame):
    """Verify walk-forward splits generate expanding folds with valid chronological partitions."""
    splitter = ChronologicalSplitter(date_column="as_of_date", embargo_days=7)
    folds = list(splitter.walk_forward_splits(
        sample_feature_df,
        n_splits=3,
        min_train_days=365,
        val_days=90,
        test_days=90
    ))

    assert len(folds) == 3
    train_sizes = []
    for train_df, val_df, test_df in folds:
        assert len(train_df) > 0
        assert len(val_df) > 0
        assert len(test_df) > 0
        train_sizes.append(len(train_df))

    # Expanding window property: each fold's train set is >= previous fold
    assert train_sizes[0] <= train_sizes[1] <= train_sizes[2]


# =========================================================================
# 2. Multi-Factor Feature Builder Tests
# =========================================================================

def test_feature_builder_extract_features():
    """Verify feature builder compiles all 6 factor categories correctly."""
    builder = FeatureBuilder()
    features = builder.extract_features(
        ticker="TATAMOTORS.NS",
        as_of_date="2022-05-22"
    )

    assert isinstance(features, CompanyScoringFeatures)
    assert features.ticker == "TATAMOTORS.NS"
    assert features.as_of_date == "2022-05-22"
    assert len(features.to_feature_vector()) == len(CompanyScoringFeatures.feature_names())
    assert features.is_large_cap == 1.0
    assert 0.0 <= features.rsi_14 <= 100.0


def test_feature_builder_with_event_and_ripple():
    """Verify feature extraction incorporating event and graph ripple propagation."""
    builder = FeatureBuilder()
    engine = RipplePropagationEngine()
    
    event = Event(
        event_id="evt_test_steel",
        headline="Steel Export Duty Levied",
        raw_source_text="Government announced 15% duty.",
        source_channel="POLICY",
        archetype=EventArchetype.POLICY_TAX_CHANGE,
        origin_entity_id="SEC_STEEL",
        origin_entity_type="SECTOR",
        shock_magnitude=-0.80,
        nlp_confidence=0.95,
        finbert_sentiment=-0.70,
        llm_classification_metadata={}
    )
    ripple_result = engine.propagate(event)

    features = builder.extract_features(
        ticker="TATASTEEL.NS",
        as_of_date="2022-05-22",
        event=event,
        ripple_result=ripple_result
    )

    assert features.event_shock_magnitude == -0.80
    assert features.finbert_sentiment_3d == -0.70
    assert features.event_nlp_confidence == 0.95
    assert features.net_ripple_score < 0.0  # Headwind propagated from SEC_STEEL


# =========================================================================
# 3. XGBoost & LightGBM Model Benchmark Tests
# =========================================================================

def test_model_training_and_benchmark_comparison(trained_model_trainer: CompanyScoringModelTrainer):
    """Verify XGBoost training and side-by-side LightGBM benchmark metrics."""
    metrics = trained_model_trainer.benchmark_metrics
    assert isinstance(metrics, ModelBenchmarkComparison)
    assert metrics.features_count == 27
    assert metrics.train_samples_count > 0
    assert metrics.test_samples_count > 0

    # Verify error metrics are positive and directional accuracy is plausible
    assert metrics.xgboost_rmse > 0.0
    assert metrics.xgboost_mae > 0.0
    assert 0.0 <= metrics.xgboost_directional_accuracy <= 1.0

    assert metrics.lightgbm_rmse > 0.0
    assert metrics.lightgbm_mae > 0.0
    assert 0.0 <= metrics.lightgbm_directional_accuracy <= 1.0

    assert "XGBoost selected as primary production model" in metrics.summary_verdict


def test_company_prediction_output_ranges(trained_model_trainer: CompanyScoringModelTrainer):
    """Verify prediction output fields, bounds, and directional classification."""
    builder = FeatureBuilder()
    features = builder.extract_features("TATAMOTORS.NS", "2022-05-22")
    
    pred: CompanyPredictionOutput = trained_model_trainer.predict_instance(features, horizon_days=7)

    assert isinstance(pred, CompanyPredictionOutput)
    assert pred.ticker == "TATAMOTORS.NS"
    assert -1.0 <= pred.predicted_impact_score <= 1.0
    assert 0.0 <= pred.confidence_score <= 1.0
    assert pred.predicted_direction in [PredictionDirection.BULLISH, PredictionDirection.BEARISH, PredictionDirection.NEUTRAL]
    assert pred.risk_label in [RiskLabel.LOW, RiskLabel.MODERATE, RiskLabel.HIGH, RiskLabel.SEVERE]


# =========================================================================
# 4. SHAP TreeExplainer Feature Attribution Tests
# =========================================================================

def test_shap_additive_efficiency_property(trained_model_trainer: CompanyScoringModelTrainer):
    """
    Verify SHAP exact additive efficiency property:
    prediction = base_value + sum(shap_values)
    """
    builder = FeatureBuilder()
    features = builder.extract_features("MARUTI.NS", "2022-05-22")
    pred = trained_model_trainer.predict_instance(features, horizon_days=7)

    shap_sum = sum(a.shap_value for a in pred.feature_attributions)
    reconstructed_pred = pred.base_value + shap_sum

    # Verify reconstruction equality within numerical precision tolerance
    assert pred.predicted_impact_score == pytest.approx(reconstructed_pred, abs=5e-3)


def test_shap_driver_rankings(trained_model_trainer: CompanyScoringModelTrainer):
    """Verify SHAP attributions are correctly ranked and split into bullish/bearish drivers."""
    builder = FeatureBuilder()
    features = builder.extract_features("TATASTEEL.NS", "2022-05-22")
    pred = trained_model_trainer.predict_instance(features, horizon_days=7)

    # Verify ranks are ordered 1 to N
    ranks = [a.rank for a in pred.feature_attributions]
    assert ranks == list(range(1, len(pred.feature_attributions) + 1))

    # Verify absolute SHAP values are descending
    abs_shaps = [abs(a.shap_value) for a in pred.feature_attributions]
    for i in range(len(abs_shaps) - 1):
        assert abs_shaps[i] >= abs_shaps[i + 1]

    # Verify top bullish drivers are strictly positive
    for b in pred.top_bullish_drivers:
        assert b.shap_value > 0
        assert b.direction_influence == "BULLISH"

    # Verify top bearish drivers are strictly negative
    for b in pred.top_bearish_drivers:
        assert b.shap_value < 0
        assert b.direction_influence == "BEARISH"


# =========================================================================
# 5. ScoringService End-to-End Tests
# =========================================================================

def test_scoring_service_single_and_batch_scoring():
    """Verify ScoringService single company scoring and batch ripple scoring."""
    service = ScoringService()
    comparison = service.ensure_model_trained()
    assert comparison is not None

    event = Event(
        event_id="evt_test_oil_surge",
        occurred_at=datetime(2022, 3, 15, tzinfo=timezone.utc),
        headline="Brent Crude Surges Past $120/bbl",
        raw_source_text="Crude oil spiked amid global supply constraints.",
        source_channel="NEWS_RSS",
        archetype=EventArchetype.COMMODITY_SHOCK,
        origin_entity_id="COMM_BRENT_CRUDE",
        origin_entity_type="COMMODITY",
        shock_magnitude=0.85,
        nlp_confidence=0.95,
        finbert_sentiment=-0.65,
        llm_classification_metadata={}
    )

    # Score single company
    pred_ioc = service.score_company(
        ticker="IOC.NS",
        as_of_date="2022-03-15",
        event=event,
        horizon_days=7
    )
    assert pred_ioc.ticker == "IOC.NS"
    assert len(pred_ioc.feature_attributions) > 0

    # Score all reached companies
    batch_preds = service.score_all_reached_companies(event=event, horizon_days=7)
    assert len(batch_preds) > 0
    tickers_scored = {p.ticker for p in batch_preds}
    assert "IOC.NS" in tickers_scored or "RELIANCE.NS" in tickers_scored
