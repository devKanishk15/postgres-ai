"""
Tools for the AI agent to interact with Prometheus and analyze PostgreSQL metrics.
These functions are exposed to the OpenAI function calling API.
"""
import httpx
from typing import Optional, Any
from datetime import datetime
from cachetools import TTLCache
import asyncio
from promql_builder import PromQLBuilder, MetricQuery


class PrometheusClient:
    """Client for querying Prometheus metrics."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cache = TTLCache(maxsize=100, ttl=30)  # Cache for 30 seconds
    
    async def query_instant(self, query: str) -> dict[str, Any]:
        """Execute an instant query against Prometheus."""
        cache_key = f"instant:{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        url = f"{self.base_url}/api/v1/query"
        params = {"query": query}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        self.cache[cache_key] = result
        return result
    
    async def query_range(
        self, 
        query: str, 
        start: int, 
        end: int, 
        step: str = "1m"
    ) -> dict[str, Any]:
        """Execute a range query against Prometheus."""
        cache_key = f"range:{query}:{start}:{end}:{step}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        url = f"{self.base_url}/api/v1/query_range"
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        self.cache[cache_key] = result
        return result
    
    async def check_health(self) -> bool:
        """Check if Prometheus is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/-/healthy")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Tool function definitions for OpenAI
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "query_prometheus_metric",
            "description": "Query a specific PostgreSQL or system/host metric from Prometheus for a given time range. Use this to fetch time-series data for analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_name": {
                        "type": "string",
                        "description": "Name of the metric to query",
                        "enum": list(PromQLBuilder.METRICS.keys())
                    },
                    "start_timestamp": {
                        "type": "integer",
                        "description": "Start time as Unix timestamp"
                    },
                    "end_timestamp": {
                        "type": "integer",
                        "description": "End time as Unix timestamp"
                    },
                    "step": {
                        "type": "string",
                        "description": "Query resolution step (e.g., '1m', '5m', '1h')",
                        "default": "1m"
                    }
                },
                "required": ["metric_name", "start_timestamp", "end_timestamp"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_metric_value",
            "description": "Get the current (latest) value of a PostgreSQL or system/host metric.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_name": {
                        "type": "string",
                        "description": "Name of the metric to query",
                        "enum": list(PromQLBuilder.METRICS.keys())
                    }
                },
                "required": ["metric_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_metric_anomalies",
            "description": "Analyze a metric's time-series data to detect anomalies like spikes, drops, or unusual patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_name": {
                        "type": "string",
                        "description": "Name of the metric to analyze",
                        "enum": list(PromQLBuilder.METRICS.keys())
                    },
                    "start_timestamp": {
                        "type": "integer",
                        "description": "Start time as Unix timestamp"
                    },
                    "end_timestamp": {
                        "type": "integer",
                        "description": "End time as Unix timestamp"
                    }
                },
                "required": ["metric_name", "start_timestamp", "end_timestamp"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_health_summary",
            "description": "Get a summary of all critical database health metrics at the current time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "correlate_metrics",
            "description": "Compare multiple metrics over a time range to find correlations between them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_names": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(PromQLBuilder.METRICS.keys())
                        },
                        "description": "List of metric names to correlate"
                    },
                    "start_timestamp": {
                        "type": "integer",
                        "description": "Start time as Unix timestamp"
                    },
                    "end_timestamp": {
                        "type": "integer",
                        "description": "End time as Unix timestamp"
                    }
                },
                "required": ["metric_names", "start_timestamp", "end_timestamp"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "get_metric_info",
            "description": "Get information about a specific metric including its description, unit, and thresholds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_name": {
                        "type": "string",
                        "description": "Name of the metric",
                        "enum": list(PromQLBuilder.METRICS.keys())
                    }
                },
                "required": ["metric_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_metrics",
            "description": "List all available PostgreSQL and system/host metrics that can be queried.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_incident_report",
            "description": "Generate a structured incident report based on the analysis performed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_type": {
                        "type": "string",
                        "description": "Type of incident detected",
                        "enum": ["connection_exhaustion", "high_disk_io", "lock_contention", "transaction_wraparound", "cache_pressure", "general_slowdown"]
                    },
                    "severity": {
                        "type": "string",
                        "description": "Severity of the incident",
                        "enum": ["low", "medium", "high", "critical"]
                    },
                    "root_cause": {
                        "type": "string",
                        "description": "Identified root cause of the incident"
                    },
                    "affected_metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of metrics that showed anomalies"
                    },
                    "recommendations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of DBA-level recommendations to resolve the issue"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "When the incident started (ISO format)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "When the incident ended or 'ongoing' (ISO format)"
                    }
                },
                "required": ["incident_type", "severity", "root_cause", "affected_metrics", "recommendations"]
            }
        }
    }
]


