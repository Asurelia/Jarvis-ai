"""
Contrôleur de clavier sécurisé pour JARVIS
Gestion de la saisie de texte, raccourcis et commandes clavier
"""
import asyncio
import time
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import pyautogui
import keyboard
from loguru import logger

class SpecialKey(Enum):
    """Touches spéciales"""
    ENTER = "enter"
    TAB = "tab"
    SPACE = "space"
    BACKSPACE = "backspace"
    DELETE = "delete"
    ESC = "escape"
    SHIFT = "shift"
    CTRL = "ctrl"
    ALT = "alt"
    WIN = "win"
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"
    F11 = "f11"
    F12 = "f12"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    HOME = "home"
    END = "end"
    PAGEUP = "pageup"
    PAGEDOWN = "pagedown"

@dataclass
class KeyboardAction:
    """Représente une action clavier"""
    action_type: str  # "type", "key", "hotkey", "combination"
    content: str
    duration: float = 0.0
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class KeyboardSecurity:
    """Gestionnaire de sécurité pour les actions clavier"""
    
    def __init__(self, sandbox_mode: bool = True):
        self.sandbox_mode = sandbox_mode
        self.action_count = 0
        self.last_reset = time.time()
        self.max_actions_per_minute = 300  # Plus permissif que la souris
        
        # Combinaisons interdites en mode sandbox
        self.forbidden_combinations = {
            "ctrl+alt+delete",
            "ctrl+shift+esc",
            "win+r",
            "win+x",
            "alt+f4"
        }
        
        # Commandes dangereuses
        self.dangerous_patterns = [
            "format",
            "del /f",
            "rm -rf",
            "shutdown",
            "reboot",
            "registry",
            "taskkill"
        ]
        
        logger.info(f"⌨️  Sécurité clavier activée (sandbox: {sandbox_mode})")
    
    def can_perform_action(self) -> bool:
        """Vérifie si une action peut être effectuée"""
        current_time = time.time()
        
        if current_time - self.last_reset >= 60:
            self.action_count = 0
            self.last_reset = current_time
        
        if self.action_count >= self.max_actions_per_minute:
            logger.warning(f"Limite d'actions clavier atteinte: {self.action_count}")
            return False
        
        self.action_count += 1
        return True
    
    def is_combination_safe(self, combination: str) -> bool:
        """Vérifie si une combinaison de touches est sécurisée"""
        combination_lower = combination.lower().replace(" ", "")
        
        # Vérifier les combinaisons interdites
        if combination_lower in self.forbidden_combinations:
            logger.warning(f"Combinaison interdite: {combination}")
            return False
        
        return True
    
    def is_text_safe(self, text: str) -> bool:
        """Vérifie si un texte est sécurisé à taper"""
        text_lower = text.lower()
        
        # Vérifier les patterns dangereux
        for pattern in self.dangerous_patterns:
            if pattern in text_lower:
                logger.warning(f"Pattern dangereux détecté: {pattern}")
                return False
        
        # En mode sandbox, limiter la longueur
        if self.sandbox_mode and len(text) > 1000:
            logger.warning(f"Texte trop long en mode sandbox: {len(text)} caractères")
            return False
        
        return True
    
    def validate_action(self, action: KeyboardAction) -> bool:
        """Valide une action clavier"""
        if not self.can_perform_action():
            return False
        
        if action.action_type == "type":
            return self.is_text_safe(action.content)
        elif action.action_type in ["hotkey", "combination"]:
            return self.is_combination_safe(action.content)
        
        return True

