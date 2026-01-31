# Enhancement: Node Exporter Integration

## Overview
To provide a more comprehensive view of database performance, we have integrated `node_exporter` into the monitoring stack. While `postgres_exporter` provides deep insights into PostgreSQL internals, `node_exporter` provides essential system-level context such as CPU pressure, memory exhaustion, and I/O wait times.

## Architecture Changes
We added a new container to the `docker-compose.yml` stack:
- **Service Name**: `node-exporter`
- **Image**: `prom/node-exporter:latest`
- **Port**: `9100` (internal and mapped to host)
- **Scrape Job**: Added to `prometheus/prometheus.yml` under the job name `node`.

## New Metrics Collected
The following system metrics are now available to the AI chatbot and can be used for analysis:

### CPU Metrics
- **CPU Load (1m, 5m, 15m)**: Tracks system load averages. High load with low CPU utilization often indicates I/O bottlenecks.
- **CPU Utilization (Total)**: Percentage of CPU in use.
- **CPU Utilization (User)**: Time spent in user-space processes.
- **CPU Utilization (I/O Wait)**: Percentage of time the CPU is idle while waiting for disk I/O. This is critical for database performance tuning.

### Memory Metrics
- **Memory Utilization**: Percentage of system memory currently in use.

## Chatbot Integration
The `PromQLBuilder` class has been updated with templates for these new metrics. The AI agent can now:
1. Detect system-level bottlenecks during the **SCAN** phase.
2. Correlate PostgreSQL lock contention or slow queries with high CPU or I/O wait during the **CORRELATE** phase.
3. Suggest hardware upgrades or resource limiting if the system is over-saturated during the **PROPOSE** phase.

## Troubleshooting
If system metrics are missing:
1. Check if the `node-exporter` container is running: `docker compose ps`
2. Verify Prometheus can reach the exporter: Check targets at `http://localhost:9090/targets`
3. Ensure the volumes for `/proc`, `/sys`, and `/` are correctly mounted in `docker-compose.yml`.
