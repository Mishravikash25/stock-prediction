"""
Scoring & ML Feature Store Schemas (Pydantic v2)
================================================
Strict validation models for point-in-time multi-factor feature sets,
SHAP feature attributions, model benchmark comparisons, and forward predictions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredictionDirection(str, Enum):
    """Categorical price impact direction."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class RiskLabel(str, Enum):
    """Calibrated tail risk exposure level."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class FeatureAttribution(BaseModel):
    """Individual feature contribution derived from SHAP TreeExplainer."""
    feature_name: str = Field(description="Normalized feature column name")
    feature_value: float = Field(description="Raw point-in-time numerical feature value")
    shap_value: float = Field(description="Exact Shapley additive contribution to model prediction")
    rank: int = Field(ge=1, description="Importance rank of this feature (1 = dominant driver)")
    direction_influence: str = Field(
        description="'BULLISH' if shap_value > 0 else 'BEARISH'"
    )


class CompanyScoringFeatures(BaseModel):
    """Point-in-time multi-factor feature vector for a specific company and timestamp."""
    ticker: str = Field(description="Target equity ticker (e.g. 'TATAMOTORS.NS')")
    as_of_date: str = Field(description="Strict point-in-time date YYYY-MM-DD")
    event_id: Optional[str] = Field(default=None, description="Linked event ID if scoring in response to an event")

    # 1. Technical & Momentum Factors
    return_1d: float = Field(default=0.0, description="1-day price return")
    return_5d: float = Field(default=0.0, description="5-day cumulative price return")
    return_20d: float = Field(default=0.0, description="20-day momentum return")
    volatility_20d: float = Field(default=0.02, description="20-day annualized rolling volatility")
    volatility_50d: float = Field(default=0.025, description="50-day annualized rolling volatility")
    relative_volume_5d: float = Field(default=1.0, description="5-day volume / 30-day average volume ratio")
    rsi_14: float = Field(default=50.0, ge=0.0, le=100.0, description="14-day Relative Strength Index")
    macd_momentum: float = Field(default=0.0, description="MACD histogram value")

    # 2. Fundamental & Exposure Factors
    beta_market: float = Field(default=1.0, description="Historical beta relative to Nifty 50")
    debt_to_equity_proxy: float = Field(default=0.5, description="Estimated debt-to-equity ratio")
    operating_margin_proxy: float = Field(default=0.15, description="Estimated operating margin")
    is_large_cap: float = Field(default=1.0, description="1.0 for Large Cap, 0.0 for Mid/Small Cap")

    # 3. News Sentiment & NLP Event Factors
    finbert_sentiment_3d: float = Field(default=0.0, ge=-1.0, le=1.0, description="3-day mean FinBERT sentiment")
    sentiment_dispersion_7d: float = Field(default=0.0, ge=0.0, description="7-day sentiment standard deviation")
    event_shock_magnitude: float = Field(default=0.0, ge=-1.0, le=1.0, description="Shock magnitude S_E of primary event")
    event_nlp_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="NLP extraction confidence C_E")

    # 4. Knowledge Graph Ripple Factors
    net_ripple_score: float = Field(default=0.0, ge=-1.0, le=1.0, description="Aggregated graph ripple score R(v)")
    min_hop_distance: float = Field(default=3.0, description="Shortest hop distance k from event origin")
    strongest_path_impact: float = Field(default=0.0, ge=-1.0, le=1.0, description="Highest-magnitude path shock")
    upstream_supplier_shock: float = Field(default=0.0, description="Sum of shocks from direct suppliers")
    downstream_customer_shock: float = Field(default=0.0, description="Sum of shocks from direct customer companies")

    # 5. Commodity Correlation Factors
    consumed_commodity_30d_pct: float = Field(default=0.0, description="30-day pct change in primary raw material")
    commodity_cost_share: float = Field(default=0.20, ge=0.0, le=1.0, description="COGS fraction of primary input commodity")

    # 6. Macroeconomic Environment Factors
    rbi_repo_rate_change_180d: float = Field(default=0.0, description="Change in RBI repo rate over prior 180 days")
    usd_inr_30d_pct: float = Field(default=0.0, description="30-day percentage change in USD/INR exchange rate")
    us_10y_yield_change: float = Field(default=0.0, description="US 10-Year Treasury yield change in bps")
    india_cpi_yoy: float = Field(default=0.05, description="Headline India CPI YoY inflation rate")

    def to_feature_vector(self) -> List[float]:
        """Convert fields into an ordered float list for model ingestion."""
        return [
            self.return_1d,
            self.return_5d,
            self.return_20d,
            self.volatility_20d,
            self.volatility_50d,
            self.relative_volume_5d,
            self.rsi_14,
            self.macd_momentum,
            self.beta_market,
            self.debt_to_equity_proxy,
            self.operating_margin_proxy,
            self.is_large_cap,
            self.finbert_sentiment_3d,
            self.sentiment_dispersion_7d,
            self.event_shock_magnitude,
            self.event_nlp_confidence,
            self.net_ripple_score,
            self.min_hop_distance,
            self.strongest_path_impact,
            self.upstream_supplier_shock,
            self.downstream_customer_shock,
            self.consumed_commodity_30d_pct,
            self.commodity_cost_share,
            self.rbi_repo_rate_change_180d,
            self.usd_inr_30d_pct,
            self.us_10y_yield_change,
            self.india_cpi_yoy,
        ]

    @classmethod
    def feature_names(cls) -> List[str]:
        """Return the canonical ordered list of feature column names."""
        return [
            "return_1d",
            "return_5d",
            "return_20d",
            "volatility_20d",
            "volatility_50d",
            "relative_volume_5d",
            "rsi_14",
            "macd_momentum",
            "beta_market",
            "debt_to_equity_proxy",
            "operating_margin_proxy",
            "is_large_cap",
            "finbert_sentiment_3d",
            "sentiment_dispersion_7d",
            "event_shock_magnitude",
            "event_nlp_confidence",
            "net_ripple_score",
            "min_hop_distance",
            "strongest_path_impact",
            "upstream_supplier_shock",
            "downstream_customer_shock",
            "consumed_commodity_30d_pct",
            "commodity_cost_share",
            "rbi_repo_rate_change_180d",
            "usd_inr_30d_pct",
            "us_10y_yield_change",
            "india_cpi_yoy",
        ]


class CompanyPredictionOutput(BaseModel):
    """Complete structured prediction result for a single company."""
    prediction_id: str = Field(description="Deterministic prediction unique ID")
    ticker: str = Field(description="Target company ticker")
    as_of_timestamp: str = Field(description="Point-in-time ISO timestamp")
    horizon_days: int = Field(default=7, description="Forecast horizon in trading days (1, 7, or 30)")
    predicted_impact_score: float = Field(
        ge=-1.0, le=1.0,
        description="Continuous predicted price impact / return score in [-1.0, 1.0]"
    )
    predicted_direction: PredictionDirection = Field(
        description="Categorical signal: BULLISH, BEARISH, or NEUTRAL"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Calibrated model certainty score"
    )
    risk_label: RiskLabel = Field(
        description="Tail risk category: LOW, MODERATE, HIGH, or SEVERE"
    )
    base_value: float = Field(description="SHAP expected value (intercept)")
    feature_attributions: List[FeatureAttribution] = Field(
        description="Full ranked list of local SHAP feature attributions"
    )
    top_bullish_drivers: List[FeatureAttribution] = Field(
        description="Top 3 positive drivers pushing prediction up"
    )
    top_bearish_drivers: List[FeatureAttribution] = Field(
        description="Top 3 negative drivers pushing prediction down"
    )
    model_version: str = Field(default="xgboost_v1.0")


class ModelBenchmarkComparison(BaseModel):
    """Documented side-by-side performance comparison between XGBoost and LightGBM."""
    train_samples_count: int
    val_samples_count: int
    test_samples_count: int
    features_count: int

    # XGBoost Primary Model
    xgboost_rmse: float
    xgboost_mae: float
    xgboost_r2: float
    xgboost_directional_accuracy: float
    xgboost_brier_score: float
    xgboost_train_time_sec: float

    # LightGBM Benchmark Fallback
    lightgbm_rmse: float
    lightgbm_mae: float
    lightgbm_r2: float
    lightgbm_directional_accuracy: float
    lightgbm_brier_score: float
    lightgbm_train_time_sec: float

    summary_verdict: str = Field(
        description="Formal engineering justification for selecting XGBoost as primary production model"
    )
