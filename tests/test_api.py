from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_conversation():
    response = client.post("/conversation/", json={"question": "What is this about?"})
    assert response.status_code == 200
    assert "answer" in response.json()

def test_podcast_turn():
    response = client.post("/conversation/podcast", json={})
    assert response.status_code == 200
    data = response.json()
    assert "curious" in data
    assert "explainer" in data