"""
Service Ollama pour JARVIS
Gestion des modèles LLM locaux pour la planification et l'analyse
"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import ollama
from loguru import logger

class ModelType(Enum):
    """Types de modèles disponibles"""
    VISION = "vision"
    CODING = "coding"
    PLANNING = "planning"
    AUTOCOMPLETE = "autocomplete"
    GENERAL = "general"

@dataclass
class ModelConfig:
    """Configuration d'un modèle"""
    name: str
    type: ModelType
    context_length: int
    temperature: float
    system_prompt: str = ""
    available: bool = False
    
class OllamaModels:
    """Configuration des modèles Ollama pour JARVIS"""
    
    MODELS = {
        ModelType.VISION: ModelConfig(
            name="llava:7b",
            type=ModelType.VISION,
            context_length=4096,
            temperature=0.1,
            system_prompt="Tu es JARVIS, un assistant IA qui peut analyser des captures d'écran. Analyse les images avec précision et décris les éléments d'interface utilisateur visibles."
        ),
        ModelType.PLANNING: ModelConfig(
            name="qwen2.5-coder:7b",
            type=ModelType.PLANNING,
            context_length=8192,
            temperature=0.2,
            system_prompt="Tu es JARVIS, un assistant IA qui planifie des actions pour contrôler un ordinateur. Donne des instructions claires et sécurisées pour accomplir les tâches demandées."
        ),
        ModelType.CODING: ModelConfig(
            name="deepseek-coder:6.7b",
            type=ModelType.CODING,
            context_length=4096,
            temperature=0.1,
            system_prompt="Tu es un assistant de programmation expert. Fournis du code Python optimisé et bien documenté."
        ),
        ModelType.AUTOCOMPLETE: ModelConfig(
            name="deepseek-coder:1.3b",
            type=ModelType.AUTOCOMPLETE,
            context_length=2048,
            temperature=0.0,
            system_prompt="Complete le texte de manière naturelle et contextuelle."
        ),
        ModelType.GENERAL: ModelConfig(
            name="llama3.2:3b",
            type=ModelType.GENERAL,
            context_length=2048,
            temperature=0.3,
            system_prompt="Tu es JARVIS, un assistant IA intelligent et utile. Réponds de manière concise et professionnelle."
        )
    }

@dataclass
class GenerationRequest:
    """Requête de génération"""
    model_type: ModelType
    prompt: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    context: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None  # Base64 encoded images
    
