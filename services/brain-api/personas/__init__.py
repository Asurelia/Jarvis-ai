"""
🎭 Module Personas - JARVIS Brain API
Système de personnalités IA inspiré des films Marvel
"""

from .base_persona import BasePersona, PersonalityTraits
from .jarvis_classic import JarvisClassicPersona
from .friday import FridayPersona
from .edith import EdithPersona
from .persona_manager import PersonaManager

__all__ = [
    'BasePersona',
    'PersonalityTraits',
    'JarvisClassicPersona',
    'FridayPersona',
    'EdithPersona',
    'PersonaManager'
]