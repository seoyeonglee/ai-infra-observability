from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class IncidentStore:
    def __init__(self, maxlen: int = 100) -> None:
        self._items: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def add(self, alert: dict[str, Any]) -> dict[str, Any]:
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        name = labels.get("alertname", "UnknownAlert")
        severity = labels.get("severity", "warning")
        status = alert.get("status", "firing")

        recommendation = self._recommend(name=name, labels=labels, annotations=annotations)

        incident = {
            "id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "alert_name": name,
            "severity": severity,
            "labels": labels,
            "summary": annotations.get("summary", ""),
            "description": annotations.get("description", ""),
            "recommended_action": recommendation,
            "execution_mode": "recommendation_only",
        }
        self._items.appendleft(incident)
        return incident

    def list(self) -> list[dict[str, Any]]:
        return list(self._items)

    @staticmethod
    def _recommend(name: str, labels: dict[str, Any], annotations: dict[str, Any]) -> str:
        lowered = name.lower()

        if "gpu" in lowered:
            return (
                "Inspect DCGM GPU utilization, memory pressure and temperature; "
                "verify workload placement and consider scaling or rescheduling after policy checks."
            )
        if "latency" in lowered:
            return (
                "Check p95 latency, queue depth and replica saturation; correlate with recent error logs "
                "before considering horizontal scaling."
            )
        if "error" in lowered or "5xx" in lowered:
            return (
                "Inspect recent structured error logs and failing routes; validate dependency health "
                "and rollback only through an approved deployment process."
            )
        if "queue" in lowered:
            return (
                "Inspect inference queue pressure and worker utilization; verify capacity before scaling."
            )
        if "down" in lowered or "unavailable" in lowered:
            return (
                "Check pod health, readiness probes and recent deployment events; restore service using "
                "the approved runbook."
            )

        hint = annotations.get("runbook_hint") or labels.get("component")
        if hint:
            return f"Inspect the affected component and follow the approved runbook. Context: {hint}"

        return "Inspect correlated metrics and logs, identify impact, and follow the approved runbook."
