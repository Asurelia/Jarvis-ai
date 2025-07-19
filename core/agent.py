"""
JARVIS - Agent IA Autonome Principal
Agent qui peut voir l'écran, contrôler souris/clavier, et utiliser n'importe quelle application
"""
import asyncio
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
from loguru import logger
import json

# Configuration du logger
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add("logs/jarvis_{time}.log", rotation="100 MB", level="DEBUG")

@dataclass
class JarvisConfig:
    """Configuration principale de Jarvis"""
    vision_enabled: bool = True
    voice_enabled: bool = True
    autocomplete_enabled: bool = True
    sandbox_mode: bool = True  # TOUJOURS True au début
    max_actions_per_minute: int = 60
    log_level: str = "INFO"
    
    # Chemins sécurisés
    safe_directories: List[str] = None
    blocked_directories: List[str] = None
    
    def __post_init__(self):
        if self.safe_directories is None:
            self.safe_directories = [
                str(Path.home() / "Documents"),
                str(Path.home() / "Desktop"),
                str(Path.home() / "Downloads")
            ]
        
        if self.blocked_directories is None:
            self.blocked_directories = [
                "C:\\Windows\\System32",
                "C:\\Program Files",
                "C:\\Program Files (x86)",
                str(Path.home() / "AppData")
            ]

class ModuleManager:
    """Gestionnaire des modules JARVIS"""
    
    def __init__(self):
        self.modules: Dict[str, Any] = {}
        self.initialized_modules: set = set()
    
    async def register_module(self, name: str, module_class, *args, **kwargs):
        """Enregistrer un nouveau module"""
        try:
            self.modules[name] = module_class(*args, **kwargs)
            logger.info(f"Module '{name}' enregistré")
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du module '{name}': {e}")
            raise
    
    async def initialize_module(self, name: str):
        """Initialiser un module spécifique"""
        if name not in self.modules:
            raise ValueError(f"Module '{name}' non enregistré")
        
        try:
            if hasattr(self.modules[name], 'initialize'):
                await self.modules[name].initialize()
            self.initialized_modules.add(name)
            logger.success(f"Module '{name}' initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du module '{name}': {e}")
            raise
    
    async def initialize_all(self):
        """Initialiser tous les modules"""
        for name in self.modules:
            if name not in self.initialized_modules:
                await self.initialize_module(name)
    
    def get_module(self, name: str):
        """Récupérer un module"""
        return self.modules.get(name)

class SecurityManager:
    """Gestionnaire de sécurité pour les actions JARVIS"""
    
    def __init__(self, config: JarvisConfig):
        self.config = config
        self.action_count = 0
        self.last_minute_reset = asyncio.get_event_loop().time()
    
    def is_path_safe(self, path: str) -> bool:
        """Vérifier si un chemin est sécurisé"""
        path = Path(path).resolve()
        
        # Vérifier les répertoires bloqués
        for blocked in self.config.blocked_directories:
            if str(path).startswith(blocked):
                logger.warning(f"Chemin bloqué détecté: {path}")
                return False
        
        # En mode sandbox, vérifier les répertoires sécurisés
        if self.config.sandbox_mode:
            for safe in self.config.safe_directories:
                if str(path).startswith(safe):
                    return True
            logger.warning(f"Chemin non autorisé en mode sandbox: {path}")
            return False
        
        return True
    
    def can_perform_action(self) -> bool:
        """Vérifier si une action peut être effectuée (rate limiting)"""
        current_time = asyncio.get_event_loop().time()
        
        # Reset du compteur toutes les minutes
        if current_time - self.last_minute_reset >= 60:
            self.action_count = 0
            self.last_minute_reset = current_time
        
        if self.action_count >= self.config.max_actions_per_minute:
            logger.warning(f"Limite d'actions atteinte: {self.action_count}/{self.config.max_actions_per_minute}")
            return False
        
        self.action_count += 1
        return True

