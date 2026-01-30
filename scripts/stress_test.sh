#!/bin/bash
# =============================================================================
# PostgreSQL Stress Test Script using pgbench
# =============================================================================
# This script runs pgbench to generate realistic database load for testing
# the monitoring and alerting capabilities of the chatbot.
#
# Usage: ./stress_test.sh [mode]
#   mode: init     - Initialize pgbench tables
#         light    - Light load (10 clients, 60 seconds)
#         medium   - Medium load (50 clients, 120 seconds)
#         heavy    - Heavy load (100 clients, 180 seconds)
#         spike    - Sudden spike (ramp up quickly, then down)
# =============================================================================

set -e

# Configuration
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGPASSWORD="${PGPASSWORD:-postgres}"
PGDATABASE="${PGDATABASE:-testdb}"

MODE="${1:-medium}"

export PGPASSWORD

echo "=============================================="
echo "PostgreSQL Stress Test"
echo "=============================================="
echo "Host: $PGHOST:$PGPORT"
echo "Database: $PGDATABASE"
echo "Mode: $MODE"
echo "=============================================="
echo ""

case $MODE in
    init)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Initializing pgbench tables..."
        pgbench -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -i -s 10
        echo ""
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Initialization complete."
        echo ""
        echo "Tables created:"
        psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "
            SELECT schemaname, tablename, 
                   pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE tablename LIKE 'pgbench%'
            ORDER BY tablename;
        "
        ;;
        
    light)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running LIGHT load test..."
        echo "Clients: 10, Duration: 60s"
        echo ""
        pgbench -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
            -c 10 -j 4 -T 60 -P 10 --no-vacuum
        ;;
        
    medium)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running MEDIUM load test..."
        echo "Clients: 50, Duration: 120s"
        echo ""
        pgbench -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
            -c 50 -j 8 -T 120 -P 10 --no-vacuum
        ;;
        
    heavy)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running HEAVY load test..."
        echo "Clients: 100, Duration: 180s"
        echo ""
        pgbench -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
            -c 100 -j 16 -T 180 -P 10 --no-vacuum
        ;;
        
    spike)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running SPIKE load test..."
        echo "This will create a sudden traffic spike pattern."
        echo ""
        
        # Phase 1: Normal load
        echo "Phase 1: Normal load (10 clients, 30s)"
        pgbench -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
            -c 10 -j 4 -T 30 -P 5 --no-vacuum
        
        # Phase 2: Traffic spike
        echo ""
        echo "Phase 2: TRAFFIC SPIKE (80 clients, 60s)"
        pgbench -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
            -c 80 -j 16 -T 60 -P 5 --no-vacuum
        
        # Phase 3: Return to normal
        echo ""
        echo "Phase 3: Recovery (10 clients, 30s)"
        pgbench -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
            -c 10 -j 4 -T 30 -P 5 --no-vacuum
        ;;
        
    custom)
        # Custom SQL workload for more realistic scenarios
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running CUSTOM workload..."
        
        # Create custom script file
        cat > /tmp/custom_workload.sql << 'EOF'
\set customer_id random(1, 1000)
\set product_id random(1, 10000)

-- Mix of operations
BEGIN;
SELECT * FROM orders WHERE customer_id = :customer_id LIMIT 10;
INSERT INTO orders (customer_id, product_name, quantity, price) 
    VALUES (:customer_id, 'StressTest Product', 1, 99.99);
UPDATE orders SET status = 'completed' WHERE id = :product_id AND status = 'pending';
COMMIT;
EOF
        
        pgbench -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
            -c 30 -j 8 -T 90 -P 10 -f /tmp/custom_workload.sql --no-vacuum
        
        rm /tmp/custom_workload.sql
        ;;
        
    *)
        echo "Unknown mode: $MODE"
        echo ""
        echo "Available modes:"
        echo "  init   - Initialize pgbench tables"
        echo "  light  - Light load (10 clients, 60s)"
        echo "  medium - Medium load (50 clients, 120s)"
        echo "  heavy  - Heavy load (100 clients, 180s)"
        echo "  spike  - Traffic spike pattern"
        echo "  custom - Custom SQL workload"
        exit 1
        ;;
esac

echo ""
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stress test complete."
echo ""

# Show final stats
echo "Final database statistics:"
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "
SELECT 
    numbackends as active_connections,
    xact_commit as transactions_committed,
    xact_rollback as transactions_rolled_back,
    blks_read as blocks_read,
    blks_hit as blocks_hit,
    CASE WHEN blks_read + blks_hit > 0 
        THEN round(blks_hit::numeric / (blks_read + blks_hit) * 100, 2)
        ELSE 100 
    END as cache_hit_ratio
FROM pg_stat_database
WHERE datname = 'testdb';
"
