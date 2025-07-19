"""
Module de conversation pour JARVIS
Interface conversationnelle naturelle avec l'utilisateur
"""

from .conversation_manager import ConversationManager
from .context_handler import ContextHandler
from .intent_recognizer import IntentRecognizer

__all__ = [
    'ConversationManager',
    'ContextHandler', 
    'IntentRecognizer'
] 