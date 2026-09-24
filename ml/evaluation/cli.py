"""
Command-Line Interface for Point-In-Time Backtesting
====================================================
Usage:
    python -m ml.evaluation.cli --model xgboost --embargo 14
    python -m ml.evaluation.cli --model lightgbm --embargo 7 --train-start 2020-01-01
"""

import argparse
import json
import logging
import sys

from ml.evaluation.backtest_harness import PointInTimeBacktestHarness

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backtest_cli")


def main():
    parser = argparse.ArgumentParser(description="Run Point-In-Time Historical Event Replay Backtest")
    parser.add_argument("--model", type=str, default="xgboost", choices=["xgboost", "lightgbm"], help="Model architecture")
    parser.add_argument("--train-start", type=str, default="2020-01-01", help="Train start date (YYYY-MM-DD)")
    parser.add_argument("--train-end", type=str, default="2022-06-30", help="Train end date (YYYY-MM-DD)")
    parser.add_argument("--val-start", type=str, default="2022-07-01", help="Validation start date (YYYY-MM-DD)")
    parser.add_argument("--val-end", type=str, default="2022-12-31", help="Validation end date (YYYY-MM-DD)")
    parser.add_argument("--test-start", type=str, default="2023-01-01", help="Out-of-sample test start (YYYY-MM-DD)")
    parser.add_argument("--test-end", type=str, default="2023-12-31", help="Out-of-sample test end (YYYY-MM-DD)")
    parser.add_argument("--embargo", type=int, default=14, help="Embargo buffer window in days")
    parser.add_argument("--json", action="store_true", help="Output full JSON report")

    args = parser.parse_args()

    print("=" * 70)
    print(" EXPLAINABLE AI MARKET RIPPLE ENGINE — POINT-IN-TIME BACKTEST")
    print("=" * 70)
    print(f" Model Architecture : {args.model.upper()}")
    print(f" Train Window       : {args.train_start} to {args.train_end}")
    print(f" Validation Window  : {args.val_start} to {args.val_end}")
    print(f" Test (Out-of-Sample): {args.test_start} to {args.test_end}")
    print(f" Embargo Buffer     : {args.embargo} days (Strict Autocorrelation Purge)")
    print("=" * 70)

    harness = PointInTimeBacktestHarness()
    result = harness.run_walk_forward_backtest(
        train_start=args.train_start,
        train_end=args.train_end,
        val_start=args.val_start,
        val_end=args.val_end,
        test_start=args.test_start,
        test_end=args.test_end,
        embargo_days=args.embargo,
        model_type=args.model,
    )

    if args.json:
        print(json.dumps(result.model_dump(), indent=2))
        return

    print("\n--- PERFORMANCE SUMMARY BY FORECAST HORIZON ---")
    print(f"{'Horizon':<10} | {'Acc (Dir)':<10} | {'Macro F1':<10} | {'MAE':<10} | {'RMSE':<10} | {'Brier':<10} | {'ECE':<10}")
    print("-" * 75)
    for h_name, h_metrics in result.horizon_metrics.items():
        print(
            f"{h_name:<10} | "
            f"{h_metrics.directional_accuracy * 100:>8.1f}% | "
            f"{h_metrics.macro_f1_score:>10.3f} | "
            f"{h_metrics.mae:>10.4f} | "
            f"{h_metrics.rmse:>10.4f} | "
            f"{h_metrics.brier_score:>10.4f} | "
            f"{h_metrics.expected_calibration_error:>10.4f}"
        )

    print("-" * 75)
    print(f"Overall Directional Accuracy: {result.overall_directional_accuracy * 100:.1f}%")
    print(f"Overall Brier Score (MSE)   : {result.overall_brier_score:.4f}")
    print(f"Verdict: {result.verdict}")
    print("=" * 70)


if __name__ == "__main__":
    main()
