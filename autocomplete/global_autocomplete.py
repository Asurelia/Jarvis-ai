"""
Système d'autocomplétion globale pour JARVIS
Fonctionne dans TOUTES les applications Windows avec hook clavier
"""
import asyncio
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque
import re
from loguru import logger

# Imports conditionnels pour Windows
try:
    import keyboard
    import win32gui
    import win32process
    import psutil
    WINDOWS_HOOKS_AVAILABLE = True
except ImportError as e:
    WINDOWS_HOOKS_AVAILABLE = False
    logger.warning(f"Hooks Windows non disponibles: {e}")

@dataclass
class TypingContext:
    """Contexte de frappe actuel"""
    current_text: str = ""
    cursor_position: int = 0
    app_name: str = ""
    window_title: str = ""
    field_type: str = "text"  # text, email, url, code, etc.
    language: str = "fr"
    last_update: float = field(default_factory=time.time)
    
    def reset(self):
        """Remet à zéro le contexte"""
        self.current_text = ""
        self.cursor_position = 0
        self.last_update = time.time()

@dataclass
class AutocompleteConfig:
    """Configuration de l'autocomplétion"""
    enabled: bool = True
    min_chars: int = 3  # Minimum de caractères pour déclencher
    max_suggestions: int = 5
    debounce_delay: float = 0.3  # Délai avant déclenchement
    show_delay: float = 0.1  # Délai d'affichage
    auto_accept_threshold: float = 0.95  # Seuil d'acceptation automatique
    
    # Applications exclues
    excluded_apps: List[str] = field(default_factory=lambda: [
        "passwordmanager", "keypass", "bitwarden", "lastpass",
        "cmd.exe", "powershell.exe", "ssh.exe"
    ])
    
    # Types de champs sensibles
    sensitive_fields: List[str] = field(default_factory=lambda: [
        "password", "pin", "ssn", "credit", "card"
    ])

class TextBuffer:
    """Buffer intelligent pour le texte en cours de frappe"""
    
    def __init__(self, max_size: int = 1000):
        self.buffer = deque(maxlen=max_size)
        self.current_word = ""
        self.words_history = deque(maxlen=50)
    
    def add_character(self, char: str):
        """Ajoute un caractère au buffer"""
        self.buffer.append(char)
        
        if char.isalnum() or char in "_-":
            self.current_word += char
        else:
            if self.current_word:
                self.words_history.append(self.current_word)
                self.current_word = ""
    
    def remove_character(self):
        """Supprime le dernier caractère (backspace)"""
        if self.buffer:
            removed = self.buffer.pop()
            if self.current_word and removed.isalnum():
                self.current_word = self.current_word[:-1]
    
    def get_current_line(self) -> str:
        """Récupère la ligne actuelle"""
        text = "".join(self.buffer)
        lines = text.split('\n')
        return lines[-1] if lines else ""
    
    def get_context(self, length: int = 100) -> str:
        """Récupère le contexte récent"""
        if len(self.buffer) <= length:
            return "".join(self.buffer)
        return "".join(list(self.buffer)[-length:])
    
    def get_word_at_cursor(self) -> str:
        """Récupère le mot en cours de frappe"""
        return self.current_word
    
    def clear(self):
        """Vide le buffer"""
        self.buffer.clear()
        self.current_word = ""

class AppContextDetector:
    """Détecteur de contexte d'application"""
    
    def __init__(self):
        self.current_app = ""
        self.current_window = ""
        self.field_patterns = {
            "email": [r"mail", r"email", r"@"],
            "url": [r"http", r"www\.", r"\.com", r"\.org"],
            "code": [r"\.py", r"\.js", r"\.html", r"function", r"class"],
            "search": [r"search", r"find", r"query"]
        }
    
    def detect_current_app(self) -> Dict[str, str]:
        """Détecte l'application et la fenêtre actuelles"""
        if not WINDOWS_HOOKS_AVAILABLE:
            return {"app": "unknown", "window": "unknown"}
        
        try:
            # Récupérer la fenêtre active
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            
            # Récupérer le processus
            thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(process_id)
            app_name = process.name()
            
            self.current_app = app_name
            self.current_window = window_title
            
            return {
                "app": app_name,
                "window": window_title,
                "process_id": process_id
            }
            
        except Exception as e:
            logger.debug(f"Erreur détection app: {e}")
            return {"app": "unknown", "window": "unknown"}
    
    def detect_field_type(self, context: str) -> str:
        """Détecte le type de champ basé sur le contexte"""
        context_lower = context.lower()
        
        for field_type, patterns in self.field_patterns.items():
            for pattern in patterns:
                if re.search(pattern, context_lower):
                    return field_type
        
        return "text"
    
    def is_sensitive_context(self, context: str, window_title: str) -> bool:
        """Vérifie si le contexte est sensible (mot de passe, etc.)"""
        sensitive_keywords = [
            "password", "passwd", "pin", "secret", "private",
            "credit", "card", "ssn", "social security"
        ]
        
        text_to_check = (context + " " + window_title).lower()
        
        return any(keyword in text_to_check for keyword in sensitive_keywords)

