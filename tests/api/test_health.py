import os
import sys

from fastapi.testclient import TestClient


API_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api"))
sys.path.append(API_PATH)

from main import app  # noqa: E402


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "services" in payload
