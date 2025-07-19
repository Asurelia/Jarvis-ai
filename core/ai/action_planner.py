"""
Planificateur d'actions pour JARVIS
Convertit les intentions utilisateur en séquences d'actions exécutables
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from loguru import logger

class ActionType(Enum):
    """Types d'actions possibles"""
    # Vision
    SCREENSHOT = "screenshot"
    ANALYZE_SCREEN = "analyze_screen"
    OCR_TEXT = "ocr_text"
    FIND_ELEMENT = "find_element"
    
    # Contrôle souris
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    SCROLL = "scroll"
    HOVER = "hover"
    
    # Contrôle clavier
    TYPE_TEXT = "type_text"
    PRESS_KEY = "press_key"
    HOTKEY = "hotkey"
    
    # Applications
    OPEN_APP = "open_app"
    SWITCH_APP = "switch_app"
    CLOSE_APP = "close_app"
    
    # Navigation
    NAVIGATE_URL = "navigate_url"
    BACK = "back"
    FORWARD = "forward"
    REFRESH = "refresh"
    
    # Système
    WAIT = "wait"
    VERIFY = "verify"
    LOOP = "loop"
    CONDITION = "condition"

@dataclass
class ActionParameter:
    """Paramètre d'une action"""
    name: str
    value: Any
    type: str  # "string", "int", "float", "bool", "list", "dict"
    required: bool = True
    description: str = ""

@dataclass
class Action:
    """Représente une action à exécuter"""
    type: ActionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    timeout: float = 30.0
    retry_count: int = 3
    continue_on_error: bool = False
    
    # Métadonnées d'exécution
    status: str = "pending"  # pending, running, completed, failed, skipped
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    start_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'action en dictionnaire"""
        return {
            "type": self.type.value,
            "parameters": self.parameters,
            "description": self.description,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "continue_on_error": self.continue_on_error,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time
        }

@dataclass
class ActionSequence:
    """Séquence d'actions à exécuter"""
    id: str
    name: str
    actions: List[Action]
    description: str = ""
    created_at: float = field(default_factory=time.time)
    
    # Métadonnées d'exécution
    status: str = "pending"
    current_action_index: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    
    @property
    def total_actions(self) -> int:
        return len(self.actions)
    
    @property
    def completion_rate(self) -> float:
        if not self.actions:
            return 0.0
        completed = sum(1 for action in self.actions if action.status == "completed")
        return completed / len(self.actions)
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