class GlobalKeyboardHook:
    """Hook clavier global pour capturer la frappe"""
    
    def __init__(self, autocomplete_system):
        self.autocomplete_system = autocomplete_system
        self.is_active = False
        self.hook_thread = None
        
    def start(self):
        """Démarre le hook clavier"""
        if not WINDOWS_HOOKS_AVAILABLE:
            logger.error("❌ Hooks Windows non disponibles")
            return False
        
        if self.is_active:
            logger.warning("⚠️ Hook déjà actif")
            return True
        
        try:
            self.is_active = True
            
            # Enregistrer les événements clavier
            keyboard.on_press(self._on_key_press)
            keyboard.on_release(self._on_key_release)
            
            logger.success("✅ Hook clavier global activé")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur activation hook: {e}")
            self.is_active = False
            return False
    
    def stop(self):
        """Arrête le hook clavier"""
        if self.is_active:
            try:
                keyboard.unhook_all()
                self.is_active = False
                logger.info("⏹️ Hook clavier désactivé")
            except Exception as e:
                logger.error(f"Erreur désactivation hook: {e}")
    
    def _on_key_press(self, key):
        """Gestionnaire d'appui de touche"""
        try:
            # Traitement asynchrone pour éviter de bloquer
            asyncio.create_task(self.autocomplete_system._handle_key_press(key))
        except Exception as e:
            logger.debug(f"Erreur traitement touche: {e}")
    
    def _on_key_release(self, key):
        """Gestionnaire de relâchement de touche"""
        try:
            asyncio.create_task(self.autocomplete_system._handle_key_release(key))
        except Exception as e:
            logger.debug(f"Erreur traitement relâchement: {e}")

