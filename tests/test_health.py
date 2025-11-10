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


def test_security_headers_present():
    """Проверка наличия security headers"""
    response = client.get("/health")

    headers = response.headers
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    assert "Referrer-Policy" in headers


def test_health_no_auth_required():
    """Health endpoint доступен без аутентификации"""
    response = client.get("/health")
    assert response.status_code == 200


def test_login_endpoint_exists():
    """Проверка что эндпоинт логина доступен"""
    response = client.post("/login", json={"username": "test", "password": "test"})
    assert response.status_code != 404
