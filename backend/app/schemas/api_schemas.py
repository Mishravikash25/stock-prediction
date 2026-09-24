"""
API Request & Response Schemas (Pydantic v2)
=============================================
Strict validation models for FastAPI v1 REST endpoints matching /docs/architecture.md.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Events Schemas
# ---------------------------------------------------------------------------

class EventItemResponse(BaseModel):
    """Event summary in search / listing response."""
    id: str
    timestamp: str
    title: str
    archetype: str
    source_headline: str
    source_url: Optional[str] = None
    origin_node_id: str
    origin_node_type: str
    magnitude: float
    confidence: float
    sentiment_score: float
    touched_sectors: List[str] = Field(default_factory=list)
    touched_commodities: List[str] = Field(default_factory=list)


class EventListResponse(BaseModel):
    """Paginated events listing."""
    total: int
    limit: int
    offset: int
    items: List[EventItemResponse]


class EventDetailResponse(BaseModel):
    """Full single event details with extracted entity linkages."""
    id: str
    timestamp: str
    title: str
    raw_text: str
    archetype: str
    magnitude: float
    confidence: float
    sentiment_score: float
    extracted_entities: List[Dict[str, Any]] = Field(default_factory=list)
    downstream_impact_count: int = 0
    top_impacted_ticker: Optional[str] = None


class DetectEventRequest(BaseModel):
    """Ad-hoc text input for on-demand event detection."""
    text: str = Field(min_length=5, description="Financial news or announcement text to detect and classify")
    publish_timestamp: Optional[str] = Field(default=None, description="Optional ISO timestamp")
    source_name: Optional[str] = Field(default="USER_SUBMITTED", description="Source channel name")


class DetectEventResponse(BaseModel):
    """On-demand event detection output."""
    detected_event: Dict[str, Any]


# ---------------------------------------------------------------------------
# 2. Ripple & Graph Schemas
# ---------------------------------------------------------------------------

class RippleGraphNode(BaseModel):
    id: str
    label: str
    type: str
    initial_shock: Optional[float] = None
    sector: Optional[str] = None
    net_ripple_score: Optional[float] = None


class RippleGraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    strength: float
    source_tag: str
    hop: int
    path_shock: float


class ImpactSummaryItem(BaseModel):
    ticker: str
    net_ripple_score: float
    hop_distance: int
    path_description: str


class RippleGraphResponse(BaseModel):
    event_id: str
    hop_decay_alpha: float
    nodes: List[RippleGraphNode]
    edges: List[RippleGraphEdge]
    impact_summary: List[ImpactSummaryItem]


# ---------------------------------------------------------------------------
# 3. Company Analysis Schemas
# ---------------------------------------------------------------------------

class CompanyItemResponse(BaseModel):
    ticker: str
    name: str
    sector_id: str
    isin: Optional[str] = None
    market_cap_category: Optional[str] = None
    summary: Optional[str] = None


class CompanyAnalysisResponse(BaseModel):
    ticker: str
    company_name: str
    sector: str
    score_timestamp: str
    prediction: Dict[str, Any]
    shap_attributions: List[Dict[str, Any]]
    structured_report: Dict[str, Any]


class TimeSeriesPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    rolling_sentiment: float
    associated_events: List[str] = Field(default_factory=list)


class CompanyTimeSeriesResponse(BaseModel):
    ticker: str
    points: List[TimeSeriesPoint]


# ---------------------------------------------------------------------------
# 4. Predictions & Backtesting Schemas
# ---------------------------------------------------------------------------

class PredictionItemResponse(BaseModel):
    id: str
    created_at: str
    ticker: str
    event_id: Optional[str] = None
    horizon_days: int
    predicted_direction: str
    predicted_score: float
    confidence: float
    actual_price_at_prediction: float
    actual_price_at_horizon: Optional[float] = None
    actual_return_pct: Optional[float] = None
    is_correct: Optional[bool] = None
    evaluated_at: Optional[str] = None


class AccuracySummary(BaseModel):
    horizon_1d_directional_acc: float
    horizon_7d_directional_acc: float
    horizon_30d_directional_acc: float
    brier_score_7d: float


class PredictionsListResponse(BaseModel):
    total: int
    accuracy_summary: AccuracySummary
    predictions: List[PredictionItemResponse]


class BacktestRunRequest(BaseModel):
    train_start_date: str = "2020-01-01"
    train_end_date: str = "2022-06-30"
    val_start_date: str = "2022-07-01"
    val_end_date: str = "2022-12-31"
    test_start_date: str = "2023-01-01"
    test_end_date: str = "2023-12-31"
    embargo_window_days: int = 7
    model_type: str = "XGBOOST"


class BacktestJobResponse(BaseModel):
    job_id: str
    status: str
    estimated_seconds: int
