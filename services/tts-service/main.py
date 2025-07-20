#!/usr/bin/env python3
"""
🗣️ JARVIS TTS Service - Coqui.ai XTTS Streaming
Service de synthèse vocale temps réel avec anti-hallucination
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
import json
import base64

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prometheus_client import make_asgi_app

# Import modules internes
from core.tts_engine import TTSEngine
from core.audio_processor import AudioProcessor
from core.stream_manager import StreamManager
from utils.config import settings
from utils.monitoring import setup_metrics, record_tts_request

# Configuration logging structuré
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# État global de l'application
app_state: Dict[str, Any] = {
    "tts_engine": None,
    "audio_processor": None,
    "stream_manager": None,
    "startup_time": None,
    "healthy": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    startup_start = asyncio.get_event_loop().time()
    
    try:
        # 🚀 Initialisation des services
        logger.info("🗣️ Démarrage TTS Service JARVIS v2.0...")
        
        # 1. TTS Engine avec Coqui.ai
        logger.info("🎯 Initialisation TTS Engine...")
        app_state["tts_engine"] = TTSEngine(
            model_name=settings.TTS_MODEL,
            device=settings.TTS_DEVICE,
            enable_anti_hallucination=settings.ANTI_HALLUCINATION
        )
        await app_state["tts_engine"].initialize()
        logger.info("✅ TTS Engine prêt")
        
        # 2. Audio Processor
        logger.info("🎵 Initialisation Audio Processor...")
        app_state["audio_processor"] = AudioProcessor(
            sample_rate=settings.SAMPLE_RATE,
            channels=settings.CHANNELS,
            chunk_size=settings.CHUNK_SIZE
        )
        await app_state["audio_processor"].initialize()
        logger.info("✅ Audio Processor prêt")
        
        # 3. Stream Manager
        logger.info("📡 Initialisation Stream Manager...")
        app_state["stream_manager"] = StreamManager(
            tts_engine=app_state["tts_engine"],
            audio_processor=app_state["audio_processor"]
        )
        await app_state["stream_manager"].initialize()
        logger.info("✅ Stream Manager prêt")
        
        # ✅ Application prête
        startup_time = asyncio.get_event_loop().time() - startup_start
        app_state["startup_time"] = startup_time
        app_state["healthy"] = True
        
        logger.info(
            "🎉 TTS Service complètement initialisé",
            startup_time_seconds=round(startup_time, 2),
            model=settings.TTS_MODEL
        )
        
        yield
        
    except Exception as e:
        logger.error("❌ Erreur lors de l'initialisation", error=str(e), exc_info=True)
        app_state["healthy"] = False
        raise
    
    finally:
        # 🛑 Nettoyage lors de l'arrêt
        logger.info("🛑 Arrêt TTS Service...")
        
        if app_state["stream_manager"]:
            await app_state["stream_manager"].shutdown()
            
        if app_state["audio_processor"]:
            await app_state["audio_processor"].shutdown()
            
        if app_state["tts_engine"]:
            await app_state["tts_engine"].shutdown()
        
        logger.info("✅ TTS Service arrêté proprement")

# 🚀 Création de l'application FastAPI
app = FastAPI(
    title="JARVIS TTS Service",
    description="Service de synthèse vocale Coqui.ai XTTS avec streaming temps réel",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 🔧 Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 📊 Métriques Prometheus
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Modèles Pydantic
class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "default"
    language: Optional[str] = "fr"
    speed: Optional[float] = 1.0
    pitch: Optional[float] = 1.0
    streaming: Optional[bool] = True

class VoiceCloneRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    
# 🛣️ Routes API

@app.get("/")
async def root():
    """Point d'entrée racine avec informations du service"""
    return {
        "name": "JARVIS TTS Service",
        "version": "2.0.0",
        "engine": "Coqui.ai XTTS",
        "status": "healthy" if app_state["healthy"] else "unhealthy",
        "startup_time": app_state.get("startup_time"),
        "services": {
            "tts_engine": app_state["tts_engine"] is not None,
            "audio_processor": app_state["audio_processor"] is not None,
            "stream_manager": app_state["stream_manager"] is not None
        },
        "endpoints": {
            "health": "/health",
            "synthesize": "/api/synthesize",
            "stream": "/api/stream",
            "voices": "/api/voices",
            "websocket": "/ws",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Check de santé du service"""
    if not app_state["healthy"]:
        raise HTTPException(status_code=503, detail="Service non disponible")
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": time.time() - app_state.get("startup_time", time.time()),
        "model_loaded": app_state["tts_engine"] is not None and app_state["tts_engine"].is_model_loaded(),
        "active_streams": app_state["stream_manager"].get_active_streams_count() if app_state["stream_manager"] else 0
    }

@app.post("/api/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Synthétiser du texte en audio
    Retourne l'audio complet en une seule réponse
    """
    if not app_state["tts_engine"]:
        raise HTTPException(status_code=503, detail="TTS Engine non disponible")
    
    try:
        start_time = time.time()
        
        # Synthétiser l'audio
        audio_data = await app_state["tts_engine"].synthesize(
            text=request.text,
            voice_id=request.voice_id,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch
        )
        
        # Traiter l'audio
        processed_audio = await app_state["audio_processor"].process(
            audio_data,
            normalize=True,
            remove_silence=True
        )
        
        # Encoder en base64
        audio_base64 = base64.b64encode(processed_audio).decode('utf-8')
        
        # Métriques
        duration = time.time() - start_time
        record_tts_request(
            voice_id=request.voice_id,
            language=request.language,
            text_length=len(request.text),
            duration=duration,
            streaming=False
        )
        
        return {
            "status": "success",
            "audio": audio_base64,
            "format": "wav",
            "sample_rate": settings.SAMPLE_RATE,
            "channels": settings.CHANNELS,
            "duration_ms": int(duration * 1000),
            "text_length": len(request.text)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur synthèse: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur synthèse: {str(e)}")

@app.post("/api/stream")
async def stream_speech(request: TTSRequest):
    """
    Streaming audio en temps réel
    Retourne un stream audio chunk par chunk
    """
    if not app_state["stream_manager"]:
        raise HTTPException(status_code=503, detail="Stream Manager non disponible")
    
    try:
        # Créer un générateur de stream
        async def audio_stream():
            async for chunk in app_state["stream_manager"].stream_synthesis(
                text=request.text,
                voice_id=request.voice_id,
                language=request.language,
                speed=request.speed,
                pitch=request.pitch
            ):
                yield chunk
        
        # Retourner le stream
        return StreamingResponse(
            audio_stream(),
            media_type="audio/wav",
            headers={
                "Cache-Control": "no-cache",
                "X-Content-Type-Options": "nosniff",
                "X-Voice-ID": request.voice_id,
                "X-Language": request.language
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur streaming: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur streaming: {str(e)}")

@app.get("/api/voices")
async def list_voices():
    """Lister les voix disponibles"""
    if not app_state["tts_engine"]:
        raise HTTPException(status_code=503, detail="TTS Engine non disponible")
    
    try:
        voices = await app_state["tts_engine"].list_voices()
        
        return {
            "status": "success",
            "voices": voices,
            "count": len(voices),
            "default_voice": "default"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur liste voix: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/api/voices/clone")
async def clone_voice(
    request: VoiceCloneRequest,
    audio_file: UploadFile = File(...)
):
    """
    Cloner une voix à partir d'un échantillon audio
    Nécessite au moins 10-30 secondes d'audio de qualité
    """
    if not app_state["tts_engine"]:
        raise HTTPException(status_code=503, detail="TTS Engine non disponible")
    
    try:
        # Vérifier le type de fichier
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Fichier audio requis")
        
        # Lire l'audio
        audio_data = await audio_file.read()
        
        # Cloner la voix
        voice_id = await app_state["tts_engine"].clone_voice(
            name=request.name,
            audio_data=audio_data,
            description=request.description
        )
        
        return {
            "status": "success",
            "voice_id": voice_id,
            "name": request.name,
            "message": "Voix clonée avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur clonage voix: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur clonage: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket pour streaming bidirectionnel
    Permet synthèse en temps réel avec latence minimale
    """
    await websocket.accept()
    session_id = f"tts_ws_{int(time.time() * 1000)}"
    
    try:
        logger.info(f"🔗 Nouvelle connexion WebSocket TTS: {session_id}")
        
        # Envoyer message de bienvenue
        await websocket.send_json({
            "type": "welcome",
            "session_id": session_id,
            "timestamp": time.time()
        })
        
        # Boucle de traitement
        while True:
            # Recevoir message
            message = await websocket.receive_text()
            data = json.loads(message)
            
            message_type = data.get("type", "unknown")
            
            if message_type == "synthesize":
                # Synthèse directe
                text = data.get("text", "")
                voice_id = data.get("voice_id", "default")
                
                if not text:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Texte requis"
                    })
                    continue
                
                # Streaming chunks audio
                chunk_index = 0
                async for audio_chunk in app_state["stream_manager"].stream_synthesis(
                    text=text,
                    voice_id=voice_id,
                    language=data.get("language", "fr"),
                    speed=data.get("speed", 1.0),
                    pitch=data.get("pitch", 1.0)
                ):
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "chunk_index": chunk_index,
                        "audio": base64.b64encode(audio_chunk).decode('utf-8'),
                        "timestamp": time.time()
                    })
                    chunk_index += 1
                
                # Fin du stream
                await websocket.send_json({
                    "type": "synthesis_complete",
                    "chunks_sent": chunk_index,
                    "timestamp": time.time()
                })
                
            elif message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": time.time()
                })
                
            else:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Type de message inconnu: {message_type}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"🔌 Déconnexion WebSocket TTS: {session_id}")
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket: {e}")
        await websocket.close()

# Configuration monitoring
setup_metrics()

if __name__ == "__main__":
    # Configuration serveur
    config = uvicorn.Config(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
    
    server = uvicorn.Server(config)
    
    logger.info(
        "🚀 Démarrage TTS Service",
        host=settings.HOST,
        port=settings.PORT,
        model=settings.TTS_MODEL
    )
    
    asyncio.run(server.serve())