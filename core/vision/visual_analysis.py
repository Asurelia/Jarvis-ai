"""
Module d'analyse visuelle pour JARVIS
Intégration avec Ollama LLaVA pour la compréhension sémantique des images
"""
import asyncio
import base64
import io
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import numpy as np
import cv2
from loguru import logger
import json
import ollama

@dataclass
class UIElement:
    """Représente un élément d'interface utilisateur détecté"""
    type: str  # "button", "text", "input", "menu", etc.
    text: str
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    clickable: bool = False
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}

@dataclass
class VisualAnalysisResult:
    """Résultat d'une analyse visuelle complète"""
    description: str
    ui_elements: List[UIElement]
    scene_type: str  # "desktop", "browser", "application", etc.
    dominant_colors: List[Tuple[int, int, int]]
    text_regions: List[Dict[str, Any]]
    actions_suggested: List[str]
    confidence: float
    processing_time: float

class UIElementDetector:
    """Détecteur d'éléments d'interface utilisateur"""
    
    def __init__(self):
        self.button_cascade = None
        self.text_detector = cv2.dnn.readNet  # Placeholder pour un modèle de détection de texte
        
    def detect_buttons(self, image: np.ndarray) -> List[UIElement]:
        """Détecte les boutons dans l'image"""
        buttons = []
        
        # Conversion en niveaux de gris
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # Détection de contours pour les boutons rectangulaires
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Approximation polygonale
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Vérifier si c'est approximativement rectangulaire
            if len(approx) >= 4:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filtres pour les boutons probables
                if 30 < w < 300 and 20 < h < 80 and w > h:
                    area = cv2.contourArea(contour)
                    rect_area = w * h
                    
                    # Ratio de remplissage pour éliminer les formes trop irrégulières
                    if area / rect_area > 0.7:
                        button = UIElement(
                            type="button",
                            text="",  # Sera rempli par OCR
                            bbox=(x, y, w, h),
                            confidence=0.7,
                            clickable=True
                        )
                        buttons.append(button)
        
        return buttons
    
    def detect_text_fields(self, image: np.ndarray) -> List[UIElement]:
        """Détecte les champs de saisie"""
        text_fields = []
        
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # Détection de rectangles allongés horizontalement (champs de saisie typiques)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Caractéristiques typiques d'un champ de saisie
            if 100 < w < 500 and 20 < h < 40 and w / h > 3:
                # Vérifier si le rectangle est bien défini
                area = cv2.contourArea(contour)
                rect_area = w * h
                
                if area / rect_area > 0.8:
                    text_field = UIElement(
                        type="input",
                        text="",
                        bbox=(x, y, w, h),
                        confidence=0.6,
                        clickable=True
                    )
                    text_fields.append(text_field)
        
        return text_fields
    
    def detect_all_elements(self, image: np.ndarray) -> List[UIElement]:
        """Détecte tous les éléments d'interface"""
        elements = []
        
        # Détecter différents types d'éléments
        elements.extend(self.detect_buttons(image))
        elements.extend(self.detect_text_fields(image))
        
        # Éliminer les doublons (éléments qui se chevauchent trop)
        elements = self._remove_overlapping_elements(elements)
        
        return elements
    
    def _remove_overlapping_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Supprime les éléments qui se chevauchent trop"""
        if not elements:
            return elements
        
        filtered = []
        
        for element in elements:
            overlaps = False
            
            for existing in filtered:
                if self._calculate_overlap(element.bbox, existing.bbox) > 0.5:
                    overlaps = True
                    # Garder celui avec la meilleure confiance
                    if element.confidence > existing.confidence:
                        filtered.remove(existing)
                        break
            
            if not overlaps:
                filtered.append(element)
        
        return filtered
    
    def _calculate_overlap(self, bbox1: Tuple[int, int, int, int], 
                          bbox2: Tuple[int, int, int, int]) -> float:
        """Calcule le pourcentage de chevauchement entre deux bbox"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Coordonnées de l'intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right <= x_left or y_bottom <= y_top:
            return 0.0
        
        # Aires
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0

