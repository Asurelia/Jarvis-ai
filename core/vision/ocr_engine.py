"""
Module OCR optimisé pour JARVIS
Combine Tesseract et EasyOCR avec cache intelligent
"""
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import pytesseract
import easyocr
import cv2
import numpy as np
from loguru import logger
import hashlib
import json
from pathlib import Path

@dataclass
class OCRResult:
    """Résultat d'une reconnaissance OCR"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    engine: str  # "tesseract" ou "easyocr"
    language: str = "fr"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bbox": self.bbox,
            "engine": self.engine,
            "language": self.language
        }

@dataclass
class OCRFullResult:
    """Résultat complet d'une analyse OCR"""
    all_text: str
    words: List[OCRResult]
    lines: List[str]
    confidence_avg: float
    processing_time: float
    image_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "all_text": self.all_text,
            "words": [word.to_dict() for word in self.words],
            "lines": self.lines,
            "confidence_avg": self.confidence_avg,
            "processing_time": self.processing_time,
            "image_hash": self.image_hash
        }

class OCRCache:
    """Cache intelligent pour les résultats OCR"""
    
    def __init__(self, max_size: int = 100, cache_file: str = "cache/ocr_cache.json"):
        self.max_size = max_size
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        
        self._load_cache()
    
    def _load_cache(self):
        """Charge le cache depuis le fichier"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = data.get('cache', {})
                    self.access_times = data.get('access_times', {})
                logger.info(f"📋 Cache OCR chargé: {len(self.cache)} entrées")
        except Exception as e:
            logger.warning(f"Erreur chargement cache OCR: {e}")
            self.cache = {}
            self.access_times = {}
    
    def _save_cache(self):
        """Sauvegarde le cache dans le fichier"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'cache': self.cache,
                    'access_times': self.access_times
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache OCR: {e}")
    
    def get(self, image_hash: str) -> Optional[OCRFullResult]:
        """Récupère un résultat du cache"""
        if image_hash in self.cache:
            self.access_times[image_hash] = time.time()
            data = self.cache[image_hash]
            
            # Reconstituer l'objet OCRFullResult
            words = [OCRResult(**word_data) for word_data in data['words']]
            result = OCRFullResult(
                all_text=data['all_text'],
                words=words,
                lines=data['lines'],
                confidence_avg=data['confidence_avg'],
                processing_time=data['processing_time'],
                image_hash=data['image_hash']
            )
            return result
        return None
    
    def put(self, image_hash: str, result: OCRFullResult):
        """Ajoute un résultat au cache"""
        if len(self.cache) >= self.max_size:
            self._cleanup()
        
        self.cache[image_hash] = result.to_dict()
        self.access_times[image_hash] = time.time()
        
        # Sauvegarde périodique
        if len(self.cache) % 10 == 0:
            self._save_cache()
    
    def _cleanup(self):
        """Nettoie le cache"""
        if not self.access_times:
            return
        
        keep_count = int(self.max_size * 0.8)
        sorted_items = sorted(self.access_times.items(), key=lambda x: x[1], reverse=True)
        
        for key, _ in sorted_items[keep_count:]:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def save(self):
        """Force la sauvegarde du cache"""
        self._save_cache()

