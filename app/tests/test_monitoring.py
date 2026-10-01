from monitoring import IncidentStore


def test_gpu_alert_returns_gpu_runbook():
    store = IncidentStore()
    incident = store.add(
        {
            "status": "firing",
            "labels": {"alertname": "GPUHighUtilization", "severity": "warning"},
            "annotations": {"summary": "GPU pressure"},
        }
    )
    assert "DCGM" in incident["recommended_action"]
    assert incident["execution_mode"] == "recommendation_only"


def test_error_alert_returns_log_investigation():
    store = IncidentStore()
    incident = store.add(
        {
            "status": "firing",
            "labels": {"alertname": "High5xxErrorRate"},
            "annotations": {},
        }
    )
    assert "error logs" in incident["recommended_action"]
