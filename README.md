# PostgreSQL Debugging Chatbot

An AI-powered chatbot for PostgreSQL performance analysis and incident Root Cause Analysis (RCA). Uses time-series metrics from Prometheus and OpenAI function calling for intelligent database debugging.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Environment                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐ │
│  │  PostgreSQL  │────▶│ postgres_exporter│────▶│    Prometheus    │ │
│  │   :5432      │     │      :9187       │     │      :9090       │ │
│  └──────────────┘     └──────────────────┘     └────────┬─────────┘ │
│                                                          │          │
│                                                          ▼          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Chatbot API (:8000)                        │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │              AI Reasoning Loop                          │  │  │
│  │  │   SCAN ──▶ CORRELATE ──▶ PROPOSE                       │  │  │
│  │  │   (Anomaly   (Root        (DBA-Level                   │  │  │
│  │  │   Detection)  Cause)       Fix)                        │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (set in `.env`)

### 1. Clone and Configure

```bash
cd postgres-ai

# Edit .env with your OpenAI API key (already configured)
cat .env
```

### 2. Start the Stack

```bash
docker compose up -d
```

### 3. Verify Services

```bash
# Check all containers are running
docker compose ps

# Verify Prometheus is scraping metrics
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'

# Check chatbot health
curl http://localhost:8000/health
```

### 4. Query the Chatbot

```bash
# Ask about database health
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How is the database performing right now?"}'

# Analyze a specific time range
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What happened to the database in the last 30 minutes?"}'

# Investigate a specific issue
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check for connection exhaustion issues"}'
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Service health check |
| `/db-health` | GET | Current database health metrics |
| `/chat` | POST | Main chat endpoint for analysis |
| `/parse-time` | POST | Parse natural language time expressions |
| `/metrics` | GET | List available PostgreSQL metrics |

## 🧪 Incident Simulation

### Connection Exhaustion

```bash
# Simulate 80 connections (80% of max)
./scripts/simulate_connection_exhaustion.sh 80

# Then ask the chatbot to analyze
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why is the database connection utilization high?"}'
```

### High Disk I/O

```bash
# Run I/O stress test
docker compose exec postgres psql -U postgres -d testdb -f /scripts/simulate_high_io.sql

# Analyze with chatbot
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze disk I/O patterns for the last 10 minutes"}'
```

### Load Testing with pgbench

```bash
# Initialize pgbench tables
./scripts/stress_test.sh init

# Run medium load test
./scripts/stress_test.sh medium

# Run spike pattern
./scripts/stress_test.sh spike
```

### Lock Contention

```bash
# Simulate deadlock
python scripts/simulate_lock_contention.py --mode deadlock

# Simulate long-running locks
python scripts/simulate_lock_contention.py --mode long_lock --hold-time 120

# Simulate contention with waiting sessions
python scripts/simulate_lock_contention.py --mode contention --waiters 10
```

## 💬 Example Queries

The chatbot understands natural language queries about database performance:

```
"What happened to the database yesterday between 10 AM and 11 AM?"
"Analyze the last 2 hours for performance issues"
"Why is the database slow right now?"
"Check for lock contention issues"
"Is transaction wraparound a concern?"
"Show me the buffer cache hit ratio trends"
"What's causing high disk I/O?"
"Generate a health report for the last 30 minutes"
```

## 📈 Monitored Metrics

| Category | Metrics |
|----------|---------|
| **Connections** | Active, Idle, Total, Utilization % |
| **Transactions** | Commits/s, Rollbacks/s, Wraparound Age |
| **Locks** | Total, Exclusive, Waiting |
| **Buffer Cache** | Hit Ratio, Blocks Read, Blocks Hit |
| **Disk I/O** | Backend Writes, Checkpoints, Write Time |
| **Tuples** | Inserted/s, Updated/s, Deleted/s, Dead Tuples |
| **Replication** | Lag (seconds) |

## 🛠️ Development

### Run Chatbot Locally (without Docker)

```bash
cd chatbot
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key"
export PROMETHEUS_URL="http://localhost:9090"

# Run the app
uvicorn main:app --reload --port 8000
```

### View Logs

```bash
# All services
docker compose logs -f

# Just chatbot
docker compose logs -f chatbot

# Just postgres
docker compose logs -f postgres
```

### Access Prometheus UI

Open http://localhost:9090 to:
- Query metrics directly
- View scrape targets
- Check alert rules

## 📁 Project Structure

```
postgres-ai/
├── docker-compose.yml          # Container orchestration
├── .env                        # Environment variables
├── prometheus/
│   └── prometheus.yml          # Prometheus configuration
├── chatbot/
│   ├── Dockerfile              # Chatbot container image
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # FastAPI application
│   ├── agent.py                # AI reasoning loop
│   ├── tools.py                # Function calling tools
│   ├── promql_builder.py       # PromQL query templates
│   └── config.py               # Configuration settings
├── scripts/
│   ├── init.sql                # Database initialization
│   ├── simulate_connection_exhaustion.sh
│   ├── simulate_high_io.sql
│   ├── simulate_lock_contention.py
│   └── stress_test.sh          # pgbench wrapper
└── docs/
    └── sample_health_report.md # Example AI-generated report
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | Model to use | `gpt-4o` |
| `PROMETHEUS_URL` | Prometheus endpoint | `http://prometheus:9090` |
| `POSTGRES_DSN` | PostgreSQL connection | `postgresql://...` |

### PostgreSQL Tuning

The default configuration sets:
- `max_connections = 100`
- `shared_preload_libraries = pg_stat_statements`
- `log_statement = all`
- `log_lock_waits = on`

Modify `docker-compose.yml` to adjust settings.

## 📝 License

MIT License - See LICENSE file for details.
