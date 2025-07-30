"""
🎭 Presets Vocaux - TTS Service
Système de presets pour personnaliser les voix
"""

from .jarvis_voice import jarvis_preset
from .preset_manager import PresetManager

__all__ = ['jarvis_preset', 'PresetManager']