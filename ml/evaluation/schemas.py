"""
Backtesting & Prediction Evaluation Schemas (Pydantic v2)
=========================================================
Strict schemas for point-in-time event replay results, directional classification metrics,
continuous error metrics (MAE/RMSE), probabilistic calibration (Brier/ECE), and horizon breakdowns.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationStatus(str, Enum):
    PENDING = "PENDING"
    EVALUATED = "EVALUATED"


class CalibrationBin(BaseModel):
    """Reliability diagram bin for confidence calibration."""
    bin_lower: float = Field(ge=0.0, le=1.0)
    bin_upper: float = Field(ge=0.0, le=1.0)
    confidence_mean: float = Field(ge=0.0, le=1.0, description="Mean predicted confidence in bin")
    accuracy_actual: float = Field(ge=0.0, le=1.0, description="Empirical fraction of correct predictions in bin")
    sample_count: int = Field(ge=0, description="Number of samples in this confidence bucket")


class HorizonEvaluationMetrics(BaseModel):
    """Comprehensive performance metrics for a specific forecast horizon (1D, 7D, or 30D)."""
    horizon_days: int = Field(description="Horizon in trading days: 1, 7, or 30")
    total_samples: int = Field(ge=0)
    evaluated_samples: int = Field(ge=0)
    pending_samples: int = Field(ge=0)

    # 1. Directional Classification Metrics
    directional_accuracy: float = Field(ge=0.0, le=1.0, description="Accuracy: (TP + TN) / Total")
    bullish_precision: float = Field(ge=0.0, le=1.0, description="Precision on Bullish calls: TP_bull / Predicted_bull")
    bullish_recall: float = Field(ge=0.0, le=1.0, description="Recall on Bullish calls: TP_bull / Actual_bull")
    bullish_f1: float = Field(ge=0.0, le=1.0)
    bearish_precision: float = Field(ge=0.0, le=1.0, description="Precision on Bearish calls: TP_bear / Predicted_bear")
    bearish_recall: float = Field(ge=0.0, le=1.0, description="Recall on Bearish calls: TP_bear / Actual_bear")
    bearish_f1: float = Field(ge=0.0, le=1.0)
    macro_f1_score: float = Field(ge=0.0, le=1.0)

    # 2. Continuous Return Estimation Error
    mae: float = Field(ge=0.0, description="Mean Absolute Error between predicted impact score and realized return")
    rmse: float = Field(ge=0.0, description="Root Mean Squared Error")
    mean_realized_return: float = Field(description="Mean realized return across horizon window")
    mean_predicted_score: float = Field(description="Mean model predicted score across horizon window")

    # 3. Probabilistic Calibration
    brier_score: float = Field(ge=0.0, le=1.0, description="Brier Score: Mean squared error of confidence vs outcome")
    expected_calibration_error: float = Field(
        ge=0.0, le=1.0,
        description="ECE: Weighted average deviation between bin confidence and empirical accuracy"
    )
    max_calibration_error: float = Field(
        ge=0.0, le=1.0,
        description="MCE: Maximum deviation across all confidence buckets"
    )
    calibration_bins: List[CalibrationBin] = Field(default_factory=list)


class ReplayEventPrediction(BaseModel):
    """Point-in-time prediction record from historical event replay."""
    event_id: str
    event_date: str
    event_archetype: str
    origin_node: str
    ticker: str
    sector: str
    horizon_days: int
    entry_price: float
    horizon_price: Optional[float] = None
    realized_return_pct: Optional[float] = None
    predicted_score: float
    predicted_direction: str
    confidence: float
    is_correct: Optional[bool] = None
    brier_score: Optional[float] = None
    shap_top_feature: Optional[str] = None


class BacktestSummaryResult(BaseModel):
    """Complete summary of a point-in-time historical backtest run."""
    backtest_id: str
    executed_at: str
    train_start_date: str
    train_end_date: str
    val_start_date: str
    val_end_date: str
    test_start_date: str
    test_end_date: str
    embargo_window_days: int
    model_type: str
    total_events_replayed: int
    total_predictions_generated: int

    # Overall Metrics Across All Horizons
    overall_directional_accuracy: float
    overall_macro_f1: float
    overall_mae: float
    overall_rmse: float
    overall_brier_score: float
    overall_ece: float

    # Stratified by Horizon
    horizon_metrics: Dict[str, HorizonEvaluationMetrics]

    # Sample Replayed Predictions
    replayed_predictions: List[ReplayEventPrediction] = Field(default_factory=list)
    verdict: str = Field(description="Engineering assessment of walk-forward generalization and calibration")
