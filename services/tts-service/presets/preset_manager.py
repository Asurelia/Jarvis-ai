"""
🎭 Preset Manager - Gestionnaire de presets vocaux
Gestion centralisée des configurations vocales personnalisées
"""

import logging
from typing import Dict, Any, Optional, List
import json
import os
from pathlib import Path

from .jarvis_voice import jarvis_preset

logger = logging.getLogger(__name__)

class PresetManager:
    """
    Gestionnaire de presets vocaux
    Permet de charger, sauvegarder et appliquer différentes configurations
    """
    
    def __init__(self, presets_dir: str = "/app/presets"):
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(exist_ok=True, parents=True)
        
        # Presets intégrés
        self.builtin_presets = {
            "jarvis": jarvis_preset,
        }
        
        # Cache des presets chargés
        self.loaded_presets: Dict[str, Any] = {}
        
        logger.info(f"🎭 Preset Manager initialisé: {self.presets_dir}")
    
    def get_preset(self, preset_name: str) -> Optional[Any]:
        """
        Obtenir un preset par son nom
        
        Args:
            preset_name: Nom du preset à charger
            
        Returns:
            Preset object ou None si non trouvé
        """
        # Vérifier les presets intégrés
        if preset_name in self.builtin_presets:
            return self.builtin_presets[preset_name]
        
        # Vérifier le cache
        if preset_name in self.loaded_presets:
            return self.loaded_presets[preset_name]
        
        # Essayer de charger depuis fichier
        try:
            preset = self._load_preset_from_file(preset_name)
            if preset:
                self.loaded_presets[preset_name] = preset
                return preset
        except Exception as e:
            logger.error(f"❌ Erreur chargement preset {preset_name}: {e}")
        
        return None
    
    def list_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        Lister tous les presets disponibles
        
        Returns:
            Dict avec infos sur chaque preset
        """
        presets_info = {}
        
        # Presets intégrés
        for name, preset in self.builtin_presets.items():
            presets_info[name] = {
                "name": getattr(preset, 'name', name),
                "description": getattr(preset, 'description', 'Preset intégré'),
                "type": "builtin",
                "available": True
            }
        
        # Presets fichiers
        try:
            for preset_file in self.presets_dir.glob("*.json"):
                name = preset_file.stem
                if name not in presets_info:
                    try:
                        with open(preset_file, 'r', encoding='utf-8') as f:
                            preset_data = json.load(f)
                        
                        presets_info[name] = {
                            "name": preset_data.get('name', name),
                            "description": preset_data.get('description', 'Preset personnalisé'),
                            "type": "custom",
                            "available": True,
                            "file": str(preset_file)
                        }
                    except Exception as e:
                        logger.warning(f"⚠️ Preset corrompu {name}: {e}")
                        presets_info[name] = {
                            "name": name,
                            "description": "Preset corrompu",
                            "type": "custom",
                            "available": False,
                            "error": str(e)
                        }
        except Exception as e:
            logger.error(f"❌ Erreur listing presets: {e}")
        
        return presets_info
    
    def save_preset(self, name: str, preset_data: Dict[str, Any]) -> bool:
        """
        Sauvegarder un preset personnalisé
        
        Args:
            name: Nom du preset
            preset_data: Données du preset
            
        Returns:
            bool: Succès de la sauvegarde
        """
        try:
            preset_file = self.presets_dir / f"{name}.json"
            
            # Ajouter métadonnées
            preset_data["created_at"] = None  # TODO: timestamp
            preset_data["version"] = "1.0"
            
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Preset sauvegardé: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde preset {name}: {e}")
            return False
    
    def delete_preset(self, name: str) -> bool:
        """
        Supprimer un preset personnalisé
        
        Args:
            name: Nom du preset à supprimer
            
        Returns:
            bool: Succès de la suppression
        """
        # Ne pas supprimer les presets intégrés
        if name in self.builtin_presets:
            logger.warning(f"⚠️ Impossible de supprimer preset intégré: {name}")
            return False
        
        try:
            preset_file = self.presets_dir / f"{name}.json"
            if preset_file.exists():
                preset_file.unlink()
                
                # Retirer du cache
                if name in self.loaded_presets:
                    del self.loaded_presets[name]
                
                logger.info(f"✅ Preset supprimé: {name}")
                return True
            else:
                logger.warning(f"⚠️ Preset non trouvé: {name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur suppression preset {name}: {e}")
            return False
    
    def _load_preset_from_file(self, name: str) -> Optional[Dict[str, Any]]:
        """Charger un preset depuis un fichier JSON"""
        preset_file = self.presets_dir / f"{name}.json"
        
        if not preset_file.exists():
            return None
        
        with open(preset_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def apply_preset_to_voice_config(
        self, 
        preset_name: str, 
        base_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Appliquer un preset à une configuration vocale
        
        Args:
            preset_name: Nom du preset à appliquer
            base_config: Configuration de base
            
        Returns:
            Dict: Configuration modifiée avec le preset
        """
        preset = self.get_preset(preset_name)
        if not preset:
            logger.warning(f"⚠️ Preset non trouvé: {preset_name}")
            return base_config
        
        # Copier la config de base
        enhanced_config = base_config.copy()
        
        try:
            # Appliquer les paramètres vocaux du preset
            if hasattr(preset, 'get_voice_parameters'):
                voice_params = preset.get_voice_parameters()
                enhanced_config.update(voice_params)
            
            # Ajouter les effets audio
            if hasattr(preset, 'get_audio_effects'):
                enhanced_config['audio_effects'] = preset.get_audio_effects()
            
            # Ajouter le preset lui-même pour référence
            enhanced_config['applied_preset'] = preset_name
            enhanced_config['preset_object'] = preset
            
            logger.info(f"✅ Preset appliqué: {preset_name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur application preset {preset_name}: {e}")
        
        return enhanced_config
    
    def get_jarvis_phrases(self, category: str = None) -> Dict[str, List[str]]:
        """
        Obtenir les phrases Jarvis
        
        Args:
            category: Catégorie spécifique (optionnel)
            
        Returns:
            Dict avec phrases par catégorie
        """
        jarvis = self.builtin_presets["jarvis"]
        
        if category:
            return {category: jarvis.get_phrases_by_category(category)}
        else:
            return jarvis.jarvis_phrases
    
    def enhance_text_with_preset(
        self, 
        text: str, 
        preset_name: str, 
        context: str = None
    ) -> str:
        """
        Améliorer un texte avec un preset spécifique
        
        Args:
            text: Texte original
            preset_name: Nom du preset
            context: Contexte (optionnel)
            
        Returns:
            str: Texte amélioré
        """
        preset = self.get_preset(preset_name)
        if not preset:
            return text
        
        try:
            if hasattr(preset, 'enhance_text_for_jarvis'):
                enhanced_text = preset.enhance_text_for_jarvis(text, context)
                
                if hasattr(preset, 'apply_jarvis_formatting'):
                    enhanced_text = preset.apply_jarvis_formatting(enhanced_text)
                
                return enhanced_text
            
        except Exception as e:
            logger.error(f"❌ Erreur amélioration texte avec preset {preset_name}: {e}")
        
        return text

# Instance globale
preset_manager = PresetManager()