class GlobalAutocomplete:
    """Système d'autocomplétion globale principal"""
    
    def __init__(self, config: AutocompleteConfig = None):
        self.config = config or AutocompleteConfig()
        self.typing_context = TypingContext()
        self.text_buffer = TextBuffer()
        self.app_detector = AppContextDetector()
        self.keyboard_hook = GlobalKeyboardHook(self)
        
        # État du système
        self.is_active = False
        self.last_suggestion_time = 0.0
        self.current_suggestions: List[str] = []
        self.debounce_timer = None
        
        # Callbacks
        self.suggestion_callback: Optional[Callable] = None
        self.context_callback: Optional[Callable] = None
        
        # Statistiques
        self.stats = {
            "keys_processed": 0,
            "suggestions_generated": 0,
            "suggestions_accepted": 0,
            "contexts_detected": 0
        }
        
        logger.info("⚡ Système d'autocomplétion globale initialisé")
    
    async def initialize(self):
        """Initialise le système d'autocomplétion"""
        try:
            logger.info("🚀 Initialisation de l'autocomplétion globale...")
            
            # Vérifier les prérequis
            if not WINDOWS_HOOKS_AVAILABLE:
                logger.error("❌ Hooks Windows requis non disponibles")
                return False
            
            # Démarrer le hook clavier
            if not self.keyboard_hook.start():
                logger.error("❌ Impossible de démarrer le hook clavier")
                return False
            
            self.is_active = True
            logger.success("✅ Autocomplétion globale prête")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation autocomplétion: {e}")
            return False
    
    async def _handle_key_press(self, key):
        """Traite l'appui d'une touche"""
        if not self.is_active or not self.config.enabled:
            return
        
        try:
            self.stats["keys_processed"] += 1
            
            # Détecter le contexte d'application
            app_context = self.app_detector.detect_current_app()
            app_name = app_context.get("app", "").lower()
            
            # Vérifier si l'app est exclue
            if any(excluded in app_name for excluded in self.config.excluded_apps):
                return
            
            # Traiter différents types de touches
            if hasattr(key, 'char') and key.char:
                # Caractère normal
                await self._handle_character(key.char, app_context)
                
            elif key.name == 'backspace':
                await self._handle_backspace()
                
            elif key.name == 'space':
                await self._handle_space(app_context)
                
            elif key.name == 'enter':
                await self._handle_enter(app_context)
                
            elif key.name == 'tab':
                await self._handle_tab()
            
        except Exception as e:
            logger.debug(f"Erreur traitement touche: {e}")
    
    async def _handle_key_release(self, key):
        """Traite le relâchement d'une touche"""
        # Pour l'instant, pas d'action spécifique sur le relâchement
        pass
    
    async def _handle_character(self, char: str, app_context: Dict[str, str]):
        """Traite un caractère normal"""
        # Ajouter au buffer
        self.text_buffer.add_character(char)
        
        # Mettre à jour le contexte
        self.typing_context.current_text = self.text_buffer.get_current_line()
        self.typing_context.app_name = app_context.get("app", "")
        self.typing_context.window_title = app_context.get("window", "")
        self.typing_context.last_update = time.time()
        
        # Détecter le type de champ
        context_text = self.text_buffer.get_context()
        self.typing_context.field_type = self.app_detector.detect_field_type(context_text)
        
        # Vérifier si c'est un contexte sensible
        if self.app_detector.is_sensitive_context(context_text, self.typing_context.window_title):
            logger.debug("🔒 Contexte sensible détecté - autocomplétion désactivée")
            return
        
        # Programmer une suggestion avec debounce
        await self._schedule_suggestion()
    
    async def _handle_backspace(self):
        """Traite la suppression (backspace)"""
        self.text_buffer.remove_character()
        self.typing_context.current_text = self.text_buffer.get_current_line()
        
        # Programmer une nouvelle suggestion
        await self._schedule_suggestion()
    
    async def _handle_space(self, app_context: Dict[str, str]):
        """Traite l'espace (fin de mot)"""
        self.text_buffer.add_character(' ')
        
        # Le mot est terminé, pas besoin de suggestion immédiate
        self.current_suggestions.clear()
    
    async def _handle_enter(self, app_context: Dict[str, str]):
        """Traite l'entrée (nouvelle ligne)"""
        self.text_buffer.add_character('\n')
        self.current_suggestions.clear()
    
    async def _handle_tab(self):
        """Traite la tabulation (accepter suggestion)"""
        if self.current_suggestions:
            # Accepter la première suggestion
            await self._accept_suggestion(self.current_suggestions[0])
    
    async def _schedule_suggestion(self):
        """Programme une suggestion avec debounce"""
        # Annuler le timer précédent
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        # Programmer une nouvelle suggestion
        self.debounce_timer = asyncio.create_task(
            self._debounced_suggestion()
        )
    
    async def _debounced_suggestion(self):
        """Suggestion avec délai pour éviter trop d'appels"""
        try:
            await asyncio.sleep(self.config.debounce_delay)
            await self._generate_suggestions()
        except asyncio.CancelledError:
            pass  # Timer annulé, normal
    
    async def _generate_suggestions(self):
        """Génère les suggestions d'autocomplétion"""
        try:
            current_word = self.text_buffer.get_word_at_cursor()
            
            # Vérifier les critères minimums
            if len(current_word) < self.config.min_chars:
                self.current_suggestions.clear()
                return
            
            # Préparer le contexte pour l'IA
            context = {
                "current_word": current_word,
                "current_line": self.typing_context.current_text,
                "context_text": self.text_buffer.get_context(),
                "app_name": self.typing_context.app_name,
                "window_title": self.typing_context.window_title,
                "field_type": self.typing_context.field_type,
                "language": self.typing_context.language
            }
            
            # Générer suggestions via callback
            if self.suggestion_callback:
                suggestions = await self.suggestion_callback(context)
                
                if suggestions:
                    self.current_suggestions = suggestions[:self.config.max_suggestions]
                    self.stats["suggestions_generated"] += 1
                    
                    logger.debug(f"💡 {len(self.current_suggestions)} suggestions pour '{current_word}'")
                    
                    # Afficher les suggestions
                    await self._show_suggestions()
                else:
                    self.current_suggestions.clear()
            
        except Exception as e:
            logger.error(f"❌ Erreur génération suggestions: {e}")
    
    async def _show_suggestions(self):
        """Affiche les suggestions à l'utilisateur"""
        if not self.current_suggestions:
            return
        
        try:
            # Notifier le callback d'affichage
            if self.context_callback:
                await self.context_callback({
                    "action": "show_suggestions",
                    "suggestions": self.current_suggestions,
                    "context": self.typing_context
                })
            
            # Log pour debug
            logger.debug(f"📋 Suggestions: {self.current_suggestions}")
            
        except Exception as e:
            logger.error(f"❌ Erreur affichage suggestions: {e}")
    
    async def _accept_suggestion(self, suggestion: str):
        """Accepte une suggestion"""
        try:
            current_word = self.text_buffer.get_word_at_cursor()
            
            # Calculer le texte à insérer (complétion seulement)
            if suggestion.startswith(current_word):
                completion = suggestion[len(current_word):]
            else:
                completion = suggestion
            
            # Simuler la frappe de la complétion
            # NOTE: Dans un vrai système, il faudrait utiliser SendInput
            logger.info(f"✅ Suggestion acceptée: '{current_word}' -> '{suggestion}'")
            
            self.stats["suggestions_accepted"] += 1
            
            # Notifier l'acceptation
            if self.context_callback:
                await self.context_callback({
                    "action": "suggestion_accepted",
                    "original": current_word,
                    "suggestion": suggestion,
                    "completion": completion
                })
            
            # Nettoyer
            self.current_suggestions.clear()
            
        except Exception as e:
            logger.error(f"❌ Erreur acceptation suggestion: {e}")
    
    def set_suggestion_callback(self, callback: Callable):
        """Définit le callback pour générer les suggestions"""
        self.suggestion_callback = callback
        logger.info("💡 Callback de suggestion configuré")
    
    def set_context_callback(self, callback: Callable):
        """Définit le callback pour les notifications de contexte"""
        self.context_callback = callback
        logger.info("📞 Callback de contexte configuré")
    
    def enable(self):
        """Active l'autocomplétion"""
        self.config.enabled = True
        logger.info("✅ Autocomplétion activée")
    
    def disable(self):
        """Désactive l'autocomplétion"""
        self.config.enabled = False
        self.current_suggestions.clear()
        logger.info("⏹️ Autocomplétion désactivée")
    
    def add_excluded_app(self, app_name: str):
        """Ajoute une application aux exclusions"""
        self.config.excluded_apps.append(app_name.lower())
        logger.info(f"🚫 Application exclue: {app_name}")
    
    def remove_excluded_app(self, app_name: str):
        """Retire une application des exclusions"""
        try:
            self.config.excluded_apps.remove(app_name.lower())
            logger.info(f"✅ Application autorisée: {app_name}")
        except ValueError:
            logger.warning(f"⚠️ Application non trouvée dans les exclusions: {app_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système"""
        stats = self.stats.copy()
        
        if stats["suggestions_generated"] > 0:
            stats["acceptance_rate"] = stats["suggestions_accepted"] / stats["suggestions_generated"]
        else:
            stats["acceptance_rate"] = 0.0
        
        stats.update({
            "is_active": self.is_active,
            "config": {
                "enabled": self.config.enabled,
                "min_chars": self.config.min_chars,
                "max_suggestions": self.config.max_suggestions,
                "excluded_apps": len(self.config.excluded_apps)
            },
            "current_context": {
                "app": self.typing_context.app_name,
                "field_type": self.typing_context.field_type,
                "current_word": self.text_buffer.get_word_at_cursor(),
                "suggestions_count": len(self.current_suggestions)
            }
        })
        
        return stats
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.stats = {
            "keys_processed": 0,
            "suggestions_generated": 0,
            "suggestions_accepted": 0,
            "contexts_detected": 0
        }
        logger.info("📊 Statistiques autocomplétion remises à zéro")
    
    async def shutdown(self):
        """Arrête le système d'autocomplétion"""
        self.is_active = False
        self.keyboard_hook.stop()
        
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        logger.info("⏹️ Système d'autocomplétion arrêté")

# Fonctions utilitaires
async def test_global_autocomplete() -> bool:
    """Test du système d'autocomplétion globale"""
    try:
        autocomplete = GlobalAutocomplete()
        
        # Callback de test
        async def test_suggestion_callback(context):
            word = context["current_word"]
            
            # Suggestions de test
            suggestions = [
                f"{word}tion",
                f"{word}ment",
                f"{word}able",
                f"{word}ing",
                f"{word}ed"
            ]
            
            return [s for s in suggestions if len(s) > len(word)]
        
        async def test_context_callback(event):
            action = event["action"]
            if action == "show_suggestions":
                logger.info(f"💡 Suggestions: {event['suggestions']}")
            elif action == "suggestion_accepted":
                logger.info(f"✅ Accepté: {event['suggestion']}")
        
        # Configurer les callbacks
        autocomplete.set_suggestion_callback(test_suggestion_callback)
        autocomplete.set_context_callback(test_context_callback)
        
        # Initialiser
        if not await autocomplete.initialize():
            return False
        
        logger.info("🧪 Test autocomplétion globale démarré")
        logger.info("Tapez dans n'importe quelle application pour tester")
        logger.info("Ctrl+C pour arrêter")
        
        # Attendre l'arrêt
        try:
            while autocomplete.is_active:
                await asyncio.sleep(1)
                
                # Afficher les stats périodiquement
                if autocomplete.stats["keys_processed"] % 100 == 0 and autocomplete.stats["keys_processed"] > 0:
                    stats = autocomplete.get_stats()
                    logger.info(f"📊 {stats['keys_processed']} touches, {stats['suggestions_generated']} suggestions")
        
        except KeyboardInterrupt:
            logger.info("⏹️ Arrêt demandé")
        
        await autocomplete.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test autocomplétion: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_global_autocomplete())