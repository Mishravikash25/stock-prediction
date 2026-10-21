# Explainable AI Market Ripple Engine

> **Real-Time Shock Propagation & Explainable Multi-Hop Asset Impact Engine**

An end-to-end quantitative financial terminal and explainable AI system that detects macroeconomic, regulatory, supply chain, and commodity shock events, propagates them through a multi-hop knowledge graph with hop-distance decay, computes multi-factor asset impact scores using XGBoost and SHAP feature attributions, and generates structured dual-thesis reports.

---

## 1. System Architecture & Tech Stack

- **Database**: PostgreSQL 16 with TimescaleDB
- **Knowledge Graph**: Neo4j 5.20 and NetworkX
- **ML / Scoring**: XGBoost, LightGBM, TreeSHAP
- **NLP**: spaCy NER and Pydantic validation
- **Backend**: FastAPI, Celery, Redis
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Recharts

---

## 2. Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker and Docker Compose

### Step 1: Start Development Databases
```bash
docker compose -f docker-compose.dev.yml up -d
```

### Step 2: Install Dependencies

**Python backend:**
```bash
pip install -r requirements.txt
```

**React frontend:**
```bash
cd frontend
npm install
cd ..
```

### Step 3: Run Migrations and Seeds
```bash
alembic -c backend/alembic.ini upgrade head
python -m backend.app.db.seeds.seed_runner
```

### Step 4: Start the Backend
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

### Step 5: Start the Frontend
Open a second terminal:
```bash
cd frontend
npm run dev
```
- Frontend: [http://localhost:5173](http://localhost:5173/)

### Step 6: Run Tests
```bash
python -m pytest -v --cov=backend --cov=ml
```

### Step 7: Run a Historical Backtest
```bash
python -m ml.evaluation.cli --model xgboost --embargo 14
```
Available options include `--model`, `--embargo`, chronological date-range arguments, and `--json`, subject to the CLI implementation.

---

## 3. Key Pages & Features

- **Dashboard (`/`)** — Metric cards, sector shock matrix, live shock feed, and shock propagation summaries.
- **Event Explorer (`/events`)** — Historical shock categories and headline classification.
- **Interactive Ripple Map (`/ripple`)** — Multi-hop shock network, decay slider, and transmission pathways.
- **Company Analysis (`/company/:ticker`)** — Impact scores, price and sentiment charts, SHAP attributions, and bull/bear thesis analysis.
- **Prediction History (`/predictions`)** — Prediction audit history, directional accuracy metrics, calibration scores, and backtesting.

> *Note*: Features and commands depend on the actual implementation and project configuration.
