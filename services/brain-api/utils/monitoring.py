"""
📊 Monitoring & Metrics - JARVIS Brain API
Configuration Prometheus et métriques applicatives
"""

import logging
import time

logger = logging.getLogger(__name__)

# Try to import Prometheus client, fallback to mock if not available
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, make_asgi_app
    PROMETHEUS_AVAILABLE = True
    logger.info("📊 Prometheus client disponible")
except ImportError:
    logger.warning("⚠️ Prometheus client non disponible, utilisation du fallback")
    PROMETHEUS_AVAILABLE = False
    # Import fallback classes
    from .monitoring_fallback import MockMetric as Counter
    from .monitoring_fallback import MockMetric as Histogram  
    from .monitoring_fallback import MockMetric as Gauge
    from .monitoring_fallback import MockMetric as Info
    
    def make_asgi_app():
        """Fallback ASGI app that returns 404"""
        async def app(scope, receive, send):
            await send({
                'type': 'http.response.start',
                'status': 404,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': b'Prometheus metrics not available',
            })
        return app

# Métriques Prometheus
REQUESTS_TOTAL = Counter(
    'jarvis_brain_requests_total',
    'Total des requêtes reçues',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'jarvis_brain_request_duration_seconds',
    'Durée des requêtes en secondes',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'jarvis_brain_websocket_connections_active',
    'Connexions WebSocket actives'
)

MEMORY_OPERATIONS = Counter(
    'jarvis_brain_memory_operations_total',
    'Opérations mémoire totales',
    ['operation_type', 'memory_type']
)

AGENT_EXECUTIONS = Counter(
    'jarvis_brain_agent_executions_total',
    'Exécutions agent totales',
    ['status']
)

AUDIO_SESSIONS = Gauge(
    'jarvis_brain_audio_sessions_active',
    'Sessions audio actives'
)

AUDIO_LATENCY = Histogram(
    'jarvis_brain_audio_latency_ms',
    'Latence audio en millisecondes'
)

LLAMA_REQUESTS = Counter(
    'jarvis_brain_llm_requests_total',
    'Requêtes LLM totales',
    ['model', 'status']
)

METACOGNITION_DECISIONS = Counter(
    'jarvis_brain_metacognition_decisions_total',
    'Décisions métacognition',
    ['decision']
)

# Info sur l'application
APP_INFO = Info(
    'jarvis_brain_app_info',
    'Informations sur l\'application Brain API'
)

def setup_metrics():
    """Initialiser les métriques Prometheus"""
    
    try:
        # Configurer les informations de l'app
        APP_INFO.info({
            'version': '2.0.0',
            'architecture': 'M.A.MM',
            'python_version': '3.11',
            'startup_time': str(time.time())
        })
        
        logger.info("📊 Métriques Prometheus initialisées")
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation métriques: {e}")

def record_request(method: str, endpoint: str, status: int, duration: float):
    """Enregistrer une requête HTTP"""
    try:
        REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement requête: {e}")

def record_websocket_connection(active_count: int):
    """Enregistrer le nombre de connexions WebSocket actives"""
    try:
        ACTIVE_CONNECTIONS.set(active_count)
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement connexions: {e}")

def record_memory_operation(operation_type: str, memory_type: str):
    """Enregistrer une opération mémoire"""
    try:
        MEMORY_OPERATIONS.labels(operation_type=operation_type, memory_type=memory_type).inc()
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement mémoire: {e}")

def record_agent_execution(status: str):
    """Enregistrer une exécution d'agent"""
    try:
        AGENT_EXECUTIONS.labels(status=status).inc()
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement agent: {e}")

def record_audio_session(active_count: int):
    """Enregistrer le nombre de sessions audio actives"""
    try:
        AUDIO_SESSIONS.set(active_count)
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement audio sessions: {e}")

def record_audio_latency(latency_ms: float):
    """Enregistrer la latence audio"""
    try:
        AUDIO_LATENCY.observe(latency_ms)
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement latence audio: {e}")

def record_llm_request(model: str, status: str):
    """Enregistrer une requête LLM"""
    try:
        LLAMA_REQUESTS.labels(model=model, status=status).inc()
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement LLM: {e}")

def record_metacognition_decision(decision: str):
    """Enregistrer une décision métacognition"""
    try:
        METACOGNITION_DECISIONS.labels(decision=decision).inc()
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement métacognition: {e}")

# Middleware FastAPI pour métriques automatiques
class MetricsMiddleware:
    """Middleware pour collecter automatiquement les métriques"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        method = scope["method"]
        path = scope["path"]
        
        # Variables pour capturer la réponse
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            record_request(method, path, status_code, duration)