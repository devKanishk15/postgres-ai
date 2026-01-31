"""
Core AI Agent for PostgreSQL debugging and RCA.
Implements the reasoning loop: SCAN -> CORRELATE -> PROPOSE
"""
import json
from datetime import datetime
from typing import Optional, Any
from openai import AsyncOpenAI
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import re

from config import get_settings
from tools import PrometheusClient, ToolExecutor, TOOL_DEFINITIONS
from promql_builder import PromQLBuilder
from history_manager import HistoryManager


class TimeRangeParser:
    """Parses natural language time ranges into Unix timestamps."""
    
    @staticmethod
    def parse(time_expression: str, reference_time: Optional[datetime] = None) -> tuple[int, int]:
        """
        Parse a natural language time expression into start and end Unix timestamps.
        
        Examples:
        - "last 30 minutes"
        - "yesterday 10am to 11am"
        - "Jan 25th 2026, 10-11 AM"
        - "2 hours ago"
        """
        ref = reference_time or datetime.now()
        
        # Pattern: "last X minutes/hours/days"
        last_pattern = r"last\s+(\d+)\s+(minute|hour|day|week)s?"
        match = re.search(last_pattern, time_expression.lower())
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            if unit == "minute":
                delta = relativedelta(minutes=amount)
            elif unit == "hour":
                delta = relativedelta(hours=amount)
            elif unit == "day":
                delta = relativedelta(days=amount)
            elif unit == "week":
                delta = relativedelta(weeks=amount)
            else:
                delta = relativedelta(hours=1)
            
            end_time = ref
            start_time = ref - delta
            return int(start_time.timestamp()), int(end_time.timestamp())
        
        # Pattern: "X minutes/hours ago"
        ago_pattern = r"(\d+)\s+(minute|hour|day)s?\s+ago"
        match = re.search(ago_pattern, time_expression.lower())
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            if unit == "minute":
                delta = relativedelta(minutes=amount)
            elif unit == "hour":
                delta = relativedelta(hours=amount)
            else:
                delta = relativedelta(days=amount)
            
            center = ref - delta
            # Return a 10-minute window around the specified time
            return int((center - relativedelta(minutes=5)).timestamp()), int((center + relativedelta(minutes=5)).timestamp())
        
        # Pattern: "today/yesterday X to Y"
        day_pattern = r"(today|yesterday)\s+(\d{1,2})\s*(am|pm)?\s*(?:to|-)\s*(\d{1,2})\s*(am|pm)?"
        match = re.search(day_pattern, time_expression.lower())
        if match:
            day_ref = match.group(1)
            start_hour = int(match.group(2))
            start_ampm = match.group(3)
            end_hour = int(match.group(4))
            end_ampm = match.group(5)
            
            if day_ref == "yesterday":
                base_date = ref.date() - relativedelta(days=1)
            else:
                base_date = ref.date()
            
            # Handle AM/PM
            if start_ampm == "pm" and start_hour < 12:
                start_hour += 12
            if end_ampm == "pm" and end_hour < 12:
                end_hour += 12
            
            start_dt = datetime.combine(base_date, datetime.min.time().replace(hour=start_hour))
            end_dt = datetime.combine(base_date, datetime.min.time().replace(hour=end_hour))
            
            return int(start_dt.timestamp()), int(end_dt.timestamp())
        
        # Pattern: "Jan 25th 2026, 10-11 AM" or similar dates
        date_range_pattern = r"([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4})\s*,?\s*(\d{1,2})(?::(\d{2}))?\s*-\s*(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?"
        match = re.search(date_range_pattern, time_expression)
        if match:
            date_str = match.group(1)
            start_hour = int(match.group(2))
            start_min = int(match.group(3)) if match.group(3) else 0
            end_hour = int(match.group(4))
            end_min = int(match.group(5)) if match.group(5) else 0
            ampm = match.group(6)
            
            # Parse the date
            try:
                base_date = date_parser.parse(date_str).date()
            except Exception:
                base_date = ref.date()
            
            # Handle AM/PM
            if ampm and ampm.lower() == "pm":
                if start_hour < 12:
                    start_hour += 12
                if end_hour < 12:
                    end_hour += 12
            
            start_dt = datetime.combine(base_date, datetime.min.time().replace(hour=start_hour, minute=start_min))
            end_dt = datetime.combine(base_date, datetime.min.time().replace(hour=end_hour, minute=end_min))
            
            return int(start_dt.timestamp()), int(end_dt.timestamp())
        
        # Try direct parsing as a fallback
        try:
            parsed = date_parser.parse(time_expression, fuzzy=True)
            # Return a 1-hour window around the parsed time
            return int((parsed - relativedelta(minutes=30)).timestamp()), int((parsed + relativedelta(minutes=30)).timestamp())
        except Exception:
            pass
        
        # Default: last 1 hour
        return int((ref - relativedelta(hours=1)).timestamp()), int(ref.timestamp())


