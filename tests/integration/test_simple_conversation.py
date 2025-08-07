#!/usr/bin/env python3
"""
Test simple du module conversationnel uniquement
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from core.ai.ollama_service import OllamaService
from core.ai.action_planner import ActionPlanner
from core.simple_conversation import SimpleConversation

async def test_simple_conversation():
    """Test minimal de conversation"""
    print("""
🤖 Test du module de conversation simple
==========================================
    """)
    
    try:
        # Initialiser les modules de base
        print("🔧 Initialisation Ollama...")
        ollama = OllamaService()
        await ollama.initialize()
        
        print("🔧 Initialisation planner...")
        planner = ActionPlanner(ollama)
        
        print("🔧 Initialisation conversation...")
        conversation = SimpleConversation(ollama, planner)
        
        print("✅ Modules initialisés !")
        
        # Tests conversationnels
        test_phrases = [
            "Bonjour !",
            "Comment vas-tu ?",
            "Peux-tu prendre une capture d'écran ?",
            "J'aimerais ouvrir YouTube",
            "Merci !"
        ]
        
        print("\n💬 Tests de conversation:")
        print("=" * 40)
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n{i}. Utilisateur: {phrase}")
            
            try:
                response, action = await conversation.chat(phrase)
                
                print(f"   JARVIS: {response}")
                
                if action:
                    print(f"   🎯 Action détectée: {action['command']}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                logger.error(f"Erreur conversation: {e}")
            
            # Pause courte
            await asyncio.sleep(0.5)
        
        print("\n🎉 Test de conversation terminé !")
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {e}")
        logger.error(f"Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_conversation())