from fastapi.testclient import TestClient

from app.main import app


def test_health_check_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data
        assert "database" in data
        if response.status_code == 200:
            assert data == {"status": "ok", "database": "connected"}


def test_health_check_degraded_when_db_down(monkeypatch) -> None:
    monkeypatch.setattr("app.main.check_db_health", lambda: False)
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json() == {"status": "degraded", "database": "disconnected"}

