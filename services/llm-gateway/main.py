#!/usr/bin/env python3
"""
🧠 LLM Gateway Service - Intelligent Model Routing for JARVIS
Optimized for AMD RX 7800 XT (16GB VRAM) with GPT-OSS 20B integration
"""

import asyncio
import time
import json
import aiohttp
import psutil
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import structlog
import GPUtil

# Configuration logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

class ModelType(Enum):
    LIGHT = "light"      # llama3.2:3b
    HEAVY = "heavy"      # gpt-oss-20b
    FALLBACK = "fallback"

class GPUStatus(Enum):
    OPTIMAL = "optimal"     # < 70% VRAM, < 75°C
    LOADED = "loaded"       # 70-85% VRAM, 75-80°C
    CRITICAL = "critical"   # > 85% VRAM, > 80°C
    ERROR = "error"

@dataclass
class ModelConfig:
    name: str
    url: str
    max_vram_mb: int
    optimal_temperature: int
    quantization: str
    context_length: int
    supports_streaming: bool = True
    warmup_time: float = 0.0

@dataclass 
class GPUMetrics:
    memory_used_mb: int
    memory_total_mb: int
    memory_percent: float
    temperature_c: float
    utilization_percent: float
    status: GPUStatus
    last_updated: float

@dataclass
class RequestComplexity:
    token_count: int
    reasoning_required: bool
    context_length: int
    multimodal: bool
    complexity_score: float  # 0.0 to 1.0