class HumanTypingSimulator:
    """Simule une frappe humaine naturelle"""
    
    def __init__(self):
        self.base_typing_speed = 0.05  # Secondes entre chaque caractère
        self.speed_variation = 0.03  # Variation de vitesse
        self.mistake_probability = 0.02  # Probabilité d'erreur de frappe
        
    def calculate_typing_delay(self) -> float:
        """Calcule un délai de frappe naturel"""
        delay = self.base_typing_speed + random.uniform(-self.speed_variation, self.speed_variation)
        return max(0.01, delay)  # Minimum 10ms
    
    def should_make_mistake(self) -> bool:
        """Détermine s'il faut faire une erreur de frappe"""
        return random.random() < self.mistake_probability
    
    def get_typing_mistake(self, char: str) -> str:
        """Génère une erreur de frappe plausible"""
        # Clavier QWERTY - lettres adjacentes
        keyboard_layout = {
            'a': 'qwsz', 'b': 'vghn', 'c': 'xdfv', 'd': 'erfcxs', 'e': 'wrfds',
            'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'i': 'ujklo', 'j': 'uikmnh',
            'k': 'ijlom', 'l': 'okp', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
            'p': 'ol', 'q': 'wa', 'r': 'etdf', 's': 'awedxz', 't': 'refgy',
            'u': 'yihj', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tugh',
            'z': 'asx'
        }
        
        if char.lower() in keyboard_layout:
            adjacent = keyboard_layout[char.lower()]
            mistake = random.choice(adjacent)
            return mistake.upper() if char.isupper() else mistake
        
        return char
    
    async def simulate_natural_typing(self, text: str, callback) -> None:
        """Simule une frappe naturelle avec erreurs occasionnelles"""
        i = 0
        while i < len(text):
            char = text[i]
            
            # Calculer le délai
            delay = self.calculate_typing_delay()
            
            # Vérifier s'il faut faire une erreur
            if self.should_make_mistake() and char.isalpha():
                # Faire une erreur
                mistake_char = self.get_typing_mistake(char)
                await callback(mistake_char)
                await asyncio.sleep(delay)
                
                # Corriger l'erreur (backspace + bon caractère)
                await callback('\b')  # Backspace
                await asyncio.sleep(delay)
                await callback(char)
                await asyncio.sleep(delay)
            else:
                # Frappe normale
                await callback(char)
                await asyncio.sleep(delay)
            
            i += 1

