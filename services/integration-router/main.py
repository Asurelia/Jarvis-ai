#!/usr/bin/env python3
"""
JARVIS AI - Integration Router Service
Central routing and integration service for all JARVIS AI components
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse, urljoin

import httpx
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
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
REQUESTS_TOTAL = Counter('integration_router_requests_total', 'Total requests', ['method', 'endpoint', 'target_service'])
REQUEST_DURATION = Histogram('integration_router_request_duration_seconds', 'Request duration')
INTEGRATIONS_PROCESSED = Counter('integration_router_integrations_total', 'Total integrations processed', ['type', 'status'])

# Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://frontend:3000")
MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL", "http://mcp-gateway:5006")
AUTOCOMPLETE_URL = os.getenv("AUTOCOMPLETE_URL", "http://autocomplete-service:5007")
AI_POD_URL = os.getenv("AI_POD_URL", "http://host.docker.internal:8080")
AUDIO_POD_URL = os.getenv("AUDIO_POD_URL", "http://host.docker.internal:5002")
CONTROL_POD_URL = os.getenv("CONTROL_POD_URL", "http://host.docker.internal:5004")
VOICE_BRIDGE_URL = os.getenv("VOICE_BRIDGE_URL", "http://host.docker.internal:3001")

# Security
security = HTTPBearer(auto_error=False)

# Service registry
SERVICE_REGISTRY = {
    "ai": {"url": AI_POD_URL, "health_path": "/health", "status": "unknown"},
    "audio": {"url": AUDIO_POD_URL, "health_path": "/health", "status": "unknown"},
    "control": {"url": CONTROL_POD_URL, "health_path": "/health", "status": "unknown"},
    "frontend": {"url": FRONTEND_URL, "health_path": "/health", "status": "unknown"},
    "mcp": {"url": MCP_GATEWAY_URL, "health_path": "/health", "status": "unknown"},
    "autocomplete": {"url": AUTOCOMPLETE_URL, "health_path": "/health", "status": "unknown"},
    "voice": {"url": VOICE_BRIDGE_URL, "health_path": "/health", "status": "unknown"},
}

# Pydantic models
class RouteRequest(BaseModel):
    target_service: str = Field(..., description="Target service name")
    method: str = Field(default="GET", description="HTTP method")
    path: str = Field(..., description="API path")
    data: Optional[Dict[str, Any]] = Field(None, description="Request data")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional headers")
    timeout: Optional[int] = Field(default=30, description="Request timeout in seconds")

class IntegrationRequest(BaseModel):
    integration_type: str = Field(..., description="Type of integration")
    source_service: str = Field(..., description="Source service")
    target_service: str = Field(..., description="Target service")
    data: Dict[str, Any] = Field(..., description="Integration data")
    priority: int = Field(default=1, ge=1, le=10, description="Priority level")

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    services: Dict[str, Dict[str, Any]]

class ServiceStatus(BaseModel):
    name: str
    url: str
    status: str
    last_check: datetime
    response_time: Optional[float] = None

# FastAPI app
app = FastAPI(
    title="JARVIS Integration Router",
    description="Central routing and integration service for all JARVIS AI components",
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
service_health_cache = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the service"""
    global http_client
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
    
    # Start health monitoring task
    asyncio.create_task(health_monitor_task())
    
    logger.info("Integration Router service started", version="1.0.0")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global http_client
    if http_client:
        await http_client.aclose()
    logger.info("Integration Router service shutting down")

async def health_monitor_task():
    """Background task to monitor service health"""
    while True:
        try:
            await update_service_health()
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error("Health monitor task failed", error=str(e))
            await asyncio.sleep(60)  # Retry after 1 minute on error

