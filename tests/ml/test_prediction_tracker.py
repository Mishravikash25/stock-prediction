"""
Unit Tests for Live Prediction Tracker & Outcome Scoring
========================================================
Tests:
- Point-in-time prediction logging with full explainability proof.
- Automated horizon evaluation at 1D, 7D, and 30D maturity.
- Non-cherry-picked audit summary aggregation.
"""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db.base import Base
from backend.app.models.predictions import DirectionEnum, Prediction
from backend.app.models.domain import Company
from ml.evaluation.prediction_tracker import LivePredictionTracker


@pytest.fixture
def sqlite_db_session():
    """Create in-memory SQLite database session with full schema for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    # Seed required foreign key company
    company = Company(
        ticker="TATAMOTORS.NS",
        name="Tata Motors Limited",
        sector_id="Automotive",
    )
    session.add(company)
    session.commit()

    yield session
    session.close()


def test_prediction_tracker_log_and_evaluate(sqlite_db_session: Session):
    """Verify prediction logging and automatic outcome scoring after maturity."""
    tracker = LivePredictionTracker(db_session=sqlite_db_session)
    t0 = datetime(2023, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    # 1. Log 7-day prediction
    pred = tracker.log_prediction(
        ticker="TATAMOTORS.NS",
        horizon_days=7,
        predicted_impact_score=-0.045,
        predicted_direction="BEARISH",
        confidence_score=0.85,
        actual_price_at_prediction=420.0,
        risk_label="MODERATE",
        created_at=t0,
        bull_case_text="EV volume ramp",
        bear_case_text="Steel input inflation",
        uncertainty_text="Commodity price bounds",
    )

    assert pred.prediction_id.startswith("pred_")
    assert pred.outcome_evaluated_at is None
    assert pred.actual_price_at_horizon is None

    # 2. Evaluate before maturity (day 3) -> should not evaluate
    t_early = t0 + timedelta(days=3)
    evaluated_early = tracker.evaluate_matured_predictions(current_time=t_early)
    assert len(evaluated_early) == 0

    # 3. Evaluate after maturity (day 7) -> should evaluate and score
    t_mature = t0 + timedelta(days=7, hours=1)
    
    # Custom price lookup function indicating price fell from 420 to 402 (-4.28%) -> Bearish hit!
    def price_fn(ticker: str, date: datetime) -> float:
        return 402.0

    evaluated = tracker.evaluate_matured_predictions(
        current_time=t_mature,
        price_lookup_fn=price_fn,
    )

    assert len(evaluated) == 1
    eval_rec = evaluated[0]
    assert eval_rec["prediction_id"] == pred.prediction_id
    assert eval_rec["actual_price_at_horizon"] == 402.0
    assert eval_rec["actual_return_pct"] < 0
    assert eval_rec["is_directionally_correct"] is True
    assert eval_rec["brier_score"] is not None
    # Brier score for correct prediction with 0.85 confidence = (0.85 - 1.0)^2 = 0.0225
    assert round(eval_rec["brier_score"], 4) == 0.0225

    # 4. Verify record in database is updated
    db_pred = sqlite_db_session.get(Prediction, pred.prediction_id)
    assert db_pred is not None
    assert db_pred.outcome_evaluated_at is not None
    assert db_pred.is_directionally_correct is True


def test_unbiased_audit_summary_no_cherry_picking(sqlite_db_session: Session):
    """Verify that all recorded predictions are factored into the accuracy summary without omission."""
    tracker = LivePredictionTracker(db_session=sqlite_db_session)
    t0 = datetime(2023, 2, 1, 10, 0, 0, tzinfo=timezone.utc)

    # Log 3 predictions: 2 hits, 1 miss
    # Pred 1: Bullish hit
    tracker.log_prediction(
        ticker="TATAMOTORS.NS",
        horizon_days=7,
        predicted_impact_score=0.05,
        predicted_direction="BULLISH",
        confidence_score=0.80,
        actual_price_at_prediction=400.0,
        created_at=t0,
    )
    # Pred 2: Bearish hit
    tracker.log_prediction(
        ticker="TATAMOTORS.NS",
        horizon_days=7,
        predicted_impact_score=-0.03,
        predicted_direction="BEARISH",
        confidence_score=0.75,
        actual_price_at_prediction=400.0,
        created_at=t0,
    )
    # Pred 3: Bullish miss (predicted bull, price fell)
    tracker.log_prediction(
        ticker="TATAMOTORS.NS",
        horizon_days=7,
        predicted_impact_score=0.04,
        predicted_direction="BULLISH",
        confidence_score=0.70,
        actual_price_at_prediction=400.0,
        created_at=t0,
    )

    # Advance time and evaluate with prices: 420 (+5%), 385 (-3.75%), 380 (-5%)
    prices = [420.0, 385.0, 380.0]
    call_idx = 0

    def mock_price(ticker: str, d: datetime) -> float:
        nonlocal call_idx
        p = prices[call_idx % len(prices)]
        call_idx += 1
        return p

    t_eval = t0 + timedelta(days=8)
    evaluated = tracker.evaluate_matured_predictions(current_time=t_eval, price_lookup_fn=mock_price)
    assert len(evaluated) == 3

    summary = tracker.get_unbiased_audit_summary()
    assert summary["total_predictions"] == 3
    assert summary["evaluated_predictions"] == 3
    assert summary["pending_predictions"] == 0

    # 2 hits out of 3 = 66.67% accuracy
    assert summary["horizon_7d_directional_acc"] == round(2 / 3, 4)
    assert summary["overall_directional_accuracy"] == round(2 / 3, 4)
    assert summary["overall_mae"] > 0
    assert summary["overall_rmse"] > 0
