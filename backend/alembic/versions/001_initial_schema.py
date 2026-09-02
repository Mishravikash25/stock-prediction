"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-02 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Raw Staging Tables
    op.create_table(
        "raw_equity_ohlcv",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_name", sa.String(length=32), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("exchange", sa.String(length=10), nullable=False),
        sa.Column("trade_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open_price", sa.Float(), nullable=False),
        sa.Column("high_price", sa.Float(), nullable=False),
        sa.Column("low_price", sa.Float(), nullable=False),
        sa.Column("close_price", sa.Float(), nullable=False),
        sa.Column("adjusted_close", sa.Float(), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "trade_timestamp", name="uq_raw_equity_ticker_time"),
    )
    op.create_index("idx_raw_equity_ticker_time", "raw_equity_ohlcv", ["ticker", "trade_timestamp"])

    op.create_table(
        "raw_macro_series",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_name", sa.String(length=32), nullable=False),
        sa.Column("series_id", sa.String(length=50), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("realtime_start", sa.Date(), nullable=True),
        sa.Column("realtime_end", sa.Date(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("series_id", "observation_date", name="uq_raw_macro_series_date"),
    )
    op.create_index("idx_raw_macro_series_date", "raw_macro_series", ["series_id", "observation_date"])

    op.create_table(
        "raw_announcements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_name", sa.String(length=32), nullable=False),
        sa.Column("guid", sa.String(length=255), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("attachment_url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_xml_or_json", sa.Text(), nullable=True),
        sa.Column("processed_status", sa.String(length=20), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guid"),
    )
    op.create_index("idx_raw_announcements_ticker_pub", "raw_announcements", ["ticker", "published_at"])

    op.create_table(
        "raw_news_articles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_name", sa.String(length=64), nullable=False),
        sa.Column("article_url", sa.Text(), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("article_body", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dedup_cluster_id", sa.String(length=64), nullable=True),
        sa.Column("processed_status", sa.String(length=20), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_url"),
    )
    op.create_index("idx_raw_news_pub", "raw_news_articles", ["published_at"])
    op.create_index("idx_raw_news_cluster", "raw_news_articles", ["dedup_cluster_id"])

    # 2. Domain Masters
    op.create_table(
        "sectors",
        sa.Column("sector_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("sector_id"),
    )

    op.create_table(
        "commodities",
        sa.Column("commodity_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("fred_series_id", sa.String(length=50), nullable=True),
        sa.Column("yf_symbol", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("commodity_id"),
    )

    op.create_table(
        "companies",
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sector_id", sa.String(length=32), nullable=False),
        sa.Column("isin", sa.String(length=20), nullable=True),
        sa.Column("market_cap_category", sa.String(length=20), nullable=False),
        sa.Column("primary_business_summary", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sector_id"], ["sectors.sector_id"]),
        sa.PrimaryKeyConstraint("ticker"),
        sa.UniqueConstraint("isin"),
    )
    op.create_index("idx_companies_sector", "companies", ["sector_id"])

    # 3. Market Hypertables
    op.create_table(
        "market_equity_daily",
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("adjusted_close", sa.Float(), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("return_1d", sa.Float(), nullable=True),
        sa.Column("return_7d", sa.Float(), nullable=True),
        sa.Column("return_30d", sa.Float(), nullable=True),
        sa.Column("rolling_volatility_30d", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticker"], ["companies.ticker"]),
        sa.PrimaryKeyConstraint("trade_date", "ticker"),
    )
    op.create_index("idx_market_equity_ticker_date", "market_equity_daily", ["ticker", "trade_date"])

    op.create_table(
        "commodity_daily",
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("commodity_id", sa.String(length=32), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("pct_change_1d", sa.Float(), nullable=True),
        sa.Column("pct_change_30d", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["commodity_id"], ["commodities.commodity_id"]),
        sa.PrimaryKeyConstraint("trade_date", "commodity_id"),
    )
    op.create_index("idx_commodity_daily_id_date", "commodity_daily", ["commodity_id", "trade_date"])

    op.create_table(
        "macro_monthly",
        sa.Column("period_date", sa.Date(), nullable=False),
        sa.Column("indicator_id", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("yoy_growth", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("period_date", "indicator_id"),
    )
    op.create_index("idx_macro_monthly_id_date", "macro_monthly", ["indicator_id", "period_date"])

    # 4. Events & Links
    op.create_table(
        "events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("raw_source_text", sa.Text(), nullable=False),
        sa.Column("source_channel", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column(
            "archetype",
            sa.Enum(
                "COMMODITY_SHOCK",
                "POLICY_TAX_CHANGE",
                "SUPPLY_DISRUPTION",
                "MACRO_RATE_SHIFT",
                name="event_archetype_enum"
            ),
            nullable=False
        ),
        sa.Column("origin_entity_id", sa.String(length=64), nullable=False),
        sa.Column("origin_entity_type", sa.String(length=32), nullable=False),
        sa.Column("shock_magnitude", sa.Float(), nullable=False),
        sa.Column("nlp_confidence", sa.Float(), nullable=False),
        sa.Column("finbert_sentiment", sa.Float(), nullable=False),
        sa.Column("llm_classification_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("idx_events_occurred", "events", ["occurred_at"])
    op.create_index("idx_events_archetype", "events", ["archetype"])

    op.create_table(
        "event_entity_links",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("mention_role", sa.String(length=32), nullable=False),
        sa.Column("resolution_confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_event_links_entity", "event_entity_links", ["entity_id"])
    op.create_index("idx_event_links_event", "event_entity_links", ["event_id"])

    # 5. ML Store & Splits
    op.create_table(
        "ml_dataset_splits",
        sa.Column("split_id", sa.String(length=64), nullable=False),
        sa.Column("split_type", sa.String(length=32), nullable=False),
        sa.Column("train_start_date", sa.Date(), nullable=False),
        sa.Column("train_end_date", sa.Date(), nullable=False),
        sa.Column("val_start_date", sa.Date(), nullable=False),
        sa.Column("val_end_date", sa.Date(), nullable=False),
        sa.Column("test_start_date", sa.Date(), nullable=False),
        sa.Column("test_end_date", sa.Date(), nullable=False),
        sa.Column("embargo_window_days", sa.Integer(), nullable=False),
        sa.Column("is_purged", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "train_start_date < train_end_date AND "
            "train_end_date < val_start_date AND "
            "val_start_date < val_end_date AND "
            "val_end_date < test_start_date AND "
            "test_start_date < test_end_date",
            name="chk_chronological_splits"
        ),
        sa.PrimaryKeyConstraint("split_id"),
    )

    op.create_table(
        "ml_feature_store",
        sa.Column("as_of_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=True),
        sa.Column("net_ripple_score", sa.Float(), nullable=False),
        sa.Column("min_hop_distance", sa.Integer(), nullable=False),
        sa.Column("direct_upstream_shock", sa.Float(), nullable=True),
        sa.Column("direct_downstream_shock", sa.Float(), nullable=True),
        sa.Column("return_momentum_5d", sa.Float(), nullable=False),
        sa.Column("return_momentum_20d", sa.Float(), nullable=False),
        sa.Column("volatility_20d", sa.Float(), nullable=False),
        sa.Column("relative_volume_5d", sa.Float(), nullable=False),
        sa.Column("finbert_sentiment_3d", sa.Float(), nullable=False),
        sa.Column("sentiment_dispersion_7d", sa.Float(), nullable=False),
        sa.Column("crude_oil_sensitivity_beta", sa.Float(), nullable=False),
        sa.Column("usd_inr_sensitivity_beta", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"]),
        sa.ForeignKeyConstraint(["ticker"], ["companies.ticker"]),
        sa.PrimaryKeyConstraint("as_of_timestamp", "ticker"),
    )
    op.create_index("idx_ml_features_ticker_time", "ml_feature_store", ["ticker", "as_of_timestamp"])
    op.create_index("idx_ml_features_event", "ml_feature_store", ["event_id"])

    # 6. Predictions
    op.create_table(
        "predictions",
        sa.Column("prediction_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=True),
        sa.Column("split_id", sa.String(length=64), nullable=True),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column(
            "predicted_direction",
            sa.Enum("BULLISH", "BEARISH", "NEUTRAL", name="direction_enum"),
            nullable=False
        ),
        sa.Column("predicted_impact_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column(
            "risk_label",
            sa.Enum("LOW", "MODERATE", "HIGH", "SEVERE", name="risk_label_enum"),
            nullable=False
        ),
        sa.Column("shap_values_json", sa.JSON(), nullable=False),
        sa.Column("graph_path_proof", sa.JSON(), nullable=False),
        sa.Column("bull_case_text", sa.Text(), nullable=False),
        sa.Column("bear_case_text", sa.Text(), nullable=False),
        sa.Column("uncertainty_text", sa.Text(), nullable=False),
        sa.Column("actual_price_at_prediction", sa.Float(), nullable=False),
        sa.Column("actual_price_at_horizon", sa.Float(), nullable=True),
        sa.Column("actual_return_pct", sa.Float(), nullable=True),
        sa.Column("is_directionally_correct", sa.Boolean(), nullable=True),
        sa.Column("brier_score", sa.Float(), nullable=True),
        sa.Column("outcome_evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("horizon_days IN (1, 7, 30)", name="chk_prediction_horizon"),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"]),
        sa.ForeignKeyConstraint(["split_id"], ["ml_dataset_splits.split_id"]),
        sa.ForeignKeyConstraint(["ticker"], ["companies.ticker"]),
        sa.PrimaryKeyConstraint("prediction_id"),
    )
    op.create_index("idx_predictions_ticker_created", "predictions", ["ticker", "created_at"])
    op.create_index("idx_predictions_eval_status", "predictions", ["outcome_evaluated_at"])


def downgrade() -> None:
    op.drop_table("predictions")
    op.drop_table("ml_feature_store")
    op.drop_table("ml_dataset_splits")
    op.drop_table("event_entity_links")
    op.drop_table("events")
    op.drop_table("macro_monthly")
    op.drop_table("commodity_daily")
    op.drop_table("market_equity_daily")
    op.drop_table("companies")
    op.drop_table("commodities")
    op.drop_table("sectors")
    op.drop_table("raw_news_articles")
    op.drop_table("raw_announcements")
    op.drop_table("raw_macro_series")
    op.drop_table("raw_equity_ohlcv")
