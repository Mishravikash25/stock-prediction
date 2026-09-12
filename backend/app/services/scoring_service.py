"""
Scoring Service
===============
FastAPI service layer managing point-in-time company multi-factor feature extraction,
XGBoost model scoring, SHAP local attributions, and database prediction generation.
"""

import logging
from typing import Any, Dict, List, Optional
import pandas as pd

from backend.app.models.domain import Company
from backend.app.models.events import Event
from backend.app.models.predictions import (
    DirectionEnum,
    Prediction,
    RiskLabelEnum,
)
from ml.graph.propagation import RipplePropagationEngine
from ml.graph.schemas import RippleGraphResult
from ml.scoring.feature_builder import FeatureBuilder
from ml.scoring.model_trainer import CompanyScoringModelTrainer
from ml.scoring.schemas import CompanyPredictionOutput, CompanyScoringFeatures, ModelBenchmarkComparison

logger = logging.getLogger(__name__)


class ScoringService:
    """End-to-end service for point-in-time multi-factor company scoring and explainability."""

    def __init__(
        self,
        trainer: Optional[CompanyScoringModelTrainer] = None,
        feature_builder: Optional[FeatureBuilder] = None,
        propagation_engine: Optional[RipplePropagationEngine] = None
    ) -> None:
        self.feature_builder = feature_builder or FeatureBuilder()
        self.propagation_engine = propagation_engine or RipplePropagationEngine()
        self.trainer = trainer or CompanyScoringModelTrainer()
        self._is_initialized = False

    def ensure_model_trained(self) -> ModelBenchmarkComparison:
        """Ensure model is trained and ready for inference; trains on baseline dataset if needed."""
        if not self._is_initialized or self.trainer.xgb_model is None:
            train_df = self.feature_builder.build_synthetic_training_dataset(n_samples=1200)
            comparison = self.trainer.train_and_benchmark(train_df)
            self._is_initialized = True
            return comparison
        return self.trainer.benchmark_metrics  # type: ignore

    def score_company(
        self,
        ticker: str,
        as_of_date: str,
        event: Optional[Event] = None,
        ripple_result: Optional[RippleGraphResult] = None,
        horizon_days: int = 7
    ) -> CompanyPredictionOutput:
        """Score a single company given an event and point-in-time context."""
        self.ensure_model_trained()

        # If ripple result is not supplied but event is, compute ripple traversal
        if ripple_result is None and event is not None:
            ripple_result = self.propagation_engine.propagate(event)

        features: CompanyScoringFeatures = self.feature_builder.extract_features(
            ticker=ticker,
            as_of_date=as_of_date,
            ripple_result=ripple_result,
            event=event
        )

        return self.trainer.predict_instance(features, horizon_days=horizon_days)

    def score_all_reached_companies(
        self,
        event: Event,
        as_of_date: Optional[str] = None,
        horizon_days: int = 7
    ) -> List[CompanyPredictionOutput]:
        """Score all companies reached by the shock ripple of a given event."""
        self.ensure_model_trained()
        ripple_result = self.propagation_engine.propagate(event)
        date_str = as_of_date or str(event.occurred_at)[:10]

        predictions = []
        for ticker in ripple_result.target_impacts:
            if ticker.endswith(".NS") or ticker.endswith(".BO"):
                pred = self.score_company(
                    ticker=ticker,
                    as_of_date=date_str,
                    event=event,
                    ripple_result=ripple_result,
                    horizon_days=horizon_days
                )
                predictions.append(pred)

        logger.info("Scored %d reached companies for event %s", len(predictions), event.event_id)
        return predictions
