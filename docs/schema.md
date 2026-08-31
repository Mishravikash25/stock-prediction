# Database & Knowledge Graph Schema Specification
**Project:** Explainable AI Market Ripple Engine  
**Document Version:** 1.0.0  
**Phase:** 2 — Schema & Data Modeling  
**Target Database Engines:** PostgreSQL 16 + TimescaleDB 2.14, Neo4j 5.x Community/Enterprise  

---

## 1. PostgreSQL & TimescaleDB Relational Schema

All tables use UTC timestamps (`TIMESTAMPTZ`), explicit UUID/surrogate keys, foreign key constraints, and performance indexes. TimescaleDB hypertables are configured on high-volume financial time-series.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RELATIONAL ENTITY MAP                             │
├──────────────────────────┬──────────────────────────┬───────────────────────┤
│    INGESTION & STAGING   │   NORMALIZED DOMAIN      │   ML & EVALUATION     │
├──────────────────────────┼──────────────────────────┼───────────────────────┤
│ • raw_equity_ohlcv       │ • sectors                │ • ml_feature_store    │
│ • raw_macro_series       │ • commodities            │ • ml_dataset_splits   │
│ • raw_announcements      │ • companies              │ • predictions         │
│ • raw_news_articles      │ • events                 │ • backtest_runs       │
│                          │ • event_entity_links     │                       │
│                          │ • market_equity_daily    │                       │
│                          │ • commodity_daily        │                       │
│                          │ • macro_monthly          │                       │
└──────────────────────────┴──────────────────────────┴───────────────────────┘
```

### 1.1 Ingestion Staging Tables (Source-Specific)

```sql
-- 1. Raw Equities Staging (yfinance .NS/.BO connector)
CREATE TABLE raw_equity_ohlcv (
    id BIGSERIAL PRIMARY KEY,
    source_name VARCHAR(32) NOT NULL DEFAULT 'yfinance',
    ticker VARCHAR(20) NOT NULL,              -- e.g., 'TATAMOTORS.NS'
    exchange VARCHAR(10) NOT NULL DEFAULT 'NSE',
    trade_timestamp TIMESTAMPTZ NOT NULL,
    open_price NUMERIC(12, 4) NOT NULL,
    high_price NUMERIC(12, 4) NOT NULL,
    low_price NUMERIC(12, 4) NOT NULL,
    close_price NUMERIC(12, 4) NOT NULL,
    adjusted_close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    raw_payload JSONB,                        -- Full response dictionary from yfinance
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_raw_equity UNIQUE (ticker, trade_timestamp)
);
CREATE INDEX idx_raw_equity_ticker_time ON raw_equity_ohlcv (ticker, trade_timestamp DESC);

-- 2. Raw Macroeconomic & Commodity Series (FRED connector)
CREATE TABLE raw_macro_series (
    id BIGSERIAL PRIMARY KEY,
    source_name VARCHAR(32) NOT NULL DEFAULT 'FRED',
    series_id VARCHAR(50) NOT NULL,           -- e.g., 'DCOILBRENTEU', 'INDCPIALLMINMEI'
    observation_date DATE NOT NULL,
    value NUMERIC(14, 4) NOT NULL,
    realtime_start DATE,
    realtime_end DATE,
    raw_payload JSONB,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_raw_macro UNIQUE (series_id, observation_date)
);
CREATE INDEX idx_raw_macro_series_date ON raw_macro_series (series_id, observation_date DESC);

