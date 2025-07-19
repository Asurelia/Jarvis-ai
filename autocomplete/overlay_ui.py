"""
Interface utilisateur overlay pour l'autocomplétion JARVIS
Fenêtre transparente toujours au-dessus avec animations
"""
import asyncio
import time
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import threading
from loguru import logger

# Imports conditionnels pour l'UI
try:
    import tkinter as tk
    from tkinter import ttk
    import win32gui
    import win32con
    import win32api
    UI_AVAILABLE = True
except ImportError as e:
    UI_AVAILABLE = False
    logger.warning(f"Modules UI non disponibles: {e}")

@dataclass
class OverlayConfig:
    """Configuration de l'overlay d'autocomplétion"""
    width: int = 300
    height: int = 150
    background_color: str = "#2D2D30"
    text_color: str = "#FFFFFF"
    selected_color: str = "#007ACC"
    border_color: str = "#3E3E42"
    font_family: str = "Segoe UI"
    font_size: int = 10
    padding: int = 8
    item_height: int = 24
    border_radius: int = 6
    opacity: float = 0.95
    animation_duration: float = 0.15
    auto_hide_delay: float = 5.0

class OverlayUI:
    """Interface overlay pour l'autocomplétion"""
    
    def __init__(self, config: OverlayConfig = None):
        self.config = config or OverlayConfig()
        
        # État de l'interface
        self.root = None
        self.canvas = None
        self.is_visible = False
        self.current_suggestions = []
        self.selected_index = 0
        self.cursor_position = (0, 0)
        
        # Animation
        self.fade_animation = None
        self.auto_hide_timer = None
        
        # Thread UI
        self.ui_thread = None
        self.ui_ready = threading.Event()
        
        # Callbacks
        self.suggestion_callback = None
        self.close_callback = None
        
        logger.info("🎨 Overlay UI d'autocomplétion initialisé")
    
    def initialize(self):
        """Initialise l'interface utilisateur"""
        if not UI_AVAILABLE:
            logger.error("❌ Modules UI non disponibles")
            return False
        
        try:
            # Démarrer l'interface dans un thread séparé
            self.ui_thread = threading.Thread(target=self._run_ui, daemon=True)
            self.ui_thread.start()
            
            # Attendre que l'UI soit prête
            if self.ui_ready.wait(timeout=5.0):
                logger.success("✅ Overlay UI prêt")
                return True
            else:
                logger.error("❌ Timeout initialisation UI")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur initialisation UI: {e}")
            return False
    
    def _run_ui(self):
        """Exécute l'interface utilisateur dans son thread"""
        try:
            # Créer la fenêtre principale
            self.root = tk.Tk()
            self.root.withdraw()  # Cacher initialement
            
            # Configuration de la fenêtre
            self.root.title("JARVIS Autocomplete")
            self.root.geometry(f"{self.config.width}x{self.config.height}")
            self.root.configure(bg=self.config.background_color)
            
            # Supprimer les décorations de fenêtre
            self.root.overrideredirect(True)
            
            # Toujours au-dessus
            self.root.attributes('-topmost', True)
            
            # Transparence (Windows)
            try:
                self.root.attributes('-alpha', self.config.opacity)
            except:
                pass  # Pas supporté sur tous les systèmes
            
            # Créer le canvas pour le dessin personnalisé
            self.canvas = tk.Canvas(
                self.root,
                width=self.config.width,
                height=self.config.height,
                bg=self.config.background_color,
                highlightthickness=0,
                bd=0
            )
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            # Événements clavier
            self.root.bind('<Key>', self._on_key_press)
            self.root.bind('<Escape>', lambda e: self.hide())
            self.root.bind('<Return>', lambda e: self._accept_selected())
            self.root.bind('<Up>', lambda e: self._move_selection(-1))
            self.root.bind('<Down>', lambda e: self._move_selection(1))
            self.root.bind('<Tab>', lambda e: self._accept_selected())
            
            # Focus pour capturer les événements clavier
            self.root.focus_set()
            
            # Signaler que l'UI est prête
            self.ui_ready.set()
            
            # Démarrer la boucle principale
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"❌ Erreur thread UI: {e}")
            self.ui_ready.set()  # Signaler même en cas d'erreur
    
    def show_suggestions(self, suggestions: List[str], cursor_pos: Tuple[int, int]):
        """Affiche les suggestions à la position donnée"""
        if not self.root:
            return
        
        try:
            self.current_suggestions = suggestions
            self.selected_index = 0
            self.cursor_position = cursor_pos
            
            # Calculer la position de la fenêtre
            x, y = self._calculate_window_position(cursor_pos)
            
            # Ajuster la taille en fonction du nombre de suggestions
            height = min(
                len(suggestions) * self.config.item_height + self.config.padding * 2,
                self.config.height
            )
            
            # Programmer l'affichage dans le thread UI
            self.root.after(0, lambda: self._show_window(x, y, height))
            
        except Exception as e:
            logger.error(f"❌ Erreur affichage suggestions: {e}")
    
    def _show_window(self, x: int, y: int, height: int):
        """Affiche la fenêtre à la position spécifiée"""
        try:
            # Positionner et redimensionner
            self.root.geometry(f"{self.config.width}x{height}+{x}+{y}")
            
            # Dessiner le contenu
            self._draw_suggestions()
            
            # Afficher avec animation
            if not self.is_visible:
                self._animate_show()
            
            # Programmer la disparition automatique
            self._schedule_auto_hide()
            
        except Exception as e:
            logger.error(f"❌ Erreur affichage fenêtre: {e}")
    
    def _calculate_window_position(self, cursor_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Calcule la position optimale de la fenêtre"""
        cursor_x, cursor_y = cursor_pos
        
        # Obtenir la taille de l'écran
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
        except:
            screen_width, screen_height = 1920, 1080  # Valeurs par défaut
        
        # Position de base: en dessous du curseur
        x = cursor_x
        y = cursor_y + 20  # Offset pour ne pas cacher le curseur
        
        # Ajustements pour rester dans l'écran
        if x + self.config.width > screen_width:
            x = screen_width - self.config.width - 10
        
        if y + self.config.height > screen_height:
            y = cursor_y - self.config.height - 10  # Au-dessus du curseur
        
        # S'assurer que c'est dans les limites
        x = max(10, x)
        y = max(10, y)
        
        return (x, y)
    
    def _draw_suggestions(self):
        """Dessine les suggestions sur le canvas"""
        if not self.canvas:
            return
        
        try:
            # Effacer le canvas
            self.canvas.delete("all")
            
            # Dessiner le fond avec bordure arrondie
            self._draw_rounded_rectangle(
                0, 0, self.config.width, 
                len(self.current_suggestions) * self.config.item_height + self.config.padding * 2,
                self.config.border_radius,
                fill=self.config.background_color,
                outline=self.config.border_color
            )
            
            # Dessiner chaque suggestion
            for i, suggestion in enumerate(self.current_suggestions):
                y_pos = self.config.padding + i * self.config.item_height
                
                # Fond de l'élément sélectionné
                if i == self.selected_index:
                    self.canvas.create_rectangle(
                        self.config.padding // 2,
                        y_pos - 2,
                        self.config.width - self.config.padding // 2,
                        y_pos + self.config.item_height - 2,
                        fill=self.config.selected_color,
                        outline="",
                        tags="selection"
                    )
                
                # Texte de la suggestion
                text_color = "#FFFFFF" if i == self.selected_index else self.config.text_color
                
                self.canvas.create_text(
                    self.config.padding,
                    y_pos + self.config.item_height // 2,
                    text=suggestion,
                    fill=text_color,
                    font=(self.config.font_family, self.config.font_size),
                    anchor="w",
                    tags="suggestion"
                )
                
                # Numéro de l'option (raccourci)
                self.canvas.create_text(
                    self.config.width - self.config.padding,
                    y_pos + self.config.item_height // 2,
                    text=str(i + 1),
                    fill="#888888",
                    font=(self.config.font_family, self.config.font_size - 2),
                    anchor="e",
                    tags="number"
                )
            
        except Exception as e:
            logger.error(f"❌ Erreur dessin suggestions: {e}")
    
    def _draw_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Dessine un rectangle avec des coins arrondis"""
        points = []
        
        # Coin supérieur gauche
        points.extend([x1, y1 + radius])
        points.extend([x1, y1 + radius])
        points.extend([x1 + radius, y1])
        
        # Côté supérieur
        points.extend([x2 - radius, y1])
        
        # Coin supérieur droit
        points.extend([x2, y1])
        points.extend([x2, y1 + radius])
        
        # Côté droit
        points.extend([x2, y2 - radius])
        
        # Coin inférieur droit
        points.extend([x2, y2])
        points.extend([x2 - radius, y2])
        
        # Côté inférieur
        points.extend([x1 + radius, y2])
        
        # Coin inférieur gauche
        points.extend([x1, y2])
        points.extend([x1, y2 - radius])
        
        # Fermer
        points.extend([x1, y1 + radius])
        
        return self.canvas.create_polygon(points, smooth=True, **kwargs)
    
    def _animate_show(self):
        """Animation d'apparition"""
        if not self.root:
            return
        
        try:
            self.root.deiconify()  # Afficher la fenêtre
            self.is_visible = True
            
            # Animation de fondu (si supportée)
            if hasattr(self.root, 'attributes'):
                steps = 10
                target_alpha = self.config.opacity
                
                def fade_step(step):
                    if step <= steps and self.is_visible:
                        alpha = (step / steps) * target_alpha
                        try:
                            self.root.attributes('-alpha', alpha)
                            self.root.after(int(self.config.animation_duration * 1000 / steps), 
                                          lambda: fade_step(step + 1))
                        except:
                            pass  # Ignoré si non supporté
                
                self.root.attributes('-alpha', 0)
                fade_step(1)
            
        except Exception as e:
            logger.error(f"❌ Erreur animation: {e}")
    
    def hide(self):
        """Cache l'overlay"""
        if not self.root or not self.is_visible:
            return
        
        try:
            self.root.after(0, self._hide_window)
        except Exception as e:
            logger.error(f"❌ Erreur masquage: {e}")
    
    def _hide_window(self):
        """Cache la fenêtre"""
        try:
            self.is_visible = False
            self.root.withdraw()
            
            # Annuler les timers
            if self.auto_hide_timer:
                self.root.after_cancel(self.auto_hide_timer)
                self.auto_hide_timer = None
            
        except Exception as e:
            logger.error(f"❌ Erreur masquage fenêtre: {e}")
    
    def _schedule_auto_hide(self):
        """Programme la disparition automatique"""
        # Annuler le timer précédent
        if self.auto_hide_timer:
            self.root.after_cancel(self.auto_hide_timer)
        
        # Programmer la disparition
        self.auto_hide_timer = self.root.after(
            int(self.config.auto_hide_delay * 1000),
            self.hide
        )
    
    def _move_selection(self, direction: int):
        """Déplace la sélection"""
        if not self.current_suggestions:
            return
        
        old_index = self.selected_index
        self.selected_index = (self.selected_index + direction) % len(self.current_suggestions)
        
        if old_index != self.selected_index:
            self._draw_suggestions()
    
    def _accept_selected(self):
        """Accepte la suggestion sélectionnée"""
        if self.current_suggestions and 0 <= self.selected_index < len(self.current_suggestions):
            selected_suggestion = self.current_suggestions[self.selected_index]
            
            # Notifier via callback
            if self.suggestion_callback:
                try:
                    self.suggestion_callback(selected_suggestion, self.selected_index)
                except Exception as e:
                    logger.error(f"❌ Erreur callback suggestion: {e}")
            
            # Cacher l'overlay
            self.hide()
    
    def _on_key_press(self, event):
        """Gestionnaire d'événements clavier"""
        try:
            # Chiffres pour sélection directe
            if event.char.isdigit():
                index = int(event.char) - 1
                if 0 <= index < len(self.current_suggestions):
                    self.selected_index = index
                    self._accept_selected()
            
        except Exception as e:
            logger.debug(f"Erreur événement clavier: {e}")
    
    def set_suggestion_callback(self, callback):
        """Définit le callback pour les suggestions acceptées"""
        self.suggestion_callback = callback
    
    def set_close_callback(self, callback):
        """Définit le callback pour la fermeture"""
        self.close_callback = callback
    
    def update_cursor_position(self, cursor_pos: Tuple[int, int]):
        """Met à jour la position du curseur"""
        self.cursor_position = cursor_pos
        
        if self.is_visible:
            # Repositionner la fenêtre
            x, y = self._calculate_window_position(cursor_pos)
            if self.root:
                self.root.after(0, lambda: self.root.geometry(f"+{x}+{y}"))
    
    def shutdown(self):
        """Arrête l'interface utilisateur"""
        if self.root:
            try:
                self.root.after(0, self.root.destroy)
            except:
                pass
        
        if self.ui_thread and self.ui_thread.is_alive():
            self.ui_thread.join(timeout=1.0)

# Fonction utilitaire pour obtenir la position du curseur
def get_cursor_position() -> Tuple[int, int]:
    """Récupère la position actuelle du curseur"""
    try:
        if UI_AVAILABLE:
            cursor_info = win32gui.GetCursorPos()
            return cursor_info
        else:
            return (100, 100)  # Position par défaut
    except Exception:
        return (100, 100)

# Fonction de test
async def test_overlay_ui():
    """Test de l'interface overlay"""
    if not UI_AVAILABLE:
        logger.error("❌ Interface UI non disponible pour le test")
        return False
    
    try:
        overlay = OverlayUI()
        
        if not overlay.initialize():
            return False
        
        # Callback de test
        def on_suggestion_accepted(suggestion, index):
            logger.info(f"✅ Suggestion acceptée: '{suggestion}' (index {index})")
        
        overlay.set_suggestion_callback(on_suggestion_accepted)
        
        # Test d'affichage
        test_suggestions = [
            "application",
            "développement", 
            "programmation",
            "intelligence",
            "automatisation"
        ]
        
        cursor_pos = get_cursor_position()
        logger.info(f"🧪 Test overlay à la position {cursor_pos}")
        
        overlay.show_suggestions(test_suggestions, cursor_pos)
        
        # Attendre un peu pour voir l'overlay
        await asyncio.sleep(10)
        
        overlay.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test overlay: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_overlay_ui())