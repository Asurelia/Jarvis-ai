#!/usr/bin/env python3
"""
Démonstration du système conversationnel (avec simulation d'Ollama si nécessaire)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

# Simulation d'Ollama si non disponible
class MockOllamaService:
    """Service Ollama simulé pour démonstration"""
    
    def __init__(self):
        self.is_available = True
    
    async def initialize(self):
        return True
    
    async def generate(self, request):
        """Génère des réponses simulées"""
        prompt = request.prompt.lower()
        
        # Reconnaissance d'intention simulée
        if "json" in prompt and ("intention" in prompt or "type" in prompt):
            if "youtube" in prompt:
                return type('Response', (), {
                    'content': '{"type": "action", "action_type": "ouvrir_site", "details": {"site": "youtube"}}'
                })()
            elif "capture" in prompt or "screenshot" in prompt:
                return type('Response', (), {
                    'content': '{"type": "action", "action_type": "capturer_ecran", "details": {}}'
                })()
            elif "bonjour" in prompt or "comment" in prompt:
                return type('Response', (), {
                    'content': '{"type": "chat", "action_type": null, "details": {}}'
                })()
            else:
                return type('Response', (), {
                    'content': '{"type": "chat", "action_type": null, "details": {}}'
                })()
        
        # Réponses conversationnelles simulées
        else:
            responses = {
                "bonjour": "Bonjour ! Je suis JARVIS, votre assistant personnel. Comment puis-je vous aider ?",
                "comment": "Je vais très bien, merci ! Je suis prêt à vous aider avec toutes vos tâches.",
                "youtube": "Parfait ! Je vais ouvrir YouTube pour vous.",
                "capture": "D'accord ! Je vais prendre une capture d'écran.",
                "merci": "De rien ! C'est un plaisir de vous aider.",
                "au revoir": "Au revoir ! N'hésitez pas à revenir si vous avez besoin d'aide."
            }
            
            for keyword, response in responses.items():
                if keyword in prompt:
                    return type('Response', (), {'content': response})()
            
            return type('Response', (), {
                'content': "Je comprends votre demande et je vais faire de mon mieux pour vous aider !"
            })()

async def test_conversation_demo():
    """Démonstration complète du système conversationnel"""
    print("""
🤖 DÉMONSTRATION - Système conversationnel JARVIS
================================================
    """)
    
    try:
        # Utiliser le vrai service si disponible, sinon simuler
        try:
            from core.ai.ollama_service import OllamaService
            ollama = OllamaService()
            await ollama.initialize()
            if not ollama.is_available:
                raise Exception("Ollama non disponible")
            print("✅ Service Ollama réel connecté")
        except:
            ollama = MockOllamaService()
            await ollama.initialize()
            print("⚡ Service Ollama simulé pour démonstration")
        
        # Créer le planner simulé
        class MockActionPlanner:
            def __init__(self, ollama_service):
                self.ollama = ollama_service
            
            async def plan_action(self, command):
                # Simulation simple de planification
                from core.ai.action_planner import ActionSequence, Action, ActionType
                
                if "youtube" in command.lower():
                    action = Action(
                        type=ActionType.WEB_NAVIGATION,
                        parameters={"url": "https://youtube.com"},
                        description="Ouvrir YouTube"
                    )
                    return ActionSequence(
                        id="open_youtube",
                        name="Ouvrir YouTube",
                        description="Navigation vers YouTube",
                        actions=[action]
                    )
                elif "capture" in command.lower() or "screenshot" in command.lower():
                    action = Action(
                        type=ActionType.TAKE_SCREENSHOT,
                        parameters={},
                        description="Prendre une capture d'écran"
                    )
                    return ActionSequence(
                        id="take_screenshot",
                        name="Capture d'écran",
                        description="Prendre une capture d'écran",
                        actions=[action]
                    )
                else:
                    return ActionSequence(
                        id="no_action",
                        name="Pas d'action",
                        description="Conversation simple",
                        actions=[]
                    )
        
        planner = MockActionPlanner(ollama)
        
        # Initialiser le système conversationnel
        from core.simple_conversation import SimpleConversation
        conversation = SimpleConversation(ollama, planner)
        
        print("✅ Système conversationnel initialisé !")
        
        # Tests de conversation interactifs
        test_phrases = [
            "Bonjour JARVIS !",
            "Comment vas-tu ?",
            "Peux-tu prendre une capture d'écran ?",
            "J'aimerais voir YouTube",
            "Merci beaucoup !",
            "Au revoir"
        ]
        
        print("\n💬 Démonstration conversationnelle:")
        print("=" * 50)
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n{i}. 👤 Utilisateur: {phrase}")
            
            try:
                response, action = await conversation.chat(phrase)
                
                print(f"   🤖 JARVIS: {response}")
                
                if action:
                    print(f"   ⚡ Action planifiée: {action['command']}")
                    print("   ✅ (Action simulée - serait exécutée dans un vrai environnement)")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                logger.error(f"Erreur conversation: {e}")
            
            # Pause pour rendre la démo plus naturelle
            await asyncio.sleep(1)
        
        print(f"\n🎉 Démonstration terminée !")
        print("\n💡 Le système conversationnel JARVIS peut:")
        print("   • Comprendre le langage naturel")
        print("   • Identifier automatiquement les intentions")
        print("   • Répondre de manière conversationnelle")
        print("   • Exécuter des actions quand nécessaire")
        print("   • Maintenir le contexte de la conversation")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        logger.error(f"Erreur démonstration: {e}")

if __name__ == "__main__":
    asyncio.run(test_conversation_demo())