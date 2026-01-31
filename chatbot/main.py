"""
FastAPI application for the PostgreSQL Debugging Chatbot.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager

from agent import PostgresDebugAgent
from config import get_settings


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request from user."""
    message: str
    conversation_id: Optional[str] = None
    

class ChatResponse(BaseModel):
    """Chat response with analysis results."""
    analysis: Optional[str]
    iterations: int
    tool_calls: list
    timestamp: str
    conversation_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    prometheus_healthy: bool
    metrics: Optional[dict] = None
    alerts: Optional[list] = None


class TimeParseRequest(BaseModel):
    """Request to parse a time expression."""
    expression: str


class TimeParseResponse(BaseModel):
    """Parsed time range."""
    expression: str
    start_timestamp: int
    end_timestamp: int
    start_iso: str
    end_iso: str


# Global agent instance
agent: Optional[PostgresDebugAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global agent
    agent = PostgresDebugAgent()
    yield
    if agent:
        await agent.close()


# Create FastAPI app
app = FastAPI(
    title="PostgreSQL Debugging Chatbot",
    description="AI-powered chatbot for PostgreSQL performance analysis and incident RCA",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "PostgreSQL Debugging Chatbot",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "db_health": "/db-health",
            "parse_time": "/parse-time"
        }
    }


@app.get("/health")
async def health_check():
    """Application health check."""
    return {"status": "healthy", "service": "postgres-chatbot"}


@app.get("/db-health", response_model=HealthResponse)
async def database_health():
    """Get current database health metrics."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent.get_quick_health()
        return HealthResponse(
            status=result.get("status", "unknown"),
            prometheus_healthy=True,
            metrics=result.get("metrics"),
            alerts=result.get("alerts")
        )
    except Exception as e:
        return HealthResponse(
            status="error",
            prometheus_healthy=False,
            alerts=[str(e)]
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for database analysis queries.
    
    Example queries:
    - "What happened to the database in the last 30 minutes?"
    - "Analyze the incident on Jan 25th 2026 10-11 AM"
    - "Why is the database slow right now?"
    - "Check for connection exhaustion issues"
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        result = await agent.analyze(request.message, conversation_id=request.conversation_id)
        return ChatResponse(
            analysis=result.get("analysis"),
            iterations=result.get("iterations", 0),
            tool_calls=result.get("tool_calls", []),
            timestamp=result.get("timestamp", ""),
            conversation_id=result.get("conversation_id")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/parse-time", response_model=TimeParseResponse)
async def parse_time(request: TimeParseRequest):
    """
    Parse a natural language time expression into timestamps.
    
    Useful for testing time parsing before making a full analysis request.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent.parse_time_range(request.expression)
        return TimeParseResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse time: {str(e)}")


@app.get("/metrics")
async def list_metrics():
    """List all available PostgreSQL metrics."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent.tool_executor.execute("list_available_metrics", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
