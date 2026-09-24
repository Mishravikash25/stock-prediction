"""
Explanation Service
===================
FastAPI service orchestrating end-to-end event ripple scoring, SHAP local
feature attribution extraction, and structured dual-thesis report generation.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from backend.app.models.domain import Company
from backend.app.models.events import Event
from backend.app.models.predictions import (
    DirectionEnum,
    Prediction,
    RiskLabelEnum,
)
from backend.app.services.graph_service import GraphService
from backend.app.services.scoring_service import ScoringService
from ml.explanation.schemas import ExplanationReportSchema
from ml.explanation.thesis_generator import ExplanationEngine
from ml.graph.schemas import RippleGraphResult, TargetNodeImpact
from ml.scoring.schemas import CompanyPredictionOutput

logger = logging.getLogger(__name__)


class ExplanationService:
    """End-to-end pipeline service producing explainable company predictions."""

    def __init__(
        self,
        scoring_service: Optional[ScoringService] = None,
        graph_service: Optional[GraphService] = None,
        explanation_engine: Optional[ExplanationEngine] = None
    ) -> None:
        self.scoring_service = scoring_service or ScoringService()
        self.graph_service = graph_service or GraphService()
        self.explanation_engine = explanation_engine or ExplanationEngine()

    def generate_company_report(
        self,
        ticker: str,
        as_of_date: str,
        event: Optional[Event] = None,
        horizon_days: int = 7
    ) -> ExplanationReportSchema:
        """Score a company and generate an audit-ready dual-thesis report."""
        # 1. Compute ripple propagation if event is present
        ripple_result: Optional[RippleGraphResult] = None
        target_impact: Optional[TargetNodeImpact] = None

        if event is not None:
            ripple_result = self.graph_service.calculate_event_ripple(event)
            target_impact = ripple_result.target_impacts.get(ticker)

        # 2. Score company with XGBoost multi-factor model
        prediction: CompanyPredictionOutput = self.scoring_service.score_company(
            ticker=ticker,
            as_of_date=as_of_date,
            event=event,
            ripple_result=ripple_result,
            horizon_days=horizon_days
        )

        # 3. Generate structured explanation report
        report = self.explanation_engine.explain(
            prediction=prediction,
            target_impact=target_impact,
            event=event
        )

        return report

    def create_prediction_orm_model(
        self,
        report: ExplanationReportSchema,
        prediction: CompanyPredictionOutput,
        actual_price_at_prediction: float = 100.0,
        split_id: Optional[str] = None
    ) -> Prediction:
        """Convert explanation report and prediction into a database-ready Prediction ORM record."""
        return Prediction(
            prediction_id=prediction.prediction_id,
            created_at=datetime.fromisoformat(f"{report.as_of_date}T00:00:00+00:00"),
            ticker=report.ticker,
            event_id=report.event_id,
            split_id=split_id,
            horizon_days=report.horizon_days,
            predicted_direction=DirectionEnum(report.predicted_direction),
            predicted_impact_score=report.predicted_impact_score,
            confidence_score=report.confidence_score,
            risk_label=RiskLabelEnum(report.risk_label),
            shap_values_json=[a.model_dump() for a in prediction.feature_attributions],
            graph_path_proof=report.model_provenance,
            bull_case_text=report.bull_case,
            bear_case_text=report.bear_case,
            uncertainty_text=report.uncertainty_section,
            actual_price_at_prediction=actual_price_at_prediction
        )
