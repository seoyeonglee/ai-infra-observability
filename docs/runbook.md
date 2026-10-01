# Example Incident Runbook

## High inference latency

**Detection**

`HighInferenceLatency` fires when p95 inference API latency stays above the configured threshold.

**Investigation**

1. Check request rate and queue depth.
2. Compare in-flight requests with replica count.
3. Search structured logs for slow/erroring requests.
4. In a GPU cluster, inspect DCGM utilization and framebuffer memory.
5. Check recent deployments and dependency health.

**Decision**

- High request volume + queue pressure: evaluate horizontal capacity.
- High GPU memory pressure: inspect model footprint/workload placement.
- Error spike after deployment: use the approved rollback process.
- Dependency degradation: contain the downstream failure before scaling the API.

## High 5xx error ratio

**Detection**

`High5xxErrorRate` fires when the ratio of server errors exceeds the configured threshold.

**Investigation**

1. Filter logs by status code and route.
2. Correlate request IDs with exceptions.
3. Check whether failures are isolated to one model/version.
4. Check dependencies and recent changes.

**Response principle**

Do not restart or scale blindly. Identify the failure mode first and use a controlled remediation path.

## GPU high utilization

**Detection**

`GPUHighUtilization` is based on DCGM metrics in a GPU-enabled Kubernetes environment.

**Investigation**

1. Confirm sustained utilization rather than a short workload burst.
2. Check inference queue depth and request rate.
3. Inspect GPU memory use and temperature.
4. Compare workload distribution across nodes/devices.

**Possible action**

Scale or redistribute workloads only after capacity and placement evidence supports the action.