class ToolExecutor:
    """Executes tool calls from the AI agent."""
    
    def __init__(self, prometheus_client: PrometheusClient):
        self.prometheus = prometheus_client
        self.builder = PromQLBuilder()
    
    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name with given arguments."""
        handlers = {
            "query_prometheus_metric": self._query_prometheus_metric,
            "get_current_metric_value": self._get_current_metric_value,
            "analyze_metric_anomalies": self._analyze_metric_anomalies,
            "get_health_summary": self._get_health_summary,
            "correlate_metrics": self._correlate_metrics,
            "get_metric_info": self._get_metric_info,
            "list_available_metrics": self._list_available_metrics,
            "generate_incident_report": self._generate_incident_report,
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            return await handler(**arguments)
        except Exception as e:
            return {"error": str(e)}
    
    async def _query_prometheus_metric(
        self,
        metric_name: str,
        start_timestamp: int,
        end_timestamp: int,
        step: str = "1m"
    ) -> dict[str, Any]:
        """Query a metric over a time range."""
        metric = PromQLBuilder.get_metric(metric_name)
        if not metric:
            return {"error": f"Unknown metric: {metric_name}"}
        
        result = await self.prometheus.query_range(
            metric.query, start_timestamp, end_timestamp, step
        )
        
        # Process and simplify the result
        if result.get("status") == "success":
            data = result.get("data", {}).get("result", [])
            processed = []
            for series in data:
                values = series.get("values", [])
                processed.append({
                    "labels": series.get("metric", {}),
                    "data_points": len(values),
                    "values": [{"time": v[0], "value": float(v[1]) if v[1] != "NaN" else None} for v in values]
                })
            return {
                "metric_name": metric_name,
                "description": metric.description,
                "unit": metric.unit,
                "time_range": {"start": start_timestamp, "end": end_timestamp},
                "series": processed
            }
        return {"error": "Query failed", "details": result}
    
    async def _get_current_metric_value(self, metric_name: str) -> dict[str, Any]:
        """Get current value of a metric."""
        metric = PromQLBuilder.get_metric(metric_name)
        if not metric:
            return {"error": f"Unknown metric: {metric_name}"}
        
        result = await self.prometheus.query_instant(metric.query)
        
        if result.get("status") == "success":
            data = result.get("data", {}).get("result", [])
            values = []
            for item in data:
                value = item.get("value", [None, None])
                values.append({
                    "labels": item.get("metric", {}),
                    "value": float(value[1]) if value[1] and value[1] != "NaN" else None,
                    "timestamp": value[0]
                })
            
            # Check thresholds
            threshold_status = "normal"
            if metric.threshold_critical and values:
                for v in values:
                    if v["value"] and v["value"] >= metric.threshold_critical:
                        threshold_status = "critical"
                        break
                    elif v["value"] and metric.threshold_warning and v["value"] >= metric.threshold_warning:
                        threshold_status = "warning"
            
            return {
                "metric_name": metric_name,
                "description": metric.description,
                "unit": metric.unit,
                "current_values": values,
                "threshold_status": threshold_status,
                "thresholds": {
                    "warning": metric.threshold_warning,
                    "critical": metric.threshold_critical
                }
            }
        return {"error": "Query failed", "details": result}
    
    async def _analyze_metric_anomalies(
        self,
        metric_name: str,
        start_timestamp: int,
        end_timestamp: int
    ) -> dict[str, Any]:
        """Analyze a metric for anomalies."""
        # First, get the data
        data = await self._query_prometheus_metric(
            metric_name, start_timestamp, end_timestamp, "1m"
        )
        
        if "error" in data:
            return data
        
        anomalies = []
        for series in data.get("series", []):
            values = [v["value"] for v in series.get("values", []) if v["value"] is not None]
            if not values:
                continue
            
            # Calculate statistics
            avg = sum(values) / len(values)
            max_val = max(values)
            min_val = min(values)
            
            # Calculate standard deviation
            variance = sum((x - avg) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            
            # Detect anomalies (values > 2 std deviations from mean)
            threshold_high = avg + (2 * std_dev)
            threshold_low = avg - (2 * std_dev) if avg - (2 * std_dev) > 0 else 0
            
            spikes = []
            drops = []
            for v in series.get("values", []):
                if v["value"] is None:
                    continue
                if v["value"] > threshold_high:
                    spikes.append({
                        "timestamp": v["time"],
                        "value": v["value"],
                        "deviation": (v["value"] - avg) / std_dev if std_dev > 0 else 0
                    })
                elif v["value"] < threshold_low:
                    drops.append({
                        "timestamp": v["time"],
                        "value": v["value"],
                        "deviation": (avg - v["value"]) / std_dev if std_dev > 0 else 0
                    })
            
            anomalies.append({
                "labels": series.get("labels", {}),
                "statistics": {
                    "average": round(avg, 2),
                    "max": round(max_val, 2),
                    "min": round(min_val, 2),
                    "std_dev": round(std_dev, 2)
                },
                "spikes": spikes[:10],  # Limit to top 10
                "drops": drops[:10],
                "has_anomalies": len(spikes) > 0 or len(drops) > 0
            })
        
        return {
            "metric_name": metric_name,
            "analysis_period": {"start": start_timestamp, "end": end_timestamp},
            "anomaly_analysis": anomalies
        }
    
    async def _get_health_summary(self) -> dict[str, Any]:
        """Get overall health summary."""
        health_metrics = PromQLBuilder.get_health_check_metrics()
        summary = {"status": "healthy", "metrics": {}, "alerts": []}
        
        for metric_name in health_metrics:
            result = await self._get_current_metric_value(metric_name)
            if "error" not in result:
                summary["metrics"][metric_name] = result
                if result.get("threshold_status") == "critical":
                    summary["status"] = "critical"
                    summary["alerts"].append(f"CRITICAL: {metric_name}")
                elif result.get("threshold_status") == "warning" and summary["status"] == "healthy":
                    summary["status"] = "warning"
                    summary["alerts"].append(f"WARNING: {metric_name}")
        
        return summary
    
    async def _correlate_metrics(
        self,
        metric_names: list[str],
        start_timestamp: int,
        end_timestamp: int
    ) -> dict[str, Any]:
        """Correlate multiple metrics."""
        results = {}
        for metric_name in metric_names:
            data = await self._query_prometheus_metric(
                metric_name, start_timestamp, end_timestamp, "1m"
            )
            if "error" not in data:
                results[metric_name] = data
        
        # Simple correlation analysis - find if metrics spiked at similar times
        correlations = []
        metric_list = list(results.keys())
        for i, m1 in enumerate(metric_list):
            for m2 in metric_list[i+1:]:
                # Check if both have anomalies around the same time
                s1 = results[m1].get("series", [{}])[0].get("values", []) if results[m1].get("series") else []
                s2 = results[m2].get("series", [{}])[0].get("values", []) if results[m2].get("series") else []
                
                if s1 and s2:
                    correlations.append({
                        "metrics": [m1, m2],
                        "data_points": min(len(s1), len(s2))
                    })
        
        return {
            "time_range": {"start": start_timestamp, "end": end_timestamp},
            "metrics_data": results,
            "correlations": correlations
        }
    
    async def _get_metric_info(self, metric_name: str) -> dict[str, Any]:
        """Get information about a metric."""
        metric = PromQLBuilder.get_metric(metric_name)
        if not metric:
            return {"error": f"Unknown metric: {metric_name}"}
        
        return {
            "name": metric.name,
            "metric_key": metric_name,
            "description": metric.description,
            "unit": metric.unit,
            "promql_query": metric.query,
            "thresholds": {
                "warning": metric.threshold_warning,
                "critical": metric.threshold_critical
            }
        }
    
    async def _list_available_metrics(self) -> dict[str, Any]:
        """List all available metrics."""
        metrics = []
        for key, metric in PromQLBuilder.get_all_metrics().items():
            metrics.append({
                "key": key,
                "name": metric.name,
                "description": metric.description,
                "unit": metric.unit
            })
        return {"available_metrics": metrics, "total_count": len(metrics)}
    
    async def _generate_incident_report(
        self,
        incident_type: str,
        severity: str,
        root_cause: str,
        affected_metrics: list[str],
        recommendations: list[str],
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> dict[str, Any]:
        """Generate a structured incident report."""
        return {
            "report_type": "incident_analysis",
            "generated_at": datetime.now().isoformat(),
            "incident": {
                "type": incident_type,
                "severity": severity,
                "timeline": {
                    "detected": start_time or "unknown",
                    "resolved": end_time or "ongoing"
                }
            },
            "analysis": {
                "root_cause": root_cause,
                "affected_metrics": affected_metrics
            },
            "recommendations": [
                {"priority": i + 1, "action": rec}
                for i, rec in enumerate(recommendations)
            ]
        }
