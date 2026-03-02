import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_genres():
    response = client.get("/api/genres")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7
    assert data[0]["id"] == "adventure"
    assert "name" in data[0]
    assert "description" in data[0]


def test_get_historical_events():
    response = client.get("/api/historical-events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 20
    first = data[0]
    assert "id" in first
    assert "title" in first
    assert "figure" in first
    assert "year" in first
    assert "summary" in first
    assert "key_facts" in first


def test_historical_event_has_shivaji():
    response = client.get("/api/historical-events")
    data = response.json()
    ids = [e["id"] for e in data]
    assert "shivaji-agra-escape" in ids