class OllamaVisionAnalyzer:
    """Analyseur utilisant Ollama LLaVA pour la compréhension visuelle"""
    
    def __init__(self, model: str = "llava:7b"):
        self.model = model
        self.client = None
        self.is_available = False
        
    async def initialize(self):
        """Initialise la connexion Ollama"""
        try:
            # Vérifier si Ollama est disponible
            models = ollama.list()
            available_models = [model['name'] for model in models['models']]
            
            if self.model in available_models:
                self.is_available = True
                logger.success(f"✅ Ollama LLaVA ({self.model}) disponible")
            else:
                logger.warning(f"⚠️  Modèle {self.model} non trouvé. Modèles disponibles: {available_models}")
                # Essayer de télécharger le modèle
                logger.info(f"🔄 Tentative de téléchargement du modèle {self.model}...")
                ollama.pull(self.model)
                self.is_available = True
                logger.success(f"✅ Modèle {self.model} téléchargé et prêt")
                
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Ollama: {e}")
            self.is_available = False
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convertit une image PIL en base64"""
        buffer = io.BytesIO()
        # Redimensionner si nécessaire pour économiser des tokens
        if image.size[0] > 1024 or image.size[1] > 1024:
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def analyze_image(self, image: Image.Image, 
                           prompt: str = None) -> Dict[str, Any]:
        """Analyse une image avec LLaVA"""
        if not self.is_available:
            return {"error": "Ollama LLaVA non disponible"}
        
        try:
            # Prompt par défaut pour l'analyse d'écran
            if prompt is None:
                prompt = """Analysez cette capture d'écran en détail. Décrivez:
1. Le type d'application ou de page web visible
2. Les éléments d'interface principaux (boutons, menus, champs de texte)
3. Le contenu textuel visible
4. Les actions possibles pour un utilisateur
5. L'état général de l'interface

Répondez en français de manière structurée."""
            
            # Conversion de l'image
            image_b64 = self._image_to_base64(image)
            
            # Appel à Ollama
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                images=[image_b64],
                stream=False
            )
            
            return {
                "description": response['response'],
                "model": self.model,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse LLaVA: {e}")
            return {"error": str(e), "success": False}
    
    async def identify_ui_elements(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Identifie les éléments d'interface avec LLaVA"""
        prompt = """Identifiez tous les éléments d'interface utilisateur visibles dans cette capture d'écran.
Pour chaque élément, indiquez:
- Type (bouton, lien, champ de texte, menu, etc.)
- Texte visible s'il y en a
- Position approximative (haut/milieu/bas, gauche/centre/droite)
- Si l'élément est cliquable

Formatez votre réponse comme une liste structurée."""
        
        result = await self.analyze_image(image, prompt)
        
        if result.get("success"):
            # TODO: Parser la réponse pour extraire les éléments structurés
            # Pour l'instant, retourner la description brute
            return [{"description": result["description"]}]
        
        return []
    
    async def suggest_actions(self, image: Image.Image, 
                            objective: str = None) -> List[str]:
        """Suggère des actions basées sur l'analyse de l'image"""
        objective_text = f"\nObjectif de l'utilisateur: {objective}" if objective else ""
        
        prompt = f"""Analysez cette capture d'écran et suggérez les actions que pourrait effectuer un utilisateur.{objective_text}

Listez les actions possibles de manière concrète et pratique:
- Cliquer sur [élément]
- Saisir du texte dans [champ]
- Naviguer vers [section]
- etc.

Soyez spécifique et utilisable pour un agent automatique."""
        
        result = await self.analyze_image(image, prompt)
        
        if result.get("success"):
            # Parser les suggestions d'actions
            actions = []
            lines = result["description"].split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    actions.append(line[1:].strip())
            
            return actions
        
        return []