class ActionPlanner:
    """Planificateur intelligent d'actions"""
    
    def __init__(self, ollama_service=None):
        self.ollama_service = ollama_service
        self.action_templates = self._init_action_templates()
        self.execution_history: List[ActionSequence] = []
        
        logger.info("📋 Planificateur d'actions initialisé")
    
    def _init_action_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialise les templates d'actions communes"""
        return {
            # Navigation web
            "open_browser": {
                "actions": [
                    {"type": "open_app", "params": {"app_name": "chrome"}},
                    {"type": "wait", "params": {"duration": 2}},
                    {"type": "verify", "params": {"condition": "browser_opened"}}
                ]
            },
            
            "google_search": {
                "actions": [
                    {"type": "navigate_url", "params": {"url": "https://google.com"}},
                    {"type": "wait", "params": {"duration": 2}},
                    {"type": "find_element", "params": {"element_type": "search_box"}},
                    {"type": "click", "params": {"target": "search_box"}},
                    {"type": "type_text", "params": {"text": "{query}"}},
                    {"type": "press_key", "params": {"key": "enter"}}
                ]
            },
            
            # Gestion de fichiers
            "open_file_explorer": {
                "actions": [
                    {"type": "hotkey", "params": {"keys": "win+e"}},
                    {"type": "wait", "params": {"duration": 1}},
                    {"type": "verify", "params": {"condition": "explorer_opened"}}
                ]
            },
            
            "save_file": {
                "actions": [
                    {"type": "hotkey", "params": {"keys": "ctrl+s"}},
                    {"type": "wait", "params": {"duration": 1}},
                    {"type": "find_element", "params": {"element_type": "save_dialog"}},
                    {"type": "type_text", "params": {"text": "{filename}"}},
                    {"type": "press_key", "params": {"key": "enter"}}
                ]
            },
            
            # Applications
            "switch_to_app": {
                "actions": [
                    {"type": "switch_app", "params": {"app_name": "{app_name}"}},
                    {"type": "wait", "params": {"duration": 0.5}},
                    {"type": "verify", "params": {"condition": "app_active"}}
                ]
            }
        }
    
    async def parse_natural_command(self, command: str, context: Dict[str, Any] = None) -> ActionSequence:
        """Parse une commande en langage naturel vers une séquence d'actions"""
        if not self.ollama_service:
            return await self._fallback_parse(command)
        
        try:
            # Construire le prompt pour l'IA
            prompt = self._build_planning_prompt(command, context)
            
            # Demander à l'IA de planifier
            response = await self.ollama_service.plan_action(command, context)
            
            if response.success:
                # Parser la réponse de l'IA
                return await self._parse_ai_response(response.content, command)
            else:
                logger.warning(f"Erreur planification IA: {response.error}")
                return await self._fallback_parse(command)
                
        except Exception as e:
            logger.error(f"Erreur parsing commande: {e}")
            return await self._fallback_parse(command)
    
    def _build_planning_prompt(self, command: str, context: Dict[str, Any] = None) -> str:
        """Construit le prompt pour la planification"""
        context_str = ""
        if context:
            context_str = f"\nContexte: {json.dumps(context, indent=2)}"
        
        available_actions = ", ".join([action.value for action in ActionType])
        
        return f"""INSTRUCTION: Tu es un assistant de planification d'actions pour JARVIS. Tu dois TOUJOURS répondre uniquement avec un JSON valide.

Commande utilisateur: {command}{context_str}

Actions disponibles: {available_actions}

Templates disponibles: {", ".join(self.action_templates.keys())}

RÉPONDS UNIQUEMENT avec ce JSON (pas de texte avant ou après):
{{
  "sequence_name": "nom_descriptif_de_la_tache",
  "description": "description_de_ce_qui_sera_fait",
  "actions": [
    {{
      "type": "open_application",
      "parameters": {{"app_name": "nom_application"}},
      "description": "description_action"
    }}
  ]
}}

EXEMPLES:
- Pour "ouvre youtube": {{"sequence_name": "Ouvrir YouTube", "description": "Lance YouTube dans le navigateur", "actions": [{{"type": "open_application", "parameters": {{"app_name": "chrome"}}, "description": "Ouvrir Chrome"}}, {{"type": "web_navigation", "parameters": {{"url": "https://youtube.com"}}, "description": "Aller sur YouTube"}}]}}

RÉPONDS SEULEMENT LE JSON:"""
    
    async def _parse_ai_response(self, ai_response: str, original_command: str) -> ActionSequence:
        """Parse la réponse de l'IA en ActionSequence"""
        try:
            logger.debug(f"🔍 Réponse brute IA: {ai_response}")
            
            # Nettoyer la réponse
            clean_response = ai_response.strip()
            
            # Extraire le JSON de la réponse (plus robuste)
            json_patterns = [
                r'\{.*\}',  # JSON simple
                r'```json\s*(\{.*\})\s*```',  # JSON dans des blocs code
                r'```\s*(\{.*\})\s*```',  # JSON dans des blocs code sans "json"
            ]
            
            json_match = None
            for pattern in json_patterns:
                json_match = re.search(pattern, clean_response, re.DOTALL)
                if json_match:
                    break
            
            if not json_match:
                # Si pas de JSON trouvé, essayer de parser directement
                if clean_response.startswith('{') and clean_response.endswith('}'):
                    json_data = clean_response
                else:
                    raise ValueError("Aucun JSON trouvé dans la réponse")
            else:
                json_data = json_match.group(1) if json_match.lastindex else json_match.group()
            
            logger.debug(f"🔍 JSON extrait: {json_data}")
            parsed_data = json.loads(json_data)
            
            # Construire la séquence d'actions
            actions = []
            for action_data in parsed_data.get("actions", []):
                action_type = ActionType(action_data["type"])
                
                action = Action(
                    type=action_type,
                    parameters=action_data.get("parameters", {}),
                    description=action_data.get("description", ""),
                    timeout=action_data.get("timeout", 30.0),
                    retry_count=action_data.get("retry_count", 3),
                    continue_on_error=action_data.get("continue_on_error", False)
                )
                
                actions.append(action)
            
            sequence = ActionSequence(
                id=f"seq_{int(time.time())}",
                name=parsed_data.get("sequence_name", "Commande planifiée"),
                description=parsed_data.get("description", original_command),
                actions=actions
            )
            
            logger.success(f"✅ Séquence planifiée: {len(actions)} actions")
            return sequence
            
        except Exception as e:
            logger.error(f"Erreur parsing réponse IA: {e}")
            return await self._fallback_parse(original_command)
    
    async def _fallback_parse(self, command: str) -> ActionSequence:
        """Parsing de fallback basé sur des règles"""
        actions = []
        sequence_name = "Analyse de situation"
        
        command_lower = command.lower()
        
        logger.info(f"🔄 Utilisation du parsing de fallback pour: {command}")
        
        # Règles basiques de reconnaissance améliorées
        if any(word in command_lower for word in ["youtube", "ouvre youtube", "lance youtube"]):
            # Ouvrir YouTube
            actions.append(Action(
                type=ActionType.OPEN_APPLICATION,
                parameters={"app_name": "chrome"},
                description="Ouvrir Chrome"
            ))
            actions.append(Action(
                type=ActionType.WEB_NAVIGATION,
                parameters={"url": "https://youtube.com"},
                description="Naviguer vers YouTube"
            ))
            sequence_name = "Ouvrir YouTube"
            
        elif any(word in command_lower for word in ["google", "recherche"]):
            # Recherche Google
            query = self._extract_search_query(command)
            template = self.action_templates["google_search"]
            actions = self._instantiate_template(template, {"query": query})
            sequence_name = f"Recherche Google: {query}"
            
        elif "open" in command_lower and "browser" in command_lower:
            # Ouvrir navigateur
            template = self.action_templates["open_browser"]
            actions = self._instantiate_template(template)
            sequence_name = "Ouvrir navigateur"
            
        elif "screenshot" in command_lower or "capture" in command_lower:
            # Capture d'écran
            actions = [Action(
                type=ActionType.SCREENSHOT,
                description="Prendre une capture d'écran"
            )]
            sequence_name = "Capture d'écran"
            
        else:
            # Action par défaut: analyser la situation
            actions = [
                Action(
                    type=ActionType.SCREENSHOT,
                    description="Prendre une capture pour comprendre la situation"
                ),
                Action(
                    type=ActionType.ANALYZE_SCREEN,
                    parameters={"objective": command},
                    description="Analyser l'écran pour planifier les actions"
                )
            ]
            sequence_name = "Analyse de situation"
        
        return ActionSequence(
            id=f"fallback_{int(time.time())}",
            name=sequence_name,
            description=command,
            actions=actions
        )
    
    def _extract_search_query(self, command: str) -> str:
        """Extrait la requête de recherche d'une commande"""
        # Patterns de recherche
        patterns = [
            r"search for (.+)",
            r"google (.+)",
            r"find (.+)",
            r"look for (.+)",
            r"recherch[er]* (.+)",
            r"cherch[er]* (.+)"
        ]
        
        command_lower = command.lower()
        
        for pattern in patterns:
            match = re.search(pattern, command_lower)
            if match:
                return match.group(1).strip()
        
        # Si aucun pattern, prendre tout après les mots-clés
        keywords = ["google", "search", "find", "recherche", "cherche"]
        for keyword in keywords:
            if keyword in command_lower:
                parts = command_lower.split(keyword, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        return command
    
    def _instantiate_template(self, template: Dict[str, Any], variables: Dict[str, str] = None) -> List[Action]:
        """Instancie un template d'actions avec des variables"""
        variables = variables or {}
        actions = []
        
        for action_data in template["actions"]:
            # Remplacer les variables dans les paramètres
            params = action_data.get("params", {})
            for key, value in params.items():
                if isinstance(value, str):
                    for var_name, var_value in variables.items():
                        value = value.replace(f"{{{var_name}}}", var_value)
                    params[key] = value
            
            action = Action(
                type=ActionType(action_data["type"]),
                parameters=params,
                description=action_data.get("description", "")
            )
            
            actions.append(action)
        
        return actions
    
    def create_custom_sequence(self, name: str, actions: List[Dict[str, Any]], 
                             description: str = "") -> ActionSequence:
        """Crée une séquence d'actions personnalisée"""
        action_objects = []
        
        for action_data in actions:
            action = Action(
                type=ActionType(action_data["type"]),
                parameters=action_data.get("parameters", {}),
                description=action_data.get("description", ""),
                timeout=action_data.get("timeout", 30.0),
                retry_count=action_data.get("retry_count", 3),
                continue_on_error=action_data.get("continue_on_error", False)
            )
            action_objects.append(action)
        
        return ActionSequence(
            id=f"custom_{int(time.time())}",
            name=name,
            description=description,
            actions=action_objects
        )
    
    def optimize_sequence(self, sequence: ActionSequence) -> ActionSequence:
        """Optimise une séquence d'actions"""
        optimized_actions = []
        
        i = 0
        while i < len(sequence.actions):
            action = sequence.actions[i]
            
            # Optimisation: fusionner les actions de type similaires
            if action.type == ActionType.TYPE_TEXT and i + 1 < len(sequence.actions):
                next_action = sequence.actions[i + 1]
                if next_action.type == ActionType.TYPE_TEXT:
                    # Fusionner les deux actions de frappe
                    combined_text = action.parameters.get("text", "") + next_action.parameters.get("text", "")
                    action.parameters["text"] = combined_text
                    action.description = f"Taper: {combined_text[:50]}..."
                    i += 1  # Ignorer la prochaine action
            
            # Optimisation: supprimer les attentes trop courtes
            elif action.type == ActionType.WAIT:
                duration = action.parameters.get("duration", 0)
                if duration < 0.1:
                    i += 1  # Ignorer cette action
                    continue
            
            optimized_actions.append(action)
            i += 1
        
        # Créer une nouvelle séquence optimisée
        optimized_sequence = ActionSequence(
            id=f"{sequence.id}_opt",
            name=f"{sequence.name} (optimisé)",
            description=sequence.description,
            actions=optimized_actions
        )
        
        logger.info(f"🔧 Séquence optimisée: {len(sequence.actions)} -> {len(optimized_actions)} actions")
        return optimized_sequence
    
    def validate_sequence(self, sequence: ActionSequence) -> List[str]:
        """Valide une séquence d'actions et retourne les erreurs"""
        errors = []
        
        if not sequence.actions:
            errors.append("Séquence vide")
            return errors
        
        for i, action in enumerate(sequence.actions):
            # Vérifier les paramètres requis
            required_params = self._get_required_parameters(action.type)
            
            for param in required_params:
                if param not in action.parameters:
                    errors.append(f"Action {i+1}: Paramètre requis manquant: {param}")
            
            # Vérifications spécifiques par type d'action
            if action.type in [ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK]:
                if "x" not in action.parameters or "y" not in action.parameters:
                    if "target" not in action.parameters:
                        errors.append(f"Action {i+1}: Position (x,y) ou target requis pour le clic")
            
            elif action.type == ActionType.TYPE_TEXT:
                if not action.parameters.get("text"):
                    errors.append(f"Action {i+1}: Texte requis pour la frappe")
            
            elif action.type == ActionType.WAIT:
                duration = action.parameters.get("duration", 0)
                if duration <= 0:
                    errors.append(f"Action {i+1}: Durée d'attente doit être positive")
        
        return errors
    
    def _get_required_parameters(self, action_type: ActionType) -> List[str]:
        """Retourne les paramètres requis pour un type d'action"""
        requirements = {
            ActionType.CLICK: [],  # x,y ou target
            ActionType.TYPE_TEXT: ["text"],
            ActionType.HOTKEY: ["keys"],
            ActionType.OPEN_APP: ["app_name"],
            ActionType.NAVIGATE_URL: ["url"],
            ActionType.WAIT: ["duration"],
            ActionType.DRAG: ["start_x", "start_y", "end_x", "end_y"],
            ActionType.SCROLL: ["direction"]
        }
        
        return requirements.get(action_type, [])
    
    def get_execution_history(self, limit: int = 50) -> List[ActionSequence]:
        """Retourne l'historique d'exécution"""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """Efface l'historique d'exécution"""
        self.execution_history.clear()
        logger.info("🗑️  Historique de planification effacé")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du planificateur"""
        if not self.execution_history:
            return {"total_sequences": 0}
        
        total_sequences = len(self.execution_history)
        successful_sequences = sum(1 for seq in self.execution_history if seq.status == "completed")
        total_actions = sum(len(seq.actions) for seq in self.execution_history)
        avg_duration = sum(seq.duration for seq in self.execution_history) / total_sequences
        
        return {
            "total_sequences": total_sequences,
            "successful_sequences": successful_sequences,
            "success_rate": successful_sequences / total_sequences if total_sequences > 0 else 0,
            "total_actions": total_actions,
            "avg_actions_per_sequence": total_actions / total_sequences if total_sequences > 0 else 0,
            "avg_sequence_duration": avg_duration,
            "available_templates": len(self.action_templates)
        }

# Fonctions utilitaires
async def quick_plan(command: str, ollama_service=None) -> ActionSequence:
    """Planification rapide d'une commande"""
    planner = ActionPlanner(ollama_service)
    return await planner.parse_natural_command(command)

def create_simple_action(action_type: str, **params) -> Action:
    """Crée une action simple"""
    return Action(
        type=ActionType(action_type),
        parameters=params
    )

if __name__ == "__main__":
    async def test_planner():
        planner = ActionPlanner()
        
        # Test de parsing simple
        print("📋 Test de planification:")
        sequence = await planner.parse_natural_command("Take a screenshot and search for 'JARVIS AI' on Google")
        
        print(f"Séquence: {sequence.name}")
        print(f"Actions: {len(sequence.actions)}")
        
        for i, action in enumerate(sequence.actions):
            print(f"  {i+1}. {action.type.value}: {action.description}")
        
        # Test de validation
        print("\n🔍 Validation:")
        errors = planner.validate_sequence(sequence)
        if errors:
            print("Erreurs trouvées:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ Séquence valide")
    
    asyncio.run(test_planner())