class LLMGateway:
    """Gateway intelligent pour routing multi-modèles optimisé AMD RX 7800 XT"""
    
    def __init__(self):
        # Configuration modèles optimisée AMD RX 7800 XT (16GB VRAM)
        self.models = {
            ModelType.LIGHT: ModelConfig(
                name="llama3.2:3b",
                url="http://host.docker.internal:11434",
                max_vram_mb=3072,    # 3GB pour llama3.2:3b
                optimal_temperature=75,
                quantization="Q4_K_M",
                context_length=8192
            ),
            ModelType.HEAVY: ModelConfig(
                name="gpt-oss-20b",
                url="http://host.docker.internal:11434",
                max_vram_mb=12288,   # 12GB pour GPT-OSS 20B en Q4
                optimal_temperature=80,
                quantization="Q4_K_M", 
                context_length=16384
            ),
            ModelType.FALLBACK: ModelConfig(
                name="llama3.2:3b",
                url="http://ollama-fallback:11434",
                max_vram_mb=3072,
                optimal_temperature=75,
                quantization="Q4_K_M",
                context_length=4096
            )
        }
        
        # État du système
        self.current_model: Optional[ModelType] = None
        self.gpu_metrics: Optional[GPUMetrics] = None
        self.model_cache: Dict[str, Any] = {}
        self.request_queue: List[Dict] = []
        
        # Statistiques
        self.stats = {
            "total_requests": 0,
            "light_model_requests": 0,
            "heavy_model_requests": 0,
            "fallback_requests": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0,
            "gpu_switches": 0,
            "failures": 0
        }
        
        # Configuration thresholds
        self.complexity_threshold = 0.6  # Au-dessus = modèle lourd
        self.vram_warning_threshold = 0.85  # 85% VRAM
        self.temperature_warning = 82  # °C
        
    async def initialize(self):
        """Initialisation du gateway avec détection GPU"""
        logger.info("🚀 Initialisation LLM Gateway...")
        
        # Détecter GPU AMD
        await self._detect_gpu()
        
        # Tester connectivité modèles
        await self._test_model_connections()
        
        # Démarrer monitoring GPU
        asyncio.create_task(self._monitor_gpu_loop())
        
        logger.info("✅ LLM Gateway initialisé", 
                   gpu_vram=f"{self.gpu_metrics.memory_total_mb}MB" if self.gpu_metrics else "unknown")

    async def _detect_gpu(self):
        """Détection et configuration GPU AMD RX 7800 XT"""
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Premier GPU détecté
                self.gpu_metrics = GPUMetrics(
                    memory_used_mb=int(gpu.memoryUsed),
                    memory_total_mb=int(gpu.memoryTotal), 
                    memory_percent=gpu.memoryUtil * 100,
                    temperature_c=gpu.temperature,
                    utilization_percent=gpu.load * 100,
                    status=self._calculate_gpu_status(gpu.memoryUtil * 100, gpu.temperature),
                    last_updated=time.time()
                )
                logger.info("🎮 GPU détecté", 
                           name=gpu.name,
                           vram_total=f"{gpu.memoryTotal}MB",
                           vram_used=f"{gpu.memoryUsed}MB")
            else:
                logger.warning("⚠️ Aucun GPU détecté, mode CPU fallback")
                
        except Exception as e:
            logger.error("❌ Erreur détection GPU", error=str(e))

    def _calculate_gpu_status(self, memory_percent: float, temperature: float) -> GPUStatus:
        """Calcul du statut GPU basé sur VRAM et température"""
        if memory_percent > 85 or temperature > 82:
            return GPUStatus.CRITICAL
        elif memory_percent > 70 or temperature > 75:
            return GPUStatus.LOADED
        else:
            return GPUStatus.OPTIMAL

    async def _monitor_gpu_loop(self):
        """Monitoring continu GPU AMD"""
        while True:
            try:
                await self._update_gpu_metrics()
                await asyncio.sleep(5)  # Update toutes les 5s
            except Exception as e:
                logger.error("❌ Erreur monitoring GPU", error=str(e))
                await asyncio.sleep(10)

    async def _update_gpu_metrics(self):
        """Mise à jour métriques GPU"""
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                self.gpu_metrics = GPUMetrics(
                    memory_used_mb=int(gpu.memoryUsed),
                    memory_total_mb=int(gpu.memoryTotal),
                    memory_percent=gpu.memoryUtil * 100,
                    temperature_c=gpu.temperature,
                    utilization_percent=gpu.load * 100,
                    status=self._calculate_gpu_status(gpu.memoryUtil * 100, gpu.temperature),
                    last_updated=time.time()
                )
        except Exception as e:
            logger.error("❌ Erreur mise à jour GPU", error=str(e))

    async def _test_model_connections(self):
        """Test connectivité modèles Ollama"""
        for model_type, config in self.models.items():
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(f"{config.url}/api/tags") as response:
                        if response.status == 200:
                            data = await response.json()
                            models = [m['name'] for m in data.get('models', [])]
                            if config.name in models:
                                logger.info(f"✅ Modèle {config.name} disponible sur {config.url}")
                            else:
                                logger.warning(f"⚠️ Modèle {config.name} non trouvé sur {config.url}")
                        else:
                            logger.error(f"❌ Connexion {config.url} échouée: {response.status}")
            except Exception as e:
                logger.error(f"❌ Test connexion {model_type}: {str(e)}")

    def analyze_request_complexity(self, messages: List[Dict], context: Dict = None) -> RequestComplexity:
        """Analyse de complexité de requête pour sélection modèle"""
        
        # Calculer nombre de tokens approximatif
        total_text = ""
        for msg in messages:
            total_text += msg.get('content', '') + " "
        
        # Estimation tokens (approximation)
        token_count = len(total_text.split()) * 1.3  # Facteur d'approximation
        
        # Analyse contenu pour déterminer complexité
        reasoning_indicators = [
            "explain", "analyze", "compare", "reasoning", "logic", "problem",
            "step by step", "think through", "complex", "detailed", "comprehensive"
        ]
        
        code_indicators = [
            "code", "function", "class", "algorithm", "programming", "debug",
            "implement", "optimize", "refactor"
        ]
        
        text_lower = total_text.lower()
        reasoning_score = sum(1 for indicator in reasoning_indicators if indicator in text_lower)
        code_score = sum(1 for indicator in code_indicators if indicator in text_lower)
        
        # Calcul score complexité (0.0 à 1.0)
        complexity_factors = {
            "token_length": min(token_count / 1000, 1.0) * 0.3,
            "reasoning": min(reasoning_score / 5, 1.0) * 0.4,
            "code": min(code_score / 3, 1.0) * 0.3
        }
        
        complexity_score = sum(complexity_factors.values())
        
        return RequestComplexity(
            token_count=int(token_count),
            reasoning_required=reasoning_score > 1,
            context_length=len(messages),
            multimodal=False,  # TODO: Détecter contenu multimodal
            complexity_score=min(complexity_score, 1.0)
        )

    def select_optimal_model(self, complexity: RequestComplexity) -> Tuple[ModelType, str]:
        """Sélection modèle optimal basée sur complexité et état GPU"""
        
        # Vérifier état GPU critique
        if self.gpu_metrics and self.gpu_metrics.status == GPUStatus.CRITICAL:
            return ModelType.FALLBACK, "GPU en état critique, utilisation fallback"
        
        # Sélection basée sur complexité
        if complexity.complexity_score >= self.complexity_threshold:
            # Requête complexe - vérifier si GPU peut gérer GPT-OSS 20B
            if self.gpu_metrics:
                required_vram = self.models[ModelType.HEAVY].max_vram_mb
                available_vram = self.gpu_metrics.memory_total_mb - self.gpu_metrics.memory_used_mb
                
                if available_vram >= required_vram:
                    return ModelType.HEAVY, f"Complexité élevée ({complexity.complexity_score:.2f}), GPU optimal"
                else:
                    return ModelType.LIGHT, f"Complexité élevée mais VRAM insuffisante ({available_vram}MB < {required_vram}MB)"
            else:
                return ModelType.HEAVY, f"Complexité élevée ({complexity.complexity_score:.2f}), pas de monitoring GPU"
        else:
            # Requête simple - utiliser modèle léger
            return ModelType.LIGHT, f"Complexité faible ({complexity.complexity_score:.2f}), modèle léger optimal"

    async def process_request(self, messages: List[Dict], stream: bool = True, **kwargs) -> Dict:
        """Traitement intelligent de requête avec sélection modèle"""
        
        start_time = time.time()
        request_id = f"req_{int(time.time() * 1000)}"
        
        try:
            # Analyse complexité
            complexity = self.analyze_request_complexity(messages)
            
            # Sélection modèle
            model_type, selection_reason = self.select_optimal_model(complexity)
            model_config = self.models[model_type]
            
            logger.info("🧠 Routage requête", 
                       request_id=request_id,
                       model=model_config.name,
                       complexity=complexity.complexity_score,
                       reason=selection_reason)
            
            # Préparer payload Ollama
            payload = {
                "model": model_config.name,
                "messages": messages,
                "stream": stream,
                "options": {
                    "temperature": kwargs.get('temperature', 0.7),
                    "top_p": kwargs.get('top_p', 0.9),
                    "max_tokens": kwargs.get('max_tokens', 2048)
                }
            }
            
            # Envoi requête
            async with aiohttp.ClientSession() as session:
                url = f"{model_config.url}/api/chat"
                
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=error_text)
                    
                    # Mise à jour statistiques
                    self.stats["total_requests"] += 1
                    if model_type == ModelType.LIGHT:
                        self.stats["light_model_requests"] += 1
                    elif model_type == ModelType.HEAVY:
                        self.stats["heavy_model_requests"] += 1
                    else:
                        self.stats["fallback_requests"] += 1
                    
                    response_time = time.time() - start_time
                    self.stats["avg_response_time"] = (
                        (self.stats["avg_response_time"] * (self.stats["total_requests"] - 1) + response_time) 
                        / self.stats["total_requests"]
                    )
                    
                    if stream:
                        return StreamingResponse(
                            self._stream_response(response, request_id, model_config.name),
                            media_type="text/plain"
                        )
                    else:
                        result = await response.json()
                        return {
                            "response": result,
                            "metadata": {
                                "model_used": model_config.name,
                                "complexity_score": complexity.complexity_score,
                                "response_time": response_time,
                                "gpu_status": self.gpu_metrics.status.value if self.gpu_metrics else "unknown"
                            }
                        }
                        
        except Exception as e:
            self.stats["failures"] += 1
            logger.error("❌ Erreur traitement requête", request_id=request_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"Erreur Gateway LLM: {str(e)}")

    async def _stream_response(self, response, request_id: str, model_name: str):
        """Streaming de réponse avec monitoring"""
        try:
            async for chunk in response.content:
                if chunk:
                    yield chunk
        except Exception as e:
            logger.error("❌ Erreur streaming", request_id=request_id, model=model_name, error=str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

# 🚀 FastAPI Application
app = FastAPI(
    title="JARVIS LLM Gateway",
    description="Gateway intelligent pour routing multi-modèles optimisé AMD RX 7800 XT",
    version="1.0.0"
)

gateway = LLMGateway()

@app.on_event("startup")
async def startup():
    await gateway.initialize()

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    stream: bool = True
    temperature: float = 0.7
    max_tokens: int = 2048

@app.post("/api/chat")
async def chat_completion(request: ChatRequest):
    """Endpoint de chat avec sélection intelligente de modèle"""
    return await gateway.process_request(
        messages=request.messages,
        stream=request.stream,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )

@app.get("/api/health")
async def health():
    """Endpoint santé avec métriques GPU"""
    return {
        "status": "healthy",
        "gpu_metrics": asdict(gateway.gpu_metrics) if gateway.gpu_metrics else None,
        "models_available": [config.name for config in gateway.models.values()],
        "stats": gateway.stats
    }

@app.get("/api/models")
async def list_models():
    """Liste des modèles disponibles"""
    return {
        "models": {
            model_type.value: {
                "name": config.name,
                "vram_required": f"{config.max_vram_mb}MB",
                "context_length": config.context_length,
                "quantization": config.quantization
            }
            for model_type, config in gateway.models.items()
        }
    }

@app.get("/api/metrics")
async def metrics():
    """Métriques détaillées système et GPU"""
    return {
        "gpu": asdict(gateway.gpu_metrics) if gateway.gpu_metrics else None,
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        },
        "gateway_stats": gateway.stats,
        "current_model": gateway.current_model.value if gateway.current_model else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5010)