@dataclass
class GenerationResponse:
    """Réponse de génération"""
    content: str
    model_used: str
    tokens_generated: int
    generation_time: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class OllamaService:
    """Service principal Ollama"""
    
    def __init__(self):
        self.models: Dict[ModelType, ModelConfig] = OllamaModels.MODELS.copy()
        self.client = None
        self.is_available = False
        self.stats = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "total_tokens": 0,
            "total_time": 0.0
        }
        
        logger.info("🤖 Service Ollama initialisé")
    
    async def initialize(self):
        """Initialise le service Ollama"""
        try:
            # Vérifier la disponibilité d'Ollama
            available_models = ollama.list()
            model_names = [model['name'] for model in available_models['models']]
            
            logger.info(f"📚 Modèles Ollama disponibles: {len(model_names)}")
            
            # Vérifier quels modèles JARVIS sont disponibles
            for model_type, config in self.models.items():
                if config.name in model_names:
                    config.available = True
                    logger.success(f"✅ {config.name} ({model_type.value}) disponible")
                else:
                    logger.warning(f"⚠️  {config.name} ({model_type.value}) non disponible")
            
            # Télécharger les modèles manquants critiques
            await self._ensure_critical_models()
            
            self.is_available = any(config.available for config in self.models.values())
            
            if self.is_available:
                logger.success("✅ Service Ollama prêt")
            else:
                logger.error("❌ Aucun modèle Ollama disponible")
                
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Ollama: {e}")
            self.is_available = False
    
    async def _ensure_critical_models(self):
        """S'assure que les modèles critiques sont disponibles"""
        critical_models = [ModelType.PLANNING, ModelType.GENERAL]
        
        for model_type in critical_models:
            config = self.models[model_type]
            if not config.available:
                try:
                    logger.info(f"🔄 Téléchargement du modèle critique: {config.name}")
                    ollama.pull(config.name)
                    config.available = True
                    logger.success(f"✅ {config.name} téléchargé avec succès")
                except Exception as e:
                    logger.error(f"❌ Erreur téléchargement {config.name}: {e}")
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Génère une réponse avec Ollama"""
        if not self.is_available:
            return GenerationResponse(
                content="",
                model_used="none",
                tokens_generated=0,
                generation_time=0.0,
                success=False,
                error="Service Ollama non disponible"
            )
        
        model_config = self.models.get(request.model_type)
        if not model_config or not model_config.available:
            # Fallback vers un modèle disponible
            fallback_config = self._get_fallback_model()
            if not fallback_config:
                return GenerationResponse(
                    content="",
                    model_used="none",
                    tokens_generated=0,
                    generation_time=0.0,
                    success=False,
                    error=f"Modèle {request.model_type.value} non disponible"
                )
            model_config = fallback_config
        
        start_time = time.time()
        self.stats["requests_total"] += 1
        
        try:
            # Préparer les paramètres
            system_prompt = request.system_prompt or model_config.system_prompt
            temperature = request.temperature if request.temperature is not None else model_config.temperature
            
            # Construire le prompt final
            if system_prompt:
                full_prompt = f"<system>{system_prompt}</system>\n\n{request.prompt}"
            else:
                full_prompt = request.prompt
            
            # Paramètres de génération
            generate_params = {
                "model": model_config.name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_ctx": model_config.context_length
                }
            }
            
            # Ajouter les images pour les modèles de vision
            if request.images and model_config.type == ModelType.VISION:
                generate_params["images"] = request.images
            
            # Limite de tokens si spécifiée
            if request.max_tokens:
                generate_params["options"]["num_predict"] = request.max_tokens
            
            # Génération
            response = ollama.generate(**generate_params)
            
            generation_time = time.time() - start_time
            
            # Extraire les statistiques
            tokens_generated = response.get("eval_count", 0)
            
            # Mettre à jour les stats
            self.stats["requests_success"] += 1
            self.stats["total_tokens"] += tokens_generated
            self.stats["total_time"] += generation_time
            
            result = GenerationResponse(
                content=response["response"],
                model_used=model_config.name,
                tokens_generated=tokens_generated,
                generation_time=generation_time,
                success=True,
                metadata={
                    "model_type": request.model_type.value,
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "total_duration": response.get("total_duration", 0)
                }
            )
            
            logger.debug(f"🤖 Génération réussie: {tokens_generated} tokens en {generation_time:.2f}s")
            return result
            
        except Exception as e:
            generation_time = time.time() - start_time
            self.stats["requests_failed"] += 1
            
            logger.error(f"❌ Erreur génération Ollama: {e}")
            
            return GenerationResponse(
                content="",
                model_used=model_config.name,
                tokens_generated=0,
                generation_time=generation_time,
                success=False,
                error=str(e)
            )
    
    def _get_fallback_model(self) -> Optional[ModelConfig]:
        """Récupère un modèle de fallback disponible"""
        # Ordre de préférence pour les fallbacks
        fallback_order = [ModelType.GENERAL, ModelType.PLANNING, ModelType.CODING]
        
        for model_type in fallback_order:
            config = self.models.get(model_type)
            if config and config.available:
                return config
        
        # Dernier recours: n'importe quel modèle disponible
        for config in self.models.values():
            if config.available:
                return config
        
        return None
    
    # Méthodes de commodité pour différents types de tâches
    
    async def plan_action(self, task_description: str, context: Dict[str, Any] = None) -> GenerationResponse:
        """Planifie une action à effectuer"""
        context_str = ""
        if context:
            context_str = f"\nContexte: {json.dumps(context, indent=2)}"
        
        prompt = f"""Tâche à accomplir: {task_description}{context_str}

