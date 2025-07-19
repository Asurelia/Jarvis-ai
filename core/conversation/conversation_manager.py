"""
Gestionnaire de conversation pour JARVIS
Interface conversationnelle naturelle
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger

from core.ai.ollama_service import OllamaService
from core.conversation.context_handler import ContextHandler
from core.conversation.intent_recognizer import IntentRecognizer
from core.orchestrator.task_orchestrator import TaskOrchestrator


class ConversationState(Enum):
    """États de la conversation"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    EXECUTING = "executing"
    RESPONDING = "responding"


@dataclass
class ConversationTurn:
    """Un tour de conversation"""
    id: str
    user_input: str
    timestamp: float
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    plan: Optional[Dict[str, Any]] = None
    response: Optional[str] = None
    execution_status: str = "pending"
    execution_result: Optional[Dict[str, Any]] = None


class ConversationManager:
    """Gestionnaire de conversation principal"""
    
    def __init__(self, ollama_service: OllamaService):
        self.ollama_service = ollama_service
        self.context_handler = ContextHandler()
        self.intent_recognizer = IntentRecognizer(ollama_service)
        self.orchestrator = TaskOrchestrator()
        
        self.state = ConversationState.IDLE
        self.conversation_history: List[ConversationTurn] = []
        self.current_turn: Optional[ConversationTurn] = None
        
        # Configuration
        self.max_history_length = 50
        self.response_timeout = 30.0
        
    async def start_conversation(self) -> str:
        """Démarre une nouvelle conversation"""
        logger.info("🎭 Démarrage de la conversation JARVIS")
        self.state = ConversationState.LISTENING
        return "Bonjour ! Je suis JARVIS, votre assistant personnel. Comment puis-je vous aider aujourd'hui ?"
    
    async def process_input(self, user_input: str, input_type: str = "text") -> str:
        """Traite une entrée utilisateur et génère une réponse"""
        try:
            self.state = ConversationState.PROCESSING
            
            # Créer un nouveau tour de conversation
            turn = ConversationTurn(
                id=f"turn_{int(time.time())}",
                user_input=user_input,
                timestamp=time.time()
            )
            self.current_turn = turn
            
            logger.info(f"💬 Entrée utilisateur: {user_input}")
            
            # 1. Reconnaissance d'intention
            intent_result = await self.intent_recognizer.recognize_intent(user_input)
            turn.intent = intent_result.get("intent")
            turn.entities = intent_result.get("entities", {})
            
            logger.info(f"🎯 Intention détectée: {turn.intent}")
            
            # 2. Génération du plan d'action
            if turn.intent != "chat":
                plan = await self._generate_action_plan(user_input, intent_result)
                turn.plan = plan
                logger.info(f"📋 Plan généré: {plan.get('name', 'Plan')}")
                
                # 3. Exécution via l'orchestrateur
                self.state = ConversationState.EXECUTING
                execution_result = await self.orchestrator.execute_plan(plan)
                turn.execution_result = execution_result
                turn.execution_status = "completed" if execution_result.get("success") else "failed"
            
            # 4. Génération de la réponse conversationnelle
            self.state = ConversationState.RESPONDING
            response = await self._generate_conversational_response(user_input, turn)
            turn.response = response
            
            # 5. Mise à jour du contexte
            self.conversation_history.append(turn)
            if len(self.conversation_history) > self.max_history_length:
                self.conversation_history.pop(0)
            
            self.context_handler.update_context(turn)
            self.state = ConversationState.LISTENING
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur dans la conversation: {e}")
            self.state = ConversationState.LISTENING
            return f"Désolé, j'ai rencontré une erreur : {str(e)}"
    
    async def _generate_action_plan(self, user_input: str, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un plan d'action basé sur l'intention"""
        prompt = f"""
Tu es JARVIS, un assistant intelligent. Génère un plan d'action JSON pour cette demande :

Demande utilisateur: {user_input}
Intention: {intent_result.get('intent')}
Entités: {json.dumps(intent_result.get('entities', {}), indent=2)}

Réponds UNIQUEMENT avec ce JSON :
{{
  "name": "Nom du plan",
  "description": "Description de ce qui va être fait",
  "priority": "high|medium|low",
  "estimated_duration": "durée estimée",
  "tasks": [
    {{
      "id": "task_1",
      "type": "task_type",
      "description": "Description de la tâche",
      "parameters": {{"param": "valeur"}},
      "dependencies": [],
      "agent": "agent_name"
    }}
  ]
}}

Types de tâches disponibles: web_navigation, file_operation, system_control, vision_analysis, ai_generation
Agents disponibles: web_agent, system_agent, vision_agent, control_agent, ai_agent
"""
        
        response = await self.ollama_service.generate_text(prompt)
        
        try:
            # Extraire le JSON de la réponse
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
            else:
                raise ValueError("Aucun JSON trouvé dans la réponse")
        except Exception as e:
            logger.error(f"Erreur parsing plan: {e}")
            # Plan de fallback
            return {
                "name": "Plan de fallback",
                "description": "Plan générique pour la demande",
                "priority": "medium",
                "estimated_duration": "30s",
                "tasks": [
                    {
                        "id": "task_1",
                        "type": "system_control",
                        "description": "Analyser la demande",
                        "parameters": {"action": "analyze", "input": user_input},
                        "dependencies": [],
                        "agent": "system_agent"
                    }
                ]
            }
    
    async def _generate_conversational_response(self, user_input: str, turn: ConversationTurn) -> str:
        """Génère une réponse conversationnelle naturelle"""
        context = self.context_handler.get_context()
        
        if turn.intent == "chat":
            # Conversation simple
            prompt = f"""
Tu es JARVIS, un assistant conversationnel amical et utile.

Historique récent:
{self._format_conversation_history(3)}

Utilisateur: {user_input}

Réponds de manière naturelle et conversationnelle, comme un ami qui aide.
"""
        else:
            # Réponse avec résultat d'exécution
            execution_summary = ""
            if turn.execution_result:
                if turn.execution_result.get("success"):
                    execution_summary = f"J'ai terminé la tâche : {turn.execution_result.get('summary', 'Tâche accomplie')}"
                else:
                    execution_summary = f"J'ai rencontré un problème : {turn.execution_result.get('error', 'Erreur inconnue')}"
            
            prompt = f"""
Tu es JARVIS, un assistant conversationnel.

Utilisateur: {user_input}

Résultat: {execution_summary}

Réponds de manière naturelle en confirmant ce qui a été fait ou en expliquant le problème.
"""
        
        response = await self.ollama_service.generate_text(prompt)
        return response.content
    
    def _format_conversation_history(self, max_turns: int = 3) -> str:
        """Formate l'historique de conversation"""
        recent_turns = self.conversation_history[-max_turns:] if self.conversation_history else []
        
        formatted = []
        for turn in recent_turns:
            formatted.append(f"Utilisateur: {turn.user_input}")
            if turn.response:
                formatted.append(f"JARVIS: {turn.response}")
        
        return "\n".join(formatted)
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """Retourne l'état actuel de la conversation"""
        return {
            "state": self.state.value,
            "current_turn": self.current_turn.id if self.current_turn else None,
            "history_length": len(self.conversation_history),
            "last_intent": self.current_turn.intent if self.current_turn else None
        }
    
    def clear_history(self):
        """Efface l'historique de conversation"""
        self.conversation_history.clear()
        self.current_turn = None
        logger.info("🗑️ Historique de conversation effacé") 