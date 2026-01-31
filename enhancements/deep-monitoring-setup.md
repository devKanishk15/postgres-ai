# Enhancement: Deep PostgreSQL Monitoring

Enabled table-level statistics and query execution monitoring (via `pg_stat_statements`) in both the exporter and the AI chatbot.

## Components Enabled

### 1. PostgreSQL Exporter Configuration
- **Custom Queries**: Added `scripts/exporter-queries.yaml` to collect metrics from `pg_stat_user_tables` and `pg_stat_statements`.
- **Docker Integration**: Updated `docker-compose.yml` to mount the query file and enabled `PG_EXPORTER_AUTO_DISCOVER_DATABASES`.

### 2. AI Chatbot Integration
- **PromQL Builder**: Updated `chatbot/promql_builder.py` with mappings for:
    - `table_size`: Total disk space per table.
    - `sequential_scans` / `index_scans`: Scan counts per table.
    - `query_calls` / `query_execution_time`: Performance stats per SQL statement.

### 3. Grafana Visualization
- Added specialized dashboards:
    - **PostgreSQL Top Queries**: SQL execution analysis.
    - **Postgres Tables**: Table and index deep-dive.

## Verification
- Verified metrics export via Prometheus API.
- Confirmed `datname` labeling works for cross-database filtering.
