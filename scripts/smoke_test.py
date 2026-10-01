import sys

import httpx


BASE_URL = "http://localhost:8000"


def require(condition: bool, message: str) -> None:
    if not condition:
        print(f"FAIL: {message}")
        sys.exit(1)


with httpx.Client(timeout=5.0) as client:
    health = client.get(f"{BASE_URL}/health")
    require(health.status_code == 200, "health endpoint")

    inference = client.post(
        f"{BASE_URL}/api/v1/inference",
        json={"prompt": "smoke test", "delay_ms": 10},
    )
    require(inference.status_code == 200, "inference endpoint")

    metrics = client.get(f"{BASE_URL}/metrics")
    require("ai_service_requests_total" in metrics.text, "Prometheus metrics")

    alert = client.post(
        f"{BASE_URL}/api/v1/alerts/prometheus",
        json={
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "GPUHighUtilization", "severity": "warning"},
                    "annotations": {"summary": "Smoke-test GPU alert"},
                }
            ],
        },
    )
    require(alert.status_code == 200, "alert webhook")
    require(alert.json()["accepted"] == 1, "incident creation")

print("PASS: API, metrics and alert workflow are healthy")
