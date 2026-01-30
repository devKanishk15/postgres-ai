-- =============================================================================
-- High Disk I/O Simulation Script
-- =============================================================================
-- This script simulates high disk I/O by performing operations that bypass
-- the buffer cache and force disk reads/writes.
--
-- Run with: psql -h localhost -U postgres -d testdb -f simulate_high_io.sql
-- =============================================================================

-- Show start time
SELECT 'Starting High I/O Simulation at ' || now() AS status;

-- -----------------------------------------------------------------------------
-- 1. Create a large temporary table to force disk writes
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS io_stress_test;

CREATE TABLE io_stress_test (
    id SERIAL PRIMARY KEY,
    data TEXT,
    payload BYTEA,
    created_at TIMESTAMP DEFAULT now()
);

SELECT 'Created stress test table' AS status;

-- Insert large amounts of data
INSERT INTO io_stress_test (data, payload)
SELECT 
    md5(random()::text) || md5(random()::text) || md5(random()::text),
    gen_random_bytes(1024)  -- 1KB of random bytes per row
FROM generate_series(1, 100000);

SELECT 'Inserted 100,000 rows with random data' AS status;

-- -----------------------------------------------------------------------------
-- 2. Force a checkpoint to write all dirty buffers to disk
-- -----------------------------------------------------------------------------
CHECKPOINT;
SELECT 'Forced checkpoint' AS status;

-- -----------------------------------------------------------------------------
-- 3. Perform sequential scans on the large table
-- -----------------------------------------------------------------------------
-- This will cause significant read I/O
SELECT count(*) FROM io_stress_test WHERE data LIKE '%abc%';
SELECT 'Completed sequential scan 1' AS status;

SELECT count(*) FROM io_stress_test WHERE length(data) > 50;
SELECT 'Completed sequential scan 2' AS status;

-- -----------------------------------------------------------------------------
-- 4. Perform updates that generate WAL and dirty buffers
-- -----------------------------------------------------------------------------
UPDATE io_stress_test 
SET data = data || '_updated'
WHERE id % 3 = 0;

SELECT 'Updated 1/3 of rows' AS status;

-- Force another checkpoint
CHECKPOINT;
SELECT 'Forced second checkpoint' AS status;

-- -----------------------------------------------------------------------------
-- 5. Create an unlogged table and fill it (stress temp space)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS temp_stress_test;

CREATE UNLOGGED TABLE temp_stress_test AS
SELECT 
    generate_series as id,
    repeat('x', 100) as padding,
    md5(random()::text) as hash
FROM generate_series(1, 50000);

SELECT 'Created unlogged table with 50,000 rows' AS status;

-- -----------------------------------------------------------------------------
-- 6. Complex aggregation that requires sorts (may spill to disk)
-- -----------------------------------------------------------------------------
SET work_mem = '1MB';  -- Force sort to spill to disk

SELECT 
    substring(data, 1, 5) as prefix,
    count(*) as cnt,
    avg(length(data)) as avg_len
FROM io_stress_test
GROUP BY substring(data, 1, 5)
ORDER BY cnt DESC
LIMIT 10;

SELECT 'Completed disk-intensive aggregation' AS status;

RESET work_mem;

-- -----------------------------------------------------------------------------
-- 7. Show I/O statistics
-- -----------------------------------------------------------------------------
SELECT 'Current Buffer/IO Statistics:' AS status;

SELECT 
    datname,
    blks_read,
    blks_hit,
    CASE WHEN blks_read + blks_hit > 0 
        THEN round(blks_hit::numeric / (blks_read + blks_hit) * 100, 2)
        ELSE 0 
    END as cache_hit_ratio
FROM pg_stat_database
WHERE datname = 'testdb';

-- Show bgwriter stats
SELECT 'Background Writer Statistics:' AS status;

SELECT 
    checkpoints_timed,
    checkpoints_req,
    buffers_checkpoint,
    buffers_backend,
    buffers_alloc
FROM pg_stat_bgwriter;

-- -----------------------------------------------------------------------------
-- 8. Cleanup (optional - comment out to keep data for analysis)
-- -----------------------------------------------------------------------------
-- DROP TABLE IF EXISTS io_stress_test;
-- DROP TABLE IF EXISTS temp_stress_test;

SELECT 'High I/O Simulation Complete at ' || now() AS status;