class VisualAnalyzer:
    """Analyseur visuel principal combinant détection CV et IA"""
    
    def __init__(self):
        self.ui_detector = UIElementDetector()
        self.llava_analyzer = OllamaVisionAnalyzer()
        
    async def initialize(self):
        """Initialise l'analyseur visuel"""
        await self.llava_analyzer.initialize()
        logger.success("✅ Analyseur visuel initialisé")
    
    async def analyze_screen(self, image: Image.Image, 
                           objective: str = None) -> VisualAnalysisResult:
        """Analyse complète d'une capture d'écran"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Conversion en numpy pour OpenCV
            img_array = np.array(image)
            
            # Détection d'éléments d'interface avec CV
            ui_elements = self.ui_detector.detect_all_elements(img_array)
            
            # Analyse avec LLaVA si disponible
            llava_result = {}
            if self.llava_analyzer.is_available:
                llava_result = await self.llava_analyzer.analyze_image(image)
            
            # Suggestions d'actions
            actions_suggested = []
            if self.llava_analyzer.is_available:
                actions_suggested = await self.llava_analyzer.suggest_actions(image, objective)
            
            # Analyse des couleurs dominantes
            dominant_colors = self._get_dominant_colors(img_array)
            
            # Classification de la scène
            scene_type = self._classify_scene(llava_result.get("description", ""))
            
            # Régions de texte (approximation basée sur les éléments UI)
            text_regions = [{"bbox": elem.bbox, "text": elem.text} for elem in ui_elements if elem.text]
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = VisualAnalysisResult(
                description=llava_result.get("description", "Analyse visuelle basique"),
                ui_elements=ui_elements,
                scene_type=scene_type,
                dominant_colors=dominant_colors,
                text_regions=text_regions,
                actions_suggested=actions_suggested,
                confidence=0.8 if self.llava_analyzer.is_available else 0.5,
                processing_time=processing_time
            )
            
            logger.info(f"🔍 Analyse visuelle complétée en {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse visuelle: {e}")
            return VisualAnalysisResult(
                description=f"Erreur d'analyse: {e}",
                ui_elements=[],
                scene_type="unknown",
                dominant_colors=[],
                text_regions=[],
                actions_suggested=[],
                confidence=0.0,
                processing_time=asyncio.get_event_loop().time() - start_time
            )
    
    def _get_dominant_colors(self, image: np.ndarray, k: int = 5) -> List[Tuple[int, int, int]]:
        """Extrait les couleurs dominantes de l'image"""
        try:
            # Redimensionner pour accélérer le calcul
            height, width = image.shape[:2]
            if height > 300 or width > 300:
                scale = min(300/height, 300/width)
                new_height, new_width = int(height*scale), int(width*scale)
                image = cv2.resize(image, (new_width, new_height))
            
            # Reshape pour k-means
            data = image.reshape((-1, 3))
            data = np.float32(data)
            
            # K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convertir en format RGB tuple
            dominant_colors = []
            for center in centers:
                color = tuple(map(int, center))
                dominant_colors.append(color)
            
            return dominant_colors
            
        except Exception as e:
            logger.error(f"Erreur extraction couleurs: {e}")
            return [(128, 128, 128)]  # Gris par défaut
    
    def _classify_scene(self, description: str) -> str:
        """Classifie le type de scène basé sur la description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["bureau", "desktop", "écran d'accueil"]):
            return "desktop"
        elif any(word in description_lower for word in ["navigateur", "browser", "web", "site"]):
            return "browser"
        elif any(word in description_lower for word in ["application", "logiciel", "programme"]):
            return "application"
        elif any(word in description_lower for word in ["fichier", "dossier", "explorateur"]):
            return "file_manager"
        elif any(word in description_lower for word in ["éditeur", "code", "texte"]):
            return "editor"
        else:
            return "unknown"
    
    async def find_element_by_text(self, image: Image.Image, 
                                  target_text: str) -> Optional[UIElement]:
        """Trouve un élément d'interface par son texte"""
        result = await self.analyze_screen(image)
        
        target_lower = target_text.lower()
        
        for element in result.ui_elements:
            if target_lower in element.text.lower():
                return element
        
        return None
    
    async def get_clickable_elements(self, image: Image.Image) -> List[UIElement]:
        """Retourne tous les éléments cliquables détectés"""
        result = await self.analyze_screen(image)
        return [elem for elem in result.ui_elements if elem.clickable]

# Fonctions utilitaires
async def quick_screen_analysis(image: Image.Image) -> str:
    """Analyse rapide d'écran pour obtenir une description"""
    analyzer = VisualAnalyzer()
    await analyzer.initialize()
    
    result = await analyzer.analyze_screen(image)
    return result.description

async def find_button_by_text(image: Image.Image, button_text: str) -> Optional[Tuple[int, int]]:
    """Trouve un bouton par son texte et retourne ses coordonnées de centre"""
    analyzer = VisualAnalyzer()
    await analyzer.initialize()
    
    element = await analyzer.find_element_by_text(image, button_text)
    
    if element and element.type == "button":
        x, y, w, h = element.bbox
        center_x = x + w // 2
        center_y = y + h // 2
        return (center_x, center_y)
    
    return None

if __name__ == "__main__":
    async def test_visual_analysis():
        from core.vision.screen_capture import quick_screenshot
        
        # Test avec une capture d'écran
        screenshot = await quick_screenshot()
        if screenshot:
            analyzer = VisualAnalyzer()
            await analyzer.initialize()
            
            result = await analyzer.analyze_screen(screenshot.image)
            
            print(f"✅ Analyse visuelle complétée:")
            print(f"📋 Description: {result.description[:200]}...")
            print(f"🔲 Éléments UI détectés: {len(result.ui_elements)}")
            print(f"🎨 Couleurs dominantes: {len(result.dominant_colors)}")
            print(f"🎯 Actions suggérées: {len(result.actions_suggested)}")
            print(f"⏱️  Temps de traitement: {result.processing_time:.2f}s")
    
    asyncio.run(test_visual_analysis())