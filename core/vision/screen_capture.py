"""
Module de capture d'écran optimisé pour JARVIS
Capture intelligente avec cache et compression
"""
import asyncio
import io
import time
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from PIL import Image, ImageGrab
import cv2
import numpy as np
from loguru import logger
import hashlib
from pathlib import Path

@dataclass
class ScreenRegion:
    """Définit une région de l'écran"""
    x: int
    y: int
    width: int
    height: int
    name: str = ""
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Retourne la bounding box PIL (left, top, right, bottom)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

@dataclass
class Screenshot:
    """Représente une capture d'écran"""
    image: Image.Image
    timestamp: float
    region: Optional[ScreenRegion] = None
    hash: Optional[str] = None
    
    def __post_init__(self):
        if self.hash is None:
            self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calcule le hash de l'image pour détecter les changements"""
        img_bytes = io.BytesIO()
        self.image.save(img_bytes, format='PNG')
        return hashlib.md5(img_bytes.getvalue()).hexdigest()
    
    def save(self, path: str) -> bool:
        """Sauvegarde la capture"""
        try:
            self.image.save(path)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def resize(self, max_width: int = 1920, max_height: int = 1080) -> 'Screenshot':
        """Redimensionne l'image en conservant le ratio"""
        width, height = self.image.size
        
        if width <= max_width and height <= max_height:
            return self
        
        ratio = min(max_width / width, max_height / height)
        new_size = (int(width * ratio), int(height * ratio))
        
        resized_image = self.image.resize(new_size, Image.Resampling.LANCZOS)
        
        return Screenshot(
            image=resized_image,
            timestamp=self.timestamp,
            region=self.region,
            hash=None  # Recalculé automatiquement
        )

class ScreenCache:
    """Cache intelligent pour les captures d'écran"""
    
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.cache: Dict[str, Screenshot] = {}
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Screenshot]:
        """Récupère une capture du cache"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def put(self, key: str, screenshot: Screenshot):
        """Ajoute une capture au cache"""
        # Nettoyage si nécessaire
        if len(self.cache) >= self.max_size:
            self._cleanup()
        
        self.cache[key] = screenshot
        self.access_times[key] = time.time()
    
    def _cleanup(self):
        """Nettoie le cache en supprimant les plus anciens"""
        if not self.access_times:
            return
        
        # Garder les 80% les plus récents
        keep_count = int(self.max_size * 0.8)
        sorted_items = sorted(self.access_times.items(), key=lambda x: x[1], reverse=True)
        
        for key, _ in sorted_items[keep_count:]:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def has_changed(self, key: str, current_hash: str) -> bool:
        """Vérifie si l'écran a changé depuis la dernière capture"""
        cached = self.get(key)
        return cached is None or cached.hash != current_hash

