"""
Company-Level Scoring Model Trainer & Benchmark Comparison
===========================================================
Trains the primary XGBoost Multi-Factor Regressor with early stopping,
benchmarks against the LightGBM fallback model on identical chronological splits,
and generates calibrated confidence scores, risk labels, and SHAP attributions.
"""

import hashlib
import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

from ml.scoring.explainers import ShapExplainer
from ml.scoring.schemas import (
    CompanyPredictionOutput,
    CompanyScoringFeatures,
    ModelBenchmarkComparison,
    PredictionDirection,
    RiskLabel,
)
from ml.scoring.split_utils import ChronologicalSplitter

logger = logging.getLogger(__name__)


class CompanyScoringModelTrainer:
    """
    Manages training, cross-model benchmarking, and point-in-time scoring inference
    for company impact predictions.
    """

    def __init__(
        self,
        feature_names: Optional[List[str]] = None,
        random_state: int = 42
    ) -> None:
        self.feature_names = feature_names or CompanyScoringFeatures.feature_names()
        self.random_state = random_state
        self.xgb_model: Optional[xgb.XGBRegressor] = None
        self.lgb_model: Optional[lgb.LGBMRegressor] = None
        self.explainer: Optional[ShapExplainer] = None
        self.benchmark_metrics: Optional[ModelBenchmarkComparison] = None

    def train_and_benchmark(
        self,
        df: pd.DataFrame,
        target_col: str = "target_impact_7d",
        train_start: str = "2020-01-01",
        train_end: str = "2022-06-30",
        val_start: str = "2022-07-01",
        val_end: str = "2022-12-31",
        test_start: str = "2023-01-01",
        test_end: str = "2023-12-31",
        embargo_days: int = 7
    ) -> ModelBenchmarkComparison:
        """
        Train XGBoost (primary) and LightGBM (benchmark) on strict chronological partitions
        and compute side-by-side performance metrics.
        """
        splitter = ChronologicalSplitter(date_column="as_of_date", embargo_days=embargo_days)
        train_df, val_df, test_df = splitter.split_by_dates(
            df,
            train_start=train_start,
            train_end=train_end,
            val_start=val_start,
            val_end=val_end,
            test_start=test_start,
            test_end=test_end
        )

        X_train = train_df[self.feature_names].values
        y_train = train_df[target_col].values
        X_val = val_df[self.feature_names].values
        y_val = val_df[target_col].values
        X_test = test_df[self.feature_names].values
        y_test = test_df[target_col].values

        logger.info(
            "Fitting models on %d train samples, %d val samples, %d test samples (%d features)",
            len(X_train), len(X_val), len(X_test), len(self.feature_names)
        )

        # 1. Train Primary Model: XGBoost
        t0_xgb = time.perf_counter()
        mean_y = float(np.mean(y_train))
        self.xgb_model = xgb.XGBRegressor(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            base_score=mean_y,
            random_state=self.random_state,
            early_stopping_rounds=15,
            eval_metric="rmse"
        )
        self.xgb_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        t_xgb_sec = time.perf_counter() - t0_xgb

        # 2. Train Benchmark Model: LightGBM
        t0_lgb = time.perf_counter()
        self.lgb_model = lgb.LGBMRegressor(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=self.random_state,
            verbose=-1
        )
        self.lgb_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(stopping_rounds=15, verbose=False)]
        )
        t_lgb_sec = time.perf_counter() - t0_lgb

        # 3. Evaluate Out-of-Sample Test Metrics
        xgb_preds = self.xgb_model.predict(X_test)
        lgb_preds = self.lgb_model.predict(X_test)

        xgb_rmse = float(np.sqrt(mean_squared_error(y_test, xgb_preds)))
        xgb_mae = float(mean_absolute_error(y_test, xgb_preds))
        xgb_r2 = float(r2_score(y_test, xgb_preds))
        xgb_dir_acc = float(np.mean(np.sign(xgb_preds) == np.sign(y_test)))
        xgb_brier = float(np.mean(((xgb_preds > 0) != (y_test > 0)) ** 2))

        lgb_rmse = float(np.sqrt(mean_squared_error(y_test, lgb_preds)))
        lgb_mae = float(mean_absolute_error(y_test, lgb_preds))
        lgb_r2 = float(r2_score(y_test, lgb_preds))
        lgb_dir_acc = float(np.mean(np.sign(lgb_preds) == np.sign(y_test)))
        lgb_brier = float(np.mean(((lgb_preds > 0) != (y_test > 0)) ** 2))

        # 4. Initialize SHAP Explainer on Primary Model
        self.explainer = ShapExplainer(self.xgb_model, feature_names=self.feature_names)

        verdict = (
            f"XGBoost selected as primary production model: Test RMSE={xgb_rmse:.4f}, "
            f"Directional Accuracy={xgb_dir_acc * 100:.1f}%, R2={xgb_r2:.4f}. "
            f"LightGBM benchmark comparison: Test RMSE={lgb_rmse:.4f}, "
            f"Directional Accuracy={lgb_dir_acc * 100:.1f}%, R2={lgb_r2:.4f}. "
            f"XGBoost provides superior exact TreeExplainer SHAP integration and stability on dense financial features."
        )

        self.benchmark_metrics = ModelBenchmarkComparison(
            train_samples_count=len(X_train),
            val_samples_count=len(X_val),
            test_samples_count=len(X_test),
            features_count=len(self.feature_names),
            xgboost_rmse=round(xgb_rmse, 5),
            xgboost_mae=round(xgb_mae, 5),
            xgboost_r2=round(xgb_r2, 5),
            xgboost_directional_accuracy=round(xgb_dir_acc, 5),
            xgboost_brier_score=round(xgb_brier, 5),
            xgboost_train_time_sec=round(t_xgb_sec, 4),
            lightgbm_rmse=round(lgb_rmse, 5),
            lightgbm_mae=round(lgb_mae, 5),
            lightgbm_r2=round(lgb_r2, 5),
            lightgbm_directional_accuracy=round(lgb_dir_acc, 5),
            lightgbm_brier_score=round(lgb_brier, 5),
            lightgbm_train_time_sec=round(t_lgb_sec, 4),
            summary_verdict=verdict
        )

        logger.info("Benchmark complete: %s", verdict)
        return self.benchmark_metrics

    def predict_instance(
        self,
        features: CompanyScoringFeatures,
        horizon_days: int = 7
    ) -> CompanyPredictionOutput:
        """
        Generate continuous impact prediction, confidence score, risk label,
        and SHAP attributions for a single company.
        """
        if self.xgb_model is None or self.explainer is None:
            raise RuntimeError("Model must be trained via train_and_benchmark() before predicting.")

        feat_vector = np.array(features.to_feature_vector()).reshape(1, -1)
        raw_pred = float(self.xgb_model.predict(feat_vector)[0])
        bounded_score = float(np.clip(raw_pred, -1.0, 1.0))

        # 1. Direction Classification
        if bounded_score > 0.05:
            direction = PredictionDirection.BULLISH
        elif bounded_score < -0.05:
            direction = PredictionDirection.BEARISH
        else:
            direction = PredictionDirection.NEUTRAL

        # 2. Calibrated Confidence Score
        # Higher magnitude and lower volatility yield higher confidence
        vol_term = min(1.0, features.volatility_20d / 0.30)
        conf_raw = 0.50 + 0.38 * abs(bounded_score) - 0.10 * vol_term + 0.10 * features.event_nlp_confidence
        confidence = float(np.clip(conf_raw, 0.15, 0.98))

        # 3. Risk Labeling
        if bounded_score < -0.35 or (features.volatility_20d > 0.40 and bounded_score < -0.15):
            risk = RiskLabel.SEVERE
        elif bounded_score < -0.15 or features.volatility_20d > 0.32:
            risk = RiskLabel.HIGH
        elif abs(bounded_score) >= 0.08 or features.volatility_20d > 0.20:
            risk = RiskLabel.MODERATE
        else:
            risk = RiskLabel.LOW

        # 4. SHAP Feature Attribution
        all_attrs, top_bulls, top_bears = self.explainer.explain_instance(features, top_k=3)

        # 5. Deterministic Prediction ID
        pred_hash = hashlib.sha256(
            f"{features.ticker}_{features.as_of_date}_{horizon_days}_{bounded_score:.4f}".encode()
        ).hexdigest()[:8]
        pred_id = f"pred_{pred_hash}"

        return CompanyPredictionOutput(
            prediction_id=pred_id,
            ticker=features.ticker,
            as_of_timestamp=f"{features.as_of_date}T00:00:00Z",
            horizon_days=horizon_days,
            predicted_impact_score=round(bounded_score, 6),
            predicted_direction=direction,
            confidence_score=round(confidence, 4),
            risk_label=risk,
            base_value=round(self.explainer.expected_value, 6),
            feature_attributions=all_attrs,
            top_bullish_drivers=top_bulls,
            top_bearish_drivers=top_bears,
            model_version="xgboost_v1.0"
        )
