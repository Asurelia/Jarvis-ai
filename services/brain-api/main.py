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
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
# Prometheus import handled in monitoring module

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
from utils.graceful_shutdown import create_jarvis_shutdown_manager, ShutdownMiddleware
from utils.redis_manager import get_redis_manager
from utils.circuit_breaker import circuit_manager

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

# État global de l'application avec optimisations
app_state: Dict[str, Any] = {
    "metacognition": None,
    "agent": None,
    "memory": None,
    "websocket_manager": None,
    "audio_streamer": None,
    "persona_manager": None,
    "redis_manager": None,
    "shutdown_manager": None,
    "startup_time": None,
    "healthy": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    startup_start = asyncio.get_event_loop().time()
    
    try:
        # 🚀 Initialisation des services avec optimisations
        logger.info("🧠 Démarrage Brain API JARVIS v2.0 Optimisé...")
        
        # 0. Graceful Shutdown Manager
        logger.info("🛑 Initialisation Graceful Shutdown Manager...")
        app_state["shutdown_manager"] = create_jarvis_shutdown_manager("brain-api")
        logger.info("✅ Graceful Shutdown Manager prêt")
        
        # 0.1 Redis Manager optimisé
        logger.info("🗃️ Initialisation Redis Manager optimisé...")
        app_state["redis_manager"] = await get_redis_manager(
            redis_url=settings.REDIS_URL,
            pool_size=50,
            max_connections=100
        )
        logger.info("✅ Redis Manager prêt")
        
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
        
        # ✅ Enregistrer hooks de shutdown
        shutdown_manager = app_state["shutdown_manager"]
        
        # Hooks en ordre de priorité (priorité basse = exécuté en premier)
        shutdown_manager.add_shutdown_hook(
            "websocket_manager", 
            lambda: app_state["websocket_manager"].shutdown() if app_state["websocket_manager"] else None,
            priority=10
        )
        shutdown_manager.add_shutdown_hook(
            "audio_streamer",
            lambda: app_state["audio_streamer"].shutdown() if app_state["audio_streamer"] else None,
            priority=20
        )
        shutdown_manager.add_shutdown_hook(
            "agent",
            lambda: app_state["agent"].shutdown() if app_state["agent"] else None,
            priority=30
        )
        shutdown_manager.add_shutdown_hook(
            "persona_manager",
            lambda: app_state["persona_manager"].shutdown() if app_state["persona_manager"] else None,
            priority=40
        )
        shutdown_manager.add_shutdown_hook(
            "memory",
            lambda: app_state["memory"].shutdown() if app_state["memory"] else None,
            priority=50
        )
        shutdown_manager.add_shutdown_hook(
            "redis_manager",
            lambda: app_state["redis_manager"].shutdown() if app_state["redis_manager"] else None,
            priority=60
        )
        shutdown_manager.add_shutdown_hook(
            "metacognition",
            lambda: app_state["metacognition"].shutdown() if app_state["metacognition"] else None,
            priority=70
        )
        
        # ✅ Application prête
        startup_time = asyncio.get_event_loop().time() - startup_start
        app_state["startup_time"] = startup_time
        app_state["healthy"] = True
        
        logger.info(
            "🎉 Brain API complètement initialisé avec optimisations",
            startup_time_seconds=round(startup_time, 2),
            services_count=len([k for k in app_state.keys() if app_state[k] is not None]),
            redis_pool_size=50,
            circuit_breakers=len(circuit_manager.circuits)
        )
        
        yield
        
    except Exception as e:
        logger.error("❌ Erreur lors de l'initialisation", error=str(e), exc_info=True)
        app_state["healthy"] = False
        raise
    
    finally:
        # 🛑 Nettoyage géré par Graceful Shutdown Manager
        logger.info("🛑 Arrêt Brain API via Graceful Shutdown...")
        
        if app_state["shutdown_manager"]:
            # Le shutdown manager s'occupe de tout dans le bon ordre
            await app_state["shutdown_manager"].shutdown()
        else:
            # Fallback manuel si pas de shutdown manager
            logger.warning("⚠️ Arrêt manuel (pas de shutdown manager)") 
            
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
            
            if app_state["redis_manager"]:
                await app_state["redis_manager"].shutdown()
                
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
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware pour ajouter les headers de sécurité"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Headers de sécurité obligatoires
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
            "X-Permitted-Cross-Domain-Policies": "none",
        }
        
        # HSTS en mode production HTTPS
        if request.headers.get("x-forwarded-proto") == "https" or request.url.scheme == "https":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # CSP strict en production
        security_mode = os.getenv("SECURITY_MODE", "production")
        if security_mode == "production":
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "connect-src 'self' wss: ws:; "
                "font-src 'self'; "
                "media-src 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            # CSP plus permissif en développement
            csp = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "connect-src 'self' http://localhost:* ws://localhost:* wss://localhost:*; "
                "img-src 'self' data: blob:;"
            )
        
        security_headers["Content-Security-Policy"] = csp
        
        # Ajouter tous les headers de sécurité
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting simple"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Nettoyer les entrées anciennes
        self.clients = {
            ip: calls for ip, calls in self.clients.items()
            if calls and calls[-1] > now - self.period
        }
        
        # Vérifier le rate limit
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        
        self.clients[client_ip] = [
            call_time for call_time in self.clients[client_ip]
            if call_time > now - self.period
        ]
        
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(self.period)}
            )
        
        self.clients[client_ip].append(now)
        return await call_next(request)

