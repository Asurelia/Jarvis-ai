"""
📊 Fallback Monitoring & Metrics - JARVIS Brain API
Simple monitoring without Prometheus when prometheus_client is not available
"""

import logging
import time
from typing import Dict, Any
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class MockMetric:
    """Mock metric class that logs instead of using Prometheus"""
    
    def __init__(self, name: str, description: str, labels: list = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self.data = defaultdict(int)
    
    def inc(self, amount: int = 1):
        """Increment counter"""
        self.data['total'] += amount
        logger.debug(f"Metric {self.name}: incremented by {amount} (total: {self.data['total']})")
    
    def set(self, value: float):
        """Set gauge value"""
        self.data['current'] = value
        logger.debug(f"Metric {self.name}: set to {value}")
    
    def observe(self, value: float):
        """Observe histogram value"""
        self.data['observations'] = self.data.get('observations', 0) + 1
        self.data['sum'] = self.data.get('sum', 0) + value
        self.data['avg'] = self.data['sum'] / self.data['observations']
        logger.debug(f"Metric {self.name}: observed {value} (avg: {self.data['avg']:.3f})")
    
    def labels(self, **kwargs):
        """Return labeled metric"""
        return MockLabeledMetric(self.name, self.description, kwargs)
    
    def info(self, info_dict: Dict[str, Any]):
        """Set info metric"""
        self.data.update(info_dict)
        logger.info(f"Metric {self.name}: info updated with {info_dict}")

class MockLabeledMetric:
    """Mock labeled metric"""
    
    def __init__(self, name: str, description: str, labels: Dict[str, str]):
        self.name = name
        self.description = description
        self.labels_dict = labels
        self.data = defaultdict(int)
    
    def inc(self, amount: int = 1):
        """Increment labeled counter"""
        key = "_".join(f"{k}:{v}" for k, v in self.labels_dict.items())
        self.data[key] += amount
        logger.debug(f"Metric {self.name}[{key}]: incremented by {amount} (total: {self.data[key]})")
    
    def observe(self, value: float):
        """Observe labeled histogram value"""
        key = "_".join(f"{k}:{v}" for k, v in self.labels_dict.items())
        obs_key = f"{key}_observations"
        sum_key = f"{key}_sum"
        
        self.data[obs_key] = self.data.get(obs_key, 0) + 1
        self.data[sum_key] = self.data.get(sum_key, 0) + value
        avg = self.data[sum_key] / self.data[obs_key]
        
        logger.debug(f"Metric {self.name}[{key}]: observed {value} (avg: {avg:.3f})")

# Mock metrics - same interface as Prometheus but using logging
REQUESTS_TOTAL = MockMetric(
    'jarvis_brain_requests_total',
    'Total des requêtes reçues',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = MockMetric(
    'jarvis_brain_request_duration_seconds',
    'Durée des requêtes en secondes',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = MockMetric(
    'jarvis_brain_websocket_connections_active',
    'Connexions WebSocket actives'
)

MEMORY_OPERATIONS = MockMetric(
    'jarvis_brain_memory_operations_total',
    'Opérations mémoire totales',
    ['operation_type', 'memory_type']
)

AGENT_EXECUTIONS = MockMetric(
    'jarvis_brain_agent_executions_total',
    'Exécutions agent totales',
    ['status']
)

AUDIO_SESSIONS = MockMetric(
    'jarvis_brain_audio_sessions_active',
    'Sessions audio actives'
)

AUDIO_LATENCY = MockMetric(
    'jarvis_brain_audio_latency_ms',
    'Latence audio en millisecondes'
)

LLAMA_REQUESTS = MockMetric(
    'jarvis_brain_llm_requests_total',
    'Requêtes LLM totales',
    ['model', 'status']
)

METACOGNITION_DECISIONS = MockMetric(
    'jarvis_brain_metacognition_decisions_total',
    'Décisions métacognition',
    ['decision']
)

APP_INFO = MockMetric(
    'jarvis_brain_app_info',
    'Informations sur l\'application Brain API'
)

def setup_metrics():
    """Initialiser les métriques fallback"""
    
    try:
        # Configurer les informations de l'app
        APP_INFO.info({
            'version': '2.0.0',
            'architecture': 'M.A.MM',
            'python_version': '3.11',
            'startup_time': str(time.time()),
            'monitoring_mode': 'fallback'
        })
        
        logger.info("📊 Métriques fallback initialisées (sans Prometheus)")
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation métriques fallback: {e}")

def record_request(method: str, endpoint: str, status: int, duration: float):
    """Enregistrer une requête HTTP"""
    try:
        REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=str(status)).inc()
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