async def update_service_health():
    """Update health status for all registered services"""
    for service_name, service_info in SERVICE_REGISTRY.items():
        try:
            start_time_check = datetime.utcnow()
            response = await http_client.get(
                urljoin(service_info["url"], service_info["health_path"]),
                timeout=5.0
            )
            response_time = (datetime.utcnow() - start_time_check).total_seconds()
            
            if response.status_code == 200:
                SERVICE_REGISTRY[service_name]["status"] = "healthy"
                service_health_cache[service_name] = {
                    "status": "healthy",
                    "last_check": datetime.utcnow(),
                    "response_time": response_time
                }
            else:
                SERVICE_REGISTRY[service_name]["status"] = "unhealthy"
                service_health_cache[service_name] = {
                    "status": "unhealthy",
                    "last_check": datetime.utcnow(),
                    "response_time": response_time
                }
        except Exception as e:
            SERVICE_REGISTRY[service_name]["status"] = "unreachable"
            service_health_cache[service_name] = {
                "status": "unreachable",
                "last_check": datetime.utcnow(),
                "error": str(e)
            }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_service(url: str, method: str = "GET", **kwargs) -> httpx.Response:
    """Make HTTP call to other services with retry logic"""
    try:
        response = await http_client.request(method, url, **kwargs)
        return response
    except httpx.RequestError as e:
        logger.error("Service call failed", url=url, error=str(e))
        raise HTTPException(status_code=503, detail=f"Service unavailable: {url}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=uptime,
        services=service_health_cache
    )

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/route")
async def route_request(request: RouteRequest):
    """Route request to target service"""
    start_time_route = datetime.utcnow()
    
    REQUESTS_TOTAL.labels(
        method=request.method, 
        endpoint="/route", 
        target_service=request.target_service
    ).inc()
    
    with REQUEST_DURATION.time():
        try:
            # Validate target service
            if request.target_service not in SERVICE_REGISTRY:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unknown service: {request.target_service}"
                )
            
            service_info = SERVICE_REGISTRY[request.target_service]
            target_url = urljoin(service_info["url"], request.path)
            
            # Prepare request parameters
            kwargs = {"timeout": request.timeout}
            if request.data:
                if request.method.upper() in ["POST", "PUT", "PATCH"]:
                    kwargs["json"] = request.data
                else:
                    kwargs["params"] = request.data
            
            if request.headers:
                kwargs["headers"] = request.headers
            
            # Make the request
            response = await call_service(target_url, request.method, **kwargs)
            
            # Return response
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"content": response.text, "status_code": response.status_code}
            
        except Exception as e:
            logger.error("Request routing failed", error=str(e), target_service=request.target_service)
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/integrate")
async def handle_integration(request: IntegrationRequest, background_tasks: BackgroundTasks):
    """Handle service integration"""
    start_time_int = datetime.utcnow()
    
    INTEGRATIONS_PROCESSED.labels(type=request.integration_type, status="started").inc()
    
    try:
        logger.info(
            "Processing integration", 
            type=request.integration_type,
            source=request.source_service,
            target=request.target_service
        )
        
        # Process integration based on type
        result = await process_integration(request)
        
        # Schedule background tasks if needed
        if request.priority >= 5:
            background_tasks.add_task(notify_services, request, result)
        
        INTEGRATIONS_PROCESSED.labels(type=request.integration_type, status="success").inc()
        
        return {
            "status": "success",
            "integration_id": f"int_{int(start_time_int.timestamp())}",
            "result": result,
            "processing_time": (datetime.utcnow() - start_time_int).total_seconds()
        }
        
    except Exception as e:
        INTEGRATIONS_PROCESSED.labels(type=request.integration_type, status="error").inc()
        logger.error("Integration failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def process_integration(request: IntegrationRequest) -> Dict[str, Any]:
    """Process different types of integrations"""
    integration_type = request.integration_type.lower()
    
    if integration_type == "chat_to_audio":
        return await integrate_chat_to_audio(request)
    elif integration_type == "audio_to_control":
        return await integrate_audio_to_control(request)
    elif integration_type == "ai_to_frontend":
        return await integrate_ai_to_frontend(request)
    elif integration_type == "mcp_integration":
        return await integrate_mcp_service(request)
    elif integration_type == "autocomplete":
        return await integrate_autocomplete(request)
    else:
        return await generic_integration(request)

async def integrate_chat_to_audio(request: IntegrationRequest) -> Dict[str, Any]:
    """Integrate chat response to audio output"""
    try:
        # Extract text from AI response
        text = request.data.get("text", "")
        voice = request.data.get("voice", "jarvis")
        
        # Route to audio service
        audio_request = RouteRequest(
            target_service="audio",
            method="POST",
            path="/process",
            data={"action": "tts", "text": text, "voice": voice}
        )
        
        audio_response = await route_request(audio_request)
        return {"audio_generated": True, "response": audio_response}
        
    except Exception as e:
        logger.error("Chat to audio integration failed", error=str(e))
        return {"audio_generated": False, "error": str(e)}

async def integrate_audio_to_control(request: IntegrationRequest) -> Dict[str, Any]:
    """Integrate audio command to system control"""
    try:
        # Extract command from audio transcription
        command = request.data.get("command", "")
        parameters = request.data.get("parameters", {})
        
        # Route to control service
        control_request = RouteRequest(
            target_service="control",
            method="POST",
            path="/execute",
            data={"command": command, "parameters": parameters}
        )
        
        control_response = await route_request(control_request)
        return {"command_executed": True, "response": control_response}
        
    except Exception as e:
        logger.error("Audio to control integration failed", error=str(e))
        return {"command_executed": False, "error": str(e)}

async def integrate_ai_to_frontend(request: IntegrationRequest) -> Dict[str, Any]:
    """Integrate AI response to frontend"""
    try:
        # Format response for frontend
        formatted_response = {
            "type": "ai_response",
            "content": request.data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to frontend (if WebSocket available)
        return {"frontend_updated": True, "data": formatted_response}
        
    except Exception as e:
        logger.error("AI to frontend integration failed", error=str(e))
        return {"frontend_updated": False, "error": str(e)}

async def integrate_mcp_service(request: IntegrationRequest) -> Dict[str, Any]:
    """Integrate with MCP gateway"""
    try:
        mcp_request = RouteRequest(
            target_service="mcp",
            method="POST",
            path="/execute",
            data=request.data
        )
        
        mcp_response = await route_request(mcp_request)
        return {"mcp_executed": True, "response": mcp_response}
        
    except Exception as e:
        logger.error("MCP integration failed", error=str(e))
        return {"mcp_executed": False, "error": str(e)}

async def integrate_autocomplete(request: IntegrationRequest) -> Dict[str, Any]:
    """Integrate with autocomplete service"""
    try:
        autocomplete_request = RouteRequest(
            target_service="autocomplete",
            method="POST",
            path="/suggest",
            data=request.data
        )
        
        autocomplete_response = await route_request(autocomplete_request)
        return {"suggestions_generated": True, "response": autocomplete_response}
        
    except Exception as e:
        logger.error("Autocomplete integration failed", error=str(e))
        return {"suggestions_generated": False, "error": str(e)}

async def generic_integration(request: IntegrationRequest) -> Dict[str, Any]:
    """Handle generic integration"""
    return {
        "integration_type": request.integration_type,
        "source_service": request.source_service,
        "target_service": request.target_service,
        "data_processed": len(str(request.data)),
        "status": "processed"
    }

async def notify_services(request: IntegrationRequest, result: Dict[str, Any]):
    """Background task to notify services of integration completion"""
    try:
        # Notify source service
        if request.source_service in SERVICE_REGISTRY:
            notification = {
                "type": "integration_completed",
                "integration_type": request.integration_type,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await call_service(
                urljoin(SERVICE_REGISTRY[request.source_service]["url"], "/notify"),
                method="POST",
                json=notification,
                timeout=10
            )
            
    except Exception as e:
        logger.error("Service notification failed", error=str(e))

@app.get("/services")
async def list_services():
    """List all registered services and their status"""
    return {
        "services": SERVICE_REGISTRY,
        "health_cache": service_health_cache,
        "timestamp": datetime.utcnow()
    }

@app.get("/status")
async def get_status():
    """Get service status"""
    healthy_services = sum(1 for s in SERVICE_REGISTRY.values() if s["status"] == "healthy")
    total_services = len(SERVICE_REGISTRY)
    
    return {
        "service": "integration-router",
        "status": "running",
        "version": "1.0.0",
        "services_healthy": f"{healthy_services}/{total_services}",
        "uptime_seconds": (datetime.utcnow() - start_time).total_seconds(),
        "timestamp": datetime.utcnow()
    }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the service
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5022,
        log_level="info",
        access_log=True,
        reload=False
    )