# Configuration CORS sécurisée selon l'environnement
security_mode = os.getenv("SECURITY_MODE", "production")
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")

if security_mode == "production":
    # Production: CORS très restrictif
    if not allowed_origins_env:
        logger.error("🚨 ERREUR SÉCURITÉ: ALLOWED_ORIGINS requis en production!")
        raise ValueError("ALLOWED_ORIGINS doit être configuré en mode production")
    
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    
    # Vérifier que les origins sont HTTPS en production
    for origin in allowed_origins:
        if not origin.startswith("https://"):
            logger.warning(f"⚠️  Origin non-HTTPS en production: {origin}")
    
    allowed_methods = ["GET", "POST", "OPTIONS"]
    allowed_headers = ["Authorization", "Content-Type", "Accept"]
    
else:
    # Développement: CORS permissif
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    
    if allowed_origins_env:
        allowed_origins.extend([origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()])
    
    allowed_origins = list(set(allowed_origins))
    allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers = ["Authorization", "Content-Type", "Accept", "Origin", "User-Agent", "X-Requested-With"]

logger.info(f"🌐 CORS configuré - Mode: {security_mode}, Origins: {len(allowed_origins)} configurées")

# Middlewares de sécurité
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting en production
if security_mode == "production":
    rate_limit_calls = int(os.getenv("RATE_LIMIT_MAX", "100"))
    rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    app.add_middleware(RateLimitMiddleware, calls=rate_limit_calls, period=rate_limit_window)

# Trusted Host en production
if security_mode == "production":
    trusted_hosts = os.getenv("TRUSTED_HOSTS", "")
    if trusted_hosts:
        hosts = [host.strip() for host in trusted_hosts.split(",") if host.strip()]
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
        logger.info(f"🛡️  Trusted hosts configurés: {hosts}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=allowed_methods,
    allow_headers=allowed_headers,
    expose_headers=["Content-Length"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware de graceful shutdown
if "shutdown_manager" in app_state and app_state["shutdown_manager"]:
    app.add_middleware(ShutdownMiddleware, shutdown_manager=app_state["shutdown_manager"])

# 📊 Métriques Prometheus
try:
    from utils.monitoring import make_asgi_app
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    logger.info("📊 Endpoint /metrics configuré")
except Exception as e:
    logger.warning(f"⚠️ Impossible de configurer /metrics: {e}")

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
            "persona_manager": app_state["persona_manager"] is not None,
            "redis_manager": app_state["redis_manager"] is not None,
            "shutdown_manager": app_state["shutdown_manager"] is not None
        },
        "optimizations": {
            "connection_pooling": True,
            "circuit_breakers": len(circuit_manager.circuits),
            "graceful_shutdown": app_state["shutdown_manager"] is not None,
            "redis_cache": app_state["redis_manager"] is not None
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