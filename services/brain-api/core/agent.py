"""
🤖 Module Agent React - JARVIS Brain API
Orchestration autonome d'outils avec framework ReAct
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class AgentStep:
    step_number: int
    state: AgentState
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict] = None
    observation: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class AgentExecution:
    task: str
    steps: List[AgentStep]
    final_answer: Optional[str] = None
    status: AgentState = AgentState.IDLE
    start_time: float = None
    end_time: float = None
    total_duration: float = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = time.time()

class ReactAgent:
    """
    Agent ReAct (Reasoning and Action) pour orchestration autonome d'outils
    Implémente le pattern Think → Act → Observe
    """
    
    def __init__(self, llm_url: str, memory_manager=None, metacognition=None):
        self.llm_url = llm_url
        self.memory_manager = memory_manager
        self.metacognition = metacognition
        
        # Configuration
        self.max_iterations = 5
        self.timeout_seconds = 30
        self.debug = True
        
        # État de l'agent
        self.current_execution: Optional[AgentExecution] = None
        self.is_active = False
        
        # Outils disponibles
        self.tools = {}
        self.tool_descriptions = {}
        
        # Statistiques
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "tools_used": {},
            "avg_duration": 0.0,
            "avg_steps": 0.0
        }
        
        logger.info("🤖 React Agent initialisé")
    
    async def initialize(self):
        """Initialisation asynchrone de l'agent"""
        logger.info("🚀 Initialisation React Agent...")
        
        # Charger les outils disponibles
        await self._load_tools()
        
        # Tester connexion LLM
        await self._test_llm_connection()
        
        logger.info(f"✅ React Agent prêt avec {len(self.tools)} outils")
    
    async def shutdown(self):
        """Arrêt propre de l'agent"""
        logger.info("🛑 Arrêt React Agent...")
        
        if self.current_execution and self.current_execution.status not in [AgentState.COMPLETED, AgentState.ERROR]:
            logger.warning("Arrêt forcé pendant une exécution")
            if self.current_execution:
                self.current_execution.status = AgentState.ERROR
        
        self._log_final_stats()
    
    async def execute_task(self, task: str, context: Optional[Dict] = None) -> AgentExecution:
        """
        Exécuter une tâche avec le framework ReAct
        
        Args:
            task: Description de la tâche à accomplir
            context: Contexte additionnel (utilisateur, historique, etc.)
        
        Returns:
            AgentExecution: Résultat de l'exécution avec toutes les étapes
        """
        if self.is_active:
            raise RuntimeError("Agent déjà en cours d'exécution")
        
        self.is_active = True
        self.stats["total_executions"] += 1
        
        # Initialiser l'exécution
        execution = AgentExecution(task=task, steps=[])
        self.current_execution = execution
        
        try:
            logger.info(f"🎯 Démarrage tâche: {task}")
            execution.status = AgentState.THINKING
            
            # Boucle ReAct principale
            for iteration in range(self.max_iterations):
                # Vérifier timeout
                if time.time() - execution.start_time > self.timeout_seconds:
                    raise TimeoutError(f"Timeout après {self.timeout_seconds}s")
                
                # Étape THINK (Réflexion)
                thought = await self._think_step(task, execution.steps, context)
                step = AgentStep(
                    step_number=iteration + 1,
                    state=AgentState.THINKING,
                    thought=thought
                )
                execution.steps.append(step)
                
                # Vérifier si on a la réponse finale
                if self._is_final_answer(thought):
                    execution.final_answer = self._extract_final_answer(thought)
                    execution.status = AgentState.COMPLETED
                    break
                
                # Étape ACT (Action)
                action, action_input = await self._act_step(thought)
                if action:
                    step.state = AgentState.ACTING
                    step.action = action
                    step.action_input = action_input
                    
                    # Étape OBSERVE (Observation)
                    observation = await self._observe_step(action, action_input)
                    step.state = AgentState.OBSERVING
                    step.observation = observation
                    
                    logger.info(f"🔄 Étape {iteration + 1}: {action} → {observation[:100]}...")
                else:
                    # Pas d'action nécessaire, on continue la réflexion
                    continue
            
            # Finaliser l'exécution
            if execution.status != AgentState.COMPLETED:
                # Générer une réponse finale si pas encore fait
                execution.final_answer = await self._generate_final_answer(execution)
                execution.status = AgentState.COMPLETED
            
            execution.end_time = time.time()
            execution.total_duration = execution.end_time - execution.start_time
            
            self.stats["successful_executions"] += 1
            self._update_stats(execution)
            
            logger.info(f"✅ Tâche complétée en {execution.total_duration:.2f}s avec {len(execution.steps)} étapes")
            
        except Exception as e:
            execution.status = AgentState.ERROR
            execution.end_time = time.time()
            execution.total_duration = execution.end_time - execution.start_time
            
            self.stats["failed_executions"] += 1
            logger.error(f"❌ Échec tâche: {e}")
            
            # Ajouter l'erreur comme dernière observation
            if execution.steps:
                execution.steps[-1].observation = f"Erreur: {str(e)}"
        
        finally:
            self.is_active = False
            self.current_execution = None
        
        return execution
    
    async def _think_step(self, task: str, previous_steps: List[AgentStep], context: Optional[Dict]) -> str:
        """Étape de réflexion - analyser la situation et planifier"""
        
        # Construire le prompt de réflexion
        prompt = self._build_thinking_prompt(task, previous_steps, context)
        
        # Utiliser la métacognition pour filtrer si nécessaire
        if self.metacognition:
            should_use_llm, reason = self.metacognition.should_activate_llm(prompt, context)
            if not should_use_llm:
                return f"Réflexion simplifiée: {reason}"
        
        # Appeler le LLM pour la réflexion
        thought = await self._call_llm(prompt)
        
        return thought
    
    async def _act_step(self, thought: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Étape d'action - décider quelle action prendre"""
        
        # Analyser la pensée pour extraire l'action
        action_match = self._parse_action_from_thought(thought)
        
        if not action_match:
            return None, None
        
        action_name = action_match.get("action")
        action_input = action_match.get("input", {})
        
        # Vérifier que l'outil existe
        if action_name not in self.tools:
            logger.warning(f"⚠️ Outil inconnu: {action_name}")
            return None, None
        
        return action_name, action_input
    
    async def _observe_step(self, action: str, action_input: Dict) -> str:
        """Étape d'observation - exécuter l'action et observer le résultat"""
        
        try:
            # Exécuter l'outil
            tool_function = self.tools[action]
            result = await tool_function(action_input)
            
            # Mettre à jour les statistiques d'utilisation des outils
            self.stats["tools_used"][action] = self.stats["tools_used"].get(action, 0) + 1
            
            return str(result)
            
        except Exception as e:
            error_msg = f"Erreur lors de l'exécution de {action}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _build_thinking_prompt(self, task: str, previous_steps: List[AgentStep], context: Optional[Dict]) -> str:
        """Construire le prompt pour l'étape de réflexion"""
        
        prompt = f"""Tu es JARVIS, un assistant IA autonome. Tu dois accomplir la tâche suivante:

TÂCHE: {task}

OUTILS DISPONIBLES:
{self._format_tools_description()}

INSTRUCTIONS:
1. Réfléchis étape par étape à comment accomplir cette tâche
2. Si tu as besoin d'utiliser un outil, indique: Action: [nom_outil] avec Input: [paramètres]
3. Si tu as assez d'informations pour répondre, indique: Réponse finale: [ta_réponse]

"""
        
        # Ajouter l'historique des étapes précédentes
        if previous_steps:
            prompt += "ÉTAPES PRÉCÉDENTES:\n"
            for step in previous_steps:
                prompt += f"Étape {step.step_number}: {step.thought}\n"
                if step.action:
                    prompt += f"Action: {step.action} → {step.observation}\n"
            prompt += "\n"
        
        # Ajouter le contexte si disponible
        if context:
            user_context = context.get("user_profile", "")
            if user_context:
                prompt += f"CONTEXTE UTILISATEUR: {user_context}\n\n"
        
        prompt += "RÉFLEXION ACTUELLE:"
        
        return prompt
    
    def _format_tools_description(self) -> str:
        """Formater la description des outils disponibles"""
        descriptions = []
        for tool_name, description in self.tool_descriptions.items():
            descriptions.append(f"- {tool_name}: {description}")
        return "\n".join(descriptions)
    
    def _parse_action_from_thought(self, thought: str) -> Optional[Dict]:
        """Parser l'action depuis la pensée de l'agent"""
        import re
        
        # Chercher pattern "Action: [nom] avec Input: [params]"
        action_pattern = r"Action:\s*(\w+).*?Input:\s*(.+?)(?:\n|$)"
        match = re.search(action_pattern, thought, re.IGNORECASE | re.DOTALL)
        
        if match:
            action_name = match.group(1).strip()
            input_str = match.group(2).strip()
            
            # Essayer de parser l'input comme JSON
            try:
                action_input = json.loads(input_str)
            except:
                # Si pas JSON, traiter comme string simple
                action_input = {"query": input_str}
            
            return {
                "action": action_name,
                "input": action_input
            }
        
        return None
    
    def _is_final_answer(self, thought: str) -> bool:
        """Vérifier si la pensée contient une réponse finale"""
        final_indicators = [
            "réponse finale:",
            "final answer:",
            "conclusion:",
            "résultat:"
        ]
        
        thought_lower = thought.lower()
        return any(indicator in thought_lower for indicator in final_indicators)
    
    def _extract_final_answer(self, thought: str) -> str:
        """Extraire la réponse finale de la pensée"""
        import re
        
        patterns = [
            r"réponse finale:\s*(.+?)(?:\n|$)",
            r"final answer:\s*(.+?)(?:\n|$)",
            r"conclusion:\s*(.+?)(?:\n|$)",
            r"résultat:\s*(.+?)(?:\n|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, thought, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Si pas de pattern, prendre la dernière phrase
        sentences = thought.split('.')
        return sentences[-1].strip() if sentences else thought
    
    async def _generate_final_answer(self, execution: AgentExecution) -> str:
        """Générer une réponse finale basée sur l'exécution"""
        
        # Résumer les observations
        observations = []
        for step in execution.steps:
            if step.observation:
                observations.append(step.observation)
        
        if observations:
            summary = " ".join(observations[-3:])  # Dernières 3 observations
            return f"Basé sur mes recherches: {summary}"
        else:
            return "Je n'ai pas pu rassembler suffisamment d'informations pour répondre complètement à votre demande."
    
    async def _call_llm(self, prompt: str) -> str:
        """Appeler le LLM local (Ollama)"""
        
        # Appel LLM via Ollama
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 512
                    }
                }
                
                async with session.post(f"{self.llm_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "Pas de réponse du LLM")
                    else:
                        logger.warning(f"LLM request failed: {response.status}")
                        return self._fallback_response(prompt)
        except Exception as e:
            logger.warning(f"LLM connection failed: {e}")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Réponse de secours si LLM indisponible"""
        
        # Réponse de secours basée sur le prompt
        if "outils disponibles" in prompt.lower():
            return "Je vais analyser les outils disponibles pour accomplir cette tâche. Laisse-moi réfléchir à la meilleure approche."
        elif "étapes précédentes" in prompt.lower():
            return "En me basant sur les étapes précédentes, je pense que je peux maintenant fournir une réponse finale."
        else:
            return "Je réfléchis à la meilleure façon d'aborder cette tâche."
    
    async def _test_llm_connection(self):
        """Tester la connexion au LLM"""
        try:
            test_response = await self._call_llm("Test de connexion")
            if test_response:
                logger.info("✅ Connexion LLM testée")
            else:
                logger.warning("⚠️ Réponse LLM vide")
        except Exception as e:
            logger.warning(f"⚠️ Connexion LLM échouée: {e}")
    
    async def _load_tools(self):
        """Charger les outils disponibles"""
        
        # Outils de base pour démarrage
        self.tools = {
            "search_web": self._tool_search_web,
            "get_time": self._tool_get_time,
            "calculate": self._tool_calculate,
            "get_weather": self._tool_get_weather,
            "read_file": self._tool_read_file,
            "system_info": self._tool_system_info
        }
        
        self.tool_descriptions = {
            "search_web": "Recherche d'informations sur internet",
            "get_time": "Obtenir l'heure et la date actuelles",
            "calculate": "Effectuer des calculs mathématiques",
            "get_weather": "Obtenir les informations météo",
            "read_file": "Lire le contenu d'un fichier",
            "system_info": "Obtenir des informations système"
        }
        
        logger.info(f"🔧 {len(self.tools)} outils chargés")
    
    # === OUTILS IMPLÉMENTÉS ===
    
    async def _tool_search_web(self, params: Dict) -> str:
        """Outil de recherche web (simulation)"""
        query = params.get("query", "")
        await asyncio.sleep(0.2)  # Simule latence réseau
        return f"Résultats de recherche pour '{query}': Information trouvée (simulation)"
    
    async def _tool_get_time(self, params: Dict) -> str:
        """Outil pour obtenir l'heure"""
        import datetime
        now = datetime.datetime.now()
        return f"Il est actuellement {now.strftime('%H:%M:%S')} le {now.strftime('%d/%m/%Y')}"
    
    async def _tool_calculate(self, params: Dict) -> str:
        """Outil de calcul"""
        expression = params.get("expression", "")
        try:
            # Sécurisé: seulement opérations de base
            allowed_chars = set("0123456789+-*/().,")
            if all(c in allowed_chars for c in expression.replace(" ", "")):
                result = eval(expression)
                return f"Le résultat de {expression} est {result}"
            else:
                return "Expression non autorisée"
        except:
            return "Erreur dans le calcul"
    
    async def _tool_get_weather(self, params: Dict) -> str:
        """Outil météo (simulation)"""
        location = params.get("location", "Paris")
        await asyncio.sleep(0.1)
        return f"Météo à {location}: 22°C, ensoleillé (simulation)"
    
    async def _tool_read_file(self, params: Dict) -> str:
        """Outil lecture de fichier (sécurisé)"""
        file_path = params.get("path", "")
        
        # Vérifications de sécurité
        import os
        from pathlib import Path
        
        try:
            path = Path(file_path).resolve()
            
            # Vérifier que le fichier existe et est lisible
            if not path.exists():
                return f"Fichier non trouvé: {file_path}"
            
            if not path.is_file():
                return f"Le chemin n'est pas un fichier: {file_path}"
            
            # Vérifier les extensions autorisées
            allowed_extensions = {'.txt', '.md', '.json', '.yaml', '.yml', '.log'}
            if path.suffix.lower() not in allowed_extensions:
                return f"Type de fichier non autorisé: {path.suffix}"
            
            # Lire le fichier avec limitation de taille
            max_size = 10 * 1024  # 10KB max
            if path.stat().st_size > max_size:
                return f"Fichier trop volumineux (>{max_size} bytes)"
            
            content = path.read_text(encoding='utf-8', errors='ignore')
            return f"Contenu de {path.name}:\n{content[:1000]}{'...' if len(content) > 1000 else ''}"
            
        except Exception as e:
            return f"Erreur lors de la lecture: {str(e)}"
    
    async def _tool_system_info(self, params: Dict) -> str:
        """Outil informations système"""
        import platform
        import psutil
        
        info = {
            "os": platform.system(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }
        
        return f"Système: {info['os']}, CPU: {info['cpu_percent']}%, RAM: {info['memory_percent']}%"
    
    def _update_stats(self, execution: AgentExecution):
        """Mettre à jour les statistiques"""
        if execution.total_duration:
            # Moyenne mobile pour la durée
            if self.stats["avg_duration"] == 0:
                self.stats["avg_duration"] = execution.total_duration
            else:
                self.stats["avg_duration"] = (self.stats["avg_duration"] + execution.total_duration) / 2
        
        # Moyenne mobile pour les étapes
        steps_count = len(execution.steps)
        if self.stats["avg_steps"] == 0:
            self.stats["avg_steps"] = steps_count
        else:
            self.stats["avg_steps"] = (self.stats["avg_steps"] + steps_count) / 2
    
    def get_stats(self) -> Dict:
        """Obtenir les statistiques de l'agent"""
        success_rate = (self.stats["successful_executions"] / self.stats["total_executions"]) * 100 if self.stats["total_executions"] > 0 else 0
        
        return {
            **self.stats,
            "success_rate": round(success_rate, 2),
            "is_active": self.is_active,
            "tools_count": len(self.tools)
        }
    
    def _log_final_stats(self):
        """Logger les statistiques finales"""
        stats = self.get_stats()
        logger.info(f"📊 Agent Stats - Succès: {stats['success_rate']}%, "
                   f"Durée moy: {stats['avg_duration']:.2f}s, "
                   f"Étapes moy: {stats['avg_steps']:.1f}")