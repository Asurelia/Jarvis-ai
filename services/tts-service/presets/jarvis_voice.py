"""
🤖 JARVIS Voice Preset - Configuration vocale style Iron Man
Paramètres pour une voix grave, métallique et sophistiquée
"""

from typing import Dict, Any, List
import numpy as np

class JarvisVoicePreset:
    """
    Preset vocal pour Jarvis - IA sophistiquée style Iron Man
    Voix grave, métallique, avec réverbération et traitement avancé
    """
    
    def __init__(self):
        self.name = "JARVIS"
        self.description = "Voix sophistiquée d'IA inspirée de Jarvis (Iron Man)"
        
        # Configuration vocale de base
        self.voice_config = {
            "speed": 0.95,  # Légèrement plus lent pour plus de gravité
            "pitch": -2.0,  # Plus grave (en demi-tons)
            "volume": 0.85, # Volume modéré mais autoritaire
            "language": "fr",
            "gender": "male",
            "tone": "sophisticated"
        }
        
        # Paramètres de réverbération pour effet métallique
        self.reverb_config = {
            "room_size": 0.7,    # Salle de taille moyenne
            "damping": 0.3,      # Peu d'amortissement pour le métal
            "wet_level": 0.25,   # Mélange subtle de réverb
            "dry_level": 0.75,   # Principalement signal direct
            "width": 0.8,        # Stéréo élargi
            "freeze_mode": False
        }
        
        # Égalisation pour boost des graves et caractère métallique
        self.eq_config = {
            "low_freq": 80,      # Fréquence grave
            "low_gain": 3.0,     # Boost des graves (+3dB)
            "mid_freq": 1000,    # Médiums
            "mid_gain": -1.0,    # Légère atténuation médiums
            "high_freq": 8000,   # Aigus
            "high_gain": 2.0,    # Boost aigus pour clarté métallique
            "presence_freq": 4000, # Présence vocale
            "presence_gain": 1.5   # Légère emphase
        }
        
        # Paramètres de compression pour consistance
        self.compression_config = {
            "threshold": -18.0,   # Seuil de compression
            "ratio": 3.0,         # Ratio de compression
            "attack": 5.0,        # Attaque rapide (ms)
            "release": 50.0,      # Relâchement (ms)
            "knee": 2.0           # Knee doux
        }
        
        # Effets spéciaux Jarvis
        self.fx_config = {
            "metallic_filter": {
                "enabled": True,
                "center_freq": 2000,
                "bandwidth": 1.5,
                "gain": 2.0
            },
            "harmonic_enhancer": {
                "enabled": True,
                "intensity": 0.3,
                "harmonics": [2, 3, 4]  # Harmoniques à enhancer
            },
            "subtle_chorus": {
                "enabled": True,
                "rate": 0.5,    # Hz
                "depth": 0.1,   # Profondeur
                "delay": 10     # ms
            }
        }
        
        # Phrases typiques de Jarvis
        self.jarvis_phrases = {
            "greetings": [
                "Bonjour, Monsieur.",
                "Comment puis-je vous assister aujourd'hui ?",
                "Tous les systèmes sont opérationnels.",
                "À votre service, Monsieur."
            ],
            "confirmations": [
                "Comme vous voudrez, Monsieur.",
                "Bien reçu, Monsieur.",
                "Immédiatement, Monsieur.",
                "Considérez que c'est fait."
            ],
            "status_reports": [
                "Systèmes nominaux à {percentage}%.",
                "Tous les paramètres sont dans les limites normales.",
                "Diagnostic complet : aucune anomalie détectée.",
                "Performances optimales maintenues."
            ],
            "initiatives": [
                "J'ai pris la liberté de...",
                "Permettez-moi de suggérer...",
                "Puis-je recommander...",
                "Il serait peut-être judicieux de..."
            ],
            "closings": [
                "Toujours un plaisir, Monsieur.",
                "À votre disposition.",
                "N'hésitez pas si vous avez besoin d'autre chose.",
                "Mission accomplie."
            ],
            "errors": [
                "Je crains qu'il y ait un problème, Monsieur.",
                "Cela semble poser quelques difficultés.",
                "Permettez-moi de résoudre cela.",
                "Un moment, je reconfigue les paramètres."
            ]
        }
        
        # Réponses contextuelles
        self.contextual_responses = {
            "weather": "D'après mes données météorologiques...",
            "time": "Il est actuellement...",
            "calculation": "Selon mes calculs...",
            "reminder": "Permettez-moi de vous rappeler...",
            "search": "D'après mes recherches...",
            "system": "État des systèmes :",
            "analysis": "Mon analyse indique que...",
            "recommendation": "Je recommande vivement..."
        }
    
    def get_voice_parameters(self) -> Dict[str, Any]:
        """Retourner les paramètres vocaux de base"""
        return self.voice_config.copy()
    
    def get_audio_effects(self) -> Dict[str, Any]:
        """Retourner la configuration des effets audio"""
        return {
            "reverb": self.reverb_config,
            "eq": self.eq_config,
            "compression": self.compression_config,
            "fx": self.fx_config
        }
    
    def get_phrases_by_category(self, category: str) -> List[str]:
        """Obtenir les phrases pour une catégorie donnée"""
        return self.jarvis_phrases.get(category, [])
    
    def get_contextual_intro(self, context: str) -> str:
        """Obtenir une introduction contextuelle"""
        return self.contextual_responses.get(context, "")
    
    def enhance_text_for_jarvis(self, text: str, context: str = None) -> str:
        """
        Améliorer le texte pour qu'il sonne plus comme Jarvis
        
        Args:
            text: Texte original
            context: Contexte de la phrase (optionnel)
            
        Returns:
            str: Texte amélioré style Jarvis
        """
        enhanced_text = text
        
        # Ajouter une introduction contextuelle si fournie
        if context and context in self.contextual_responses:
            intro = self.contextual_responses[context]
            enhanced_text = f"{intro} {enhanced_text}"
        
        # Remplacer certains mots pour un style plus sophistiqué
        replacements = {
            "ok": "très bien",
            "d'accord": "parfaitement",
            "oui": "certainement",
            "non": "je crains que non",
            "peut-être": "il est possible que",
            "probablement": "selon toute vraisemblance"
        }
        
        for old, new in replacements.items():
            enhanced_text = enhanced_text.replace(old, new)
        
        return enhanced_text
    
    def apply_jarvis_formatting(self, text: str) -> str:
        """
        Appliquer le formatage spécifique à Jarvis
        (pauses, emphases, etc.)
        """
        # Ajouter des pauses dramatiques
        formatted_text = text
        
        # Pauses après "Monsieur"
        formatted_text = formatted_text.replace("Monsieur.", "Monsieur. <break time='0.3s'/>")
        formatted_text = formatted_text.replace("Monsieur,", "Monsieur, <break time='0.2s'/>")
        
        # Emphases sur les mots importants
        emphasis_words = ["systèmes", "analyse", "recommande", "diagnostic", "optimal"]
        for word in emphasis_words:
            formatted_text = formatted_text.replace(
                word, 
                f"<emphasis level='moderate'>{word}</emphasis>"
            )
        
        # Vitesse légèrement ralentie pour les chiffres et pourcentages
        import re
        formatted_text = re.sub(
            r'(\d+%?)', 
            r"<prosody rate='0.9'>\1</prosody>", 
            formatted_text
        )
        
        return formatted_text

# Instance globale du preset
jarvis_preset = JarvisVoicePreset()