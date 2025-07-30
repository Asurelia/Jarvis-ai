#!/usr/bin/env python3
"""
🎬 Démonstration du système de personas JARVIS
Script interactif pour explorer les différentes personnalités IA
"""

import asyncio
import aiohttp
import json
from typing import Dict, List

class PersonaDemo:
    """Démonstration interactive des personas"""
    
    def __init__(self, api_url: str = "http://localhost:8001/api/persona"):
        self.api_url = api_url
        self.session = None
        
        # Messages de démonstration pour chaque contexte
        self.demo_messages = {
            "greeting": "Hello, I'm ready to help you today.",
            "technical": "Please analyze the security vulnerabilities in our system and provide a detailed report.",
            "casual": "Hey, what's the weather like today?",
            "error": "I apologize, but I encountered an issue while processing your request.",
            "complex": "I need you to coordinate between multiple systems, analyze the data, and execute the optimal solution while maintaining security protocols.",
            "farewell": "Thank you for your assistance today. I'll be offline for maintenance."
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def switch_persona(self, persona_name: str) -> bool:
        """Changer vers une persona"""
        try:
            payload = {
                "reason": "demo_exploration",
                "user_id": "demo_user",
                "context": {"demo_mode": True}
            }
            
            async with self.session.post(f"{self.api_url}/switch/{persona_name}", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("success", False)
                return False
        except Exception as e:
            print(f"Erreur changement persona: {e}")
            return False
    
    async def format_message(self, content: str, context: Dict = None) -> str:
        """Formater un message avec la persona active"""
        try:
            payload = {
                "content": content,
                "context": context or {}
            }
            
            async with self.session.post(f"{self.api_url}/format", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("formatted", content)
                return content
        except Exception as e:
            print(f"Erreur formatage: {e}")
            return content
    
    async def get_persona_info(self, persona_name: str) -> Dict:
        """Obtenir les infos d'une persona"""
        try:
            async with self.session.get(f"{self.api_url}/{persona_name}/info") as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except Exception as e:
            print(f"Erreur récupération info: {e}")
            return {}
    
    def print_persona_header(self, persona_info: Dict):
        """Afficher l'en-tête d'une persona"""
        icons = {
            "JARVIS Classic": "🎩",
            "FRIDAY": "🌟", 
            "EDITH": "🔒"
        }
        
        name = persona_info.get("name", "Unknown")
        icon = icons.get(name, "🤖")
        
        print("\n" + "="*80)
        print(f"{icon} {name.upper()}")
        print("="*80)
        print(f"Description: {persona_info.get('description', 'N/A')}")
        print(f"Style: {persona_info.get('response_style', 'N/A').title()}")
        
        # Afficher les traits de personnalité
        personality = persona_info.get("personality", {})
        if personality:
            print("\nTraits de personnalité:")
            for trait, value in personality.items():
                bar_length = 20
                filled = int(value * bar_length)
                bar = "█" * filled + "░" * (bar_length - filled)
                percentage = int(value * 100)
                print(f"  {trait.title():12} {bar} {percentage:3d}%")
        
        print()
    
    async def demonstrate_persona(self, persona_name: str):
        """Démontrer une persona avec différents messages"""
        # Changer vers la persona
        success = await self.switch_persona(persona_name)
        if not success:
            print(f"❌ Impossible de changer vers {persona_name}")
            return
        
        # Récupérer les infos de la persona
        persona_info = await self.get_persona_info(persona_name)
        self.print_persona_header(persona_info)
        
        # Démontrer avec différents types de messages
        contexts = {
            "greeting": {"interaction_type": "greeting", "user_mood": "neutral"},
            "technical": {"task_type": "technical", "complexity": "high", "urgency": "medium"},
            "casual": {"interaction_type": "casual", "user_mood": "relaxed"},
            "error": {"situation": "error", "severity": "medium"},
            "complex": {"task_type": "complex", "security_sensitive": True, "multi_step": True},
            "farewell": {"interaction_type": "farewell", "session_end": True}
        }
        
        for msg_type, context in contexts.items():
            original = self.demo_messages[msg_type]
            formatted = await self.format_message(original, context)
            
            print(f"📝 {msg_type.title()} ({context.get('task_type', 'general')}):")
            print(f"   Original:  {original}")
            print(f"   Formaté:   {formatted}")
            print()
    
    async def run_comparison_demo(self):
        """Démonstration comparative des trois personas"""
        print("🎭 DÉMONSTRATION COMPARATIVE DES PERSONAS JARVIS")
        print("="*80)
        print("Cette démonstration montre comment chaque persona traite les mêmes messages")
        print("avec son style et sa personnalité uniques.\n")
        
        personas = ["jarvis_classic", "friday", "edith"]
        
        # Démonstration de chaque persona
        for persona in personas:
            await self.demonstrate_persona(persona)
            
            # Petite pause pour la lisibilité
            print("Appuyez sur Entrée pour continuer vers la persona suivante...")
            input()
    
    async def run_interactive_demo(self):
        """Démonstration interactive"""
        print("🎮 MODE INTERACTIF")
        print("="*50)
        print("Entrez vos messages et voyez comment chaque persona les traite!")
        print("Commandes: 'quit' pour quitter, 'switch <persona>' pour changer")
        print("Personas disponibles: jarvis_classic, friday, edith\n")
        
        current_persona = "jarvis_classic"
        await self.switch_persona(current_persona)
        
        while True:
            try:
                # Afficher la persona actuelle
                persona_icons = {"jarvis_classic": "🎩", "friday": "🌟", "edith": "🔒"}
                icon = persona_icons.get(current_persona, "🤖")
                
                user_input = input(f"\n{icon} [{current_persona}] Votre message: ").strip()
                
                if user_input.lower() == 'quit':
                    print("👋 Démonstration terminée!")
                    break
                
                if user_input.lower().startswith('switch '):
                    new_persona = user_input[7:].strip()
                    if new_persona in persona_icons:
                        success = await self.switch_persona(new_persona)
                        if success:
                            current_persona = new_persona
                            print(f"✅ Changé vers {new_persona}")
                        else:
                            print(f"❌ Impossible de changer vers {new_persona}")
                    else:
                        print("❌ Persona inconnue. Utilisez: jarvis_classic, friday, ou edith")
                    continue
                
                if user_input:
                    # Détecter le contexte automatiquement
                    context = self._analyze_context(user_input)
                    formatted = await self.format_message(user_input, context)
                    
                    print(f"🤖 Réponse: {formatted}")
                    if context:
                        print(f"📊 Contexte détecté: {context}")
            
            except KeyboardInterrupt:
                print("\n👋 Démonstration interrompue!")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def _analyze_context(self, message: str) -> Dict:
        """Analyser le contexte d'un message pour améliorer le formatage"""
        context = {}
        
        message_lower = message.lower()
        
        # Détecter le type de tâche
        if any(word in message_lower for word in ['security', 'analyze', 'scan', 'threat']):
            context['task_type'] = 'security'
        elif any(word in message_lower for word in ['weather', 'time', 'hello', 'hi']):
            context['task_type'] = 'casual'
        elif any(word in message_lower for word in ['error', 'problem', 'issue', 'bug']):
            context['task_type'] = 'error_handling'
        elif any(word in message_lower for word in ['complex', 'coordinate', 'multiple']):
            context['task_type'] = 'complex'
        
        # Détecter l'urgence
        if any(word in message_lower for word in ['urgent', 'critical', 'emergency', 'asap']):
            context['urgency'] = 'high'
        elif any(word in message_lower for word in ['soon', 'quickly', 'fast']):
            context['urgency'] = 'medium'
        
        # Détecter l'humeur
        if any(word in message_lower for word in ['please', 'thank', 'appreciate']):
            context['user_mood'] = 'polite'
        elif any(word in message_lower for word in ['help', 'stuck', 'confused']):
            context['user_mood'] = 'frustrated'
        
        return context
    
    async def show_statistics(self):
        """Afficher les statistiques d'utilisation"""
        try:
            async with self.session.get(f"{self.api_url}/statistics") as response:
                if response.status == 200:
                    stats = await response.json()
                    
                    print("\n📊 STATISTIQUES D'UTILISATION")
                    print("="*50)
                    print(f"Total interactions: {stats['total_interactions']}")
                    print(f"Total transitions: {stats['total_transitions']}")
                    print(f"Persona actuelle: {stats['current_persona']}")
                    
                    print("\nUtilisation par persona:")
                    for name, data in stats['personas'].items():
                        print(f"  {name:15} {data['usage_count']:3d} utilisations ({data['usage_percentage']:5.1f}%)")
                
        except Exception as e:
            print(f"❌ Erreur récupération stats: {e}")


async def main():
    """Point d'entrée principal"""
    print("🎭 DÉMONSTRATION SYSTÈME DE PERSONAS JARVIS AI")
    print("="*60)
    
    try:
        async with PersonaDemo() as demo:
            while True:
                print("\n🎯 OPTIONS DE DÉMONSTRATION:")
                print("1. Démonstration comparative complète")
                print("2. Mode interactif")
                print("3. Afficher les statistiques")
                print("4. Quitter")
                
                choice = input("\nVotre choix (1-4): ").strip()
                
                if choice == '1':
                    await demo.run_comparison_demo()
                elif choice == '2':
                    await demo.run_interactive_demo()
                elif choice == '3':
                    await demo.show_statistics()
                elif choice == '4':
                    print("👋 Au revoir!")
                    break
                else:
                    print("❌ Choix invalide. Utilisez 1, 2, 3 ou 4.")
    
    except KeyboardInterrupt:
        print("\n👋 Démonstration interrompue!")
    except Exception as e:
        print(f"💥 Erreur critique: {e}")


if __name__ == "__main__":
    asyncio.run(main())