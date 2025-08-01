"""
🔍 Template d'instrumentation Prometheus pour les services JARVIS AI
Utilitaire pour ajouter rapidement des métriques à tous les services
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
import psutil
from typing import Optional


class PrometheusInstrumentation:
    """Classe d'instrumentation Prometheus réutilisable"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.registry = CollectorRegistry()
        self._init_common_metrics()
        
    def _init_common_metrics(self):
        """Initialise les métriques communes à tous les services"""
        prefix = f"{self.service_name.lower().replace('-', '_')}"
        
        # Métriques de requêtes HTTP
        self.http_requests = Counter(
            f'{prefix}_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            f'{prefix}_http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Métriques de performance
        self.memory_usage = Gauge(
            f'{prefix}_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            f'{prefix}_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        # Métriques d'erreur
        self.errors = Counter(
            f'{prefix}_errors_total',
            'Total errors',
            ['error_type'],
            registry=self.registry
        )
        
        # Métriques de connexions
        self.active_connections = Gauge(
            f'{prefix}_active_connections',
            'Number of active connections',
            registry=self.registry
        )
        
        # Métriques de santé
        self.service_up = Gauge(
            f'{prefix}_up',
            'Service availability',
            registry=self.registry
        )
        
        # Marquer le service comme actif
        self.service_up.set(1)
    
    def add_custom_metric(self, metric_type: str, name: str, description: str, labels: Optional[list] = None):
        """Ajoute une métrique custom"""
        prefix = f"{self.service_name.lower().replace('-', '_')}"
        full_name = f"{prefix}_{name}"
        
        if metric_type == "counter":
            return Counter(full_name, description, labels or [], registry=self.registry)
        elif metric_type == "histogram":
            return Histogram(full_name, description, labels or [], registry=self.registry)
        elif metric_type == "gauge":
            return Gauge(full_name, description, labels or [], registry=self.registry)
        else:
            raise ValueError(f"Type de métrique non supporté: {metric_type}")
    
    def update_system_metrics(self):
        """Met à jour les métriques système"""
        try:
            process = psutil.Process()
            self.memory_usage.set(process.memory_info().rss)
            self.cpu_usage.set(process.cpu_percent())
        except Exception as e:
            self.errors.labels(error_type='system_metrics').inc()
    
    def get_metrics_response(self):
        """Retourne la réponse Prometheus formatée"""
        self.update_system_metrics()
        return Response(
            generate_latest(self.registry),
            media_type=CONTENT_TYPE_LATEST
        )
    
    def instrument_request(self, method: str, endpoint: str):
        """Décorateur pour instrumenter une requête"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                
                try:
                    self.http_requests.labels(method=method, endpoint=endpoint, status='started').inc()
                    result = await func(*args, **kwargs)
                    self.http_requests.labels(method=method, endpoint=endpoint, status='success').inc()
                    return result
                except Exception as e:
                    status = "error"
                    self.http_requests.labels(method=method, endpoint=endpoint, status='error').inc()
                    self.errors.labels(error_type='http_request').inc()
                    raise
                finally:
                    duration = time.time() - start_time
                    self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
            
            return wrapper
        return decorator


# Métriques spécifiques par service

class TTSMetrics(PrometheusInstrumentation):
    """Métriques spécifiques au service TTS"""
    
    def __init__(self):
        super().__init__("tts-service")
        
        # Métriques TTS spécifiques
        self.synthesis_duration = self.add_custom_metric(
            "histogram", "synthesis_duration_seconds",
            "Time spent synthesizing speech", ["voice", "language"]
        )
        
        self.audio_generation_duration = self.add_custom_metric(
            "histogram", "audio_generation_duration_seconds",
            "Duration of generated audio", ["voice"]
        )
        
        self.model_load_time = self.add_custom_metric(
            "gauge", "model_load_time_seconds",
            "Time taken to load TTS model"
        )
        
        self.streaming_sessions = self.add_custom_metric(
            "gauge", "streaming_sessions_active",
            "Number of active streaming sessions"
        )


class SystemControlMetrics(PrometheusInstrumentation):
    """Métriques spécifiques au service System Control"""
    
    def __init__(self):
        super().__init__("system-control")
        
        # Métriques de contrôle système
        self.actions_executed = self.add_custom_metric(
            "counter", "actions_executed_total",
            "Total system actions executed", ["action_type", "status"]
        )
        
        self.action_duration = self.add_custom_metric(
            "histogram", "action_duration_seconds",
            "Time taken to execute actions", ["action_type"]
        )
        
        self.security_violations = self.add_custom_metric(
            "counter", "security_violations_total",
            "Total security violations detected", ["violation_type"]
        )


class TerminalMetrics(PrometheusInstrumentation):
    """Métriques spécifiques au service Terminal"""
    
    def __init__(self):
        super().__init__("terminal-service")
        
        # Métriques de terminal
        self.sessions_created = self.add_custom_metric(
            "counter", "sessions_created_total",
            "Total terminal sessions created"
        )
        
        self.active_sessions = self.add_custom_metric(
            "gauge", "sessions_active",
            "Number of active terminal sessions"
        )
        
        self.commands_executed = self.add_custom_metric(
            "counter", "commands_executed_total",
            "Total commands executed", ["status", "user"]
        )
        
        self.command_duration = self.add_custom_metric(
            "histogram", "command_duration_seconds",
            "Time taken to execute commands"
        )


class MCPGatewayMetrics(PrometheusInstrumentation):
    """Métriques spécifiques au service MCP Gateway"""
    
    def __init__(self):
        super().__init__("mcp-gateway")
        
        # Métriques MCP
        self.mcp_requests = self.add_custom_metric(
            "counter", "mcp_requests_total",
            "Total MCP protocol requests", ["method", "status"]
        )
        
        self.mcp_response_time = self.add_custom_metric(
            "histogram", "mcp_response_time_seconds",
            "MCP request response time", ["method"]
        )
        
        self.tools_invoked = self.add_custom_metric(
            "counter", "tools_invoked_total",
            "Total tools invoked", ["tool_name", "status"]
        )


class AutocompleteMetrics(PrometheusInstrumentation):
    """Métriques spécifiques au service Autocomplete"""
    
    def __init__(self):
        super().__init__("autocomplete-service")
        
        # Métriques d'autocomplétion
        self.suggestions_generated = self.add_custom_metric(
            "counter", "suggestions_generated_total",
            "Total suggestions generated", ["context_type"]
        )
        
        self.suggestion_accuracy = self.add_custom_metric(
            "histogram", "suggestion_accuracy_score",
            "Accuracy score of suggestions"
        )
        
        self.learning_updates = self.add_custom_metric(
            "counter", "learning_updates_total",
            "Total learning model updates"
        )


class GPUStatsMetrics(PrometheusInstrumentation):
    """Métriques spécifiques au service GPU Stats"""
    
    def __init__(self):
        super().__init__("gpu-stats-service")
        
        # Métriques GPU
        self.gpu_utilization = self.add_custom_metric(
            "gauge", "gpu_utilization_percent",
            "GPU utilization percentage", ["gpu_id"]
        )
        
        self.gpu_memory_usage = self.add_custom_metric(
            "gauge", "gpu_memory_usage_bytes",
            "GPU memory usage in bytes", ["gpu_id"]
        )
        
        self.gpu_temperature = self.add_custom_metric(
            "gauge", "gpu_temperature_celsius",
            "GPU temperature in Celsius", ["gpu_id"]
        )
        
        self.gpu_power_draw = self.add_custom_metric(
            "gauge", "gpu_power_draw_watts",
            "GPU power consumption in watts", ["gpu_id"]
        )


class BrainAPIMetrics(PrometheusInstrumentation):
    """Métriques spécifiques au service Brain API"""
    
    def __init__(self):
        super().__init__("brain-api")
        
        # Métriques de conversation
        self.conversations_started = self.add_custom_metric(
            "counter", "conversations_started_total",
            "Total conversations started", ["persona"]
        )
        
        self.messages_processed = self.add_custom_metric(
            "counter", "messages_processed_total",
            "Total messages processed", ["persona", "type"]
        )
        
        self.ai_response_time = self.add_custom_metric(
            "histogram", "ai_response_time_seconds",
            "Time taken to generate AI responses", ["persona", "model"]
        )
        
        self.memory_operations = self.add_custom_metric(
            "counter", "memory_operations_total",
            "Total memory operations", ["operation_type", "status"]
        )
        
        self.websocket_connections = self.add_custom_metric(
            "gauge", "websocket_connections_active",
            "Number of active WebSocket connections"
        )