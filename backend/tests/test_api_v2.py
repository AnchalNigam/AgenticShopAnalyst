"""Tests for AgenticShop V2 API endpoint and Plan-and-Solve engine."""

from __future__ import annotations

from fastapi.testclient import TestClient
from app.main import app


def test_v2_analyst_query_validation() -> None:
    """Verify input validation on V2 endpoint."""
    with TestClient(app) as client:
        # Too short question
        response = client.post("/api/v2/analyst/query", json={"question": "x"})
        assert response.status_code == 422


def test_v2_analyst_query_endpoint_live() -> None:
    """Verify end-to-end V2 execution for compound question through HTTP POST."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v2/analyst/query",
            json={
                "question": "Compare our revenue growth between July and August 2026 and identify the top contributing category."
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "plan" in data
        assert len(data["plan"]["tasks"]) >= 2
        assert len(data["task_results"]) >= 2
        assert "scratchpad" in data
        assert len(data["executive_brief"]) > 20
        assert len(data["execution_steps"]) >= 3

        # Check plan decomposition step exists in trace
        plan_step = next(s for s in data["execution_steps"] if s["action"] == "plan_decomposition")
        assert plan_step is not None
