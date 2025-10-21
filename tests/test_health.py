from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    response_data = r.json()
    assert response_data["status"] == "ok"
    assert "database" in response_data
    assert response_data["database"] in ["connected", "disconnected"]
