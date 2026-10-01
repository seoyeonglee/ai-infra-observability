# AI Infra Observability

Production-minded observability reference project for **GPU-backed AI inference infrastructure**.

This repository demonstrates how to monitor an AI service end to end using **Python, FastAPI, Prometheus, VictoriaMetrics, Grafana, EFK, Alertmanager, Kubernetes, and NVIDIA DCGM Exporter**.

The project is intentionally designed so that the full application/metrics/logging pipeline can be exercised on a laptop without a GPU, while Kubernetes deployments can attach real GPU telemetry through DCGM Exporter.

## What this project demonstrates

- Python/FastAPI monitoring API for AI inference workloads
- Prometheus metric scraping and alert rules
- VictoriaMetrics remote-write storage
- Grafana dashboard provisioning
- EFK-based structured log collection and search
- Alertmanager webhook integration
- Rule-based incident classification and safe automated response recommendations
- Kubernetes deployment manifests
- NVIDIA GPU metric collection with DCGM Exporter
- CI tests for API and incident logic
- Load generation and smoke-test utilities

## Architecture

~~~mermaid
flowchart LR
    C[Load Generator / Client] --> API[FastAPI AI Monitoring Service]
    API -->|/metrics| P[Prometheus]
    P -->|remote_write| VM[VictoriaMetrics]
    VM --> G[Grafana]
    P --> AM[Alertmanager]
    AM -->|Webhook| API

    API -->|JSON logs| FB[Fluent Bit]
    FB --> ES[Elasticsearch]
    ES --> K[Kibana]

    K8S[Kubernetes Cluster] --> P
    DCGM[NVIDIA DCGM Exporter] -->|GPU metrics| P

    API --> IR[Incident / Runbook Engine]
    AM --> IR
~~~

## Local stack

| Layer | Component | Purpose |
|---|---|---|
| Application | FastAPI | AI workload API, health, metrics, monitoring endpoints |
| Metrics | Prometheus | Scraping, alert evaluation |
| Long-term metrics | VictoriaMetrics | Prometheus-compatible metric storage |
| Visualization | Grafana | Provisioned observability dashboard |
| Logs | Fluent Bit | Structured log collection |
| Log storage | Elasticsearch | Searchable centralized logs |
| Log UI | Kibana | Log exploration |
| Alerting | Alertmanager | Alert routing to monitoring API |
| GPU monitoring | DCGM Exporter | NVIDIA GPU telemetry in Kubernetes |

## Key signals

### Service metrics
- request count and error count
- request latency histogram
- in-flight requests
- synthetic inference latency
- synthetic inference queue depth
- model health/state

### GPU metrics in Kubernetes
DCGM Exporter supplies real NVIDIA GPU signals such as utilization, memory usage, temperature and power where NVIDIA GPUs are available.

The local Docker Compose demo does **not** fabricate physical GPU telemetry. It demonstrates the rest of the pipeline without requiring GPU hardware.

## Quick start

### 1. Start the stack

~~~bash
docker compose up --build
~~~

### 2. Generate traffic

~~~bash
python scripts/generate_load.py --requests 200 --concurrency 10
~~~

### 3. Run a smoke test

~~~bash
python scripts/smoke_test.py
~~~

### 4. Open the tools

- API docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- VictoriaMetrics: http://localhost:8428
- Grafana: http://localhost:3000
- Kibana: http://localhost:5601
- Alertmanager: http://localhost:9093

Default local Grafana credentials are configured for demonstration only and should be changed outside a local environment.

## API overview

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness/health |
| `/metrics` | GET | Prometheus exposition |
| `/api/v1/overview` | GET | Current application observability snapshot |
| `/api/v1/inference` | POST | Simulated inference workload for telemetry generation |
| `/api/v1/incidents` | GET | Recent alert/incident decisions |
| `/api/v1/alerts/prometheus` | POST | Alertmanager webhook receiver |

## Automated response model

The project separates **detection** from **action**.

Alertmanager sends active alerts to the FastAPI webhook. The incident engine classifies the event and returns a runbook-oriented action such as:

- inspect recent error logs
- check queue pressure
- verify replica saturation
- inspect GPU memory/utilization
- consider scaling the workload

For safety and portability, the default implementation records and recommends actions rather than mutating a cluster automatically. This makes the behavior auditable and prevents a portfolio demo from executing unsafe infrastructure changes.

The code is structured so a production implementation can place approved Kubernetes actions behind explicit policy and RBAC controls.

## Example alert scenarios

- high 5xx error rate
- elevated p95 request latency
- high inference queue depth
- target unavailable

Prometheus evaluates alert rules and Alertmanager forwards the event to the API, where the incident logic records a normalized incident and response recommendation.

## Kubernetes

The `kubernetes/` directory contains:

- namespace and application deployment
- service and Prometheus scrape annotations
- resource requests/limits and probes
- NVIDIA DCGM Exporter DaemonSet
- GPU alerting configuration examples

Apply the manifests to a cluster after reviewing image names and environment-specific settings.

~~~bash
kubectl apply -f kubernetes/
~~~

## Observability design decisions

### Why Prometheus + VictoriaMetrics?
Prometheus handles collection and alert evaluation well. VictoriaMetrics provides a Prometheus-compatible storage path and demonstrates a scalable remote-write architecture.

### Why EFK?
Fluent Bit is lightweight for container log forwarding, while Elasticsearch/Kibana provide familiar centralized search and analysis.

### Why structured JSON logs?
Structured logs make correlation, filtering, alert investigation and downstream automation much easier than free-form text.

### Why expose a monitoring API?
Operational systems often need a normalized API that internal tools can consume without directly coupling to every monitoring backend.

## Repository structure

~~~text
.
├── app/
│   ├── main.py
│   ├── monitoring.py
│   ├── logging_config.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
├── prometheus/
├── alertmanager/
├── grafana/
│   ├── dashboards/
│   └── provisioning/
├── fluent-bit/
├── kubernetes/
├── scripts/
├── docs/
├── docker-compose.yml
└── .github/workflows/ci.yml
~~~

## Test

~~~bash
pip install -r app/requirements.txt
pytest app/tests -q
~~~

## Security and production considerations

A real production deployment should additionally include:

- authentication/authorization for operational APIs
- TLS and secret management
- Elasticsearch/Grafana authentication hardening
- Kubernetes NetworkPolicies
- least-privilege service accounts and RBAC
- retention and PII/log-redaction policies
- alert deduplication, escalation and ownership
- SLO/SLI definitions tied to business impact
- controlled, auditable remediation policies

## Scope

This is a portfolio/reference implementation focused on observability architecture and operational problem solving. It is not presented as a substitute for hands-on production GPU-cluster operations.

## License

MIT
