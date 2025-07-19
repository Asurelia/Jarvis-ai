"""
Exécuteur d'actions automatique pour JARVIS
Prend les séquences d'actions planifiées et les exécute de manière sécurisée
"""
import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from loguru import logger

# Import des modules JARVIS
from .action_planner import ActionSequence, Action, ActionType
from ..vision.screen_capture import ScreenCapture
from ..vision.ocr_engine import OCREngine
from ..vision.visual_analysis import VisualAnalyzer
from ..control.mouse_controller import MouseController
from ..control.keyboard_controller import KeyboardController
from ..control.app_detector import AppDetector

class ExecutionResult(Enum):
    """Résultats d'exécution possibles"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    WAITING_USER = "waiting_user"

@dataclass
class ExecutionContext:
    """Contexte d'exécution d'une action"""
    current_screenshot: Optional[Any] = None
    screen_analysis: Optional[Dict[str, Any]] = None
    detected_elements: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class ExecutionConfig:
    """Configuration de l'exécuteur"""
    sandbox_mode: bool = True
    require_confirmation: bool = True
    max_execution_time: float = 300.0  # 5 minutes max
    screenshot_verification: bool = True
    auto_retry: bool = True
    pause_between_actions: float = 0.5
    
    # Seuils de confiance pour l'exécution automatique
    auto_click_confidence: float = 0.8
    auto_type_confidence: float = 0.9
    auto_app_confidence: float = 0.7