class PostgresDebugAgent:
    """
    AI Agent for PostgreSQL debugging and Root Cause Analysis.
    
    Implements a reasoning loop:
    1. SCAN: Analyze metrics for anomalies
    2. CORRELATE: Find relationships between anomalous metrics
    3. PROPOSE: Generate DBA-level fixes
    """
    
    SYSTEM_PROMPT = """You are an expert Database Reliability Engineer (DBRE) AI assistant 
specializing in PostgreSQL performance analysis and incident root cause analysis.

Your role is to:
1. **SCAN**: Analyze database and system metrics to identify anomalies.
2. **CORRELATE**: Find relationships between metrics. Use both PostgreSQL and host-level metrics.
3. **PROPOSE**: Recommend specific DBA-level fixes.

**EFFICIENCY RULES**:
- **BATCHING**: If you need multiple metrics, query them in a single tool call if the tool supports it, or sequential calls before summarizing.
- **SPEED**: Be concise. Focus on the most likely root causes first.
- **SYSTEM METRICS**: You have access to `cpu_utilization`, `cpu_load1`, `memory_utilization`, etc. Use them early to rule out resource saturation.

When analyzing:
1. Identify the time range.
2. Query relevant metrics.
3. Generate a clear report with actionable recommendations.

Always be specific."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.model = settings.openai_model
        self.prometheus = PrometheusClient(settings.prometheus_url)
        self.tool_executor = ToolExecutor(self.prometheus)
        self.time_parser = TimeRangeParser()
        self.history_manager = HistoryManager(storage_dir="../enhancements/conversations")
    
    async def analyze(self, user_message: str, conversation_id: Optional[str] = None) -> dict[str, Any]:
        """
        Main entry point for analysis.
        Implements the SCAN -> CORRELATE -> PROPOSE reasoning loop.
        """
        if conversation_id:
            self.conversation_history = self.history_manager.get_history(conversation_id)
        else:
            self.conversation_history = []
        
        # If history is empty, initialize with system prompt
        if not self.conversation_history:
            self.conversation_history = [
                {"role": "system", "content": self.SYSTEM_PROMPT}
            ]
        
        # Add context about current time for time parsing
        current_time = datetime.now()
        context = f"\n\nCurrent time: {current_time.isoformat()}\n\nUser query: {user_message}"
        
        self.conversation_history.append({
            "role": "user",
            "content": context
        })
        
        # Run the reasoning loop
        max_iterations = 6
        iteration = 0
        final_response = None
        tool_calls_made = []
        
        while iteration < max_iterations:
            iteration += 1
            
            # Call the LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # If no tool calls, we're done
            if not message.tool_calls:
                final_response = message.content
                break
            
            # Execute tool calls
            self.conversation_history.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # Execute the tool
                result = await self.tool_executor.execute(tool_name, arguments)
                
                tool_calls_made.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result_summary": self._summarize_result(result)
                })
                
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
        
        # Save history if conversation_id is provided
        if conversation_id:
            # Add final response if available
            if final_response:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_response
                })
            self.history_manager.save_history(conversation_id, self.conversation_history)
        
        return {
            "analysis": final_response,
            "iterations": iteration,
            "tool_calls": tool_calls_made,
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id
        }
    
    def _summarize_result(self, result: dict[str, Any]) -> str:
        """Create a brief summary of a tool result for logging."""
        if "error" in result:
            return f"Error: {result['error']}"
        if "metric_name" in result:
            return f"Retrieved {result['metric_name']} data"
        if "available_metrics" in result:
            return f"Listed {result['total_count']} metrics"
        if "report_type" in result:
            return f"Generated {result['incident']['type']} report"
        return "Completed"
    
    async def get_quick_health(self) -> dict[str, Any]:
        """Get a quick health check without AI analysis."""
        return await self.tool_executor.execute("get_health_summary", {})
    
    async def parse_time_range(self, expression: str) -> dict[str, Any]:
        """Parse a time expression and return timestamps."""
        start, end = self.time_parser.parse(expression)
        return {
            "expression": expression,
            "start_timestamp": start,
            "end_timestamp": end,
            "start_iso": datetime.fromtimestamp(start).isoformat(),
            "end_iso": datetime.fromtimestamp(end).isoformat()
        }
    
    async def close(self):
        """Clean up resources."""
        await self.prometheus.close()
