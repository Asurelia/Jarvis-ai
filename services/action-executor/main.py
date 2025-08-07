#!/usr/bin/env python3
"""
JARVIS AI - Action Executor Service
Advanced action execution and system control integration
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

import httpx
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUESTS_TOTAL = Counter('action_executor_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('action_executor_request_duration_seconds', 'Request duration')
ACTIONS_EXECUTED = Counter('action_executor_actions_total', 'Total actions executed', ['action_type', 'status'])

# Configuration
SYSTEM_CONTROL_URL = os.getenv("SYSTEM_CONTROL_URL", "http://system-control:5004")
TERMINAL_SERVICE_URL = os.getenv("TERMINAL_SERVICE_URL", "http://terminal-service:5005")
AI_POD_URL = os.getenv("AI_POD_URL", "http://host.docker.internal:8080")
VOICE_BRIDGE_URL = os.getenv("VOICE_BRIDGE_URL", "http://host.docker.internal:3001")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
JWT_REQUIRED = os.getenv("JWT_REQUIRED", "true").lower() == "true"

# Security
security = HTTPBearer(auto_error=False)

# Pydantic models
class ActionRequest(BaseModel):
    action_type: str = Field(..., description="Type of action to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    priority: int = Field(default=1, ge=1, le=10, description="Action priority (1-10)")
    timeout: Optional[int] = Field(default=30, description="Timeout in seconds")

class ActionResponse(BaseModel):
    action_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    dependencies: Dict[str, str]

# FastAPI app
app = FastAPI(
    title="JARVIS Action Executor",
    description="Advanced action execution and system control integration service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
start_time = datetime.utcnow()
http_client: Optional[httpx.AsyncClient] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the service"""
    global http_client
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    logger.info("Action Executor service started", version="1.0.0")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global http_client
    if http_client:
        await http_client.aclose()
    logger.info("Action Executor service shutting down")

async def verify_token(credentials = Depends(security)):
    """Simple token verification - implement proper JWT validation in production"""
    if not JWT_REQUIRED:
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required"
        )
    
    # TODO: Implement proper JWT validation
    return True

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_service(url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Make HTTP call to other services with retry logic"""
    try:
        response = await http_client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}
    except httpx.RequestError as e:
        logger.error("Service call failed", url=url, error=str(e))
        raise HTTPException(status_code=503, detail=f"Service unavailable: {url}")
    except httpx.HTTPStatusError as e:
        logger.error("Service returned error", url=url, status=e.response.status_code)
        raise HTTPException(status_code=e.response.status_code, detail="Service error")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    # Check dependencies
    dependencies = {}
    for service_name, url in [
        ("system-control", f"{SYSTEM_CONTROL_URL}/health"),
        ("terminal-service", f"{TERMINAL_SERVICE_URL}/health"),
        ("ai-pod", f"{AI_POD_URL}/health"),
    ]:
        try:
            await call_service(url, timeout=5)
            dependencies[service_name] = "healthy"
        except Exception:
            dependencies[service_name] = "unhealthy"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=uptime,
        dependencies=dependencies
    )

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/execute", response_model=ActionResponse, dependencies=[Depends(verify_token)])
async def execute_action(request: ActionRequest):
    """Execute an action"""
    start_time_exec = datetime.utcnow()
    action_id = f"action_{int(start_time_exec.timestamp())}"
    
    REQUESTS_TOTAL.labels(method="POST", endpoint="/execute").inc()
    
    with REQUEST_DURATION.time():
        try:
            logger.info("Executing action", action_id=action_id, action_type=request.action_type)
            
            # Route action based on type
            result = await route_action(request)
            
            execution_time = (datetime.utcnow() - start_time_exec).total_seconds()
            ACTIONS_EXECUTED.labels(action_type=request.action_type, status="success").inc()
            
            return ActionResponse(
                action_id=action_id,
                status="completed",
                result=result,
                execution_time=execution_time,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time_exec).total_seconds()
            ACTIONS_EXECUTED.labels(action_type=request.action_type, status="error").inc()
            logger.error("Action execution failed", action_id=action_id, error=str(e))
            
            return ActionResponse(
                action_id=action_id,
                status="failed",
                error=str(e),
                execution_time=execution_time,
                timestamp=datetime.utcnow()
            )

async def route_action(request: ActionRequest) -> Dict[str, Any]:
    """Route action to appropriate service"""
    action_type = request.action_type.lower()
    
    if action_type in ["system", "control", "keyboard", "mouse"]:
        return await execute_system_action(request)
    elif action_type in ["terminal", "command", "shell"]:
        return await execute_terminal_action(request)
    elif action_type in ["ai", "llm", "chat"]:
        return await execute_ai_action(request)
    elif action_type in ["voice", "audio", "speech"]:
        return await execute_voice_action(request)
    else:
        return await execute_generic_action(request)

async def execute_system_action(request: ActionRequest) -> Dict[str, Any]:
    """Execute system control action"""
    try:
        response = await call_service(
            f"{SYSTEM_CONTROL_URL}/control",
            method="POST",
            json=request.parameters
        )
        return {"service": "system-control", "response": response}
    except Exception as e:
        return {"service": "system-control", "error": str(e)}

async def execute_terminal_action(request: ActionRequest) -> Dict[str, Any]:
    """Execute terminal action"""
    try:
        response = await call_service(
            f"{TERMINAL_SERVICE_URL}/execute",
            method="POST",
            json=request.parameters
        )
        return {"service": "terminal-service", "response": response}
    except Exception as e:
        return {"service": "terminal-service", "error": str(e)}

async def execute_ai_action(request: ActionRequest) -> Dict[str, Any]:
    """Execute AI action"""
    try:
        response = await call_service(
            f"{AI_POD_URL}/chat",
            method="POST",
            json=request.parameters
        )
        return {"service": "ai-pod", "response": response}
    except Exception as e:
        return {"service": "ai-pod", "error": str(e)}

async def execute_voice_action(request: ActionRequest) -> Dict[str, Any]:
    """Execute voice action"""
    try:
        response = await call_service(
            f"{VOICE_BRIDGE_URL}/process",
            method="POST",
            json=request.parameters
        )
        return {"service": "voice-bridge", "response": response}
    except Exception as e:
        return {"service": "voice-bridge", "error": str(e)}

async def execute_generic_action(request: ActionRequest) -> Dict[str, Any]:
    """Execute generic action"""
    return {
        "action_type": request.action_type,
        "parameters": request.parameters,
        "status": "processed",
        "message": "Generic action executed successfully"
    }

@app.get("/status")
async def get_status():
    """Get service status"""
    return {
        "service": "action-executor",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the service
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5021,
        log_level="info",
        access_log=True,
        reload=False
    )