from __future__ import annotations

import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

from logging_config import configure_logging
from monitoring import IncidentStore

configure_logging()
logger = logging.getLogger("ai-infra-observability")

REQUESTS = Counter(
    "ai_service_requests_total",
    "Total HTTP requests handled by the AI service",
    ["route", "method", "status"],
)
ERRORS = Counter(
    "ai_service_errors_total",
    "Total failed AI inference requests",
    ["model", "error_type"],
)
LATENCY = Histogram(
    "ai_service_request_duration_seconds",
    "Request duration in seconds",
    ["route"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
IN_FLIGHT = Gauge(
    "ai_service_in_flight_requests",
    "Current requests being processed",
)
INFERENCE_QUEUE = Gauge(
    "ai_inference_queue_depth",
    "Synthetic inference queue depth",
    ["model"],
)
MODEL_HEALTH = Gauge(
    "ai_model_health",
    "Model health where 1=healthy and 0=unhealthy",
    ["model"],
)
INFERENCE_LATENCY = Histogram(
    "ai_inference_duration_seconds",
    "Synthetic model inference duration",
    ["model"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

MODEL_NAME = "demo-llm"
MODEL_HEALTH.labels(MODEL_NAME).set(1)
INFERENCE_QUEUE.labels(MODEL_NAME).set(0)

incidents = IncidentStore()


class InferenceRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    simulate_error: bool = False
    delay_ms: int | None = Field(default=None, ge=0, le=5000)


class AlertmanagerPayload(BaseModel):
    status: str
    alerts: list[dict[str, Any]] = []


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("service_started")
    yield
    logger.info("service_stopped")


app = FastAPI(
    title="AI Infra Observability API",
    version="1.0.0",
    description="Reference monitoring API for GPU-backed AI inference infrastructure.",
    lifespan=lifespan,
)


@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    route = request.url.path
    started = time.perf_counter()
    IN_FLIGHT.inc()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["x-request-id"] = request_id
        return response
    finally:
        elapsed = time.perf_counter() - started
        IN_FLIGHT.dec()
        REQUESTS.labels(route=route, method=request.method, status=str(status_code)).inc()
        LATENCY.labels(route=route).observe(elapsed)
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "route": route,
                "status_code": status_code,
                "latency_ms": round(elapsed * 1000, 2),
            },
        )


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/overview")
async def overview():
    return {
        "service": "ai-infra-observability",
        "model": MODEL_NAME,
        "health": "healthy",
        "incident_count": len(incidents.list()),
        "observability_backends": {
            "metrics": ["Prometheus", "VictoriaMetrics", "Grafana"],
            "logs": ["Fluent Bit", "Elasticsearch", "Kibana"],
            "alerts": ["Prometheus", "Alertmanager"],
            "gpu": ["NVIDIA DCGM Exporter (Kubernetes)"],
        },
    }


@app.post("/api/v1/inference")
async def inference(payload: InferenceRequest):
    queue_depth = random.randint(0, 15)
    INFERENCE_QUEUE.labels(MODEL_NAME).set(queue_depth)

    delay = payload.delay_ms / 1000 if payload.delay_ms is not None else random.uniform(0.05, 0.45)
    with INFERENCE_LATENCY.labels(MODEL_NAME).time():
        await asyncio.sleep(delay)

    if payload.simulate_error:
        ERRORS.labels(MODEL_NAME, "simulated").inc()
        logger.error("simulated_inference_failure", extra={"model": MODEL_NAME})
        return Response(
            content='{"detail":"simulated inference failure"}',
            status_code=500,
            media_type="application/json",
        )

    return {
        "model": MODEL_NAME,
        "result": f"observed:{payload.prompt[:80]}",
        "latency_ms": round(delay * 1000, 2),
        "queue_depth": queue_depth,
    }


@app.get("/api/v1/incidents")
async def list_incidents():
    return {"items": incidents.list()}


@app.post("/api/v1/alerts/prometheus")
async def receive_alerts(payload: AlertmanagerPayload):
    normalized = []
    for alert in payload.alerts:
        normalized_alert = {**alert, "status": alert.get("status", payload.status)}
        incident = incidents.add(normalized_alert)
        normalized.append(incident)
        logger.warning(
            "alert_received",
            extra={"incident_id": incident["id"]},
        )
    return {"accepted": len(normalized), "incidents": normalized}
