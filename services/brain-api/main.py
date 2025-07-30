#!/usr/bin/env python3
"""
🧠 JARVIS Brain API - Main Entry Point
Architecture M.A.MM: Métacognition, Agent, Memory Manager
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app

# Import modules internes
from core.metacognition import MetacognitionEngine
from core.agent import ReactAgent
from core.memory import HybridMemoryManager
from core.websocket_manager import WebSocketManager
from core.audio_streamer import AudioStreamer
from personas.persona_manager import PersonaManager
from api.routes import health, chat, memory, agent, metacognition, audio, persona
from utils.config import settings
from utils.monitoring import setup_metrics

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
    "metacognition": None,
    "agent": None,
    "memory": None,
    "websocket_manager": None,
    "audio_streamer": None,
    "persona_manager": None,
    "startup_time": None,
    "healthy": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    startup_start = asyncio.get_event_loop().time()
    
    try:
        # 🚀 Initialisation des services
        logger.info("🧠 Démarrage Brain API JARVIS v2.0...")
        
        # 1. Métacognition Engine
        logger.info("🤔 Initialisation Métacognition Engine...")
        app_state["metacognition"] = MetacognitionEngine(
            hallucination_threshold=settings.METACOGNITION_THRESHOLD,
            complexity_min_score=settings.COMPLEXITY_MIN_SCORE
        )
        await app_state["metacognition"].initialize()
        logger.info("✅ Métacognition Engine prêt")
        
        # 2. Memory Manager hybride
        logger.info("🧮 Initialisation Memory Manager...")
        app_state["memory"] = HybridMemoryManager(
            db_url=settings.MEMORY_DB_URL,
            redis_url=settings.REDIS_URL
        )
        await app_state["memory"].initialize()
        logger.info("✅ Memory Manager prêt")
        
        # 3. Persona Manager
        logger.info("🎭 Initialisation Persona Manager...")
        app_state["persona_manager"] = PersonaManager(
            memory_manager=app_state["memory"],
            default_persona="jarvis_classic"
        )
        await app_state["persona_manager"].initialize()
        logger.info("✅ Persona Manager prêt")
        
        # 4. React Agent avec Persona Manager
        logger.info("🤖 Initialisation React Agent...")
        app_state["agent"] = ReactAgent(
            llm_url=settings.OLLAMA_URL,
            memory_manager=app_state["memory"],
            metacognition=app_state["metacognition"],
            persona_manager=app_state["persona_manager"]
        )
        await app_state["agent"].initialize()
        logger.info("✅ React Agent prêt")
        
        # 5. Audio Streamer
        logger.info("🎵 Initialisation Audio Streamer...")
        app_state["audio_streamer"] = AudioStreamer()
        await app_state["audio_streamer"].initialize()
        logger.info("✅ Audio Streamer prêt")
        
        # 6. WebSocket Manager avec Audio Streamer
        logger.info("🔌 Initialisation WebSocket Manager...")
        app_state["websocket_manager"] = WebSocketManager(
            agent=app_state["agent"],
            memory=app_state["memory"],
            audio_streamer=app_state["audio_streamer"]
        )
        await app_state["websocket_manager"].initialize()
        logger.info("✅ WebSocket Manager prêt")
        
        # ✅ Application prête
        startup_time = asyncio.get_event_loop().time() - startup_start
        app_state["startup_time"] = startup_time
        app_state["healthy"] = True
        
        logger.info(
            "🎉 Brain API complètement initialisé",
            startup_time_seconds=round(startup_time, 2),
            services_count=len([k for k in app_state.keys() if app_state[k] is not None])
        )
        
        yield
        
    except Exception as e:
        logger.error("❌ Erreur lors de l'initialisation", error=str(e), exc_info=True)
        app_state["healthy"] = False
        raise
    
    finally:
        # 🛑 Nettoyage lors de l'arrêt
        logger.info("🛑 Arrêt Brain API...")
        
        if app_state["websocket_manager"]:
            await app_state["websocket_manager"].shutdown()
            
        if app_state["audio_streamer"]:
            await app_state["audio_streamer"].shutdown()
            
        if app_state["agent"]:
            await app_state["agent"].shutdown()
            
        if app_state["persona_manager"]:
            await app_state["persona_manager"].shutdown()
            
        if app_state["memory"]:
            await app_state["memory"].shutdown()
            
        if app_state["metacognition"]:
            await app_state["metacognition"].shutdown()
        
        logger.info("✅ Brain API arrêté proprement")

# 🚀 Création de l'application FastAPI
app = FastAPI(
    title="JARVIS Brain API",
    description="Cerveau central JARVIS - Architecture M.A.MM (Métacognition, Agent, Memory)",
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

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 📊 Métriques Prometheus
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# 🛣️ Routes API
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(metacognition.router, prefix="/api/metacognition", tags=["Metacognition"])
app.include_router(audio.router, prefix="/api/audio", tags=["Audio"])
app.include_router(persona.router, prefix="/api/persona", tags=["Persona"])

# 🔌 WebSocket endpoint
from core.websocket_handler import websocket_endpoint
app.add_websocket_route("/ws", websocket_endpoint)

@app.get("/")
async def root():
    """Point d'entrée racine avec informations de l'API"""
    return {
        "name": "JARVIS Brain API",
        "version": "2.0.0",
        "architecture": "M.A.MM (Métacognition, Agent, Memory)",
        "status": "healthy" if app_state["healthy"] else "unhealthy",
        "startup_time": app_state.get("startup_time"),
        "services": {
            "metacognition": app_state["metacognition"] is not None,
            "agent": app_state["agent"] is not None,
            "memory": app_state["memory"] is not None,
            "websocket": app_state["websocket_manager"] is not None,
            "audio_streamer": app_state["audio_streamer"] is not None,
            "persona_manager": app_state["persona_manager"] is not None
        },
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "memory": "/api/memory", 
            "agent": "/api/agent",
            "metacognition": "/api/metacognition",
            "websocket": "/ws",
            "audio": "/api/audio",
            "persona": "/api/persona",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Gestionnaire global d'exceptions"""
    logger.error(
        "🚨 Exception non gérée",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return HTTPException(
        status_code=500,
        detail="Erreur interne du serveur Brain API"
    )

def signal_handler(signum, frame):
    """Gestionnaire de signaux pour arrêt propre"""
    logger.info(f"📶 Signal reçu: {signum}, arrêt en cours...")
    sys.exit(0)

async def main():
    """Point d'entrée principal"""
    # Configuration signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configuration monitoring
    setup_metrics()
    
    # Configuration serveur
    config = uvicorn.Config(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        server_header=False,
        date_header=False
    )
    
    server = uvicorn.Server(config)
    
    try:
        logger.info(
            "🚀 Démarrage serveur Brain API",
            host=settings.HOST,
            port=settings.PORT,
            log_level=settings.LOG_LEVEL
        )
        
        await server.serve()
        
    except Exception as e:
        logger.error("❌ Erreur serveur", error=str(e), exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())