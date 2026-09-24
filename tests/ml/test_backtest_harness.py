"""
Unit Tests for Point-In-Time Backtesting Harness & Metrics
==========================================================
Tests:
- Strict point-in-time event replay with purge & embargo windows.
- Directional classification metrics (Accuracy, Precision, Recall, Macro F1).
- Continuous regression error metrics (MAE, RMSE).
- Probabilistic calibration (Brier Score, ECE, Reliability Bins).
"""

import numpy as np
import pytest

from ml.evaluation.backtest_harness import PointInTimeBacktestHarness
from ml.evaluation.metrics import MetricsCalculator
from ml.evaluation.schemas import BacktestSummaryResult, HorizonEvaluationMetrics


def test_metrics_calculator_directional_accuracy():
    """Verify precision, recall, and directional accuracy on deterministic ground truth."""
    # Actual:  [Up,   Up,   Down, Down, Up] -> [1, 1, 0, 0, 1]
    # Predict: [Up,   Down, Down, Up,   Up] -> [1, 0, 0, 1, 1]
    # Hits: 1st (TP_bull), 3rd (TP_bear/TN_bull), 5th (TP_bull) -> 3/5 = 60.0%
    y_true = [1, 1, 0, 0, 1]
    y_pred = [1, 0, 0, 1, 1]

    metrics = MetricsCalculator.compute_directional_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 0.60
    assert metrics["bullish_precision"] == round(2 / 3, 4)
    assert metrics["bullish_recall"] == round(2 / 3, 4)
    assert metrics["bearish_precision"] == 0.50
    assert metrics["bearish_recall"] == 0.50
    assert metrics["macro_f1"] > 0.50


def test_metrics_calculator_continuous_errors():
    """Verify continuous error metrics (MAE, RMSE)."""
    # Actual:  [0.05, -0.02, 0.03, -0.04]
    # Predict: [0.04, -0.01, 0.01, -0.06]
    # diff:    [-0.01, 0.01, -0.02, -0.02]
    # abs diff: [0.01, 0.01, 0.02, 0.02] -> mean = 0.015
    # sq diff:  [0.0001, 0.0001, 0.0004, 0.0004] -> mean = 0.00025 -> sqrt = 0.0158
    y_true = [0.05, -0.02, 0.03, -0.04]
    y_pred = [0.04, -0.01, 0.01, -0.06]

    res = MetricsCalculator.compute_continuous_errors(y_true, y_pred)
    assert res["mae"] == 0.015
    assert res["rmse"] == round(np.sqrt(0.00025), 4)


def test_probabilistic_calibration_and_brier():
    """Verify Brier Score, ECE, and reliability diagram binning."""
    confidences = [0.90, 0.80, 0.70, 0.60, 0.40]
    is_correct = [True, True, False, True, False]
    # Conf: [0.9, 0.8, 0.7, 0.6, 0.4]
    # Out:  [1.0, 1.0, 0.0, 1.0, 0.0]
    # SqDiff: [0.01, 0.04, 0.49, 0.16, 0.16] -> sum = 0.86 / 5 = 0.172

    brier, ece, mce, bins = MetricsCalculator.compute_calibration(
        confidences, is_correct, num_bins=5
    )
    assert brier == 0.172
    assert 0.0 <= ece <= 1.0
    assert 0.0 <= mce <= 1.0
    assert len(bins) == 5


def test_point_in_time_backtest_harness_walk_forward():
    """Verify point-in-time backtest runs with embargo windows and returns structured results."""
    harness = PointInTimeBacktestHarness()

    result = harness.run_walk_forward_backtest(
        train_start="2020-01-01",
        train_end="2022-06-30",
        val_start="2022-07-01",
        val_end="2022-12-31",
        test_start="2023-01-01",
        test_end="2023-12-31",
        embargo_days=14,
        model_type="xgboost",
    )

    assert isinstance(result, BacktestSummaryResult)
    assert result.embargo_window_days == 14
    assert result.total_predictions_generated > 0
    assert "1D" in result.horizon_metrics
    assert "7D" in result.horizon_metrics
    assert "30D" in result.horizon_metrics

    # Check 7D horizon metrics
    m7 = result.horizon_metrics["7D"]
    assert 0.0 <= m7.directional_accuracy <= 1.0
    assert 0.0 <= m7.brier_score <= 1.0
    assert m7.mae >= 0.0
    assert m7.rmse >= 0.0
    assert len(result.replayed_predictions) > 0

    # Ensure no lookahead dates in replayed predictions
    for p in result.replayed_predictions:
        assert p.event_date >= "2023-01-01"
        assert p.event_date <= "2023-12-31"
        assert p.predicted_direction in ["BULLISH", "BEARISH"]
        assert 0.0 <= p.confidence <= 1.0
