#!/usr/bin/env python3
"""
JARVIS AI - Audio Router Service
Intelligent audio routing and processing service
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from io import BytesIO
import base64

import httpx
import structlog
import uvicorn
import numpy as np
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from tenacity import retry, stop_after_attempt, wait_exponential
import soundfile as sf
import librosa

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
REQUESTS_TOTAL = Counter('audio_router_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('audio_router_request_duration_seconds', 'Request duration')
AUDIO_PROCESSED = Counter('audio_router_processed_total', 'Total audio files processed', ['type', 'status'])

# Configuration
TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://tts-service:5002")
STT_SERVICE_URL = os.getenv("STT_SERVICE_URL", "http://stt-service:5003")
VOICE_BRIDGE_URL = os.getenv("VOICE_BRIDGE_URL", "http://host.docker.internal:3001")

# Pydantic models
class AudioProcessRequest(BaseModel):
    action: str = Field(..., description="Action to perform: tts, stt, enhance, route")
    text: Optional[str] = Field(None, description="Text for TTS")
    voice: Optional[str] = Field(default="jarvis", description="Voice preset")
    language: Optional[str] = Field(default="en", description="Language code")
    audio_format: Optional[str] = Field(default="wav", description="Audio format")
    sample_rate: Optional[int] = Field(default=22050, description="Sample rate")

class AudioResponse(BaseModel):
    status: str
    audio_data: Optional[str] = None  # Base64 encoded
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time: float
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    dependencies: Dict[str, str]

# FastAPI app
app = FastAPI(
    title="JARVIS Audio Router",
    description="Intelligent audio routing and processing service",
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
active_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize the service"""
    global http_client
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
    logger.info("Audio Router service started", version="1.0.0")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global http_client
    if http_client:
        await http_client.aclose()
    logger.info("Audio Router service shutting down")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_service(url: str, method: str = "GET", **kwargs) -> Union[Dict[str, Any], bytes]:
    """Make HTTP call to other services with retry logic"""
    try:
        response = await http_client.request(method, url, **kwargs)
        response.raise_for_status()
        
        # Handle different content types
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        elif "audio" in content_type:
            return response.content
        else:
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
        ("tts-service", f"{TTS_SERVICE_URL}/health"),
        ("stt-service", f"{STT_SERVICE_URL}/health"),
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

