# Feasibility Assessment & Technical Critique
**Project:** Explainable AI Market Ripple Engine  
**Review Stage:** Phase 1 — Pre-Architecture Architectural & Feasibility Review  
**Audience:** Academic Reviewers, Systems Architects, Quant Researchers  

---

## 1. Feasibility Assessment

### 1.1 Team Scale & Semester Timeline Realities
Building an end-to-end quantitative intelligence system combining graph databases, deep NLP, gradient boosting, local explainability, and a reactive financial terminal interface within a single semester (12–16 weeks) is **achievable only if architectural boundaries are strictly enforced and overengineering is ruthlessly pruned**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             ENGINEERING SPECTRUM                            │
├──────────────────────────────────────┬──────────────────────────────────────┤
│    FEASIBLE (Semester / Solo-Team)   │    RESEARCH-LAB / INSTITUTIONAL      │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Curated ontology (50-100 nodes)   │ • Open-domain dynamic graph learning │
│ • 1-3 hop deterministic propagation  │ • Continuous structural causal DAGs  │
│ • Fixed schema event extraction      │ • Unsupervised event discovery       │
│ • XGBoost tabular multi-factor model │ • End-to-end Deep Graph Neural Nets  │
│ • SHAP local feature attribution     │ • Microsecond order-book execution   │
│ • Point-in-time historical backtest  │ • High-frequency multi-asset alpha   │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

### 1.2 Explicit Risk Register

#### Risk 1: Multi-Hop Causal Graph Inference (CRITICAL RISK)
* **The Trap:** Attempting to infer automated causal DAGs (*Directed Acyclic Graphs*) or causal mechanisms from raw financial news or price co-movements using algorithms like PC, FCI, or continuous DAG learning (NOTEARS). Financial time series have low signal-to-noise ratios, non-stationarity, and widespread latent confounding.
* **The Solution:** The system **must not claim causal inference**. Instead, it must implement an **Economic Dependency & Transmission Graph**.
  * Edges represent verified structural relationships: `SUPPLIES_TO`, `CONSUMES_COMMODITY`, `COMPETES_WITH`, `SUBSIDIARY_OF`, `REGULATED_BY`.
  * Every edge maintains:
    1. `strength` $\in [0.0, 1.0]$: Elasticity / historical correlation / supply-share weight.
    2. `source`: Tagged strictly as `manual_seed` (curated fundamental data) or `inferred` (statistical co-movement / supply-chain extraction with documented method).
    3. `confidence` $\in [0.0, 1.0]$.
  * Graph traversals calculate **Shock Attenuation** along paths rather than unproven causality:
    $$\text{PathImpact}(P) = \text{ShockMagnitude} \times \prod_{e \in P} \text{strength}(e) \times \alpha^{\text{hop\_count}}$$
    where $\alpha \in (0, 1]$ is a decay factor preventing explosive distant propagation.

#### Risk 2: NLP Entity Resolution & Event Hallucination
* **The Trap:** Unstructured text extraction frequently conflates parent entities, subsidiaries, tickers, and generic industry nouns (e.g., confusing "Tata Steel" with "Tata Motors" when reading a conglomerate report, or confusing global Brent crude with domestic gas regulations).
* **The Solution:** Two-stage deterministic + LLM pipeline:
  1. High-precision NER dictionary and spaCy phrase matcher to anchor exact entities to database IDs.
  2. LLM classification running behind a strict **Pydantic v2 JSON Schema** with temperature $0.0$, outputting structured event archetypes (e.g., `INPUT_COST_SPIKE`, `EXPORT_DUTY_CHANGE`, `SUPPLY_BOTTLENECK`, `DEMAND_CONTRACTION`), magnitude $[-1.0, 1.0]$, and confidence $[0.0, 1.0]$.

#### Risk 3: Lookahead Leakage in Time-Series Alignment
* **The Trap:** Using data points (e.g., quarterly earnings, revised macroeconomic metrics, or afternoon news) to predict morning market moves, or utilizing random $K$-fold cross-validation.
* **The Solution:** Mandatory **Chronological Walk-Forward Validation** (Purged & Embargoed Time-Series Splits). No feature calculation may access timestamps $t \ge t_{\text{prediction}}$.

#### Risk 4: Heterogeneous Stack Overload
* **The Trap:** Juggling 7 independent services (FastAPI, Celery, Redis, TimescaleDB, Neo4j, Vite, PyTorch/Transformers) can lead to integration gridlock.
* **The Solution:** Modular, decoupled interface boundaries with mock fixtures for every subsystem. The frontend communicates with a unified FastAPI REST API; ML pipelines operate asynchronously via Celery; Neo4j queries are wrapped behind a clean Repository Pattern.

---

## 2. Novelty & Academic Defense