class ScreenCapture:
    """Module principal de capture d'écran"""
    
    def __init__(self):
        self.cache = ScreenCache()
        self.last_screenshot: Optional[Screenshot] = None
        self.monitors: List[Dict[str, Any]] = []
        self.default_region: Optional[ScreenRegion] = None
        
        # Configuration
        self.compression_quality = 85
        self.max_resolution = (1920, 1080)
        self.change_threshold = 0.05  # 5% de pixels différents = changement
        
        logger.info("📸 Module ScreenCapture initialisé")
    
    async def initialize(self):
        """Initialise le module de capture"""
        try:
            await self.detect_monitors()
            await self.set_default_region()
            logger.success("✅ ScreenCapture initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation ScreenCapture: {e}")
            raise
    
    async def detect_monitors(self):
        """Détecte les moniteurs disponibles"""
        try:
            # Pour l'instant, utilise le moniteur principal
            # TODO: Implémenter la détection multi-moniteurs avec win32api sur Windows
            screen_size = ImageGrab.grab().size
            self.monitors = [{
                'id': 0,
                'primary': True,
                'width': screen_size[0],
                'height': screen_size[1],
                'x': 0,
                'y': 0
            }]
            logger.info(f"📺 Moniteur détecté: {screen_size[0]}x{screen_size[1]}")
        except Exception as e:
            logger.error(f"Erreur détection moniteurs: {e}")
            # Valeurs par défaut
            self.monitors = [{'id': 0, 'primary': True, 'width': 1920, 'height': 1080, 'x': 0, 'y': 0}]
    
    async def set_default_region(self):
        """Définit la région par défaut (écran complet)"""
        if self.monitors:
            primary = next((m for m in self.monitors if m.get('primary')), self.monitors[0])
            self.default_region = ScreenRegion(
                x=primary['x'],
                y=primary['y'],
                width=primary['width'],
                height=primary['height'],
                name="full_screen"
            )
    
    async def capture(self, region: Optional[ScreenRegion] = None, 
                     use_cache: bool = True) -> Optional[Screenshot]:
        """Capture une région de l'écran"""
        try:
            region = region or self.default_region
            if not region:
                logger.error("Aucune région définie pour la capture")
                return None
            
            cache_key = f"{region.x}_{region.y}_{region.width}_{region.height}"
            
            # Capture rapide pour vérifier les changements
            if use_cache:
                quick_capture = ImageGrab.grab(bbox=region.bbox)
                quick_hash = hashlib.md5(quick_capture.tobytes()).hexdigest()
                
                if not self.cache.has_changed(cache_key, quick_hash):
                    cached = self.cache.get(cache_key)
                    if cached:
                        logger.debug("📸 Capture récupérée du cache")
                        return cached
            
            # Nouvelle capture
            start_time = time.time()
            image = ImageGrab.grab(bbox=region.bbox)
            
            screenshot = Screenshot(
                image=image,
                timestamp=time.time(),
                region=region
            )
            
            # Redimensionner si nécessaire
            if image.size[0] > self.max_resolution[0] or image.size[1] > self.max_resolution[1]:
                screenshot = screenshot.resize(*self.max_resolution)
            
            # Mise en cache
            if use_cache:
                self.cache.put(cache_key, screenshot)
            
            self.last_screenshot = screenshot
            
            capture_time = (time.time() - start_time) * 1000
            logger.debug(f"📸 Capture effectuée en {capture_time:.1f}ms - {image.size}")
            
            return screenshot
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la capture: {e}")
            return None
    
    async def capture_window(self, window_title: str) -> Optional[Screenshot]:
        """Capture une fenêtre spécifique par son titre"""
        # TODO: Implémenter la capture de fenêtre spécifique
        # Nécessite pywin32 sur Windows pour GetWindowRect
        logger.warning("Capture de fenêtre spécifique pas encore implémentée")
        return await self.capture()
    
    async def capture_region_by_name(self, region_name: str) -> Optional[Screenshot]:
        """Capture une région prédéfinie par nom"""
        regions = {
            "taskbar": ScreenRegion(0, -40, 1920, 40, "taskbar"),
            "desktop": self.default_region,
            "top_half": ScreenRegion(0, 0, 1920, 540, "top_half"),
            "bottom_half": ScreenRegion(0, 540, 1920, 540, "bottom_half")
        }
        
        region = regions.get(region_name)
        if not region:
            logger.warning(f"Région '{region_name}' non trouvée")
            return None
        
        return await self.capture(region)
    
    def has_screen_changed(self, threshold: float = None) -> bool:
        """Vérifie si l'écran a changé depuis la dernière capture"""
        if not self.last_screenshot:
            return True
        
        threshold = threshold or self.change_threshold
        
        try:
            current = ImageGrab.grab(bbox=self.last_screenshot.region.bbox if self.last_screenshot.region else None)
            
            # Redimensionner pour comparaison rapide
            if current.size != self.last_screenshot.image.size:
                current = current.resize(self.last_screenshot.image.size)
            
            # Convertir en arrays numpy pour comparaison
            current_array = np.array(current)
            last_array = np.array(self.last_screenshot.image)
            
            # Calculer le pourcentage de pixels différents
            diff = np.sum(current_array != last_array) / current_array.size
            
            return diff > threshold
            
        except Exception as e:
            logger.error(f"Erreur lors de la comparaison: {e}")
            return True
    
    async def continuous_capture(self, interval: float = 1.0, 
                               callback=None) -> None:
        """Capture continue avec callback"""
        logger.info(f"🔄 Capture continue démarrée (intervalle: {interval}s)")
        
        try:
            while True:
                if self.has_screen_changed():
                    screenshot = await self.capture()
                    if screenshot and callback:
                        await callback(screenshot)
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            logger.info("⏹️  Capture continue arrêtée")
        except Exception as e:
            logger.error(f"❌ Erreur capture continue: {e}")
    
    def get_screen_info(self) -> Dict[str, Any]:
        """Retourne les informations sur l'écran"""
        return {
            "monitors": self.monitors,
            "default_region": {
                "x": self.default_region.x,
                "y": self.default_region.y,
                "width": self.default_region.width,
                "height": self.default_region.height
            } if self.default_region else None,
            "cache_size": len(self.cache.cache),
            "last_capture": self.last_screenshot.timestamp if self.last_screenshot else None
        }
    
    async def save_screenshot(self, filename: str, region: Optional[ScreenRegion] = None) -> bool:
        """Capture et sauvegarde une capture d'écran"""
        screenshot = await self.capture(region, use_cache=False)
        if screenshot:
            # Créer le dossier si nécessaire
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            return screenshot.save(filename)
        return False

# Fonctions utilitaires
def create_region(x: int, y: int, width: int, height: int, name: str = "") -> ScreenRegion:
    """Crée une région d'écran"""
    return ScreenRegion(x, y, width, height, name)

async def quick_screenshot(save_path: Optional[str] = None) -> Optional[Screenshot]:
    """Capture rapide de l'écran complet"""
    capture = ScreenCapture()
    await capture.initialize()
    
    screenshot = await capture.capture(use_cache=False)
    
    if screenshot and save_path:
        screenshot.save(save_path)
        logger.info(f"📸 Capture sauvegardée: {save_path}")
    
    return screenshot

if __name__ == "__main__":
    async def test_capture():
        capture = ScreenCapture()
        await capture.initialize()
        
        # Test de capture
        screenshot = await capture.capture()
        if screenshot:
            print(f"✅ Capture réussie: {screenshot.image.size}")
            screenshot.save("test_capture.png")
        
        # Test de détection de changement
        print(f"Écran changé: {capture.has_screen_changed()}")
    
    asyncio.run(test_capture())