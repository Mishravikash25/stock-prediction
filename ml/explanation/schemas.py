"""
Explanation Engine Schemas (Pydantic v2)
========================================
Strict validation models for structured dual-thesis reports, transmission narratives,
bull/bear cases, uncertainty analyses, and factor catalyst/headwind summaries.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DriverSummary(BaseModel):
    """Summary of a key factor driver derived from SHAP attributions."""
    feature_name: str = Field(description="Canonical feature name (e.g. 'net_ripple_score', 'return_20d')")
    factor_category: str = Field(description="'GRAPH_RIPPLE', 'TECHNICAL', 'SENTIMENT', 'COMMODITY', 'MACRO', or 'FUNDAMENTAL'")
    direction: str = Field(description="'BULLISH' or 'BEARISH'")
    impact_magnitude: float = Field(description="Exact absolute Shapley attribution magnitude")
    narrative_summary: str = Field(description="Concise 1-line business explanation of this factor's influence")


class ExplanationReportSchema(BaseModel):
    """
    Complete audit-ready financial report for a company prediction.
    Strictly explains numbers without inventing, overriding, or calculating them.
    """
    ticker: str = Field(description="Target equity ticker (e.g. 'TATAMOTORS.NS')")
    company_name: str = Field(description="Canonical company name")
    event_id: Optional[str] = Field(default=None, description="Linked event ID if generated in response to an event")
    as_of_date: str = Field(description="Point-in-time timestamp YYYY-MM-DD")
    horizon_days: int = Field(default=7, description="Forecast horizon (1, 7, or 30 days)")

    # Model Invariants (Exact numbers passed directly from scoring and graph engines)
    predicted_impact_score: float = Field(
        ge=-1.0, le=1.0,
        description="Continuous predicted price impact in [-1.0, 1.0]"
    )
    predicted_direction: str = Field(
        description="'BULLISH', 'BEARISH', or 'NEUTRAL'"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Calibrated model certainty in [0.0, 1.0]"
    )
    risk_label: str = Field(
        description="'LOW', 'MODERATE', 'HIGH', or 'SEVERE'"
    )
    net_ripple_score: float = Field(
        ge=-1.0, le=1.0,
        description="Aggregated graph ripple score R(v) from knowledge graph traversal"
    )
    shortest_hop_distance: int = Field(
        ge=1,
        description="Shortest transmission graph hop distance from event origin"
    )

    # Structured Language Sections
    executive_summary: str = Field(
        description="Concise 2-3 sentence overview connecting origin event to company outcome"
    )
    transmission_narrative: str = Field(
        description="Step-by-step prose detailing the exact graph path, edge types, and source tags"
    )
    bull_case: str = Field(
        description="Detailed upside thesis grounded in positive SHAP drivers and catalysts"
    )
    bear_case: str = Field(
        description="Detailed downside thesis grounded in negative SHAP drivers and headwinds"
    )
    uncertainty_section: str = Field(
        description="Transparent analysis of model assumptions, macro volatility, and tail risks"
    )

    # Catalysts & Headwinds
    top_catalysts: List[DriverSummary] = Field(
        default_factory=list,
        description="Top positive factor drivers"
    )
    top_headwinds: List[DriverSummary] = Field(
        default_factory=list,
        description="Top negative factor drivers"
    )

    model_provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata tracking model version, SHAP base value, and edge source attribution"
    )