class TesseractEngine:
    """Moteur Tesseract pour OCR"""
    
    def __init__(self):
        self.config = "--oem 3 --psm 6"  # LSTM OCR Engine + Uniform text block
        self.languages = ['fra', 'eng']  # Français + Anglais
        
    def extract_text(self, image: Image.Image, language: str = 'fra+eng') -> OCRFullResult:
        """Extraction de texte avec Tesseract"""
        start_time = time.time()
        
        try:
            # Conversion en numpy array pour preprocessing
            img_array = np.array(image)
            
            # Preprocessing pour améliorer la reconnaissance
            img_array = self._preprocess_image(img_array)
            
            # OCR avec données détaillées
            data = pytesseract.image_to_data(
                img_array, 
                lang=language, 
                config=self.config, 
                output_type=pytesseract.Output.DICT
            )
            
            # Extraction du texte complet
            all_text = pytesseract.image_to_string(
                img_array, 
                lang=language, 
                config=self.config
            ).strip()
            
            # Traitement des résultats détaillés
            words = []
            confidences = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text and int(data['conf'][i]) > 0:
                    bbox = (
                        data['left'][i],
                        data['top'][i],
                        data['width'][i],
                        data['height'][i]
                    )
                    
                    word_result = OCRResult(
                        text=text,
                        confidence=float(data['conf'][i]) / 100.0,
                        bbox=bbox,
                        engine="tesseract",
                        language=language
                    )
                    
                    words.append(word_result)
                    confidences.append(word_result.confidence)
            
            # Lignes de texte
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Confiance moyenne
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            image_hash = hashlib.md5(image.tobytes()).hexdigest()
            
            return OCRFullResult(
                all_text=all_text,
                words=words,
                lines=lines,
                confidence_avg=avg_confidence,
                processing_time=processing_time,
                image_hash=image_hash
            )
            
        except Exception as e:
            logger.error(f"Erreur Tesseract OCR: {e}")
            return OCRFullResult(
                all_text="",
                words=[],
                lines=[],
                confidence_avg=0.0,
                processing_time=time.time() - start_time,
                image_hash=hashlib.md5(image.tobytes()).hexdigest()
            )
    
    def _preprocess_image(self, img_array: np.ndarray) -> np.ndarray:
        """Preprocessing de l'image pour améliorer l'OCR"""
        # Conversion en niveaux de gris si nécessaire
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Amélioration du contraste
        img_array = cv2.convertScaleAbs(img_array, alpha=1.2, beta=10)
        
        # Débruitage
        img_array = cv2.fastNlMeansDenoising(img_array)
        
        # Binarisation adaptative pour améliorer la lisibilité
        img_array = cv2.adaptiveThreshold(
            img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return img_array

class EasyOCREngine:
    """Moteur EasyOCR pour OCR"""
    
    def __init__(self):
        self.reader = None
        self.languages = ['fr', 'en']
        
    async def initialize(self):
        """Initialise EasyOCR (peut être lent au premier démarrage)"""
        try:
            logger.info("🔄 Initialisation EasyOCR...")
            self.reader = easyocr.Reader(self.languages, gpu=True)  # Essaie GPU d'abord
            logger.success("✅ EasyOCR initialisé avec GPU")
        except Exception as e:
            logger.warning(f"GPU non disponible pour EasyOCR, fallback CPU: {e}")
            try:
                self.reader = easyocr.Reader(self.languages, gpu=False)
                logger.success("✅ EasyOCR initialisé avec CPU")
            except Exception as e2:
                logger.error(f"❌ Erreur initialisation EasyOCR: {e2}")
                raise
    
    def extract_text(self, image: Image.Image) -> OCRFullResult:
        """Extraction de texte avec EasyOCR"""
        if not self.reader:
            raise RuntimeError("EasyOCR non initialisé")
        
        start_time = time.time()
        
        try:
            # Conversion en numpy array
            img_array = np.array(image)
            
            # OCR avec EasyOCR
            results = self.reader.readtext(img_array)
            
            # Traitement des résultats
            words = []
            all_text_parts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if text.strip() and confidence > 0.1:  # Seuil de confiance minimum
                    # Conversion bbox EasyOCR vers format standard
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    
                    x, y = int(min(x_coords)), int(min(y_coords))
                    width = int(max(x_coords) - min(x_coords))
                    height = int(max(y_coords) - min(y_coords))
                    
                    word_result = OCRResult(
                        text=text.strip(),
                        confidence=confidence,
                        bbox=(x, y, width, height),
                        engine="easyocr",
                        language="auto"
                    )
                    
                    words.append(word_result)
                    all_text_parts.append(text.strip())
                    confidences.append(confidence)
            
            # Texte complet
            all_text = ' '.join(all_text_parts)
            
            # Lignes (approximation basée sur la position Y)
            words_sorted = sorted(words, key=lambda w: w.bbox[1])  # Tri par Y
            lines = []
            current_line = []
            last_y = -1
            line_threshold = 20  # Pixels de tolérance pour les lignes
            
            for word in words_sorted:
                if last_y == -1 or abs(word.bbox[1] - last_y) <= line_threshold:
                    current_line.append(word.text)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word.text]
                last_y = word.bbox[1]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Confiance moyenne
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            image_hash = hashlib.md5(image.tobytes()).hexdigest()
            
            return OCRFullResult(
                all_text=all_text,
                words=words,
                lines=lines,
                confidence_avg=avg_confidence,
                processing_time=processing_time,
                image_hash=image_hash
            )
            
        except Exception as e:
            logger.error(f"Erreur EasyOCR: {e}")
            return OCRFullResult(
                all_text="",
                words=[],
                lines=[],
                confidence_avg=0.0,
                processing_time=time.time() - start_time,
                image_hash=hashlib.md5(image.tobytes()).hexdigest()
            )