### 2.1 What Makes This Novel (Defensible Claims)
1. **Multi-Hop Supply & Commodity Shock Propagation:** Unlike traditional sentiment dashboards that associate an article directly with the single company mentioned, this engine propagates shocks upstream and downstream (e.g., *Australian Coking Coal Port Closure $\rightarrow$ Indian Blast-Furnace Steel Makers $\rightarrow$ Auto OEM Margin Squeeze $\rightarrow$ Tire & Component Suppliers*).
2. **Hybrid Symbolic Knowledge Graph + Tabular Gradient Boosting:** Bridges symbolic domain knowledge (explicit supply-chain topology) with statistical learning (XGBoost multi-factor model), leveraging SHAP values to explain the exact feature contributions.
3. **Structured Dual-Thesis Explainability:** Eliminates generic LLM cheerleading. The explanation layer is forced to generate a balanced **Bull Case**, **Bear Case**, and **Uncertainty Analysis** anchored strictly to top SHAP features and graph traversal paths—without inventing numbers.
4. **Point-in-Time Traceable Backtesting & Calibration:** Every prediction is logged with an immutable timestamp and automatically evaluated against real historical horizons (1-day, 7-day, 30-day), computing directional accuracy and Brier calibration scores.

### 2.2 What is NOT Defensible (Claims to Explicitly Avoid)
* ❌ *"AI that predicts future stock prices with guaranteed profit."* (Markets are stochastic; the engine provides risk/impact likelihood scores, not price prophecies).
* ❌ *"Fully autonomous zero-shot causal discovery from open web text."* (Causal discovery from observational text is an unsolved academic research problem; we provide deterministic transmission graphs with statistical weights).
* ❌ *"Replaces institutional quant models."* (This is an explainable decision-support and risk-attribution engine for fundamental and quant analysts).

---

## 3. MVP Scope vs. Advanced Horizon

To ensure successful delivery within the target timeline, features are strictly partitioned:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PROJECT SCOPE MATRIX                             │
├──────────────────────────────────────┬──────────────────────────────────────┤
│            IN-SCOPE (MVP)            │         DEFERRED (Advanced)          │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Universe: 30-50 liquid Indian      │ • Complete NSE 500 / Global Universe │
│   equities across 4 sectors:         │ • Automated dynamic relation         │
│   (Automotive, Steel/Metals,         │   extraction via unsupervised        │
│    Energy/Oil, IT Services)          │   relation classification / node2vec │
│ • Graph: ~100 nodes, ~250 edges      │ • Real-time WebSocket tick streaming │
│   (Commodities, Sectors, Tickers)    │ • Intraday minute-by-minute backtest │
│ • 4 Core Event Archetypes:           │ • Full order routing / execution sim │
│   - Commodity price shocks           │ • Multi-asset options / derivatives  │
│   - Import/Export policy changes     │   implied volatility propagation     │
│   - Major supply disruptions         │                                      │
│   - Macro/Interest rate shifts       │                                      │
│ • Propagation: 1 to 3 hops (BFS/     │                                      │
│   Dijkstra with decay factor)        │                                      │
│ • ML: XGBoost + SHAP explanations    │                                      │
│ • Dual-theme UI with Force-Graph map │                                      │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 4. Data Reality Check

Every data feed in this system must be real, accessible, and resilient. Below is the audited source catalog:

| Data Domain | Recommended Source | Tier | Rate Limits & Constraints | Mitigation / Architecture Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Indian Equities (OHLCV)** | `yfinance` (`.NS`, `.BO` tickers) | **Free** | ~2,000 requests/hour; potential IP throttle if unbuffered | Stored locally in TimescaleDB. Incremental daily sync with exponential backoff. |
| **Corporate Actions & Fundamentals** | `yfinance` + NSE Corporate Announcements RSS | **Free** | RSS polling every 15 mins; fundamentals refreshed quarterly | Ingestion worker stages raw JSON in Postgres `raw_financials` before parsing. |
| **Global Commodities & Forex** | Federal Reserve Economic Data (**FRED**) API + Yahoo Finance | **Free** (API key required for FRED) | FRED: 120 requests/minute. High reliability for Brent, Copper, Steel, USD/INR | Nightly batch ETL into TimescaleDB commodity tables. |
| **Macro Indicators (India)** | FRED (India CPI, Policy Rate) + RBI DBIE | **Free** | Monthly/Quarterly release cadence | Cached indefinitely with versioned release dates (point-in-time valid). |
| **Financial News / Press** | Google News RSS + Economic Times / Moneycontrol RSS | **Free** | Public RSS feeds, rate limit: ~1 request/sec | Celery Beat polling worker with RSS feed deduplication (via `sentence-transformers`). |
| **Alternative Equities API** | Alpha Vantage | **Freemium** | 25 requests/day (Free tier) | Used as a documented secondary fallback source. |

### Offline Testing & CI/CD Guarantee
To adhere strictly to engineering hygiene and CI speed:
* **All unit and integration tests run against pre-recorded mock fixtures (JSON/CSV)** stored under `tests/fixtures/`.
* No network calls are made during CI builds (`pytest`).
* Live connectors run only during manual ETL triggers or scheduled Celery background tasks.

---

## 5. Architectural Recommendations & Next Steps

1. **Keep Graph Clean:** Structure Neo4j with clear label definitions (`Company`, `Industry`, `Commodity`, `MacroFactor`, `Event`) and relationship types (`SUPPLIES`, `CONSUMES`, `COMPETES`, `IMPACTS`).
2. **Strict Time Integrity:** Store all market data and news events with timezone-aware UTC timestamps and effective market session flags.
3. **Pydantic Validation Barrier:** Isolate the LLM layer completely behind strict Pydantic schemas so language generation failure can never crash the scoring engine or inject unvalidated floats.
4. **Approval to Proceed:** Proceed to **Phase 2 (Architecture & Database Schema Design)** to draft `/docs/architecture.md` and `/docs/schema.md`.