class JarvisAgent:
    """Agent IA Autonome Principal"""
    
    def __init__(self, config: Optional[JarvisConfig] = None):
        self.config = config or JarvisConfig()
        self.module_manager = ModuleManager()
        self.security_manager = SecurityManager(self.config)
        self.running = False
        self.event_queue = asyncio.Queue()
        self.modules = {}  # Dictionnaire des modules JARVIS
        
        logger.info("🤖 JARVIS Agent initialisé")
        if self.config.sandbox_mode:
            logger.warning("🛡️  Mode SANDBOX activé - actions limitées")
    
    async def initialize(self):
        """Initialiser tous les modules JARVIS"""
        logger.info("🚀 Initialisation de JARVIS...")
        
        try:
            # Enregistrer et initialiser les modules
            logger.info("🔧 Enregistrement des modules JARVIS...")
            
            # Vision Module
            from core.vision.screen_capture import ScreenCapture
            from core.vision.ocr_engine import OCREngine
            from core.vision.visual_analysis import VisualAnalyzer
            
            vision_modules = {
                'screen_capture': ScreenCapture(),
                'ocr_engine': OCREngine(),
                'visual_analyzer': VisualAnalyzer()
            }
            
            for name, module in vision_modules.items():
                await module.initialize()
                self.modules[name] = module
            
            # Control Module  
            from core.control.mouse_controller import MouseController
            from core.control.keyboard_controller import KeyboardController
            from core.control.app_detector import AppDetector
            
            control_modules = {
                'mouse': MouseController(sandbox_mode=self.config.sandbox_mode),
                'keyboard': KeyboardController(sandbox_mode=self.config.sandbox_mode),
                'app_detector': AppDetector()
            }
            
            for name, module in control_modules.items():
                await module.initialize()
                self.modules[name] = module
            
            # AI Module
            from core.ai.ollama_service import OllamaService
            from core.ai.action_planner import ActionPlanner
            from core.ai.memory_system import MemorySystem
            
            ai_modules = {
                'ollama': OllamaService(),
                'memory': MemorySystem(),
            }
            
            for name, module in ai_modules.items():
                await module.initialize()
                self.modules[name] = module
            
            # Ajouter le planner avec ollama
            self.modules['planner'] = ActionPlanner(self.modules['ollama'])
            
            # Voice Module
            if self.config.voice_enabled:
                try:
                    from core.voice.voice_interface import VoiceInterface
                    voice_module = VoiceInterface()
                    if await voice_module.initialize():
                        self.modules['voice'] = voice_module
                        logger.success("✅ Module vocal initialisé")
                except Exception as e:
                    logger.warning(f"⚠️ Module vocal non disponible: {e}")
            
            # Autocomplete Module
            if self.config.autocomplete_enabled:
                try:
                    from ...autocomplete.global_autocomplete import GlobalAutocomplete
                    autocomplete_module = GlobalAutocomplete()
                    if await autocomplete_module.initialize():
                        self.modules['autocomplete'] = autocomplete_module
                        logger.success("✅ Module autocomplétion initialisé")
                except Exception as e:
                    logger.warning(f"⚠️ Module autocomplétion non disponible: {e}")
            
            # Initialiser tous les modules
            await self.module_manager.initialize_all()
            
            logger.success("✅ JARVIS initialisé avec succès!")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            raise
    
    async def process_command(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Traiter une commande utilisateur"""
        context = context or {}
        
        logger.info(f"📝 Commande reçue: {command}")
        
        if not self.security_manager.can_perform_action():
            return {
                "success": False,
                "error": "Rate limit dépassé",
                "retry_after": 60
            }
        
        try:
            # TODO: Implémenter le traitement des commandes
            # 1. Analyser la commande avec le module AI
            # 2. Planifier les actions nécessaires
            # 3. Exécuter les actions via les modules appropriés
            # 4. Retourner le résultat
            
            result = {
                "success": True,
                "command": command,
                "context": context,
                "actions_performed": [],
                "timestamp": asyncio.get_event_loop().time()
            }
            
            logger.success(f"✅ Commande traitée: {command}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la commande: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def take_screenshot(self) -> Optional[str]:
        """Prendre une capture d'écran"""
        vision_module = self.module_manager.get_module('vision')
        if vision_module:
            return await vision_module.take_screenshot()
        return None
    
    async def analyze_screen(self) -> Dict[str, Any]:
        """Analyser le contenu de l'écran"""
        vision_module = self.module_manager.get_module('vision')
        if vision_module:
            return await vision_module.analyze_screen()
        return {}
    
    async def main_loop(self):
        """Boucle principale d'événements"""
        logger.info("🔄 Démarrage de la boucle principale...")
        
        while self.running:
            try:
                # Traiter les événements en attente
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=0.1)
                    await self.handle_event(event)
                except asyncio.TimeoutError:
                    pass
                
                # TODO: Tâches périodiques
                # - Analyser l'écran si nécessaire
                # - Vérifier les notifications
                # - Nettoyer la mémoire
                
                await asyncio.sleep(0.1)  # Éviter la surcharge CPU
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle principale: {e}")
                await asyncio.sleep(1)  # Attendre avant de continuer
    
    async def handle_event(self, event: Dict[str, Any]):
        """Gérer un événement"""
        event_type = event.get('type')
        logger.debug(f"Événement reçu: {event_type}")
        
        # TODO: Implémenter la gestion des différents types d'événements
        # - voice_command
        # - screen_change
        # - user_input
        # - system_notification
    
    async def start(self):
        """Démarrer l'agent"""
        self.running = True
        logger.info("🚀 JARVIS démarre...")
        
        try:
            await self.main_loop()
        except KeyboardInterrupt:
            logger.info("⏹️  Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Arrêter l'agent"""
        self.running = False
        logger.info("⏹️  Arrêt de JARVIS...")
        
        # Arrêter tous les modules
        for name, module in self.module_manager.modules.items():
            try:
                if hasattr(module, 'stop'):
                    await module.stop()
                logger.info(f"Module '{name}' arrêté")
            except Exception as e:
                logger.error(f"Erreur lors de l'arrêt du module '{name}': {e}")
        
        logger.success("✅ JARVIS arrêté")

# Fonctions utilitaires
async def create_agent(config_file: Optional[str] = None) -> JarvisAgent:
    """Créer et configurer un agent JARVIS"""
    config = JarvisConfig()
    
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config = JarvisConfig(**config_data)
            logger.info(f"Configuration chargée depuis {config_file}")
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de la config: {e}")
    
    agent = JarvisAgent(config)
    await agent.initialize()
    return agent

if __name__ == "__main__":
    async def main():
        agent = await create_agent()
        await agent.start()
    
    # Démarrer JARVIS
    asyncio.run(main())