class OCREngine:
    """Moteur OCR principal combinant Tesseract et EasyOCR"""
    
    def __init__(self, use_cache: bool = True):
        self.tesseract = TesseractEngine()
        self.easyocr = EasyOCREngine()
        self.cache = OCRCache() if use_cache else None
        self.fallback_engine = "tesseract"  # Moteur de fallback
        
        logger.info("🔍 Moteur OCR initialisé")
    
    async def initialize(self):
        """Initialise tous les moteurs OCR"""
        try:
            # Vérifier Tesseract
            try:
                pytesseract.get_tesseract_version()
                logger.success("✅ Tesseract disponible")
            except Exception as e:
                logger.error(f"❌ Tesseract non disponible: {e}")
                raise
            
            # Initialiser EasyOCR
            await self.easyocr.initialize()
            
            logger.success("✅ Moteur OCR complètement initialisé")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation OCR: {e}")
            raise
    
    async def extract_text(self, image: Image.Image, 
                          engine: str = "auto", 
                          use_cache: bool = True) -> OCRFullResult:
        """
        Extraction de texte depuis une image
        
        Args:
            image: Image PIL
            engine: "tesseract", "easyocr", "auto" ou "both"
            use_cache: Utiliser le cache
        """
        # Vérification du cache
        image_hash = hashlib.md5(image.tobytes()).hexdigest()
        
        if use_cache and self.cache:
            cached_result = self.cache.get(image_hash)
            if cached_result:
                logger.debug("🔍 Résultat OCR récupéré du cache")
                return cached_result
        
        try:
            result = None
            
            if engine == "tesseract":
                result = self.tesseract.extract_text(image)
            
            elif engine == "easyocr":
                result = self.easyocr.extract_text(image)
            
            elif engine == "both":
                # Utiliser les deux moteurs et combiner
                result = await self._combine_engines(image)
            
            elif engine == "auto":
                # Choix automatique du meilleur moteur
                result = await self._auto_select_engine(image)
            
            else:
                raise ValueError(f"Moteur OCR non reconnu: {engine}")
            
            # Mise en cache
            if result and use_cache and self.cache:
                self.cache.put(image_hash, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction OCR: {e}")
            # Fallback vers le moteur par défaut
            if engine != self.fallback_engine:
                logger.info(f"🔄 Fallback vers {self.fallback_engine}")
                return await self.extract_text(image, self.fallback_engine, use_cache)
            
            # Retourner un résultat vide en cas d'échec total
            return OCRFullResult(
                all_text="",
                words=[],
                lines=[],
                confidence_avg=0.0,
                processing_time=0.0,
                image_hash=image_hash
            )
    
    async def _auto_select_engine(self, image: Image.Image) -> OCRFullResult:
        """Sélection automatique du meilleur moteur"""
        # Pour l'instant, privilégier EasyOCR pour sa robustesse
        # TODO: Implémenter une logique plus sophistiquée basée sur le type d'image
        try:
            return self.easyocr.extract_text(image)
        except Exception:
            logger.warning("🔄 EasyOCR échoué, fallback vers Tesseract")
            return self.tesseract.extract_text(image)
    
    async def _combine_engines(self, image: Image.Image) -> OCRFullResult:
        """Combine les résultats des deux moteurs"""
        # Exécuter les deux moteurs
        tesseract_result = self.tesseract.extract_text(image)
        easyocr_result = self.easyocr.extract_text(image)
        
        # Choisir le meilleur résultat basé sur la confiance
        if tesseract_result.confidence_avg > easyocr_result.confidence_avg:
            best_result = tesseract_result
            logger.debug("🔍 Tesseract sélectionné (meilleure confiance)")
        else:
            best_result = easyocr_result
            logger.debug("🔍 EasyOCR sélectionné (meilleure confiance)")
        
        # TODO: Implémenter une fusion plus sophistiquée des résultats
        return best_result
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du moteur OCR"""
        stats = {
            "cache_size": len(self.cache.cache) if self.cache else 0,
            "tesseract_available": True,  # Déjà vérifié à l'initialisation
            "easyocr_available": self.easyocr.reader is not None
        }
        return stats
    
    def save_cache(self):
        """Sauvegarde le cache OCR"""
        if self.cache:
            self.cache.save()
            logger.info("💾 Cache OCR sauvegardé")

# Fonctions utilitaires
async def quick_ocr(image: Image.Image, engine: str = "auto") -> str:
    """OCR rapide pour récupérer juste le texte"""
    ocr_engine = OCREngine()
    await ocr_engine.initialize()
    
    result = await ocr_engine.extract_text(image, engine)
    return result.all_text

async def analyze_text_regions(image: Image.Image) -> List[OCRResult]:
    """Analyse détaillée des régions de texte"""
    ocr_engine = OCREngine()
    await ocr_engine.initialize()
    
    result = await ocr_engine.extract_text(image, "both")
    return result.words

if __name__ == "__main__":
    async def test_ocr():
        from core.vision.screen_capture import quick_screenshot
        
        # Test avec une capture d'écran
        screenshot = await quick_screenshot()
        if screenshot:
            ocr_engine = OCREngine()
            await ocr_engine.initialize()
            
            result = await ocr_engine.extract_text(screenshot.image, "auto")
            
            print(f"✅ Texte extrait ({result.confidence_avg:.1%} confiance):")
            print(result.all_text[:200] + "..." if len(result.all_text) > 200 else result.all_text)
            print(f"📊 {len(result.words)} mots détectés en {result.processing_time:.2f}s")
    
    asyncio.run(test_ocr())