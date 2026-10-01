from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_inference():
    response = client.post("/api/v1/inference", json={"prompt": "hello", "delay_ms": 0})
    assert response.status_code == 200
    assert response.json()["model"] == "demo-llm"


def test_alert_webhook():
    response = client.post(
        "/api/v1/alerts/prometheus",
        json={
            "status": "firing",
            "alerts": [
                {
                    "labels": {"alertname": "HighInferenceLatency", "severity": "warning"},
                    "annotations": {"summary": "Latency is elevated"},
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["accepted"] == 1
