# Explainable AI Market Ripple Engine

> **Real-Time Shock Propagation & Explainable Multi-Hop Asset Impact Engine**

An end-to-end quantitative financial terminal and explainable AI system that detects macroeconomic, regulatory, supply chain, and commodity shock events, propagates them through a multi-hop knowledge graph with $\alpha^{\text{hop}}$ distance decay, computes multi-factor asset impact scores via XGBoost with local SHAP feature attributions, and generates schema-constrained dual-thesis reports with strict zero-hallucination guarantees.

---

## 1. System Architecture & Tech Stack

- **Relational & Time Series**: PostgreSQL 16 with TimescaleDB hypertables
- **Knowledge Graph**: Neo4j 5.20 (Community Edition) & NetworkX for topological traversal
- **ML / Scoring Engine**: XGBoost (primary) + LightGBM (benchmark) + TreeSHAP
- **NLP & Event Extraction**: spaCy NER + LLM-behind-a-schema with Pydantic v2 validation
- **Backend API**: FastAPI + Celery + Redis for asynchronous job scheduling
- **Frontend Terminal**: React 19 + TypeScript + Vite + Tailwind CSS with dark/light CSS variable tokens & Recharts

---

## 2. Running Locally

Follow these step-by-step commands to set up and run the entire development environment locally.

### Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** and `npm` installed
- **Docker & Docker Compose** (for running local databases)

---

### Step 1: Start the Development Databases
Run the lightweight dev compose file which launches only the 3 required databases:

```bash
docker compose -f docker-compose.dev.yml up -d
```

This starts:
- **PostgreSQL / TimescaleDB** on `localhost:5432` (`postgres:password`, DB: `market_ripple`)
- **Neo4j Graph Database** on `localhost:7474` (HTTP) and `localhost:7687` (Bolt) (`neo4j:market_ripple_secret`)
- **Redis Broker** on `localhost:6379`

> *Note*: If developing without Docker, the backend automatically defaults to an in-memory SQLite store and seed graphs with full functionality.

---

### Step 2: Install Python & Frontend Dependencies

#### Python Backend & ML:
```bash
pip install -r requirements.txt
```

#### React Frontend:
```bash
cd frontend
npm install
cd ..
```

---

### Step 3: Run Database Migrations & Seeds

Apply the initial schema migrations and seed the curated knowledge graph nodes, supply chain edges, and historical events:

```bash
# Apply Alembic schema migrations
alembic -c backend/alembic.ini upgrade head

# Seed domain master data, sectors, commodities, companies, and Neo4j graph
python -m backend.app.db.seeds.seed_runner
```

---

### Step 4: Start the FastAPI Backend Server

Start the live REST backend on port `8000`:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

- API Docs (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 5: Start the React + Vite Frontend Terminal

In a separate terminal window, launch the frontend development server:

```bash
cd frontend
npm run dev
```

- Financial Terminal UI: [http://localhost:5173](http://localhost:5173)

---

### Step 6: Run the Full Test Suite

Run the unit and integration test suite across all modules (Ingestion, DB, NLP, Graph, Scoring, Explanation, Backtesting, API):

```bash
python -m pytest -v --cov=backend --cov=ml
```

---

### Step 7: Run a Point-In-Time Backtest via CLI

Execute a walk-forward historical event replay with strict chronological purge and embargo buffers:

```bash
python -m ml.evaluation.cli --model xgboost --embargo 14
```

Options:
- `--model`: `xgboost` (default) or `lightgbm`
- `--embargo`: Embargo buffer window in days (default: `14`)
- `--train-start`, `--train-end`, `--val-start`, `--val-end`, `--test-start`, `--test-end`: Custom chronological date ranges
- `--json`: Output full structured JSON report

---

## 3. Key Pages & Features

1. **Dashboard** (`/`):
   - High-level metric cards, sector shock matrix, live shock feed, and top shock propagations.
2. **Event Explorer** (`/events`):
   - Categorized historical shocks with archetype filtering (`COMMODITY_SHOCK`, `POLICY_TAX_CHANGE`, `SUPPLY_DISRUPTION`, `MACRO_RATE_SHIFT`) and on-demand ad-hoc headline classifier modal.
3. **Interactive Ripple Map** (`/ripple`):
   - Multi-hop shock network canvas with $\alpha^{\text{hop}}$ decay slider, node inspector, and downstream transmission pathways.
4. **Company Analysis** (`/company/:ticker`):
   - Multi-factor XGBoost impact score, price/sentiment chart, local SHAP feature attributions bar chart, and schema-constrained Dual-Thesis card (Bull Case vs. Bear Case vs. Uncertainty).
5. **Prediction History & Backtesting** (`/predictions`):
   - Immutable audit ledger with 1D/7D/30D directional accuracy metrics, Brier calibration scores, and walk-forward backtest job runner.