-- 3. Raw Corporate Filings & Announcements (NSE Corporate RSS connector)
CREATE TABLE raw_announcements (
    id BIGSERIAL PRIMARY KEY,
    source_name VARCHAR(32) NOT NULL DEFAULT 'NSE_RSS',
    guid VARCHAR(255) NOT NULL UNIQUE,
    ticker VARCHAR(20) NOT NULL,
    company_name VARCHAR(255),
    category VARCHAR(100),                    -- e.g., 'Financial Results', 'Board Meeting', 'Acquisition'
    headline TEXT NOT NULL,
    attachment_url TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    raw_xml_or_json TEXT,
    processed_status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'PROCESSED', 'FAILED'
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_raw_announcements_ticker_pub ON raw_announcements (ticker, published_at DESC);

-- 4. Raw Financial News Articles (Google News RSS / Economic Times / Moneycontrol)
CREATE TABLE raw_news_articles (
    id BIGSERIAL PRIMARY KEY,
    source_name VARCHAR(64) NOT NULL,         -- 'ECONOMIC_TIMES', 'MONEYCONTROL', 'GOOGLE_NEWS_RSS'
    article_url TEXT NOT NULL UNIQUE,
    headline TEXT NOT NULL,
    summary TEXT,
    article_body TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    dedup_cluster_id VARCHAR(64),             -- sentence-transformers cluster hash
    processed_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_raw_news_pub ON raw_news_articles (published_at DESC);
CREATE INDEX idx_raw_news_cluster ON raw_news_articles (dedup_cluster_id);
```

---

### 1.2 Core Domain & TimescaleDB Hypertables

```sql
-- Sector Registry (MVP Universe: 4 Target Sectors)
CREATE TABLE sectors (
    sector_id VARCHAR(32) PRIMARY KEY,        -- 'SEC_AUTO', 'SEC_STEEL', 'SEC_ENERGY', 'SEC_IT'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Commodity Master (MVP Universe: 8 Target Commodities)
CREATE TABLE commodities (
    commodity_id VARCHAR(32) PRIMARY KEY,     -- 'COMM_BRENT_CRUDE', 'COMM_COKING_COAL', 'COMM_HRC_STEEL', etc.
    name VARCHAR(100) NOT NULL,
    unit VARCHAR(30) NOT NULL,                -- 'USD/Barrel', 'USD/MT', 'INR/10g'
    fred_series_id VARCHAR(50),
    yf_symbol VARCHAR(20),                    -- 'CL=F', 'HG=F'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Company Registry (MVP Universe: ~35 Target Liquid Indian Equities)
CREATE TABLE companies (
    ticker VARCHAR(20) PRIMARY KEY,           -- 'TATAMOTORS.NS'
    name VARCHAR(255) NOT NULL,
    sector_id VARCHAR(32) NOT NULL REFERENCES sectors(sector_id),
    isin VARCHAR(20) UNIQUE,
    market_cap_category VARCHAR(20) NOT NULL, -- 'LARGE_CAP', 'MID_CAP'
    primary_business_summary TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_companies_sector ON companies (sector_id);

-- Hypertable: Clean Daily Equity Market Series
CREATE TABLE market_equity_daily (
    trade_date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL REFERENCES companies(ticker),
    open NUMERIC(12, 4) NOT NULL,
    high NUMERIC(12, 4) NOT NULL,
    low NUMERIC(12, 4) NOT NULL,
    close NUMERIC(12, 4) NOT NULL,
    adjusted_close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    return_1d NUMERIC(8, 6),
    return_7d NUMERIC(8, 6),
    return_30d NUMERIC(8, 6),
    rolling_volatility_30d NUMERIC(8, 6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (trade_date, ticker)
);
-- Convert to TimescaleDB Hypertable partitioned by trade_date
SELECT create_hypertable('market_equity_daily', 'trade_date', if_not_exists => TRUE);

-- Hypertable: Clean Daily Commodity Price Series
CREATE TABLE commodity_daily (
    trade_date DATE NOT NULL,
    commodity_id VARCHAR(32) NOT NULL REFERENCES commodities(commodity_id),
    price NUMERIC(14, 4) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    pct_change_1d NUMERIC(8, 6),
    pct_change_30d NUMERIC(8, 6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (trade_date, commodity_id)
);
SELECT create_hypertable('commodity_daily', 'trade_date', if_not_exists => TRUE);

-- Hypertable: Clean Macroeconomic Monthly Series
CREATE TABLE macro_monthly (
    period_date DATE NOT NULL,
    indicator_id VARCHAR(50) NOT NULL,        -- 'INDIA_CPI', 'RBI_REPO_RATE', 'USD_INR_EXCHANGE'
    value NUMERIC(14, 4) NOT NULL,
    yoy_growth NUMERIC(8, 6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (period_date, indicator_id)
);
SELECT create_hypertable('macro_monthly', 'period_date', if_not_exists => TRUE);
```

---

### 1.3 Event Detection & Extraction Tables

```sql
-- Core Structured Events (4 Archetypes)
CREATE TYPE event_archetype_enum AS ENUM (
    'COMMODITY_SHOCK',
    'POLICY_TAX_CHANGE',
    'SUPPLY_DISRUPTION',
    'MACRO_RATE_SHIFT'
);

CREATE TABLE events (
    event_id VARCHAR(64) PRIMARY KEY,         -- 'evt_c8f2a1b9'
    occurred_at TIMESTAMPTZ NOT NULL,         -- Actual event point-in-time timestamp
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    headline TEXT NOT NULL,
    raw_source_text TEXT NOT NULL,
    source_channel VARCHAR(64) NOT NULL,      -- 'NEWS_RSS', 'NSE_ANNOUNCEMENT', 'FRED_ANOMALY'
    source_url TEXT,
    archetype event_archetype_enum NOT NULL,
    origin_entity_id VARCHAR(64) NOT NULL,    -- Initial graph node ID (Sector, Commodity, or Company)
    origin_entity_type VARCHAR(32) NOT NULL,  -- 'SECTOR', 'COMMODITY', 'COMPANY', 'MACRO'
    shock_magnitude NUMERIC(5, 4) NOT NULL,   -- Range [-1.0000, 1.0000]
    nlp_confidence NUMERIC(5, 4) NOT NULL,    -- Range [0.0000, 1.0000]
    finbert_sentiment NUMERIC(5, 4) NOT NULL, -- Range [-1.0000, 1.0000]
    llm_classification_metadata JSONB NOT NULL, -- Full validated Pydantic JSON dump
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_events_occurred ON events (occurred_at DESC);
CREATE INDEX idx_events_archetype ON events (archetype);

-- Event Entity Links (Many-to-Many resolved entities)
CREATE TABLE event_entity_links (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(64) NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    entity_id VARCHAR(64) NOT NULL,           -- Node ID in graph (e.g. 'TATASTEEL.NS', 'COMM_COKING_COAL')
    entity_type VARCHAR(32) NOT NULL,         -- 'COMPANY', 'COMMODITY', 'SECTOR'
    mention_role VARCHAR(32) NOT NULL,        -- 'PRIMARY_SOURCE', 'DIRECT_TARGET', 'MENTIONED_PEER'
    resolution_confidence NUMERIC(5, 4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_event_links_entity ON event_entity_links (entity_id);
```

---

### 1.4 Point-in-Time ML Feature Store & Split Management

```sql
-- Chronological Dataset Split Registry with Explicit Embargo Windows
CREATE TABLE ml_dataset_splits (
    split_id VARCHAR(64) PRIMARY KEY,         -- e.g., 'SPLIT_2020_2023_WALK_FORWARD_V1'
    split_type VARCHAR(32) NOT NULL,          -- 'TRAIN_VAL_TEST_CHRONOLOGICAL'
    train_start_date DATE NOT NULL,
    train_end_date DATE NOT NULL,
    val_start_date DATE NOT NULL,
    val_end_date DATE NOT NULL,
    test_start_date DATE NOT NULL,
    test_end_date DATE NOT NULL,
    embargo_window_days INT NOT NULL DEFAULT 7, -- Explicit buffer to eliminate autocorrelation leakage
    is_purged BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_chronological_splits CHECK (
        train_start_date < train_end_date AND
        train_end_date < val_start_date AND
        val_start_date < val_end_date AND
        val_end_date < test_start_date AND
        test_start_date < test_end_date
    )
);

-- Point-in-Time Validated Feature Store
CREATE TABLE ml_feature_store (
    as_of_timestamp TIMESTAMPTZ NOT NULL,     -- Strictly no data beyond this timestamp
    ticker VARCHAR(20) NOT NULL REFERENCES companies(ticker),
    event_id VARCHAR(64) REFERENCES events(event_id),
    
    -- Graph Propagation Features
    net_ripple_score NUMERIC(8, 6) NOT NULL,  -- R(v) from graph traversal
    min_hop_distance INT NOT NULL,            -- Shortest hop from event origin
    direct_upstream_shock NUMERIC(8, 6),
    direct_downstream_shock NUMERIC(8, 6),
    
    -- Technical & Momentum Features (Point-in-Time)
    return_momentum_5d NUMERIC(8, 6) NOT NULL,
    return_momentum_20d NUMERIC(8, 6) NOT NULL,
    volatility_20d NUMERIC(8, 6) NOT NULL,
    relative_volume_5d NUMERIC(8, 4) NOT NULL,
    
    -- Sentiment Features
    finbert_sentiment_3d NUMERIC(6, 4) NOT NULL,
    sentiment_dispersion_7d NUMERIC(6, 4) NOT NULL,
    
    -- Macro & Commodity Sensitivity Features
    crude_oil_sensitivity_beta NUMERIC(8, 4) NOT NULL,
    usd_inr_sensitivity_beta NUMERIC(8, 4) NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (as_of_timestamp, ticker)
);
SELECT create_hypertable('ml_feature_store', 'as_of_timestamp', if_not_exists => TRUE);
```

---

### 1.5 Prediction Tracker & Automated Outcome Scoring

```sql
CREATE TYPE direction_enum AS ENUM ('BULLISH', 'BEARISH', 'NEUTRAL');
CREATE TYPE risk_label_enum AS ENUM ('LOW', 'MODERATE', 'HIGH', 'SEVERE');

CREATE TABLE predictions (
    prediction_id VARCHAR(64) PRIMARY KEY,     -- 'pred_90a42f'
    created_at TIMESTAMPTZ NOT NULL,           -- Point-in-time when signal was generated
    ticker VARCHAR(20) NOT NULL REFERENCES companies(ticker),
    event_id VARCHAR(64) REFERENCES events(event_id),
    split_id VARCHAR(64) REFERENCES ml_dataset_splits(split_id),
    
    -- Model Output
    horizon_days INT NOT NULL,                 -- 1, 7, or 30
    predicted_direction direction_enum NOT NULL,
    predicted_impact_score NUMERIC(6, 4) NOT NULL, -- Continuous output [-1.0000, 1.0000]
    confidence_score NUMERIC(5, 4) NOT NULL,   -- Model confidence [0.0000, 1.0000]
    risk_label risk_label_enum NOT NULL,
    
    -- Raw Explainability Payload
    shap_values_json JSONB NOT NULL,           -- Array of {feature, value, shap_contribution}
    graph_path_proof JSONB NOT NULL,           -- List of nodes and edges involved
    
    -- Structured Dual-Thesis Generated Text (LLM)
    bull_case_text TEXT NOT NULL,
    bear_case_text TEXT NOT NULL,
    uncertainty_text TEXT NOT NULL,
    
    -- Forward Outcome Verification (Filled at horizon maturity)
    actual_price_at_prediction NUMERIC(12, 4) NOT NULL,
    actual_price_at_horizon NUMERIC(12, 4),
    actual_return_pct NUMERIC(8, 4),
    is_directionally_correct BOOLEAN,
    brier_score NUMERIC(6, 4),
    outcome_evaluated_at TIMESTAMPTZ,
    
    CONSTRAINT chk_horizon CHECK (horizon_days IN (1, 7, 30))
);
CREATE INDEX idx_predictions_ticker ON predictions (ticker, created_at DESC);
CREATE INDEX idx_predictions_eval_status ON predictions (outcome_evaluated_at);
```

---

## 2. Neo4j Knowledge Graph Model

Neo4j serves as the source of truth for structural industry taxonomies, physical supply networks, commodity input dependencies, and regulatory authorities.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            NEO4J GRAPH TOPOLOGY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   (Commodity: COMM_COKING_COAL)                                            │
│                 │                                                           │
│                 │ CONSUMES_COMMODITY {strength: 0.85, cost_share: 0.35}     │
│                 ▼                                                           │
│   (Company: TATASTEEL.NS) ─── SUPPLIES_TO {strength: 0.70} ──► (Company:    │
│                 ▲                                              TATAMOTORS)  │
│                 │                                                   │       │
│                 │ BELONGS_TO                                        │       │
│                 │                                                   ▼       │
│   (Sector: SEC_STEEL) ◄── REGULATED_BY {tariff_exposure: 0.90} ─── (Sector:│
│                                                                   SEC_AUTO) │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Node Definitions & Properties

```cypher
// 1. Company Node
CREATE CONSTRAINT uq_company_ticker IF NOT EXISTS
FOR (c:Company) REQUIRE c.ticker IS UNIQUE;

// Node Example:
// (:Company {
//    ticker: "TATAMOTORS.NS",
//    name: "Tata Motors Limited",
//    sector: "Automotive",
//    market_cap_category: "LARGE_CAP",
//    beta: 1.25,
//    created_at: datetime()
// })

// 2. Sector Node
CREATE CONSTRAINT uq_sector_id IF NOT EXISTS
FOR (s:Sector) REQUIRE s.sector_id IS UNIQUE;

// Node Example:
// (:Sector {
//    sector_id: "SEC_AUTO",
//    name: "Automotive & Components",
//    gdp_share_pct: 7.1
// })

// 3. Commodity Node
CREATE CONSTRAINT uq_commodity_id IF NOT EXISTS
FOR (m:Commodity) REQUIRE m.commodity_id IS UNIQUE;

// Node Example:
// (:Commodity {
//    commodity_id: "COMM_HRC_STEEL",
//    name: "Hot Rolled Steel Coil",
//    unit: "INR/MT",
//    global_benchmark: "CRU_STEEL_INDEX"
// })

// 4. MacroFactor Node
CREATE CONSTRAINT uq_macro_id IF NOT EXISTS
FOR (f:MacroFactor) REQUIRE f.factor_id IS UNIQUE;

// Node Example:
// (:MacroFactor {
//    factor_id: "MACRO_RBI_REPO",
//    name: "RBI Monetary Policy Repo Rate",
//    frequency: "BI_MONTHLY"
// })

// 5. Event Node (Temporary or persistent point-in-time projection)
CREATE CONSTRAINT uq_event_id IF NOT EXISTS
FOR (e:Event) REQUIRE e.event_id IS UNIQUE;
```

---

### 2.2 Relationship Types & Semantic Constraints

Every relationship MUST include `strength`, `source`, `confidence`, and `updated_at`.

```cypher
// 1. Physical Supply Chain Link: Company -> Company
// Semantic: Supplier -> Customer
(:Company)-[:SUPPLIES_TO {
    strength: 0.70,                  // Revenue or procurement dependency [0.0, 1.0]
    lead_time_days: 14,             // Delivery buffer
    substitution_friction: 0.80,    // Difficulty of switching suppliers [0.0, 1.0]
    source: "manual_seed",          // 'manual_seed' | 'inferred'
    inference_method: null,         // e.g., '10k_filing_nlp' or 'node2vec_link_pred'
    confidence: 0.95,
    updated_at: datetime()
}]->(:Company)

// 2. Input Commodity Dependency: Company -> Commodity
// Semantic: Company relies on Commodity as primary raw material
(:Company)-[:CONSUMES_COMMODITY {
    strength: 0.85,                  // Direct price sensitivity weight [0.0, 1.0]
    cost_share_pct: 0.35,           // Fraction of Cost of Goods Sold (COGS)
    pricing_power_pass_through: 0.40,// Ability to pass price increases to end-consumer
    source: "manual_seed",
    confidence: 0.92,
    updated_at: datetime()
}]->(:Commodity)

// 3. Industry Taxonomy Membership
(:Company)-[:BELONGS_TO {
    is_primary: true
}]->(:Sector)

// 4. Regulatory & Macroeconomic Exposure
(:Company)-[:REGULATED_BY {
    strength: 0.90,
    tariff_exposure: 0.75,          // Exposure to export/import tax revisions
    subsidy_dependence: 0.10,
    source: "manual_seed",
    confidence: 0.90
}]->(:Sector)

(:Sector)-[:SENSITIVE_TO {
    strength: 0.65,                  // Correlation to interest rate / inflation
    elasticity_direction: "INVERSE", // Higher repo rate -> Lower demand
    source: "manual_seed",
    confidence: 0.88
}]->(:MacroFactor)
```

---

## 3. Concrete MVP Universe Definition

The MVP targets **4 Interconnected Sectors, 8 Strategic Commodities, 4 Macro Factors, and 36 Core Liquid Equities**.

### 3.1 Sectors & Commodities Reference

```
Sectors:
├── SEC_AUTO   (Automotive, Commercial Vehicles & Auto Ancillaries)
├── SEC_STEEL  (Steel, Iron Ore & Metallurgical Coking Coal)
├── SEC_ENERGY (Oil & Gas Refining, Exploration & Petrochemicals)
└── SEC_IT     (Information Technology & Enterprise Services)

Commodities:
├── COMM_BRENT_CRUDE   (Energy)
├── COMM_NATURAL_GAS   (Energy / Chemicals)
├── COMM_COKING_COAL   (Metals / Blast Furnace Input)
├── COMM_IRON_ORE      (Metals Input)
├── COMM_HRC_STEEL     (Industrial Metal / Auto Raw Material)
├── COMM_ALUMINUM      (Lightweight Auto / Electrical)
├── COMM_COPPER        (Wiring / Electronics)
└── COMM_CHIP_SEMI     (Semiconductor Components)

Macro Factors:
├── MACRO_RBI_REPO     (Reserve Bank of India Repo Rate)
├── MACRO_USD_INR      (Foreign Exchange Rate)
├── MACRO_INDIA_CPI    (Headline Inflation)
└── MACRO_US_10Y_YIELD (US 10-Year Treasury Yield)
```

### 3.2 Target Equities Catalog (~36 Nodes)

```
1. Automotive & Ancillaries:
   - TATAMOTORS.NS (OEM Commercial & Passenger)
   - MARUTI.NS     (OEM Passenger Vehicles)
   - M&M.NS        (OEM Tractors & SUVs)
   - BAJAJ-AUTO.NS (2-Wheeler / 3-Wheeler)
   - BHARATFORG.NS (Forging / Auto Components)
   - MOTHERSON.NS  (Wiring Systems & Modules)
   - BOSCHLTD.NS   (Auto Electronics & Fuel Injection)
   - APOLLOTYRE.NS (Tires & Rubber)
   - MRF.NS        (Tires & Rubber)

2. Steel & Metals:
   - TATASTEEL.NS  (Integrated Steel Producer)
   - JSWSTEEL.NS   (Flat & Long Steel Producer)
   - JINDALSTEL.NS (Steel & Mining)
   - SAIL.NS       (State Integrated Steel)
   - HINDALCO.NS   (Aluminum & Copper)
   - VEDL.NS       (Diversified Mining & Zinc)
   - NMDC.NS       (Iron Ore Mining)
   - NATIONALUM.NS (Bauxite & Aluminum)

3. Energy & Oil/Gas:
   - RELIANCE.NS   (Oil Refining, Petrochem & Retail)
   - ONGC.NS       (Upstream Crude Exploration)
   - IOC.NS        (Oil Refining & Marketing)
   - BPCL.NS       (Oil Refining & Marketing)
   - GAIL.NS       (Natural Gas Transmission)
   - OIL.NS        (Upstream Crude Exploration)
   - PETRONET.NS   (LNG Regasification)
   - GUJGASLTD.NS  (City Gas Distribution)

4. IT Services & Tech:
   - TCS.NS        (Global IT & Consulting)
   - INFY.NS       (Global IT & Digital Transformation)
   - WIPRO.NS      (IT Services)
   - HCLTECH.NS    (IT Services & Engineering R&D)
   - TECHM.NS      (Telecom & IT Solutions)
   - LTIM.NS       (Mid-to-Large IT Services)
   - PERSISTENT.NS (Digital Engineering)
   - COFORGE.NS    (Domain-focused IT Solutions)
```

---

## 4. LLM Event Classification Schema (Pydantic v2 Specification)

The NLP classification engine strictly outputs to the following Python Pydantic model (`ml/nlp/event_detector.py`), guaranteeing zero unvalidated numerical fields:

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, confloat

class EventArchetype(str, Enum):
    COMMODITY_SHOCK = "COMMODITY_SHOCK"
    POLICY_TAX_CHANGE = "POLICY_TAX_CHANGE"
    SUPPLY_DISRUPTION = "SUPPLY_DISRUPTION"
    MACRO_RATE_SHIFT = "MACRO_RATE_SHIFT"

class ExtractedEntity(BaseModel):
    name: str = Field(description="Exact entity text mentioned in article")
    matched_node_id: str = Field(description="Canonical node ID from Neo4j (e.g., 'TATASTEEL.NS')")
    entity_type: str = Field(description="'COMPANY', 'COMMODITY', 'SECTOR', or 'MACRO'")
    confidence: confloat(ge=0.0, le=1.0) = Field(description="Resolution certainty")

class LLMEventExtractionSchema(BaseModel):
    event_title: str = Field(description="Concise 1-line professional headline of the market event")
    archetype: EventArchetype = Field(description="Primary archetype from the 4 approved categories")
    origin_node_id: str = Field(description="Root graph node triggering the shock (e.g., 'COMM_COKING_COAL')")
    shock_magnitude: confloat(ge=-1.0, le=1.0) = Field(
        description="Estimated immediate direction and scale of shock (-1.0 severe negative, +1.0 severe positive)"
    )
    confidence: confloat(ge=0.0, le=1.0) = Field(description="Classification confidence score")
    direct_transmission_mechanism: str = Field(
        description="Specific economic mechanism (e.g., 'Export tariff increases domestic inventory and lowers realized margin')"
    )
    extracted_entities: List[ExtractedEntity] = Field(default_factory=list)
    touched_sectors: List[str] = Field(description="List of primary sector IDs affected")
    touched_commodities: List[str] = Field(description="List of primary commodity IDs affected")
```