class KeyboardController:
    """Contrôleur principal du clavier"""
    
    def __init__(self, sandbox_mode: bool = True):
        self.security = KeyboardSecurity(sandbox_mode)
        self.typing_simulator = HumanTypingSimulator()
        self.action_history: List[KeyboardAction] = []
        self.caps_lock_state = False
        self.num_lock_state = True
        
        logger.info("⌨️  Contrôleur clavier initialisé")
    
    async def initialize(self):
        """Initialise le contrôleur"""
        try:
            # Vérifier l'état des locks
            self.caps_lock_state = keyboard.is_pressed('caps lock')
            logger.success("✅ Contrôleur clavier prêt")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation clavier: {e}")
            raise
    
    async def type_text(self, text: str, human_like: bool = True, 
                       typing_speed: float = None) -> bool:
        """Tape un texte"""
        action = KeyboardAction("type", text)
        
        if not self.security.validate_action(action):
            logger.warning(f"Action type_text refusée: {text[:50]}...")
            return False
        
        try:
            if human_like:
                # Frappe humaine naturelle
                async def type_char(char):
                    if char == '\b':  # Backspace
                        pyautogui.press('backspace')
                    else:
                        pyautogui.write(char, interval=0)
                
                await self.typing_simulator.simulate_natural_typing(text, type_char)
            else:
                # Frappe directe
                interval = typing_speed or 0.01
                pyautogui.write(text, interval=interval)
            
            self.action_history.append(action)
            logger.debug(f"⌨️  Texte tapé: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur frappe texte: {e}")
            return False
    
    async def press_key(self, key: SpecialKey, duration: float = 0.1) -> bool:
        """Appuie sur une touche spéciale"""
        action = KeyboardAction("key", key.value, duration)
        
        if not self.security.validate_action(action):
            logger.warning(f"Action press_key refusée: {key.value}")
            return False
        
        try:
            if duration > 0.1:
                # Appui long
                pyautogui.keyDown(key.value)
                await asyncio.sleep(duration)
                pyautogui.keyUp(key.value)
            else:
                # Appui court
                pyautogui.press(key.value)
            
            self.action_history.append(action)
            logger.debug(f"⌨️  Touche appuyée: {key.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur appui touche: {e}")
            return False
    
    async def press_combination(self, *keys: str) -> bool:
        """Appuie sur une combinaison de touches"""
        combination = "+".join(keys)
        action = KeyboardAction("combination", combination)
        
        if not self.security.validate_action(action):
            logger.warning(f"Combinaison refusée: {combination}")
            return False
        
        try:
            pyautogui.hotkey(*keys)
            
            self.action_history.append(action)
            logger.debug(f"⌨️  Combinaison effectuée: {combination}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur combinaison: {e}")
            return False
    
    async def send_hotkey(self, hotkey: str) -> bool:
        """Envoie un raccourci clavier (format: ctrl+c, alt+tab, etc.)"""
        action = KeyboardAction("hotkey", hotkey)
        
        if not self.security.validate_action(action):
            logger.warning(f"Raccourci refusé: {hotkey}")
            return False
        
        try:
            keys = hotkey.split('+')
            keys = [key.strip() for key in keys]
            pyautogui.hotkey(*keys)
            
            self.action_history.append(action)
            logger.debug(f"⌨️  Raccourci envoyé: {hotkey}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur raccourci: {e}")
            return False
    
    # Raccourcis communs
    async def copy(self) -> bool:
        """Copier (Ctrl+C)"""
        return await self.send_hotkey("ctrl+c")
    
    async def paste(self) -> bool:
        """Coller (Ctrl+V)"""
        return await self.send_hotkey("ctrl+v")
    
    async def cut(self) -> bool:
        """Couper (Ctrl+X)"""
        return await self.send_hotkey("ctrl+x")
    
    async def undo(self) -> bool:
        """Annuler (Ctrl+Z)"""
        return await self.send_hotkey("ctrl+z")
    
    async def redo(self) -> bool:
        """Refaire (Ctrl+Y)"""
        return await self.send_hotkey("ctrl+y")
    
    async def select_all(self) -> bool:
        """Tout sélectionner (Ctrl+A)"""
        return await self.send_hotkey("ctrl+a")
    
    async def save(self) -> bool:
        """Sauvegarder (Ctrl+S)"""
        return await self.send_hotkey("ctrl+s")
    
    async def open_file(self) -> bool:
        """Ouvrir un fichier (Ctrl+O)"""
        return await self.send_hotkey("ctrl+o")
    
    async def new_file(self) -> bool:
        """Nouveau fichier (Ctrl+N)"""
        return await self.send_hotkey("ctrl+n")
    
    async def find(self) -> bool:
        """Rechercher (Ctrl+F)"""
        return await self.send_hotkey("ctrl+f")
    
    async def replace(self) -> bool:
        """Remplacer (Ctrl+H)"""
        return await self.send_hotkey("ctrl+h")
    
    async def alt_tab(self) -> bool:
        """Changer d'application (Alt+Tab)"""
        return await self.send_hotkey("alt+tab")
    
    # Navigation
    async def move_cursor(self, direction: str, distance: int = 1) -> bool:
        """Déplace le curseur"""
        direction_map = {
            "left": SpecialKey.LEFT,
            "right": SpecialKey.RIGHT,
            "up": SpecialKey.UP,
            "down": SpecialKey.DOWN,
            "home": SpecialKey.HOME,
            "end": SpecialKey.END,
            "pageup": SpecialKey.PAGEUP,
            "pagedown": SpecialKey.PAGEDOWN
        }
        
        if direction not in direction_map:
            logger.warning(f"Direction inconnue: {direction}")
            return False
        
        key = direction_map[direction]
        
        for _ in range(distance):
            if not await self.press_key(key):
                return False
            if distance > 1:
                await asyncio.sleep(0.05)  # Petite pause entre les appuis
        
        return True
    
    async def select_text(self, direction: str, distance: int = 1) -> bool:
        """Sélectionne du texte avec Shift + flèches"""
        direction_map = {
            "left": "shift+left",
            "right": "shift+right",
            "up": "shift+up",
            "down": "shift+down",
            "word_left": "ctrl+shift+left",
            "word_right": "ctrl+shift+right",
            "line": "shift+end",
            "all": "ctrl+a"
        }
        
        if direction not in direction_map:
            logger.warning(f"Direction de sélection inconnue: {direction}")
            return False
        
        hotkey = direction_map[direction]
        
        for _ in range(distance):
            if not await self.send_hotkey(hotkey):
                return False
            if distance > 1:
                await asyncio.sleep(0.05)
        
        return True
    
    # Fonctions de suppression
    async def delete_text(self, direction: str = "forward", count: int = 1) -> bool:
        """Supprime du texte"""
        if direction == "forward":
            key = SpecialKey.DELETE
        elif direction == "backward":
            key = SpecialKey.BACKSPACE
        else:
            logger.warning(f"Direction de suppression inconnue: {direction}")
            return False
        
        for _ in range(count):
            if not await self.press_key(key):
                return False
            await asyncio.sleep(0.05)
        
        return True
    
    async def clear_field(self) -> bool:
        """Efface complètement un champ (Ctrl+A puis Delete)"""
        if await self.select_all():
            return await self.delete_text("forward")
        return False
    
    # Fonctions de fenêtre
    async def minimize_window(self) -> bool:
        """Minimise la fenêtre active (Win+Down)"""
        return await self.send_hotkey("win+down")
    
    async def maximize_window(self) -> bool:
        """Maximise la fenêtre active (Win+Up)"""
        return await self.send_hotkey("win+up")
    
    async def close_window(self) -> bool:
        """Ferme la fenêtre active (Alt+F4)"""
        # Attention: peut être dangereux, vérifier en mode sandbox
        if self.security.sandbox_mode:
            logger.warning("Fermeture de fenêtre bloquée en mode sandbox")
            return False
        return await self.send_hotkey("alt+f4")
    
    # Utilitaires
    def get_action_history(self, limit: int = 50) -> List[KeyboardAction]:
        """Récupère l'historique des actions"""
        return self.action_history[-limit:]
    
    def clear_history(self):
        """Efface l'historique des actions"""
        self.action_history.clear()
        logger.debug("📋 Historique des actions clavier effacé")
    
    async def emergency_stop(self):
        """Arrêt d'urgence - relâche toutes les touches"""
        try:
            # Relâcher les touches de modification communes
            for key in ['ctrl', 'alt', 'shift', 'win']:
                pyautogui.keyUp(key)
            
            # Envoyer Escape pour annuler les actions en cours
            pyautogui.press('escape')
            
            logger.warning("🚨 Arrêt d'urgence clavier activé")
            
        except Exception as e:
            logger.error(f"Erreur arrêt d'urgence clavier: {e}")

# Fonctions utilitaires
async def quick_type(text: str, human_like: bool = True) -> bool:
    """Frappe rapide de texte"""
    controller = KeyboardController()
    await controller.initialize()
    
    return await controller.type_text(text, human_like)

async def quick_hotkey(hotkey: str) -> bool:
    """Raccourci rapide"""
    controller = KeyboardController()
    await controller.initialize()
    
    return await controller.send_hotkey(hotkey)

if __name__ == "__main__":
    async def test_keyboard():
        controller = KeyboardController(sandbox_mode=True)
        await controller.initialize()
        
        # Test de frappe
        print("Test de frappe (5 secondes)...")
        await asyncio.sleep(5)  # Laisser le temps de se positionner
        
        await controller.type_text("Bonjour, ceci est un test de JARVIS!", human_like=True)
        
        # Test de raccourcis
        print("Test de sélection...")
        await controller.select_all()
        
        print("Test de copie...")
        await controller.copy()
        
        print("✅ Tests terminés")
    
    asyncio.run(test_keyboard())