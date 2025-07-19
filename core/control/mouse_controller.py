"""
Contrôleur de souris sécurisé pour JARVIS
Gestion des clics, déplacements et glisser-déposer avec sécurité
"""
import asyncio
import time
import random
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import pyautogui
import numpy as np
from loguru import logger

# Configuration sécurisée de pyautogui
pyautogui.FAILSAFE = True  # Coin supérieur gauche pour arrêt d'urgence
pyautogui.PAUSE = 0.1  # Pause entre chaque action

class MouseButton(Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"

@dataclass
class MouseAction:
    """Représente une action de souris"""
    action_type: str  # "click", "move", "drag", "scroll"
    x: int
    y: int
    button: MouseButton = MouseButton.LEFT
    duration: float = 0.5
    clicks: int = 1
    scroll_amount: int = 0
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class MouseSecurity:
    """Gestionnaire de sécurité pour les actions de souris"""
    
    def __init__(self, sandbox_mode: bool = True):
        self.sandbox_mode = sandbox_mode
        self.action_count = 0
        self.last_reset = time.time()
        self.max_actions_per_minute = 120
        self.forbidden_zones: List[Tuple[int, int, int, int]] = []
        self.screen_bounds = self._get_screen_bounds()
        
        # Zones interdites par défaut (coin failsafe, zones système)
        self.add_forbidden_zone(0, 0, 100, 100)  # Coin failsafe
        
        logger.info(f"🛡️  Sécurité souris activée (sandbox: {sandbox_mode})")
    
    def _get_screen_bounds(self) -> Tuple[int, int]:
        """Récupère les dimensions de l'écran"""
        try:
            return pyautogui.size()
        except Exception:
            return (1920, 1080)  # Valeur par défaut
    
    def add_forbidden_zone(self, x: int, y: int, width: int, height: int):
        """Ajoute une zone interdite"""
        self.forbidden_zones.append((x, y, x + width, y + height))
        logger.debug(f"Zone interdite ajoutée: ({x}, {y}, {width}, {height})")
    
    def is_position_safe(self, x: int, y: int) -> bool:
        """Vérifie si une position est sécurisée"""
        # Vérifier les limites de l'écran
        if not (0 <= x <= self.screen_bounds[0] and 0 <= y <= self.screen_bounds[1]):
            logger.warning(f"Position hors écran: ({x}, {y})")
            return False
        
        # Vérifier les zones interdites
        for zone in self.forbidden_zones:
            x1, y1, x2, y2 = zone
            if x1 <= x <= x2 and y1 <= y <= y2:
                logger.warning(f"Position dans zone interdite: ({x}, {y})")
                return False
        
        return True
    
    def can_perform_action(self) -> bool:
        """Vérifie si une action peut être effectuée"""
        current_time = time.time()
        
        # Reset du compteur chaque minute
        if current_time - self.last_reset >= 60:
            self.action_count = 0
            self.last_reset = current_time
        
        if self.action_count >= self.max_actions_per_minute:
            logger.warning(f"Limite d'actions souris atteinte: {self.action_count}")
            return False
        
        self.action_count += 1
        return True
    
    def validate_action(self, action: MouseAction) -> bool:
        """Valide une action de souris avant exécution"""
        if not self.can_perform_action():
            return False
        
        if not self.is_position_safe(action.x, action.y):
            return False
        
        # En mode sandbox, restrictions supplémentaires
        if self.sandbox_mode:
            # Limiter les zones autorisées
            center_x, center_y = self.screen_bounds[0] // 2, self.screen_bounds[1] // 2
            max_distance = min(self.screen_bounds) // 3
            
            distance = ((action.x - center_x) ** 2 + (action.y - center_y) ** 2) ** 0.5
            if distance > max_distance:
                logger.warning(f"Action hors zone sandbox: distance {distance:.0f} > {max_distance}")
                return False
        
        return True

class HumanMouseSimulator:
    """Simule des mouvements de souris humains"""
    
    @staticmethod
    def generate_bezier_path(start: Tuple[int, int], end: Tuple[int, int], 
                           num_points: int = 20) -> List[Tuple[int, int]]:
        """Génère un chemin de Bézier entre deux points"""
        x1, y1 = start
        x2, y2 = end
        
        # Points de contrôle aléatoires pour un mouvement naturel
        ctrl1_x = x1 + random.randint(-50, 50)
        ctrl1_y = y1 + random.randint(-50, 50)
        ctrl2_x = x2 + random.randint(-50, 50)
        ctrl2_y = y2 + random.randint(-50, 50)
        
        path = []
        for i in range(num_points):
            t = i / (num_points - 1)
            
            # Courbe de Bézier cubique
            x = (1-t)**3 * x1 + 3*(1-t)**2*t * ctrl1_x + 3*(1-t)*t**2 * ctrl2_x + t**3 * x2
            y = (1-t)**3 * y1 + 3*(1-t)**2*t * ctrl1_y + 3*(1-t)*t**2 * ctrl2_y + t**3 * y2
            
            path.append((int(x), int(y)))
        
        return path
    
    @staticmethod
    def add_mouse_jitter(x: int, y: int, jitter_amount: int = 2) -> Tuple[int, int]:
        """Ajoute un léger tremblement naturel"""
        jitter_x = random.randint(-jitter_amount, jitter_amount)
        jitter_y = random.randint(-jitter_amount, jitter_amount)
        return (x + jitter_x, y + jitter_y)
    
    @staticmethod
    def calculate_move_duration(distance: float) -> float:
        """Calcule une durée de mouvement réaliste basée sur la distance"""
        # Loi de Fitts simplifiée pour le temps de mouvement
        min_duration = 0.1
        max_duration = 2.0
        
        # Plus c'est loin, plus c'est long (avec un maximum)
        duration = min_duration + (distance / 1000) * 0.5
        return min(duration, max_duration)

class MouseController:
    """Contrôleur principal de la souris"""
    
    def __init__(self, sandbox_mode: bool = True):
        self.security = MouseSecurity(sandbox_mode)
        self.simulator = HumanMouseSimulator()
        self.current_position = pyautogui.position()
        self.action_history: List[MouseAction] = []
        self.is_dragging = False
        
        logger.info("🖱️  Contrôleur de souris initialisé")
    
    async def initialize(self):
        """Initialise le contrôleur"""
        try:
            # Vérifier que pyautogui fonctionne
            self.current_position = pyautogui.position()
            logger.success("✅ Contrôleur de souris prêt")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation souris: {e}")
            raise
    
    async def move_to(self, x: int, y: int, duration: float = None, 
                     human_like: bool = True) -> bool:
        """Déplace la souris vers une position"""
        action = MouseAction("move", x, y, duration=duration or 0.5)
        
        if not self.security.validate_action(action):
            logger.warning(f"Action move_to refusée: ({x}, {y})")
            return False
        
        try:
            start_pos = self.current_position
            
            if human_like:
                # Mouvement humain avec courbe de Bézier
                path = self.simulator.generate_bezier_path(start_pos, (x, y))
                
                # Calculer la durée automatiquement si non spécifiée
                if duration is None:
                    distance = ((x - start_pos[0])**2 + (y - start_pos[1])**2)**0.5
                    duration = self.simulator.calculate_move_duration(distance)
                
                # Déplacer le long du chemin
                step_duration = duration / len(path)
                
                for point in path:
                    jittered_point = self.simulator.add_mouse_jitter(*point)
                    pyautogui.moveTo(*jittered_point, duration=step_duration)
                    await asyncio.sleep(step_duration)
            
            else:
                # Mouvement direct
                pyautogui.moveTo(x, y, duration=duration)
                await asyncio.sleep(duration)
            
            self.current_position = (x, y)
            self.action_history.append(action)
            
            logger.debug(f"🖱️  Souris déplacée vers ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur déplacement souris: {e}")
            return False
    
    async def click(self, x: Optional[int] = None, y: Optional[int] = None,
                   button: MouseButton = MouseButton.LEFT, clicks: int = 1,
                   interval: float = 0.1) -> bool:
        """Effectue un clic de souris"""
        # Utiliser la position actuelle si non spécifiée
        if x is None or y is None:
            x, y = self.current_position
        
        action = MouseAction("click", x, y, button, clicks=clicks)
        
        if not self.security.validate_action(action):
            logger.warning(f"Action click refusée: ({x}, {y})")
            return False
        
        try:
            # Déplacer vers la position si nécessaire
            if (x, y) != self.current_position:
                await self.move_to(x, y)
            
            # Effectuer le clic
            pyautogui.click(x, y, clicks=clicks, interval=interval, button=button.value)
            
            self.action_history.append(action)
            logger.debug(f"🖱️  Clic {button.value} effectué à ({x}, {y})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur clic souris: {e}")
            return False
    
    async def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Effectue un double-clic"""
        return await self.click(x, y, clicks=2, interval=0.05)
    
    async def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Effectue un clic droit"""
        return await self.click(x, y, button=MouseButton.RIGHT)
    
    async def drag_to(self, start_x: int, start_y: int, end_x: int, end_y: int,
                     duration: float = 1.0, button: MouseButton = MouseButton.LEFT) -> bool:
        """Effectue un glisser-déposer"""
        start_action = MouseAction("drag_start", start_x, start_y, button, duration)
        end_action = MouseAction("drag_end", end_x, end_y, button, duration)
        
        if not (self.security.validate_action(start_action) and 
                self.security.validate_action(end_action)):
            logger.warning(f"Action drag refusée: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            return False
        
        try:
            # Déplacer vers le point de départ
            await self.move_to(start_x, start_y)
            
            # Commencer le glisser
            pyautogui.mouseDown(button=button.value)
            self.is_dragging = True
            
            # Attendre un peu
            await asyncio.sleep(0.1)
            
            # Déplacer vers la destination avec courbe humaine
            path = self.simulator.generate_bezier_path((start_x, start_y), (end_x, end_y))
            step_duration = duration / len(path)
            
            for point in path:
                jittered_point = self.simulator.add_mouse_jitter(*point)
                pyautogui.moveTo(*jittered_point, duration=step_duration)
                await asyncio.sleep(step_duration)
            
            # Relâcher le bouton
            pyautogui.mouseUp(button=button.value)
            self.is_dragging = False
            
            self.current_position = (end_x, end_y)
            self.action_history.extend([start_action, end_action])
            
            logger.debug(f"🖱️  Glisser-déposer effectué: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur glisser-déposer: {e}")
            # S'assurer que le bouton est relâché en cas d'erreur
            if self.is_dragging:
                pyautogui.mouseUp(button=button.value)
                self.is_dragging = False
            return False
    
    async def scroll(self, x: int, y: int, scroll_amount: int) -> bool:
        """Effectue un défilement"""
        action = MouseAction("scroll", x, y, scroll_amount=scroll_amount)
        
        if not self.security.validate_action(action):
            logger.warning(f"Action scroll refusée: ({x}, {y})")
            return False
        
        try:
            # Déplacer vers la position si nécessaire
            if (x, y) != self.current_position:
                await self.move_to(x, y)
            
            # Effectuer le défilement
            pyautogui.scroll(scroll_amount, x=x, y=y)
            
            self.action_history.append(action)
            logger.debug(f"🖱️  Défilement effectué à ({x}, {y}), amount: {scroll_amount}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur défilement: {e}")
            return False
    
    async def hover(self, x: int, y: int, duration: float = 1.0) -> bool:
        """Survole une position pendant une durée"""
        if await self.move_to(x, y):
            await asyncio.sleep(duration)
            logger.debug(f"🖱️  Survol effectué à ({x}, {y}) pendant {duration}s")
            return True
        return False
    
    def get_position(self) -> Tuple[int, int]:
        """Récupère la position actuelle de la souris"""
        try:
            self.current_position = pyautogui.position()
            return self.current_position
        except Exception as e:
            logger.error(f"Erreur récupération position: {e}")
            return self.current_position
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Récupère la taille de l'écran"""
        return self.security.screen_bounds
    
    def add_forbidden_zone(self, x: int, y: int, width: int, height: int):
        """Ajoute une zone interdite"""
        self.security.add_forbidden_zone(x, y, width, height)
    
    def get_action_history(self, limit: int = 50) -> List[MouseAction]:
        """Récupère l'historique des actions"""
        return self.action_history[-limit:]
    
    def clear_history(self):
        """Efface l'historique des actions"""
        self.action_history.clear()
        logger.debug("📋 Historique des actions souris effacé")
    
    async def emergency_stop(self):
        """Arrêt d'urgence - relâche tous les boutons"""
        try:
            if self.is_dragging:
                pyautogui.mouseUp()
                self.is_dragging = False
            
            # Déplacer vers le coin failsafe
            pyautogui.moveTo(0, 0)
            logger.warning("🚨 Arrêt d'urgence souris activé")
            
        except Exception as e:
            logger.error(f"Erreur arrêt d'urgence: {e}")

# Fonctions utilitaires
async def quick_click(x: int, y: int, button: str = "left") -> bool:
    """Clic rapide à une position"""
    controller = MouseController()
    await controller.initialize()
    
    mouse_button = MouseButton(button)
    return await controller.click(x, y, mouse_button)

async def safe_drag(start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
    """Glisser-déposer sécurisé"""
    controller = MouseController()
    await controller.initialize()
    
    return await controller.drag_to(start_x, start_y, end_x, end_y)

if __name__ == "__main__":
    async def test_mouse():
        controller = MouseController(sandbox_mode=True)
        await controller.initialize()
        
        # Test de déplacement
        print("Test de déplacement...")
        await controller.move_to(500, 300)
        
        # Test de clic
        print("Test de clic...")
        await controller.click()
        
        # Test de défilement
        print("Test de défilement...")
        await controller.scroll(500, 300, 3)
        
        print("✅ Tests terminés")
    
    asyncio.run(test_mouse())