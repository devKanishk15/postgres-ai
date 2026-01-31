# Grafana Monitoring Setup

This folder contains the configuration and provisioning for Grafana to visualize PostgreSQL and system metrics.

## Components

### 1. Dashboards (`/dashboards`)
- **Node Exporter Full (ID 1860)**: Comprehensive system metrics including CPU, Memory, Disk, and Network.
- **PostgreSQL Database (ID 9628)**: Detailed database overview including connections, throughput, and cache hits.
- **PostgreSQL Top Queries (ID 12485)**: Query performance analysis using `pg_stat_statements` (Slow queries, frequency).
- **Postgres Tables (ID 14114)**: deep-dive into table/index sizes, vacuum status, and tuple activity.

### 2. Provisioning (`/provisioning`)
- **Data Sources**: Automatically configures Prometheus (`http://prometheus:9090`) as the default data source.
- **Dashboards**: Automatically loads JSON files from the `/dashboards` directory into Grafana.

## How to Access

1.  Start the stack:
    ```bash
    docker-compose up -d
    ```
2.  Open your browser to: `http://localhost:3000`
3.  **Login**:
    - **Username**: `admin`
    - **Password**: `admin`
4.  Navigate to **Dashboards** -> **Browse** to see the pre-loaded dashboards.

## Configuration Details

- **Docker Service**: Defined in `docker-compose.yml` under the `grafana` service.
- **Volumes**:
    - `./grafana/provisioning:/etc/grafana/provisioning`: Configures data sources and providers.
    - `./grafana/dashboards:/var/lib/grafana/dashboards`: Source for dashboard JSON files.
