# Architecture Notes

## Goal

Provide a compact but production-minded observability design for GPU-backed AI inference workloads.

The design focuses on four operational questions:

1. Is the service available?
2. Is inference becoming slow or unreliable?
3. Is capacity pressure building?
4. Can an operator move from an alert to relevant evidence and a safe runbook quickly?

## Signal flow

### Metrics

FastAPI exposes Prometheus-format metrics at `/metrics`.

Prometheus scrapes the application, evaluates alert rules and remote-writes samples to VictoriaMetrics. Grafana uses VictoriaMetrics as the primary dashboard data source.

In a GPU-enabled Kubernetes cluster, DCGM Exporter exposes NVIDIA GPU metrics that can be scraped by the cluster monitoring stack.

### Logs

Application logs are emitted as structured JSON. Fluent Bit tails container logs and forwards them to Elasticsearch. Kibana provides centralized search and investigation.

Useful fields include:

- timestamp
- log level
- request ID
- route
- HTTP status
- latency
- model name
- incident ID

### Alerts and incidents

Prometheus evaluates symptoms such as high p95 latency, elevated 5xx ratio and queue pressure.

Alertmanager groups alerts and sends them to the FastAPI monitoring webhook. The incident engine normalizes each alert into an incident and maps it to a runbook-oriented recommendation.

This project deliberately defaults to **recommendation-only remediation**. In a production system, automated cluster mutations should be guarded by explicit policy, RBAC, approvals, rollout safety and audit logging.

## Why these metrics?

| Signal | Operational question |
|---|---|
| Request rate | Is workload volume changing? |
| p95 latency | Is user-visible performance degrading? |
| 5xx error rate | Is inference reliability degrading? |
| Queue depth | Is demand exceeding processing capacity? |
| In-flight requests | Is the service becoming saturated? |
| DCGM GPU utilization | Are accelerators saturated or underused? |
| DCGM framebuffer memory | Is model/workload placement creating memory pressure? |

## Scaling path

For a larger environment:

- run Prometheus per cluster or use an agent-based collection strategy
- retain long-term metrics in a clustered VictoriaMetrics deployment
- add service, cluster and model dimensions to dashboards
- introduce SLOs and burn-rate alerts
- use OpenTelemetry for traces
- centralize logs with retention tiers and privacy controls
- integrate incident ownership and paging
- put automated remediation behind a policy engine and least-privilege service account

## Security considerations

Observability data can contain sensitive operational context. Production deployment should enforce:

- authenticated access to Grafana/Kibana/monitoring APIs
- TLS between components
- secret management
- log redaction
- retention controls
- Kubernetes NetworkPolicies
- least-privilege RBAC
- immutable incident/audit records for automated actions
