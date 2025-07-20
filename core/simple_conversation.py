"""
Module de conversation simple et naturel pour JARVIS
Pas de sur-ingénierie, juste de la conversation directe
"""

import asyncio
import json
import re
from typing import Dict, Any, Optional
from loguru import logger

from core.ai.ollama_service import OllamaService, GenerationRequest, ModelType
from core.ai.action_planner import ActionPlanner


class SimpleConversation:
    """Gestionnaire de conversation minimaliste et efficace"""
    
    def __init__(self, ollama_service: OllamaService, action_planner: ActionPlanner):
        self.ollama = ollama_service
        self.planner = action_planner
        self.context = []  # Historique simple
        
    async def chat(self, user_input: str) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        Traite une entrée utilisateur de manière naturelle
        Retourne: (réponse_conversationnelle, action_à_exécuter)
        """
        logger.info(f"💬 Utilisateur: {user_input}")
        
        # 1. Comprendre l'intention dans le contexte conversationnel
        intention = await self._extract_intention(user_input)
        
        # 2. Générer une réponse naturelle ET identifier les actions
        response, action = await self._process_conversation(user_input, intention)
        
        # 3. Ajouter au contexte
        self.context.append({"user": user_input, "jarvis": response})
        if len(self.context) > 10:  # Garder seulement les 10 derniers échanges
            self.context.pop(0)
            
        return response, action
    
    async def _extract_intention(self, user_input: str) -> Dict[str, Any]:
        """Extrait l'intention de manière simple et directe"""
        prompt = f"""Analyse cette phrase et identifie ce que l'utilisateur veut:

Phrase: "{user_input}"

Réponds en JSON avec ces champs:
- type: "action" (si demande de faire quelque chose) ou "chat" (si simple conversation)
- action_type: si type="action", quel type (ouvrir_app, rechercher, capturer_ecran, etc.)
- details: détails pertinents extraits

Exemples:
"J'aimerais voir YouTube" -> {{"type": "action", "action_type": "ouvrir_site", "details": {{"site": "youtube"}}}}
"Comment vas-tu?" -> {{"type": "chat", "action_type": null, "details": {{}}}}
"Peux-tu prendre une capture d'écran?" -> {{"type": "action", "action_type": "capturer_ecran", "details": {{}}}}

JSON seulement:"""

        try:
            request = GenerationRequest(
                model_type=ModelType.GENERAL,
                prompt=prompt
            )
            response = await self.ollama.generate(request)
            
            # Extraire le JSON de la réponse
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"type": "chat", "action_type": None, "details": {}}
        except:
            return {"type": "chat", "action_type": None, "details": {}}
    
    async def _process_conversation(self, user_input: str, intention: Dict[str, Any]) -> tuple[str, Optional[Dict[str, Any]]]:
        """Traite la conversation et génère réponse + action"""
        
        # Contexte conversationnel
        context_str = self._format_context()
        
        if intention["type"] == "chat":
            # Simple conversation
            prompt = f"""Tu es JARVIS, un assistant IA amical et serviable.

Historique récent:
{context_str}

Utilisateur: {user_input}

Réponds de manière naturelle et conversationnelle:"""

            request = GenerationRequest(
                model_type=ModelType.GENERAL,
                prompt=prompt
            )
            response = await self.ollama.generate(request)
            return response.content, None
            
        else:
            # Conversation avec action
            action_desc = self._get_action_description(intention)
            
            # Générer la réponse conversationnelle
            prompt = f"""Tu es JARVIS, un assistant IA qui va aider l'utilisateur.

L'utilisateur a dit: "{user_input}"
Tu vas: {action_desc}

Réponds de manière naturelle en confirmant ce que tu vas faire, de façon concise et amicale:"""

            request = GenerationRequest(
                model_type=ModelType.GENERAL,
                prompt=prompt
            )
            response = await self.ollama.generate(request)
            
            # Préparer l'action pour le planner
            action_command = self._build_action_command(intention)
            
            return response.content, {"command": action_command, "original": user_input}
    
    def _format_context(self) -> str:
        """Formate le contexte de conversation"""
        if not self.context:
            return "Début de conversation"
            
        formatted = []
        for exchange in self.context[-3:]:  # Derniers 3 échanges
            formatted.append(f"User: {exchange['user']}")
            formatted.append(f"JARVIS: {exchange['jarvis']}")
        
        return "\n".join(formatted)
    
    def _get_action_description(self, intention: Dict[str, Any]) -> str:
        """Décrit l'action de manière naturelle"""
        action_type = intention.get("action_type", "")
        details = intention.get("details", {})
        
        descriptions = {
            "ouvrir_app": f"ouvrir {details.get('app', 'l\'application')}",
            "ouvrir_site": f"ouvrir {details.get('site', 'le site web')}",
            "rechercher": f"rechercher {details.get('query', 'sur internet')}",
            "capturer_ecran": "prendre une capture d'écran",
            "analyser_ecran": "analyser ce qui est à l'écran",
            "taper_texte": f"taper le texte: {details.get('text', '')}",
            "cliquer": "effectuer un clic",
        }
        
        return descriptions.get(action_type, "effectuer l'action demandée")
    
    def _build_action_command(self, intention: Dict[str, Any]) -> str:
        """Construit la commande d'action pour le planner"""
        action_type = intention.get("action_type", "")
        details = intention.get("details", {})
        
        # Mapper vers des commandes que le planner comprend
        command_map = {
            "ouvrir_app": f"open {details.get('app', 'application')}",
            "ouvrir_site": f"open {details.get('site', 'website')}",
            "rechercher": f"search {details.get('query', '')}",
            "capturer_ecran": "take screenshot",
            "analyser_ecran": "analyze screen",
            "taper_texte": f"type {details.get('text', '')}",
            "cliquer": f"click {details.get('target', '')}",
        }
        
        return command_map.get(action_type, "analyze situation")