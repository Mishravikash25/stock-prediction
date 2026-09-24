"""
FastAPI REST Integration Test Suite
===================================
Tests all v1 REST API routes using httpx AsyncClient hitting an in-memory test database.
Verifies:
1. Health check (/health)
2. Events search, filtering, detail, and NLP on-demand detection (/api/v1/events)
3. Graph ripple traversal and subgraph visualization payload (/api/v1/ripple/graph)
4. Company catalog, multi-factor analysis with SHAP and dual-thesis, and timeseries (/api/v1/companies)
5. Predictions audit history and async backtest job dispatching (/api/v1/predictions)
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Verify GET /health returns 200 OK and healthy status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "HEALTHY"
        assert data["service"] == "market_ripple_backend"


@pytest.mark.asyncio
async def test_get_events_list_and_filter():
    """Verify GET /api/v1/events with pagination and archetype filtering."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Unfiltered listing
        resp = await client.get("/api/v1/events?limit=10&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) > 0

        # 2. Filter by archetype
        resp_arch = await client.get("/api/v1/events?archetype=POLICY_TAX_CHANGE")
        assert resp_arch.status_code == 200
        data_arch = resp_arch.json()
        for item in data_arch["items"]:
            assert item["archetype"] == "POLICY_TAX_CHANGE"


@pytest.mark.asyncio
async def test_get_event_by_id():
    """Verify GET /api/v1/events/{id} returns full event details with entity links."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/events/evt_2022_steel_tariff_hike")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "evt_2022_steel_tariff_hike"
        assert data["archetype"] == "POLICY_TAX_CHANGE"
        assert "extracted_entities" in data
        assert data["downstream_impact_count"] > 0


@pytest.mark.asyncio
async def test_post_events_detect_endpoint():
    """Verify POST /api/v1/events/detect performs on-demand NLP event detection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "Government of India imposes 15% export duty on steel products to control domestic prices.",
            "source_name": "TEST_FEED"
        }
        resp = await client.post("/api/v1/events/detect", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "detected_event" in data
        assert data["detected_event"]["archetype"] == "POLICY_TAX_CHANGE"
        assert "reasoning" in data["detected_event"]


@pytest.mark.asyncio
async def test_get_ripple_graph_endpoint():
    """Verify GET /api/v1/ripple/graph returns cytoscape nodes, edges, and impact summaries."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/ripple/graph?event_id=evt_2022_steel_tariff_hike&max_hops=3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_id"] == "evt_2022_steel_tariff_hike"
        assert "nodes" in data
        assert "edges" in data
        assert "impact_summary" in data
        assert len(data["nodes"]) > 0
        assert len(data["edges"]) > 0


@pytest.mark.asyncio
async def test_get_companies_list():
    """Verify GET /api/v1/companies returns target equities."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/companies")
        assert resp.status_code == 200
        companies = resp.json()
        assert isinstance(companies, list)
        assert len(companies) > 0
        tickers = [c["ticker"] for c in companies]
        assert "TATAMOTORS.NS" in tickers
        assert "TATASTEEL.NS" in tickers


@pytest.mark.asyncio
async def test_get_company_analysis_endpoint():
    """Verify GET /api/v1/companies/{ticker}/analysis returns prediction, SHAP, and dual-thesis."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/companies/TATAMOTORS.NS/analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "TATAMOTORS.NS"
        assert "prediction" in data
        assert "shap_attributions" in data
        assert "structured_report" in data

        report = data["structured_report"]
        assert len(report["bull_case"]) > 50
        assert len(report["bear_case"]) > 50
        assert len(report["uncertainty_analysis"]) > 50


@pytest.mark.asyncio
async def test_get_company_timeseries_endpoint():
    """Verify GET /api/v1/companies/{ticker}/timeseries returns price and sentiment points."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/companies/MARUTI.NS/timeseries")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "MARUTI.NS"
        assert "points" in data
        assert len(data["points"]) > 0
        assert "close" in data["points"][0]
        assert "rolling_sentiment" in data["points"][0]


@pytest.mark.asyncio
async def test_get_predictions_history_and_accuracy():
    """Verify GET /api/v1/predictions returns prediction ledger and accuracy summary."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/predictions")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "accuracy_summary" in data
        assert "predictions" in data
        assert data["accuracy_summary"]["horizon_7d_directional_acc"] > 0.0


@pytest.mark.asyncio
async def test_post_backtest_run_job_and_poll():
    """Verify POST /api/v1/predictions/backtest/run launches async job."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "train_start_date": "2020-01-01",
            "train_end_date": "2022-06-30",
            "val_start_date": "2022-07-01",
            "val_end_date": "2022-12-31",
            "test_start_date": "2023-01-01",
            "test_end_date": "2023-12-31",
            "embargo_window_days": 7
        }
        resp = await client.post("/api/v1/predictions/backtest/run", json=payload)
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["status"] in ["QUEUED", "RUNNING", "COMPLETED"]

        # Poll job status
        poll_resp = await client.get(f"/api/v1/predictions/jobs/{data['job_id']}")
        assert poll_resp.status_code == 200
        poll_data = poll_resp.json()
        assert "job_id" in poll_data


@pytest.mark.asyncio
async def test_404_error_on_nonexistent_company():
    """Verify 404 error when querying non-existent ticker."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/companies/NON_EXISTENT_COMPANY_XYZ/analysis")
        assert resp.status_code == 404
