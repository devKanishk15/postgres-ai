# PostgreSQL Debugging Chatbot

An AI-powered chatbot for PostgreSQL performance analysis and incident Root Cause Analysis (RCA). Uses time-series metrics from Prometheus and OpenAI function calling for intelligent database debugging.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Environment                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────────┐                           │
│  │  PostgreSQL  │────▶│ postgres_exporter│───────┐                   │
│  │   :5432      │     │      :9187       │       │                   │
│  └──────────────┘     └──────────────────┘       │                   │
│                                                  ▼                   │
│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐  │
│  │  Host System │────▶│  node_exporter   │────▶│    Prometheus    │  │
│  │  (CPU/Mem)   │     │      :9100       │     │      :9090       │  │
│  └──────────────┘     └──────────────────┘     └────────┬─────────┘  │
│                                                          │           │
│                                                          ▼           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Chatbot API (:8000)                        │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │              AI Reasoning Loop                          │  │   │
│  │  │   SCAN ──▶ CORRELATE ──▶ PROPOSE                       │  │   │
│  │  │   (Anomaly   (Root        (DBA-Level                   │  │   │
│  │  │   Detection)  Cause)       Fix)                        │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
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
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "How is the database performing right now?"}'

# Analyze a specific time range
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "What happened to the database in the last 30 minutes?"}'

# Investigate a specific issue
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "Check for connection exhaustion issues"}'
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
docker exec -it postgres-db /scripts/simulate_connection_exhaustion.sh 80

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
docker exec -it postgres-db /scripts/stress_test.sh init

# Run medium load test
docker exec -it postgres-db /scripts/stress_test.sh medium

# Run spike pattern
docker exec -it postgres-db /scripts/stress_test.sh spike
```

### Lock Contention

```bash
# Simulate deadlock
docker exec -it postgres-chatbot python /scripts/simulate_lock_contention.py --mode deadlock

# Simulate long-running locks
docker exec -it postgres-chatbot python /scripts/simulate_lock_contention.py --mode long_lock --hold-time 120

# Simulate contention with waiting sessions
docker exec -it postgres-chatbot python /scripts/simulate_lock_contention.py --mode contention --waiters 10
```

## 💻 Frontend UI

The project now includes a modern React-based chatbot interface for easier interaction and real-time monitoring.

### 1. Setup and Run (Docker)

```bash
docker compose up -d
```

The UI will be available at [http://localhost:5173](http://localhost:5173).

### 2. Development Setup (Local)

If you wish to run the frontend locally for development:

```bash
cd frontend
npm install
npm run dev
```

### 2. Key Features

- **Real-time Health Sidebar**: Monitor CPU, Memory, Connections, and Transactions at a glance.
- **Rich AI Chat**: Interact with the AI agent using natural language with full Markdown support for analysis reports.
- **Tool Visualization**: See which metrics the AI is inspecting in real-time.
- **System Health Status**: Visual indicators (Green/Yellow/Red) for database and infrastructure health.

---

## 💬 Example Queries
...
## 📁 Project Structure

```
postgres-ai/
├── docker-compose.yml          # Container orchestration
├── .env                        # Environment variables
├── frontend/                   # [NEW] React + TS Chat Interface
│   ├── src/
│   │   ├── components/         # Chat and Sidebar components
│   │   ├── api.ts              # Backend API client
│   │   └── App.tsx             # Main layout
│   └── tailwind.config.js      # Styling configuration
├── prometheus/
│   └── prometheus.yml          # Prometheus configuration
├── chatbot/
│   ├── Dockerfile              # Chatbot container image
│   ├── requirements.txt        # Python dependencies
...
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
