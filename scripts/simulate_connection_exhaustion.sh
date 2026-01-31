#!/bin/bash
# =============================================================================
# Connection Exhaustion Simulation Script
# =============================================================================
# This script simulates a connection exhaustion incident by opening many
# idle connections until the PostgreSQL connection pool is nearly exhausted.
#
# Usage: ./simulate_connection_exhaustion.sh [num_connections]
# Default: 80 connections (80% of max_connections=100)
# =============================================================================

set -e

# Configuration
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGPASSWORD="${PGPASSWORD:-postgres}"
PGDATABASE="${PGDATABASE:-testdb}"

NUM_CONNECTIONS="${1:-80}"
CONNECTION_HOLD_TIME="${2:-120}"  # seconds to hold connections

echo "=============================================="
echo "Connection Exhaustion Simulation"
echo "=============================================="
echo "Host: $PGHOST:$PGPORT"
echo "Database: $PGDATABASE"
echo "Target Connections: $NUM_CONNECTIONS"
echo "Hold Time: ${CONNECTION_HOLD_TIME}s"
echo "=============================================="
echo ""

# Export password for psql
export PGPASSWORD

# Array to store background process PIDs
declare -a PIDS

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up connections..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    echo "All connections closed."
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting connection flood..."
echo ""

# Open connections in parallel
for i in $(seq 1 $NUM_CONNECTIONS); do
    # Each connection runs a query that holds the connection open
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "
        SELECT pg_sleep($CONNECTION_HOLD_TIME);
    " > /dev/null 2>&1 &
    
    PIDS+=($!)
    
    # Progress indicator
    if [ $((i % 10)) -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Opened $i connections..."
    fi
done

echo ""
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Successfully opened $NUM_CONNECTIONS connections"
echo ""

# Check current connection count
echo "Current connection status:"
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "
SELECT 
    count(*) as total_connections,
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
    round(count(*)::numeric / (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') * 100, 2) as utilization_percent
FROM pg_stat_activity;
"

echo ""
echo "Connection states:"
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "
SELECT state, count(*) 
FROM pg_stat_activity 
GROUP BY state 
ORDER BY count(*) DESC;
"

echo ""
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Holding connections for ${CONNECTION_HOLD_TIME} seconds..."
echo "Press Ctrl+C to release connections early."
echo ""

# Wait for connections to complete or user interrupt
sleep $CONNECTION_HOLD_TIME

echo ""
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Connection hold period complete."
