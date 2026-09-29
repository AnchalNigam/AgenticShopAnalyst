"""Tests for Analyst FastAPI routes and Web UI endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_serve_web_ui() -> None:
    """Verify that root endpoint serves the index.html dashboard."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "AgenticShop" in response.text
        assert "AI Business Analyst" in response.text


def test_get_system_overview() -> None:
    """Verify overview endpoint returns DB table counts and metadata."""
    with TestClient(app) as client:
        response = client.get("/api/v1/analyst/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["database_connected"] is True
        assert "orders" in data["table_counts"]
        assert len(data["sample_questions"]) >= 4


def test_analyst_query_validation() -> None:
    """Verify input validation on the query endpoint."""
    with TestClient(app) as client:
        # Too short question
        response = client.post("/api/v1/analyst/query", json={"question": "a"})
        assert response.status_code == 422


def test_analyst_query_endpoint_live() -> None:
    """Verify end-to-end execution through the HTTP POST endpoint."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analyst/query",
            json={"question": "What was our revenue in August?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["sql_query"] is not None
        assert "revenue" in data["sql_query"].lower()
        assert len(data["query_results"]) > 0
        assert len(data["execution_steps"]) >= 2
        tool_step = next(s for s in data["execution_steps"] if s["action"] == "tool_call")
        assert tool_step["tool_name"] == "execute_sql_query"


def test_analyst_query_endpoint_simulate_error() -> None:
    """Verify endpoint handles simulate_error=True and returns self_correction_attempt step."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analyst/query",
            json={"question": "What was our revenue in August?", "simulate_error": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Check that self_correction_attempt is present in execution steps
        actions = [s["action"] for s in data["execution_steps"]]
        assert "self_correction_attempt" in actions
        assert "tool_call" in actions
        assert "synthesis" in actions
