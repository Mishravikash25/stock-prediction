"""
Quantitative Evaluation & Calibration Metrics Calculator
=========================================================
Computes point-in-time financial forecasting metrics:
- Directional classification: Accuracy, Precision, Recall, F1 (Bullish/Bearish/Macro)
- Continuous return regression: MAE, RMSE, Pearson Correlation
- Probabilistic calibration: Brier Score, Expected Calibration Error (ECE), Reliability Bins
"""

import math
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np

from ml.evaluation.schemas import CalibrationBin, HorizonEvaluationMetrics


class MetricsCalculator:
    """Computes comprehensive evaluation metrics for forecast predictions vs realized outcomes."""

    @staticmethod
    def compute_directional_metrics(
        y_true_binary: Sequence[int],
        y_pred_binary: Sequence[int]
    ) -> Dict[str, float]:
        """
        Compute classification metrics for binary direction (1 = Bullish / Up, 0 = Bearish / Down).
        
        Parameters
        ----------
        y_true_binary: Sequence of 1 (actual up/bullish) or 0 (actual down/bearish)
        y_pred_binary: Sequence of 1 (predicted up/bullish) or 0 (predicted down/bearish)
        """
        if len(y_true_binary) == 0 or len(y_pred_binary) == 0:
            return {
                "accuracy": 0.0,
                "bullish_precision": 0.0,
                "bullish_recall": 0.0,
                "bullish_f1": 0.0,
                "bearish_precision": 0.0,
                "bearish_recall": 0.0,
                "bearish_f1": 0.0,
                "macro_f1": 0.0,
            }

        y_t = np.array(y_true_binary, dtype=int)
        y_p = np.array(y_pred_binary, dtype=int)
        n = len(y_t)

        tp_bull = np.sum((y_p == 1) & (y_t == 1))
        fp_bull = np.sum((y_p == 1) & (y_t == 0))
        fn_bull = np.sum((y_p == 0) & (y_t == 1))
        tn_bull = np.sum((y_p == 0) & (y_t == 0))

        accuracy = float((tp_bull + tn_bull) / n) if n > 0 else 0.0

        # Bullish class (1)
        bull_prec = float(tp_bull / (tp_bull + fp_bull)) if (tp_bull + fp_bull) > 0 else 0.0
        bull_rec = float(tp_bull / (tp_bull + fn_bull)) if (tp_bull + fn_bull) > 0 else 0.0
        bull_f1 = (
            float(2 * bull_prec * bull_rec / (bull_prec + bull_rec))
            if (bull_prec + bull_rec) > 0
            else 0.0
        )

        # Bearish class (0)
        tp_bear = tn_bull
        fp_bear = fn_bull
        fn_bear = fp_bull

        bear_prec = float(tp_bear / (tp_bear + fp_bear)) if (tp_bear + fp_bear) > 0 else 0.0
        bear_rec = float(tp_bear / (tp_bear + fn_bear)) if (tp_bear + fn_bear) > 0 else 0.0
        bear_f1 = (
            float(2 * bear_prec * bear_rec / (bear_prec + bear_rec))
            if (bear_prec + bear_rec) > 0
            else 0.0
        )

        macro_f1 = float((bull_f1 + bear_f1) / 2.0)

        return {
            "accuracy": round(accuracy, 4),
            "bullish_precision": round(bull_prec, 4),
            "bullish_recall": round(bull_rec, 4),
            "bullish_f1": round(bull_f1, 4),
            "bearish_precision": round(bear_prec, 4),
            "bearish_recall": round(bear_rec, 4),
            "bearish_f1": round(bear_f1, 4),
            "macro_f1": round(macro_f1, 4),
        }

    @staticmethod
    def compute_continuous_errors(
        y_true_returns: Sequence[float],
        y_pred_scores: Sequence[float]
    ) -> Dict[str, float]:
        """
        Compute continuous regression errors between predicted scores and actual returns.
        """
        if len(y_true_returns) == 0 or len(y_pred_scores) == 0:
            return {
                "mae": 0.0,
                "rmse": 0.0,
                "mean_realized_return": 0.0,
                "mean_predicted_score": 0.0,
            }

        y_t = np.array(y_true_returns, dtype=float)
        y_p = np.array(y_pred_scores, dtype=float)

        diff = y_p - y_t
        mae = float(np.mean(np.abs(diff)))
        rmse = float(np.sqrt(np.mean(diff ** 2)))
        mean_t = float(np.mean(y_t))
        mean_p = float(np.mean(y_p))

        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "mean_realized_return": round(mean_t, 4),
            "mean_predicted_score": round(mean_p, 4),
        }

    @staticmethod
    def compute_calibration(
        confidences: Sequence[float],
        is_correct: Sequence[bool],
        num_bins: int = 5
    ) -> Tuple[float, float, float, List[CalibrationBin]]:
        """
        Compute probabilistic calibration metrics:
        - Brier Score: MSE between predicted confidence and outcome {0, 1}
        - ECE (Expected Calibration Error): Weighted average calibration error across confidence bins
        - MCE (Maximum Calibration Error): Max absolute calibration error across bins
        - Calibration Bins: Reliability diagram bins
        """
        if len(confidences) == 0 or len(is_correct) == 0:
            return 0.0, 0.0, 0.0, []

        confs = np.array(confidences, dtype=float)
        corrects = np.array(is_correct, dtype=float)
        n = len(confs)

        # 1. Brier Score: mean((confidence - outcome)^2)
        brier_score = float(np.mean((confs - corrects) ** 2))

        # 2. Reliability diagram bins
        bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
        calibration_bins: List[CalibrationBin] = []
        ece = 0.0
        mce = 0.0

        for i in range(num_bins):
            bin_lower = float(bin_boundaries[i])
            bin_upper = float(bin_boundaries[i + 1])

            if i == num_bins - 1:
                in_bin = (confs >= bin_lower) & (confs <= bin_upper)
            else:
                in_bin = (confs >= bin_lower) & (confs < bin_upper)

            count = int(np.sum(in_bin))
            if count > 0:
                conf_mean = float(np.mean(confs[in_bin]))
                acc_actual = float(np.mean(corrects[in_bin]))
                bin_error = abs(acc_actual - conf_mean)

                ece += (count / n) * bin_error
                mce = max(mce, bin_error)

                calibration_bins.append(
                    CalibrationBin(
                        bin_lower=round(bin_lower, 2),
                        bin_upper=round(bin_upper, 2),
                        confidence_mean=round(conf_mean, 4),
                        accuracy_actual=round(acc_actual, 4),
                        sample_count=count,
                    )
                )
            else:
                calibration_bins.append(
                    CalibrationBin(
                        bin_lower=round(bin_lower, 2),
                        bin_upper=round(bin_upper, 2),
                        confidence_mean=round((bin_lower + bin_upper) / 2.0, 4),
                        accuracy_actual=0.0,
                        sample_count=0,
                    )
                )

        return (
            round(brier_score, 4),
            round(float(ece), 4),
            round(float(mce), 4),
            calibration_bins,
        )

    @classmethod
    def evaluate_horizon_dataset(
        cls,
        horizon_days: int,
        predicted_scores: Sequence[float],
        confidences: Sequence[float],
        realized_returns: Sequence[float],
        total_samples: Optional[int] = None
    ) -> HorizonEvaluationMetrics:
        """
        Compute full structured evaluation metrics for a given horizon dataset.
        """
        n_eval = len(realized_returns)
        total_count = total_samples if total_samples is not None else n_eval
        pending_count = max(0, total_count - n_eval)

        if n_eval == 0:
            return HorizonEvaluationMetrics(
                horizon_days=horizon_days,
                total_samples=total_count,
                evaluated_samples=0,
                pending_samples=pending_count,
                directional_accuracy=0.0,
                bullish_precision=0.0,
                bullish_recall=0.0,
                bullish_f1=0.0,
                bearish_precision=0.0,
                bearish_recall=0.0,
                bearish_f1=0.0,
                macro_f1_score=0.0,
                mae=0.0,
                rmse=0.0,
                mean_realized_return=0.0,
                mean_predicted_score=0.0,
                brier_score=0.0,
                expected_calibration_error=0.0,
                max_calibration_error=0.0,
                calibration_bins=[],
            )

        # Directional mapping (Threshold = 0.0 for impact score & return)
        y_true_binary = [1 if r >= 0 else 0 for r in realized_returns]
        y_pred_binary = [1 if p >= 0 else 0 for p in predicted_scores]
        is_correct = [yt == yp for yt, yp in zip(y_true_binary, y_pred_binary)]

        dir_metrics = cls.compute_directional_metrics(y_true_binary, y_pred_binary)
        cont_metrics = cls.compute_continuous_errors(realized_returns, predicted_scores)
        brier, ece, mce, cal_bins = cls.compute_calibration(confidences, is_correct)

        return HorizonEvaluationMetrics(
            horizon_days=horizon_days,
            total_samples=total_count,
            evaluated_samples=n_eval,
            pending_samples=pending_count,
            directional_accuracy=dir_metrics["accuracy"],
            bullish_precision=dir_metrics["bullish_precision"],
            bullish_recall=dir_metrics["bullish_recall"],
            bullish_f1=dir_metrics["bullish_f1"],
            bearish_precision=dir_metrics["bearish_precision"],
            bearish_recall=dir_metrics["bearish_recall"],
            bearish_f1=dir_metrics["bearish_f1"],
            macro_f1_score=dir_metrics["macro_f1"],
            mae=cont_metrics["mae"],
            rmse=cont_metrics["rmse"],
            mean_realized_return=cont_metrics["mean_realized_return"],
            mean_predicted_score=cont_metrics["mean_predicted_score"],
            brier_score=brier,
            expected_calibration_error=ece,
            max_calibration_error=mce,
            calibration_bins=cal_bins,
        )