Planifie les étapes détaillées pour accomplir cette tâche en utilisant les outils disponibles:
- Vision (capture et analyse d'écran)
- Contrôle souris (clic, déplacement, glisser-déposer)
- Contrôle clavier (frappe, raccourcis)
- Détection d'applications

Fournis un plan structuré avec:
1. Analyse de la situation actuelle
2. Étapes séquentielles à suivre
3. Actions spécifiques pour chaque étape
4. Vérifications à effectuer

Sois précis et sécurisé dans tes recommandations."""
        
        request = GenerationRequest(
            model_type=ModelType.PLANNING,
            prompt=prompt,
            context=context
        )
        
        return await self.generate(request)
    
    async def analyze_screen(self, image_base64: str, objective: str = None) -> GenerationResponse:
        """Analyse une capture d'écran"""
        objective_text = f"\nObjectif: {objective}" if objective else ""
        
        prompt = f"""Analyse cette capture d'écran en détail.{objective_text}

Décris:
1. Le type d'application ou de page visible
2. Les éléments d'interface principaux (boutons, menus, champs)
3. Le contenu textuel important
4. L'état actuel de l'interface
5. Les actions possibles pour l'utilisateur

Sois précis et détaillé dans ton analyse."""
        
        request = GenerationRequest(
            model_type=ModelType.VISION,
            prompt=prompt,
            images=[image_base64]
        )
        
        return await self.generate(request)
    
    async def generate_code(self, task: str, language: str = "python") -> GenerationResponse:
        """Génère du code pour une tâche"""
        prompt = f"""Génère du code {language} pour accomplir cette tâche: {task}

Exigences:
- Code propre et bien documenté
- Gestion d'erreurs appropriée
- Type hints si applicable
- Commentaires explicatifs
- Code fonctionnel et testé

Fournis uniquement le code, sans explications supplémentaires."""
        
        request = GenerationRequest(
            model_type=ModelType.CODING,
            prompt=prompt,
            temperature=0.1
        )
        
        return await self.generate(request)
    
    async def autocomplete_text(self, text: str, context: str = "") -> GenerationResponse:
        """Auto-complétion de texte"""
        context_text = f"Contexte: {context}\n\n" if context else ""
        
        prompt = f"""{context_text}Texte à compléter: {text}

Complete ce texte de manière naturelle et contextuelle. Fournis seulement la suite du texte, sans répéter le texte original."""
        
        request = GenerationRequest(
            model_type=ModelType.AUTOCOMPLETE,
            prompt=prompt,
            max_tokens=100,
            temperature=0.0
        )
        
        return await self.generate(request)
    
    async def chat(self, message: str, conversation_history: List[Dict[str, str]] = None) -> GenerationResponse:
        """Discussion générale avec JARVIS"""
        history_text = ""
        if conversation_history:
            for entry in conversation_history[-5:]:  # Garder les 5 derniers messages
                role = entry.get("role", "user")
                content = entry.get("content", "")
                history_text += f"{role}: {content}\n"
        
        prompt = f"""{history_text}user: {message}

Réponds de manière naturelle et utile en tant que JARVIS."""
        
        request = GenerationRequest(
            model_type=ModelType.GENERAL,
            prompt=prompt
        )
        
        return await self.generate(request)
    
    # Méthodes de gestion
    
    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles disponibles"""
        return [config.name for config in self.models.values() if config.available]
    
    def get_model_info(self, model_type: ModelType) -> Optional[Dict[str, Any]]:
        """Retourne les informations d'un modèle"""
        config = self.models.get(model_type)
        if not config:
            return None
        
        return {
            "name": config.name,
            "type": config.type.value,
            "context_length": config.context_length,
            "temperature": config.temperature,
            "available": config.available,
            "system_prompt": config.system_prompt[:100] + "..." if len(config.system_prompt) > 100 else config.system_prompt
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du service"""
        stats = self.stats.copy()
        
        if stats["requests_total"] > 0:
            stats["success_rate"] = stats["requests_success"] / stats["requests_total"]
            stats["avg_tokens_per_request"] = stats["total_tokens"] / stats["requests_success"] if stats["requests_success"] > 0 else 0
            stats["avg_time_per_request"] = stats["total_time"] / stats["requests_success"] if stats["requests_success"] > 0 else 0
        
        stats["available_models"] = len(self.get_available_models())
        stats["service_available"] = self.is_available
        
        return stats
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.stats = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "total_tokens": 0,
            "total_time": 0.0
        }
        logger.info("📊 Statistiques Ollama remises à zéro")

# Fonctions utilitaires
async def quick_generate(prompt: str, model_type: ModelType = ModelType.GENERAL) -> str:
    """Génération rapide"""
    service = OllamaService()
    await service.initialize()
    
    request = GenerationRequest(model_type=model_type, prompt=prompt)
    response = await service.generate(request)
    
    return response.content if response.success else f"Erreur: {response.error}"

async def quick_chat(message: str) -> str:
    """Chat rapide avec JARVIS"""
    service = OllamaService()
    await service.initialize()
    
    response = await service.chat(message)
    return response.content if response.success else f"Erreur: {response.error}"

if __name__ == "__main__":
    async def test_ollama():
        service = OllamaService()
        await service.initialize()
        
        if not service.is_available:
            print("❌ Service Ollama non disponible")
            return
        
        # Test de chat
        print("🤖 Test de chat:")
        response = await service.chat("Bonjour JARVIS, peux-tu te présenter?")
        if response.success:
            print(f"JARVIS: {response.content}")
            print(f"📊 {response.tokens_generated} tokens en {response.generation_time:.2f}s")
        
        # Test de planification
        print("\n📋 Test de planification:")
        response = await service.plan_action("Ouvrir le navigateur et aller sur Google")
        if response.success:
            print(f"Plan: {response.content[:200]}...")
        
        # Statistiques
        print("\n📊 Statistiques:")
        stats = service.get_stats()
        print(f"- Requêtes: {stats['requests_total']} (succès: {stats['requests_success']})")
        print(f"- Modèles disponibles: {stats['available_models']}")
    
    asyncio.run(test_ollama())