@app.post("/process", response_model=AudioResponse)
async def process_audio(request: AudioProcessRequest):
    """Process audio request"""
    start_time_proc = datetime.utcnow()
    
    REQUESTS_TOTAL.labels(method="POST", endpoint="/process").inc()
    
    with REQUEST_DURATION.time():
        try:
            logger.info("Processing audio", action=request.action)
            
            result = await route_audio_action(request)
            
            processing_time = (datetime.utcnow() - start_time_proc).total_seconds()
            AUDIO_PROCESSED.labels(type=request.action, status="success").inc()
            
            return AudioResponse(
                status="completed",
                **result,
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time_proc).total_seconds()
            AUDIO_PROCESSED.labels(type=request.action, status="error").inc()
            logger.error("Audio processing failed", action=request.action, error=str(e))
            
            return AudioResponse(
                status="failed",
                metadata={"error": str(e)},
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...), action: str = Form(...)):
    """Upload and process audio file"""
    start_time_proc = datetime.utcnow()
    
    try:
        # Read audio file
        audio_content = await file.read()
        
        if action == "stt":
            # Send to STT service
            files = {"file": (file.filename, audio_content, file.content_type)}
            response = await call_service(
                f"{STT_SERVICE_URL}/transcribe",
                method="POST",
                files=files
            )
            
            processing_time = (datetime.utcnow() - start_time_proc).total_seconds()
            return AudioResponse(
                status="completed",
                text=response.get("text", ""),
                metadata=response.get("metadata", {}),
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )
        
        elif action == "enhance":
            # Audio enhancement
            enhanced_audio = await enhance_audio(audio_content)
            encoded_audio = base64.b64encode(enhanced_audio).decode('utf-8')
            
            processing_time = (datetime.utcnow() - start_time_proc).total_seconds()
            return AudioResponse(
                status="completed",
                audio_data=encoded_audio,
                metadata={"format": "wav", "enhanced": True},
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
            
    except Exception as e:
        logger.error("Audio upload processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def route_audio_action(request: AudioProcessRequest) -> Dict[str, Any]:
    """Route audio action to appropriate service"""
    action = request.action.lower()
    
    if action == "tts":
        return await process_tts(request)
    elif action == "stt":
        raise HTTPException(status_code=400, detail="STT requires audio file upload")
    elif action == "enhance":
        raise HTTPException(status_code=400, detail="Audio enhancement requires audio file upload")
    elif action == "route":
        return await route_to_voice_bridge(request)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

async def process_tts(request: AudioProcessRequest) -> Dict[str, Any]:
    """Process text-to-speech"""
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required for TTS")
    
    try:
        # Prepare TTS request
        tts_data = {
            "text": request.text,
            "voice": request.voice or "jarvis",
            "language": request.language or "en",
            "format": request.audio_format or "wav"
        }
        
        # Call TTS service
        audio_content = await call_service(
            f"{TTS_SERVICE_URL}/synthesize",
            method="POST",
            json=tts_data
        )
        
        # If we get JSON response, extract audio data
        if isinstance(audio_content, dict):
            if "audio_data" in audio_content:
                return {"audio_data": audio_content["audio_data"]}
            else:
                return audio_content
        else:
            # Direct audio content
            encoded_audio = base64.b64encode(audio_content).decode('utf-8')
            return {"audio_data": encoded_audio}
            
    except Exception as e:
        logger.error("TTS processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"TTS processing failed: {str(e)}")

async def route_to_voice_bridge(request: AudioProcessRequest) -> Dict[str, Any]:
    """Route request to voice bridge"""
    try:
        response = await call_service(
            f"{VOICE_BRIDGE_URL}/process",
            method="POST",
            json=request.dict()
        )
        return response
    except Exception as e:
        logger.error("Voice bridge routing failed", error=str(e))
        return {"status": "voice_bridge_unavailable", "message": str(e)}

async def enhance_audio(audio_content: bytes) -> bytes:
    """Enhance audio quality"""
    try:
        # Load audio with librosa
        audio_data, sample_rate = librosa.load(BytesIO(audio_content), sr=None)
        
        # Apply basic audio enhancement
        # Remove silence
        audio_data, _ = librosa.effects.trim(audio_data, top_db=20)
        
        # Normalize audio
        audio_data = librosa.util.normalize(audio_data)
        
        # Reduce noise (simple spectral gating)
        stft = librosa.stft(audio_data)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Simple noise reduction
        noise_threshold = np.percentile(magnitude, 10)
        mask = magnitude > noise_threshold
        magnitude_clean = magnitude * mask
        
        # Reconstruct audio
        stft_clean = magnitude_clean * np.exp(1j * phase)
        audio_enhanced = librosa.istft(stft_clean)
        
        # Convert back to bytes
        output_buffer = BytesIO()
        sf.write(output_buffer, audio_enhanced, sample_rate, format='WAV')
        return output_buffer.getvalue()
        
    except Exception as e:
        logger.error("Audio enhancement failed", error=str(e))
        # Return original audio if enhancement fails
        return audio_content

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "audio":
                # Process audio stream
                result = await process_audio_stream(message.get("data"))
                await websocket.send_text(json.dumps(result))
            elif message.get("type") == "text":
                # Process TTS
                request = AudioProcessRequest(action="tts", text=message.get("text"))
                result = await process_tts(request)
                await websocket.send_text(json.dumps(result))
            
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        active_connections.remove(websocket)

async def process_audio_stream(audio_data: str) -> Dict[str, Any]:
    """Process streaming audio data"""
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)
        
        # Send to STT service for real-time processing
        files = {"file": ("stream.wav", audio_bytes, "audio/wav")}
        response = await call_service(
            f"{STT_SERVICE_URL}/transcribe",
            method="POST",
            files=files
        )
        
        return {
            "type": "transcription",
            "text": response.get("text", ""),
            "confidence": response.get("confidence", 0.0)
        }
        
    except Exception as e:
        logger.error("Audio stream processing failed", error=str(e))
        return {"type": "error", "message": str(e)}

@app.get("/status")
async def get_status():
    """Get service status"""
    return {
        "service": "audio-router",
        "status": "running",
        "version": "1.0.0",
        "active_connections": len(active_connections),
        "timestamp": datetime.utcnow()
    }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the service
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5020,
        log_level="info",
        access_log=True,
        reload=False
    )