"""API smoke tests (health + schema imports)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_document_status_empty():
    res = client.get("/api/document")
    assert res.status_code == 200
    body = res.json()
    assert "indexed" in body


def test_query_without_document():
    res = client.post("/api/query", json={"question": "What is this about?"})
    assert res.status_code == 400