class ActionExecutor:
    """Exécuteur d'actions principal"""
    
    def __init__(self, config: ExecutionConfig = None):
        self.config = config or ExecutionConfig()
        
        # Modules JARVIS
        self.screen_capture = None
        self.ocr_engine = None
        self.visual_analyzer = None
        self.mouse_controller = None
        self.keyboard_controller = None
        self.app_detector = None
        
        # État de l'exécution
        self.is_executing = False
        self.current_sequence = None
        self.current_action_index = 0
        self.execution_context = ExecutionContext()
        
        # Callbacks
        self.confirmation_callback: Optional[Callable] = None
        self.progress_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        
        # Historique d'exécution
        self.execution_history: List[Dict[str, Any]] = []
        
        # Statistiques
        self.stats = {
            "sequences_executed": 0,
            "actions_executed": 0,
            "actions_successful": 0,
            "actions_failed": 0,
            "total_execution_time": 0.0
        }
        
        logger.info("⚡ Exécuteur d'actions initialisé")
    
    async def initialize(self, modules: Dict[str, Any]):
        """Initialise l'exécuteur avec les modules JARVIS"""
        try:
            logger.info("🚀 Initialisation de l'exécuteur d'actions...")
            
            # Récupérer les modules
            self.screen_capture = modules.get('screen_capture')
            self.ocr_engine = modules.get('ocr')
            self.visual_analyzer = modules.get('vision_analyzer')
            self.mouse_controller = modules.get('mouse')
            self.keyboard_controller = modules.get('keyboard')
            self.app_detector = modules.get('app_detector')
            
            # Vérifier les modules critiques
            required_modules = ['screen_capture', 'mouse', 'keyboard']
            missing_modules = []
            
            for module_name in required_modules:
                if not modules.get(module_name):
                    missing_modules.append(module_name)
            
            if missing_modules:
                raise RuntimeError(f"Modules requis manquants: {missing_modules}")
            
            logger.success("✅ Exécuteur d'actions prêt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation exécuteur: {e}")
            return False
    
    async def execute_sequence(self, sequence: ActionSequence) -> Dict[str, Any]:
        """Exécute une séquence d'actions complète"""
        if self.is_executing:
            return {
                "success": False,
                "error": "Exécution déjà en cours",
                "sequence_id": sequence.id
            }
        
        start_time = time.time()
        self.is_executing = True
        self.current_sequence = sequence
        self.current_action_index = 0
        self.execution_context = ExecutionContext()
        
        sequence.status = "running"
        sequence.start_time = start_time
        
        logger.info(f"🚀 Début d'exécution: {sequence.name} ({len(sequence.actions)} actions)")
        
        try:
            # Demander confirmation si nécessaire
            if self.config.require_confirmation:
                confirmed = await self._request_confirmation(sequence)
                if not confirmed:
                    sequence.status = "cancelled"
                    return {
                        "success": False,
                        "error": "Exécution annulée par l'utilisateur",
                        "sequence_id": sequence.id
                    }
            
            # Exécuter chaque action
            for i, action in enumerate(sequence.actions):
                self.current_action_index = i
                
                # Notifier le progrès
                if self.progress_callback:
                    await self.progress_callback(i, len(sequence.actions), action)
                
                # Exécuter l'action
                result = await self._execute_action(action)
                
                # Pause entre les actions
                if i < len(sequence.actions) - 1:
                    await asyncio.sleep(self.config.pause_between_actions)
                
                # Gérer l'échec
                if result == ExecutionResult.FAILED:
                    if not action.continue_on_error:
                        sequence.status = "failed"
                        sequence.failure_count += 1
                        break
                elif result == ExecutionResult.SUCCESS:
                    sequence.success_count += 1
                elif result == ExecutionResult.CANCELLED:
                    sequence.status = "cancelled"
                    break
            
            # Finaliser l'exécution
            execution_time = time.time() - start_time
            sequence.end_time = time.time()
            
            if sequence.status == "running":
                sequence.status = "completed"
            
            # Créer le résultat
            result = {
                "success": sequence.status == "completed",
                "sequence_id": sequence.id,
                "actions_executed": self.current_action_index + 1,
                "actions_successful": sequence.success_count,
                "actions_failed": sequence.failure_count,
                "execution_time": execution_time,
                "status": sequence.status
            }
            
            # Mettre à jour les statistiques
            self.stats["sequences_executed"] += 1
            self.stats["total_execution_time"] += execution_time
            
            # Ajouter à l'historique
            self.execution_history.append(result)
            
            logger.info(f"✅ Exécution terminée: {sequence.name} ({result['success']})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'exécution: {e}")
            sequence.status = "failed"
            
            if self.error_callback:
                await self.error_callback(e, sequence, self.current_action_index)
            
            return {
                "success": False,
                "error": str(e),
                "sequence_id": sequence.id,
                "execution_time": time.time() - start_time
            }
        
        finally:
            self.is_executing = False
            self.current_sequence = None
            self.current_action_index = 0
    
    async def _execute_action(self, action: Action) -> ExecutionResult:
        """Exécute une action individuelle"""
        action.status = "running"
        action.start_time = time.time()
        
        logger.debug(f"🔄 Exécution: {action.type.value} - {action.description}")
        
        try:
            # Prendre une capture d'écran avant l'action si nécessaire
            if self.config.screenshot_verification and action.type not in [ActionType.WAIT]:
                await self._update_screen_context()
            
            # Exécuter selon le type d'action
            if action.type == ActionType.SCREENSHOT:
                result = await self._execute_screenshot(action)
            elif action.type == ActionType.ANALYZE_SCREEN:
                result = await self._execute_analyze_screen(action)
            elif action.type == ActionType.OCR_TEXT:
                result = await self._execute_ocr_text(action)
            elif action.type == ActionType.FIND_ELEMENT:
                result = await self._execute_find_element(action)
            elif action.type == ActionType.CLICK:
                result = await self._execute_click(action)
            elif action.type == ActionType.DOUBLE_CLICK:
                result = await self._execute_double_click(action)
            elif action.type == ActionType.RIGHT_CLICK:
                result = await self._execute_right_click(action)
            elif action.type == ActionType.TYPE_TEXT:
                result = await self._execute_type_text(action)
            elif action.type == ActionType.PRESS_KEY:
                result = await self._execute_press_key(action)
            elif action.type == ActionType.HOTKEY:
                result = await self._execute_hotkey(action)
            elif action.type == ActionType.WAIT:
                result = await self._execute_wait(action)
            elif action.type == ActionType.OPEN_APP:
                result = await self._execute_open_app(action)
            elif action.type == ActionType.SWITCH_APP:
                result = await self._execute_switch_app(action)
            else:
                logger.warning(f"⚠️ Type d'action non supporté: {action.type.value}")
                result = ExecutionResult.SKIPPED
            
            # Finaliser l'action
            action.execution_time = time.time() - action.start_time
            
            if result == ExecutionResult.SUCCESS:
                action.status = "completed"
                self.stats["actions_successful"] += 1
            elif result == ExecutionResult.FAILED:
                action.status = "failed"
                self.stats["actions_failed"] += 1
            else:
                action.status = result.value
            
            self.stats["actions_executed"] += 1
            
            return result
            
        except Exception as e:
            action.execution_time = time.time() - action.start_time
            action.status = "failed"
            action.error = str(e)
            
            logger.error(f"❌ Erreur exécution action {action.type.value}: {e}")
            
            # Retry si configuré
            if (self.config.auto_retry and 
                self.execution_context.retry_count < self.execution_context.max_retries):
                
                self.execution_context.retry_count += 1
                logger.info(f"🔄 Retry {self.execution_context.retry_count}/{self.execution_context.max_retries}")
                
                await asyncio.sleep(1.0)  # Pause avant retry
                return await self._execute_action(action)
            
            self.stats["actions_failed"] += 1
            return ExecutionResult.FAILED
    
    # === Exécuteurs d'actions spécifiques ===
    
    async def _execute_screenshot(self, action: Action) -> ExecutionResult:
        """Exécute une capture d'écran"""
        try:
            screenshot = await self.screen_capture.capture()
            if screenshot:
                # Sauvegarder si demandé
                if action.parameters.get("save_path"):
                    screenshot.save(action.parameters["save_path"])
                
                # Mettre à jour le contexte
                self.execution_context.current_screenshot = screenshot
                action.result = {"screenshot_size": screenshot.image.size}
                
                return ExecutionResult.SUCCESS
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_analyze_screen(self, action: Action) -> ExecutionResult:
        """Exécute une analyse d'écran"""
        try:
            if not self.visual_analyzer:
                return ExecutionResult.SKIPPED
            
            screenshot = self.execution_context.current_screenshot
            if not screenshot:
                screenshot = await self.screen_capture.capture()
            
            if screenshot:
                objective = action.parameters.get("objective", "")
                analysis = await self.visual_analyzer.analyze_screen(screenshot.image, objective)
                
                self.execution_context.screen_analysis = analysis.__dict__
                action.result = {
                    "elements_found": len(analysis.ui_elements),
                    "scene_type": analysis.scene_type,
                    "description": analysis.description[:100]
                }
                
                return ExecutionResult.SUCCESS
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_find_element(self, action: Action) -> ExecutionResult:
        """Trouve un élément sur l'écran"""
        try:
            element_type = action.parameters.get("element_type")
            text = action.parameters.get("text", "")
            
            # Utiliser l'analyse d'écran existante ou en créer une nouvelle
            if not self.execution_context.screen_analysis and self.visual_analyzer:
                await self._execute_analyze_screen(action)
            
            # Chercher l'élément (implémentation basique)
            # TODO: Améliorer avec des techniques de vision plus avancées
            
            if self.execution_context.screen_analysis:
                ui_elements = self.execution_context.screen_analysis.get("ui_elements", [])
                
                for element in ui_elements:
                    if (element_type == "any" or 
                        element.get("type") == element_type or
                        text.lower() in element.get("text", "").lower()):
                        
                        # Élément trouvé
                        action.result = {
                            "element_found": True,
                            "element": element.__dict__ if hasattr(element, '__dict__') else element,
                            "position": element.get("bbox") if hasattr(element, 'bbox') else None
                        }
                        
                        # Ajouter aux variables pour usage ultérieur
                        var_name = action.parameters.get("store_as", "found_element")
                        self.execution_context.variables[var_name] = element
                        
                        return ExecutionResult.SUCCESS
            
            # Élément non trouvé
            action.result = {"element_found": False}
            return ExecutionResult.FAILED
            
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_click(self, action: Action) -> ExecutionResult:
        """Exécute un clic de souris"""
        try:
            x = action.parameters.get("x")
            y = action.parameters.get("y")
            target = action.parameters.get("target")
            
            # Si target est spécifié, chercher les coordonnées
            if target and not (x and y):
                if target in self.execution_context.variables:
                    element = self.execution_context.variables[target]
                    if hasattr(element, 'bbox') and element.bbox:
                        # Calculer le centre de l'élément
                        bbox = element.bbox
                        x = bbox[0] + bbox[2] // 2
                        y = bbox[1] + bbox[3] // 2
                    else:
                        return ExecutionResult.FAILED
                else:
                    return ExecutionResult.FAILED
            
            if x is not None and y is not None:
                success = await self.mouse_controller.click(x, y)
                
                action.result = {"clicked": success, "position": (x, y)}
                return ExecutionResult.SUCCESS if success else ExecutionResult.FAILED
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_double_click(self, action: Action) -> ExecutionResult:
        """Exécute un double-clic"""
        try:
            x = action.parameters.get("x")
            y = action.parameters.get("y")
            
            if x is not None and y is not None:
                success = await self.mouse_controller.double_click(x, y)
                action.result = {"double_clicked": success, "position": (x, y)}
                return ExecutionResult.SUCCESS if success else ExecutionResult.FAILED
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_right_click(self, action: Action) -> ExecutionResult:
        """Exécute un clic droit"""
        try:
            x = action.parameters.get("x")
            y = action.parameters.get("y")
            
            if x is not None and y is not None:
                success = await self.mouse_controller.right_click(x, y)
                action.result = {"right_clicked": success, "position": (x, y)}
                return ExecutionResult.SUCCESS if success else ExecutionResult.FAILED
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_type_text(self, action: Action) -> ExecutionResult:
        """Exécute la saisie de texte"""
        try:
            text = action.parameters.get("text", "")
            human_like = action.parameters.get("human_like", True)
            
            if text:
                success = await self.keyboard_controller.type_text(text, human_like)
                action.result = {"typed": success, "text_length": len(text)}
                return ExecutionResult.SUCCESS if success else ExecutionResult.FAILED
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_press_key(self, action: Action) -> ExecutionResult:
        """Exécute l'appui sur une touche"""
        try:
            from ..control.keyboard_controller import SpecialKey
            
            key = action.parameters.get("key")
            duration = action.parameters.get("duration", 0.1)
            
            if key:
                # Convertir en SpecialKey si nécessaire
                if isinstance(key, str):
                    try:
                        special_key = SpecialKey(key)
                    except ValueError:
                        # Touche non reconnue
                        return ExecutionResult.FAILED
                else:
                    special_key = key
                
                success = await self.keyboard_controller.press_key(special_key, duration)
                action.result = {"key_pressed": success, "key": key}
                return ExecutionResult.SUCCESS if success else ExecutionResult.FAILED
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_hotkey(self, action: Action) -> ExecutionResult:
        """Exécute un raccourci clavier"""
        try:
            keys = action.parameters.get("keys")
            
            if keys:
                # Support des formats "ctrl+c" et ["ctrl", "c"]
                if isinstance(keys, str):
                    success = await self.keyboard_controller.send_hotkey(keys)
                elif isinstance(keys, list):
                    success = await self.keyboard_controller.press_combination(*keys)
                else:
                    return ExecutionResult.FAILED
                
                action.result = {"hotkey_sent": success, "keys": keys}
                return ExecutionResult.SUCCESS if success else ExecutionResult.FAILED
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_wait(self, action: Action) -> ExecutionResult:
        """Exécute une attente"""
        try:
            duration = action.parameters.get("duration", 1.0)
            await asyncio.sleep(duration)
            
            action.result = {"waited": duration}
            return ExecutionResult.SUCCESS
            
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_open_app(self, action: Action) -> ExecutionResult:
        """Ouvre une application"""
        try:
            app_name = action.parameters.get("app_name")
            executable = action.parameters.get("executable")
            
            if app_name or executable:
                # TODO: Implémenter l'ouverture d'application
                # Pour l'instant, simuler le succès
                action.result = {"app_opened": True, "app": app_name or executable}
                return ExecutionResult.SUCCESS
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_switch_app(self, action: Action) -> ExecutionResult:
        """Bascule vers une application"""
        try:
            app_name = action.parameters.get("app_name")
            
            if app_name and self.app_detector:
                apps = await self.app_detector.find_application_by_name(app_name)
                if apps:
                    success = await self.app_detector.activate_application(apps[0])
                    action.result = {"app_switched": success, "app": app_name}
                    return ExecutionResult.SUCCESS if success else ExecutionResult.FAILED
                else:
                    action.result = {"app_switched": False, "error": "Application non trouvée"}
                    return ExecutionResult.FAILED
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    async def _execute_ocr_text(self, action: Action) -> ExecutionResult:
        """Exécute la reconnaissance de texte"""
        try:
            if not self.ocr_engine:
                return ExecutionResult.SKIPPED
            
            screenshot = self.execution_context.current_screenshot
            if not screenshot:
                screenshot = await self.screen_capture.capture()
            
            if screenshot:
                result = await self.ocr_engine.extract_text(screenshot.image)
                
                action.result = {
                    "text_found": len(result.all_text) > 0,
                    "text_length": len(result.all_text),
                    "words_count": len(result.words),
                    "confidence": result.confidence_avg
                }
                
                # Stocker le texte pour usage ultérieur
                self.execution_context.variables["ocr_text"] = result.all_text
                
                return ExecutionResult.SUCCESS
            else:
                return ExecutionResult.FAILED
                
        except Exception as e:
            action.error = str(e)
            return ExecutionResult.FAILED
    
    # === Méthodes utilitaires ===
    
    async def _update_screen_context(self):
        """Met à jour le contexte d'écran"""
        try:
            screenshot = await self.screen_capture.capture()
            if screenshot:
                self.execution_context.current_screenshot = screenshot
        except Exception as e:
            logger.debug(f"Erreur mise à jour contexte écran: {e}")
    
    async def _request_confirmation(self, sequence: ActionSequence) -> bool:
        """Demande confirmation à l'utilisateur"""
        if self.confirmation_callback:
            try:
                return await self.confirmation_callback(sequence)
            except Exception as e:
                logger.error(f"Erreur callback confirmation: {e}")
                return False
        
        # Par défaut, accepter en mode non-interactif
        return True
    
    # === Configuration et callbacks ===
    
    def set_confirmation_callback(self, callback: Callable):
        """Définit le callback de confirmation"""
        self.confirmation_callback = callback
    
    def set_progress_callback(self, callback: Callable):
        """Définit le callback de progression"""
        self.progress_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """Définit le callback d'erreur"""
        self.error_callback = callback
    
    def enable_sandbox_mode(self):
        """Active le mode sandbox"""
        self.config.sandbox_mode = True
        logger.info("🛡️ Mode sandbox activé")
    
    def disable_sandbox_mode(self):
        """Désactive le mode sandbox"""
        self.config.sandbox_mode = False
        logger.warning("⚠️ Mode sandbox désactivé")
    
    # === Statistiques ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'exécution"""
        stats = self.stats.copy()
        
        if stats["actions_executed"] > 0:
            stats["success_rate"] = stats["actions_successful"] / stats["actions_executed"]
            stats["avg_execution_time"] = stats["total_execution_time"] / stats["sequences_executed"] if stats["sequences_executed"] > 0 else 0
        else:
            stats["success_rate"] = 0.0
            stats["avg_execution_time"] = 0.0
        
        stats.update({
            "is_executing": self.is_executing,
            "current_sequence": self.current_sequence.id if self.current_sequence else None,
            "config": {
                "sandbox_mode": self.config.sandbox_mode,
                "require_confirmation": self.config.require_confirmation,
                "auto_retry": self.config.auto_retry
            }
        })
        
        return stats
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne l'historique d'exécution"""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """Efface l'historique d'exécution"""
        self.execution_history.clear()
        logger.info("🗑️ Historique d'exécution effacé")
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.stats = {
            "sequences_executed": 0,
            "actions_executed": 0,
            "actions_successful": 0,
            "actions_failed": 0,
            "total_execution_time": 0.0
        }
        logger.info("📊 Statistiques d'exécution remises à zéro")

# Fonctions utilitaires
async def test_action_executor(modules: Dict[str, Any]):
    """Test de l'exécuteur d'actions"""
    try:
        from .action_planner import ActionPlanner, ActionSequence, Action, ActionType
        
        executor = ActionExecutor()
        
        if not await executor.initialize(modules):
            return False
        
        # Créer une séquence de test
        test_actions = [
            Action(
                type=ActionType.SCREENSHOT,
                description="Prendre une capture d'écran",
                parameters={}
            ),
            Action(
                type=ActionType.WAIT,
                description="Attendre 1 seconde",
                parameters={"duration": 1.0}
            ),
            Action(
                type=ActionType.ANALYZE_SCREEN,
                description="Analyser l'écran",
                parameters={"objective": "Tester l'analyse"}
            )
        ]
        
        test_sequence = ActionSequence(
            id="test_sequence",
            name="Séquence de test",
            description="Test de l'exécuteur d'actions",
            actions=test_actions
        )
        
        # Callbacks de test
        async def confirmation_callback(sequence):
            logger.info(f"🤔 Confirmation demandée pour: {sequence.name}")
            return True  # Auto-accepter pour le test
        
        async def progress_callback(current, total, action):
            logger.info(f"📊 Progression: {current+1}/{total} - {action.description}")
        
        executor.set_confirmation_callback(confirmation_callback)
        executor.set_progress_callback(progress_callback)
        
        # Exécuter la séquence
        result = await executor.execute_sequence(test_sequence)
        
        logger.info(f"✅ Test terminé:")
        logger.info(f"  - Succès: {result['success']}")
        logger.info(f"  - Actions exécutées: {result['actions_executed']}")
        logger.info(f"  - Temps d'exécution: {result['execution_time']:.2f}s")
        
        # Statistiques
        stats = executor.get_stats()
        logger.info(f"📊 Statistiques:")
        logger.info(f"  - Taux de succès: {stats['success_rate']:.1%}")
        logger.info(f"  - Actions totales: {stats['actions_executed']}")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"❌ Erreur test exécuteur: {e}")
        return False

if __name__ == "__main__":
    # Test basique sans modules
    async def basic_test():
        executor = ActionExecutor()
        stats = executor.get_stats()
        logger.info(f"📊 Exécuteur initialisé: {stats}")
    
    asyncio.run(basic_test())