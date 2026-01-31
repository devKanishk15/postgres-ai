"""
PromQL query builder for PostgreSQL metrics.
Provides templates and utilities for constructing PromQL queries.
"""
from typing import Optional
from dataclasses import dataclass


@dataclass
class MetricQuery:
    """Represents a PromQL metric query with metadata."""
    name: str
    query: str
    description: str
    unit: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None


class PromQLBuilder:
    """Builder for PostgreSQL-related PromQL queries."""
    
    # Core PostgreSQL Metrics
    METRICS = {
        # Connection Metrics
        "active_connections": MetricQuery(
            name="Active Connections",
            query="pg_stat_activity_count{state='active'}",
            description="Number of active database connections",
            unit="connections",
            threshold_warning=80,
            threshold_critical=95
        ),
        "idle_connections": MetricQuery(
            name="Idle Connections",
            query="pg_stat_activity_count{state='idle'}",
            description="Number of idle database connections",
            unit="connections"
        ),
        "total_connections": MetricQuery(
            name="Total Connections",
            query="sum(pg_stat_activity_count)",
            description="Total number of database connections",
            unit="connections",
            threshold_warning=80,
            threshold_critical=95
        ),
        "max_connections": MetricQuery(
            name="Max Connections",
            query="pg_settings_max_connections",
            description="Maximum allowed connections",
            unit="connections"
        ),
        "connection_utilization": MetricQuery(
            name="Connection Utilization",
            query="(sum(pg_stat_activity_count) / pg_settings_max_connections) * 100",
            description="Percentage of max connections in use",
            unit="percent",
            threshold_warning=80,
            threshold_critical=95
        ),
        
        # Transaction Metrics
        "transactions_committed": MetricQuery(
            name="Transactions Committed",
            query="rate(pg_stat_database_xact_commit{datname='testdb'}[5m])",
            description="Rate of committed transactions per second",
            unit="tx/s"
        ),
        "transactions_rolled_back": MetricQuery(
            name="Transactions Rolled Back",
            query="rate(pg_stat_database_xact_rollback{datname='testdb'}[5m])",
            description="Rate of rolled back transactions per second",
            unit="tx/s"
        ),
        "transaction_wraparound": MetricQuery(
            name="Transaction Wraparound Age",
            query="pg_database_wraparound_age_datfrozenxid_age",
            description="Age of oldest unfrozen transaction ID",
            unit="transactions",
            threshold_warning=500000000,
            threshold_critical=1000000000
        ),
        
        # Lock Metrics
        "locks_total": MetricQuery(
            name="Total Locks",
            query="sum(pg_locks_count)",
            description="Total number of locks held",
            unit="locks"
        ),
        "exclusive_locks": MetricQuery(
            name="Exclusive Locks",
            query="pg_locks_count{mode='ExclusiveLock'}",
            description="Number of exclusive locks",
            unit="locks"
        ),
        "waiting_locks": MetricQuery(
            name="Waiting Locks",
            query="pg_locks_count{granted='false'}",
            description="Number of locks waiting to be granted",
            unit="locks",
            threshold_warning=5,
            threshold_critical=20
        ),
        
        # Buffer/Cache Metrics
        "buffer_cache_hit_ratio": MetricQuery(
            name="Buffer Cache Hit Ratio",
            query="(pg_stat_database_blks_hit{datname='testdb'} / (pg_stat_database_blks_hit{datname='testdb'} + pg_stat_database_blks_read{datname='testdb'})) * 100",
            description="Percentage of requests served from buffer cache",
            unit="percent",
            threshold_warning=95,  # Below this is concerning
            threshold_critical=90
        ),
        "blocks_read": MetricQuery(
            name="Blocks Read",
            query="rate(pg_stat_database_blks_read{datname='testdb'}[5m])",
            description="Rate of disk blocks read per second",
            unit="blocks/s"
        ),
        "blocks_hit": MetricQuery(
            name="Blocks Hit",
            query="rate(pg_stat_database_blks_hit{datname='testdb'}[5m])",
            description="Rate of buffer cache hits per second",
            unit="blocks/s"
        ),
        
        # Disk I/O Metrics
        "backend_writes": MetricQuery(
            name="Backend Buffer Writes",
            query="rate(pg_stat_bgwriter_buffers_backend_total[5m])",
            description="Rate of buffers written directly by backend",
            unit="buffers/s",
            threshold_warning=100,
            threshold_critical=500
        ),
        "checkpoints": MetricQuery(
            name="Checkpoints",
            query="rate(pg_stat_bgwriter_checkpoints_timed_total[5m])",
            description="Rate of scheduled checkpoints",
            unit="checkpoints/s"
        ),
        "checkpoint_write_time": MetricQuery(
            name="Checkpoint Write Time",
            query="rate(pg_stat_bgwriter_checkpoint_write_time_total[5m])",
            description="Time spent writing checkpoint files",
            unit="ms/s"
        ),
        
        # Tuple Metrics
        "rows_inserted": MetricQuery(
            name="Rows Inserted",
            query="rate(pg_stat_database_tup_inserted{datname='testdb'}[5m])",
            description="Rate of rows inserted per second",
            unit="rows/s"
        ),
        "rows_updated": MetricQuery(
            name="Rows Updated",
            query="rate(pg_stat_database_tup_updated{datname='testdb'}[5m])",
            description="Rate of rows updated per second",
            unit="rows/s"
        ),
        "rows_deleted": MetricQuery(
            name="Rows Deleted",
            query="rate(pg_stat_database_tup_deleted{datname='testdb'}[5m])",
            description="Rate of rows deleted per second",
            unit="rows/s"
        ),
        "dead_tuples": MetricQuery(
            name="Dead Tuples",
            query="pg_stat_user_tables_n_dead_tup",
            description="Number of dead tuples needing vacuum",
            unit="tuples",
            threshold_warning=10000,
            threshold_critical=100000
        ),
        
        # Replication Metrics
        "replication_lag": MetricQuery(
            name="Replication Lag",
            query="pg_replication_lag",
            description="Replication lag in seconds",
            unit="seconds",
            threshold_warning=30,
            threshold_critical=120
        ),
        
        # Database Size
        "database_size": MetricQuery(
            name="Database Size",
            query="pg_database_size_bytes{datname='testdb'}",
            description="Size of the database in bytes",
            unit="bytes"
        ),
        
        # System Metrics (Node Exporter)
        "cpu_load1": MetricQuery(
            name="CPU Load (1m)",
            query="node_load1",
            description="System load average over the last 1 minute",
            unit="load"
        ),
        "cpu_load5": MetricQuery(
            name="CPU Load (5m)",
            query="node_load5",
            description="System load average over the last 5 minutes",
            unit="load"
        ),
        "cpu_load15": MetricQuery(
            name="CPU Load (15m)",
            query="node_load15",
            description="System load average over the last 15 minutes",
            unit="load"
        ),
        "cpu_utilization": MetricQuery(
            name="CPU Utilization",
            query="100 - (avg by(instance)(irate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)",
            description="Total CPU utilization percentage",
            unit="percent",
            threshold_warning=70,
            threshold_critical=90
        ),
        "cpu_utilization_user": MetricQuery(
            name="CPU Utilization (User)",
            query="avg by(instance)(irate(node_cpu_seconds_total{mode='user'}[5m])) * 100",
            description="CPU time spent in user mode",
            unit="percent"
        ),
        "cpu_utilization_iowait": MetricQuery(
            name="CPU Utilization (I/O Wait)",
            query="avg by(instance)(irate(node_cpu_seconds_total{mode='iowait'}[5m])) * 100",
            description="CPU time spent waiting for I/O",
            unit="percent",
            threshold_warning=10,
            threshold_critical=25
        ),
        "memory_utilization": MetricQuery(
            name="Memory Utilization",
            query="((node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes) * 100",
            description="Percentage of system memory in use",
            unit="percent",
            threshold_warning=80,
            threshold_critical=95
        ),
        
        # Table & Index Metrics
        "table_size": MetricQuery(
            name="Table Size",
            query="pg_stat_user_tables_total_size_bytes{datname='testdb'}",
            description="Total size of table including indexes",
            unit="bytes"
        ),
        "sequential_scans": MetricQuery(
            name="Sequential Scans",
            query="rate(pg_stat_user_tables_seq_scan{datname='testdb'}[5m])",
            description="Rate of sequential scans per second",
            unit="scans/s"
        ),
        "index_scans": MetricQuery(
            name="Index Scans",
            query="rate(pg_stat_user_tables_idx_scan{datname='testdb'}[5m])",
            description="Rate of index scans per second",
            unit="scans/s"
        ),
        
        # Query Performance (requires pg_stat_statements)
        "query_execution_time": MetricQuery(
            name="Query Execution Time",
            query="rate(pg_stat_statements_total_time_seconds{datname='testdb'}[5m])",
            description="Total time spent executing queries",
            unit="seconds/s"
        ),
        "query_calls": MetricQuery(
            name="Query Calls",
            query="rate(pg_stat_statements_calls{datname='testdb'}[5m])",
            description="Rate of query executions",
            unit="calls/s"
        ),
        "query_mean_time": MetricQuery(
            name="Mean Query Time",
            query="sum(rate(pg_stat_statements_total_time_seconds{datname='testdb'}[5m])) / sum(rate(pg_stat_statements_calls{datname='testdb'}[5m]))",
            description="Average time per query execution",
            unit="seconds"
        ),
    }
    
    @classmethod
    def get_metric(cls, metric_name: str) -> Optional[MetricQuery]:
        """Get a metric query by name."""
        return cls.METRICS.get(metric_name)
    
    @classmethod
    def get_all_metrics(cls) -> dict[str, MetricQuery]:
        """Get all available metrics."""
        return cls.METRICS
    
    @classmethod
    def build_range_query(cls, metric_name: str, start_time: int, end_time: int, step: str = "1m") -> Optional[str]:
        """Build a range query URL path for a metric."""
        metric = cls.get_metric(metric_name)
        if not metric:
            return None
        return f"/api/v1/query_range?query={metric.query}&start={start_time}&end={end_time}&step={step}"
    
    @classmethod
    def build_instant_query(cls, metric_name: str) -> Optional[str]:
        """Build an instant query URL path for a metric."""
        metric = cls.get_metric(metric_name)
        if not metric:
            return None
        return f"/api/v1/query?query={metric.query}"
    
    @classmethod
    def get_health_check_metrics(cls) -> list[str]:
        """Get list of metrics for health check."""
        return [
            "connection_utilization",
            "buffer_cache_hit_ratio",
            "transaction_wraparound",
            "waiting_locks",
            "backend_writes",
            "dead_tuples",
            "cpu_utilization",
            "memory_utilization",
            "cpu_load1"
        ]
    
    @classmethod
    def get_incident_metrics(cls) -> list[str]:
        """Get list of metrics for incident analysis."""
        return [
            "active_connections",
            "total_connections",
            "connection_utilization",
            "transactions_committed",
            "transactions_rolled_back",
            "locks_total",
            "exclusive_locks",
            "waiting_locks",
            "buffer_cache_hit_ratio",
            "blocks_read",
            "backend_writes",
            "rows_inserted",
            "rows_updated",
            "dead_tuples",
            "cpu_utilization",
            "cpu_utilization_iowait",
            "memory_utilization",
            "cpu_load1",
            "table_size",
            "sequential_scans",
            "index_scans",
            "query_mean_time"
        ]
