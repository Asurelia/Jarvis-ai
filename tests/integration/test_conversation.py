#!/usr/bin/env python3
"""
Test rapide du système conversationnel de JARVIS
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agent import create_agent
from loguru import logger

async def test_conversation():
    """Test simple de conversation"""
    print("""
🤖 Test du système conversationnel JARVIS
==========================================
    """)
    
    # Créer l'agent
    print("🔧 Initialisation de JARVIS...")
    try:
        agent = await create_agent()
        print("✅ JARVIS initialisé avec succès !")
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {e}")
        return
    
    # Tests conversationnels
    test_phrases = [
        "Bonjour JARVIS, comment vas-tu?",
        "Peux-tu prendre une capture d'écran?",
        "J'aimerais voir YouTube",
        "Merci beaucoup!",
        "Au revoir"
    ]
    
    print("\n💬 Tests de conversation:")
    print("=" * 40)
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"\n{i}. Utilisateur: {phrase}")
        
        try:
            result = await agent.process_command(phrase, mode="conversation")
            
            if result.get("success"):
                response = result.get("response", "")
                action_executed = result.get("action_executed", False)
                
                print(f"   JARVIS: {response}")
                
                if action_executed:
                    print("   ✅ Action exécutée !")
                    
            else:
                print(f"   ❌ Erreur: {result.get('error', 'Erreur inconnue')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Pause courte entre les tests
        await asyncio.sleep(1)
    
    print("\n🎉 Test conversationnel terminé !")

if __name__ == "__main__":
    asyncio.run(test_conversation())