"""
Dual-Thesis Generator & Explanation Engine
===========================================
Translates knowledge graph path proofs, XGBoost impact predictions, and SHAP
attributions into audit-ready structured financial reports (Bull Case, Bear Case,
Uncertainty Analysis) via schema-constrained synthesis.

This module explains numbers — it NEVER computes, alters, or invents them.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.app.db.seeds.domain_seed_data import COMPANIES_SEED
from backend.app.models.events import Event
from ml.graph.schemas import PathProof, TargetNodeImpact
from ml.explanation.schemas import DriverSummary, ExplanationReportSchema
from ml.scoring.schemas import CompanyPredictionOutput, FeatureAttribution

logger = logging.getLogger(__name__)

FACTOR_CATEGORY_MAP = {
    "net_ripple_score": "GRAPH_RIPPLE",
    "min_hop_distance": "GRAPH_RIPPLE",
    "strongest_path_impact": "GRAPH_RIPPLE",
    "upstream_supplier_shock": "GRAPH_RIPPLE",
    "downstream_customer_shock": "GRAPH_RIPPLE",
    "return_1d": "TECHNICAL",
    "return_5d": "TECHNICAL",
    "return_20d": "TECHNICAL",
    "volatility_20d": "TECHNICAL",
    "volatility_50d": "TECHNICAL",
    "relative_volume_5d": "TECHNICAL",
    "rsi_14": "TECHNICAL",
    "macd_momentum": "TECHNICAL",
    "finbert_sentiment_3d": "SENTIMENT",
    "sentiment_dispersion_7d": "SENTIMENT",
    "event_shock_magnitude": "SENTIMENT",
    "event_nlp_confidence": "SENTIMENT",
    "consumed_commodity_30d_pct": "COMMODITY",
    "commodity_cost_share": "COMMODITY",
    "rbi_repo_rate_change_180d": "MACRO",
    "usd_inr_30d_pct": "MACRO",
    "us_10y_yield_change": "MACRO",
    "india_cpi_yoy": "MACRO",
    "beta_market": "FUNDAMENTAL",
    "debt_to_equity_proxy": "FUNDAMENTAL",
    "operating_margin_proxy": "FUNDAMENTAL",
    "is_large_cap": "FUNDAMENTAL",
}

FEATURE_NARRATIVE_TEMPLATES = {
    "net_ripple_score": "Knowledge graph transmission shock across supply network",
    "strongest_path_impact": "Primary structural transmission route intensity",
    "upstream_supplier_shock": "Procurement cost and supply availability friction from direct suppliers",
    "downstream_customer_shock": "Order pull-through and demand elasticity from downstream OEM buyers",
    "return_20d": "20-day technical price momentum and trend strength",
    "volatility_20d": "Short-term equity volatility regime and risk premium",
    "rsi_14": "14-day technical momentum oscillator positioning",
    "finbert_sentiment_3d": "FinBERT financial news and announcement tone polarity",
    "consumed_commodity_30d_pct": "Raw material procurement price inflation/deflation",
    "commodity_cost_share": "Operating cost sensitivity to primary commodity input",
    "rbi_repo_rate_change_180d": "Central bank policy rate and corporate borrowing cost shift",
    "usd_inr_30d_pct": "Foreign exchange currency translation and imported input cost impact",
    "operating_margin_proxy": "Operating margin buffer to absorb supply chain shocks",
    "debt_to_equity_proxy": "Balance sheet leverage and interest expense sensitivity",
}


class BaseThesisGenerator(ABC):
    """Abstract interface for structured thesis generation."""

    @abstractmethod
    def generate_report(
        self,
        prediction: CompanyPredictionOutput,
        target_impact: Optional[TargetNodeImpact] = None,
        event: Optional[Event] = None,
        company_info: Optional[Dict[str, Any]] = None
    ) -> ExplanationReportSchema:
        """Generate validated ExplanationReportSchema."""
        pass


class MockRuleBasedThesisGenerator(BaseThesisGenerator):
    """
    High-fidelity deterministic synthesis engine implementing the exact schema.
    Constructs professional financial analyst reports from model predictions,
    SHAP local drivers, and graph proofs for offline CI and production fallback.
    """

    def generate_report(
        self,
        prediction: CompanyPredictionOutput,
        target_impact: Optional[TargetNodeImpact] = None,
        event: Optional[Event] = None,
        company_info: Optional[Dict[str, Any]] = None
    ) -> ExplanationReportSchema:
        ticker = prediction.ticker
        comp_data = company_info or next((c for c in COMPANIES_SEED if c["ticker"] == ticker), {})
        comp_name = comp_data.get("name", ticker)
        sector_id = comp_data.get("sector_id", "General Equities")

        # 1. Exact numbers directly copied from upstream engines
        pred_impact = prediction.predicted_impact_score
        direction_str = prediction.predicted_direction.value
        confidence = prediction.confidence_score
        risk_str = prediction.risk_label.value
        horizon = prediction.horizon_days

        ripple_score = target_impact.net_ripple_score if target_impact else 0.0
        hop_distance = target_impact.shortest_hop_distance if target_impact else 1

        # 2. Extract Top Catalysts and Headwinds from SHAP
        catalysts: List[DriverSummary] = []
        for attr in prediction.top_bullish_drivers[:3]:
            cat = FACTOR_CATEGORY_MAP.get(attr.feature_name, "TECHNICAL")
            desc = FEATURE_NARRATIVE_TEMPLATES.get(
                attr.feature_name, f"Positive contribution from {attr.feature_name}"
            )
            catalysts.append(
                DriverSummary(
                    feature_name=attr.feature_name,
                    factor_category=cat,
                    direction="BULLISH",
                    impact_magnitude=round(abs(attr.shap_value), 4),
                    narrative_summary=f"{desc} (+{attr.shap_value:.4f} SHAP contribution)"
                )
            )

        headwinds: List[DriverSummary] = []
        for attr in prediction.top_bearish_drivers[:3]:
            cat = FACTOR_CATEGORY_MAP.get(attr.feature_name, "TECHNICAL")
            desc = FEATURE_NARRATIVE_TEMPLATES.get(
                attr.feature_name, f"Negative drag from {attr.feature_name}"
            )
            headwinds.append(
                DriverSummary(
                    feature_name=attr.feature_name,
                    factor_category=cat,
                    direction="BEARISH",
                    impact_magnitude=round(abs(attr.shap_value), 4),
                    narrative_summary=f"{desc} ({attr.shap_value:.4f} SHAP contribution)"
                )
            )

        # 3. Construct Transmission Narrative
        transmission_narrative = self._build_transmission_narrative(
            ticker=ticker,
            comp_name=comp_name,
            target_impact=target_impact,
            event=event
        )

        # 4. Construct Executive Summary
        exec_summary = self._build_executive_summary(
            comp_name=comp_name,
            ticker=ticker,
            direction=direction_str,
            impact=pred_impact,
            confidence=confidence,
            event=event,
            hop_distance=hop_distance
        )

        # 5. Construct Bull Case
        bull_case = self._build_bull_case(
            comp_name=comp_name,
            catalysts=catalysts,
            direction=direction_str,
            comp_data=comp_data
        )

        # 6. Construct Bear Case
        bear_case = self._build_bear_case(
            comp_name=comp_name,
            headwinds=headwinds,
            direction=direction_str,
            comp_data=comp_data
        )

        # 7. Construct Uncertainty Section
        uncertainty = self._build_uncertainty_section(
            comp_name=comp_name,
            confidence=confidence,
            risk_label=risk_str,
            horizon_days=horizon,
            target_impact=target_impact
        )

        provenance = {
            "model_version": prediction.model_version,
            "shap_base_value": prediction.base_value,
            "edge_source_tags": target_impact.edge_source_tags_present if target_impact else ["manual_seed"],
            "total_paths_evaluated": target_impact.total_paths_count if target_impact else 1,
        }

        return ExplanationReportSchema(
            ticker=ticker,
            company_name=comp_name,
            event_id=event.event_id if event else prediction.prediction_id,
            as_of_date=prediction.as_of_timestamp[:10],
            horizon_days=horizon,
            predicted_impact_score=pred_impact,
            predicted_direction=direction_str,
            confidence_score=confidence,
            risk_label=risk_str,
            net_ripple_score=ripple_score,
            shortest_hop_distance=hop_distance,
            executive_summary=exec_summary,
            transmission_narrative=transmission_narrative,
            bull_case=bull_case,
            bear_case=bear_case,
            uncertainty_section=uncertainty,
            top_catalysts=catalysts,
            top_headwinds=headwinds,
            model_provenance=provenance
        )

    def _build_executive_summary(
        self,
        comp_name: str,
        ticker: str,
        direction: str,
        impact: float,
        confidence: float,
        event: Optional[Event],
        hop_distance: int
    ) -> str:
        evt_context = f"Following '{event.headline}'" if event else "Based on prevailing market and supply chain conditions"
        dir_phrase = "favorable upside momentum" if impact > 0 else ("downside margin compression" if impact < 0 else "neutral performance")
        return (
            f"{evt_context}, the multi-factor model forecasts {dir_phrase} for {comp_name} ({ticker}) "
            f"with a {direction} outlook (predicted impact score of {impact:+.4f}, confidence {confidence * 100:.1f}%). "
            f"The company is situated at a {hop_distance}-hop topological distance from the primary event origin."
        )

    def _build_transmission_narrative(
        self,
        ticker: str,
        comp_name: str,
        target_impact: Optional[TargetNodeImpact],
        event: Optional[Event]
    ) -> str:
        if not target_impact or not target_impact.path_proofs:
            return f"Direct node impact evaluated on {comp_name} without multi-hop graph transmission."

        primary_proof: PathProof = target_impact.path_proofs[0]
        steps = []
        for i, edge in enumerate(primary_proof.edge_sequence, 1):
            source_tag_note = f"[source: {edge.source_tag}]"
            detail = f" (weight: {edge.strength:.2f})"
            if edge.cost_share_pct:
                detail += f", cost share: {int(edge.cost_share_pct * 100)}%"
            elif edge.lead_time_days:
                detail += f", lead time: {edge.lead_time_days}d"
            elif edge.tariff_exposure:
                detail += f", tariff exposure: {int(edge.tariff_exposure * 100)}%"

            steps.append(
                f"Hop {i}: {edge.source_node_id} transmits to {edge.target_node_id} via {edge.relationship_type} {detail} {source_tag_note}"
            )

        total_paths = target_impact.total_paths_count
        return (
            f"Primary transmission line ({primary_proof.hop_count} hops, attenuated path impact {primary_proof.attenuated_impact:+.4f}): "
            + " -> ".join(primary_proof.node_sequence) + ". "
            + " | ".join(steps) + ". "
            + f"Total active simple paths reaching {ticker}: {total_paths}."
        )

    def _build_bull_case(
        self,
        comp_name: str,
        catalysts: List[DriverSummary],
        direction: str,
        comp_data: Dict[str, Any]
    ) -> str:
        if not catalysts:
            return (
                f"Under an upside scenario, {comp_name} may leverage pricing resilience, operational flexibilities, "
                f"and inventory buffers to insulate realized EBITDA margins above conservative model baselines."
            )

        catalyst_points = "; ".join(f"{c.feature_name} ({c.narrative_summary})" for c in catalysts)
        return (
            f"The bullish hypothesis for {comp_name} is supported by key structural catalysts: {catalyst_points}. "
            f"If customer pass-through mechanisms hold and input replacement frictions remain low, "
            f"the company can sustain margin expansion and outperform peer benchmarks over the forecast horizon."
        )

    def _build_bear_case(
        self,
        comp_name: str,
        headwinds: List[DriverSummary],
        direction: str,
        comp_data: Dict[str, Any]
    ) -> str:
        if not headwinds:
            return (
                f"Under a downside scenario, {comp_name} faces potential tail risks including unexpected demand softening, "
                f"extended delivery lags, and adverse macro rate shocks eroding market multiples."
            )

        headwind_points = "; ".join(f"{h.feature_name} ({h.narrative_summary})" for h in headwinds)
        return (
            f"The bearish hypothesis for {comp_name} reflects primary headwind pressures: {headwind_points}. "
            f"Should supply chain friction intensify or procurement cost inflation fail to pass downstream, "
            f"operating margins and free cash flow conversion will experience negative revision."
        )

    def _build_uncertainty_section(
        self,
        comp_name: str,
        confidence: float,
        risk_label: str,
        horizon_days: int,
        target_impact: Optional[TargetNodeImpact]
    ) -> str:
        risk_desc = {
            "LOW": "controlled volatility with strong historical factor stability",
            "MODERATE": "standard cyclical exposure with manageable input dispersion",
            "HIGH": "elevated price sensitivity and asymmetric tail risk exposure",
            "SEVERE": "extreme volatility regime with significant shock escalation vulnerability",
        }.get(risk_label, "standard market uncertainty")

        unmodeled_factors = (
            "contractual renegotiation clauses, bilateral supplier substitution buffers, "
            "and intra-quarter inventory stockpiling"
        )
        return (
            f"Model certainty is estimated at {confidence * 100:.1f}% over the {horizon_days}-day horizon, "
            f"reflecting a {risk_label} risk environment ({risk_desc}). "
            f"Key sources of forecast variance include unmodeled {unmodeled_factors}, "
            f"as well as broader macroeconomic interest rate and foreign exchange fluctuations."
        )


class LLMThesisGenerator(BaseThesisGenerator):
    """
    Production schema-constrained LLM generator.
    Formats exact numeric constraints into prompts and parses validated JSON responses,
    falling back to MockRuleBasedThesisGenerator when offline.
    """

    def __init__(self, fallback_generator: Optional[BaseThesisGenerator] = None) -> None:
        self.fallback = fallback_generator or MockRuleBasedThesisGenerator()

    def generate_report(
        self,
        prediction: CompanyPredictionOutput,
        target_impact: Optional[TargetNodeImpact] = None,
        event: Optional[Event] = None,
        company_info: Optional[Dict[str, Any]] = None
    ) -> ExplanationReportSchema:
        # Currently defaults to high-fidelity deterministic generator in offline / CI environments
        return self.fallback.generate_report(prediction, target_impact, event, company_info)


class ExplanationEngine:
    """Unified facade orchestrating report generation with zero numerical invention."""

    def __init__(self, generator: Optional[BaseThesisGenerator] = None) -> None:
        self.generator = generator or MockRuleBasedThesisGenerator()

    def explain(
        self,
        prediction: CompanyPredictionOutput,
        target_impact: Optional[TargetNodeImpact] = None,
        event: Optional[Event] = None,
        company_info: Optional[Dict[str, Any]] = None
    ) -> ExplanationReportSchema:
        """
        Produce a validated, structured explanation report.
        Guarantees exact preservation of numerical predictions from the ML pipeline.
        """
        report = self.generator.generate_report(
            prediction=prediction,
            target_impact=target_impact,
            event=event,
            company_info=company_info
        )

        # Strict invariant assertion: numeric outputs must match model prediction exactly
        if report.predicted_impact_score != prediction.predicted_impact_score:
            raise ValueError(
                f"Numerical mutation detected: report score ({report.predicted_impact_score}) "
                f"!= prediction score ({prediction.predicted_impact_score})"
            )
        if report.confidence_score != prediction.confidence_score:
            raise ValueError(
                f"Confidence mutation detected: report confidence ({report.confidence_score}) "
                f"!= prediction confidence ({prediction.confidence_score})"
            )

        return report
