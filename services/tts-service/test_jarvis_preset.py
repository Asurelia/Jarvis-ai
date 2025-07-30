#!/usr/bin/env python3
"""
🤖 Test Script - JARVIS Voice Preset
Test et démonstration des capacités vocales de Jarvis
"""

import asyncio
import aiohttp
import json
import base64
import os
from pathlib import Path
import time

# Configuration du service TTS
TTS_SERVICE_URL = "http://localhost:5002"
OUTPUT_DIR = Path("test_outputs")

class JarvisVoiceTest:
    """Testeur pour le preset vocal Jarvis"""
    
    def __init__(self, service_url: str = TTS_SERVICE_URL):
        self.service_url = service_url
        self.session = None
        
        # Créer répertoire de sortie
        OUTPUT_DIR.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_service_health(self):
        """Vérifier que le service TTS est accessible"""
        print("🏥 Test de santé du service...")
        
        try:
            async with self.session.get(f"{self.service_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Service TTS opérationnel")
                    print(f"   Modèle chargé: {data.get('model_loaded', False)}")
                    print(f"   Uptime: {data.get('uptime', 0):.2f}s")
                    return True
                else:
                    print(f"❌ Service non disponible (status: {response.status})")
                    return False
        
        except Exception as e:
            print(f"❌ Erreur connexion service: {e}")
            return False
    
    async def test_presets_available(self):
        """Vérifier que les presets sont disponibles"""
        print("\n🎭 Test des presets disponibles...")
        
        try:
            async with self.session.get(f"{self.service_url}/api/presets") as response:
                if response.status == 200:
                    data = await response.json()
                    presets = data.get('presets', {})
                    
                    print(f"✅ {len(presets)} preset(s) disponible(s):")
                    for name, info in presets.items():
                        print(f"   - {name}: {info.get('description', 'N/A')}")
                    
                    # Vérifier Jarvis spécifiquement
                    if 'jarvis' in presets:
                        print(f"✅ Preset Jarvis trouvé!")
                        return True
                    else:
                        print(f"❌ Preset Jarvis non trouvé")
                        return False
                
                else:
                    print(f"❌ Erreur récupération presets (status: {response.status})")
                    return False
        
        except Exception as e:
            print(f"❌ Erreur test presets: {e}")
            return False
    
    async def test_jarvis_phrases(self):
        """Tester les phrases typiques de Jarvis"""
        print("\n💬 Test des phrases Jarvis...")
        
        try:
            async with self.session.get(f"{self.service_url}/api/jarvis/phrases") as response:
                if response.status == 200:
                    data = await response.json()
                    phrases = data.get('phrases', {})
                    
                    print(f"✅ {data.get('total_phrases', 0)} phrases dans {len(phrases)} catégories:")
                    for category, phrase_list in phrases.items():
                        print(f"   - {category}: {len(phrase_list)} phrases")
                        if phrase_list:
                            print(f"     Exemple: \"{phrase_list[0]}\"")
                    
                    return True
                
                else:
                    print(f"❌ Erreur récupération phrases (status: {response.status})")
                    return False
        
        except Exception as e:
            print(f"❌ Erreur test phrases: {e}")
            return False
    
    async def synthesize_jarvis_sample(self, text: str, filename: str, context: str = None, phrase_category: str = None):
        """Synthétiser un échantillon avec Jarvis"""
        print(f"\n🎙️ Synthèse Jarvis: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        try:
            payload = {
                "text": text,
                "context": context,
                "phrase_category": phrase_category
            }
            
            start_time = time.time()
            
            async with self.session.post(
                f"{self.service_url}/api/tts/jarvis",
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Décoder l'audio
                    audio_b64 = data.get('audio', '')
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        
                        # Sauvegarder
                        output_path = OUTPUT_DIR / f"{filename}.wav"
                        with open(output_path, 'wb') as f:
                            f.write(audio_bytes)
                        
                        duration = time.time() - start_time
                        print(f"✅ Audio généré: {output_path}")
                        print(f"   Durée génération: {duration:.2f}s")
                        print(f"   Taille audio: {len(audio_bytes)} bytes")
                        print(f"   Texte original: \"{data.get('original_text', '')}\"")
                        print(f"   Texte amélioré: \"{data.get('enhanced_text', '')}\"")
                        print(f"   Effets appliqués: {data.get('voice_effects', 'none')}")
                        
                        return True
                    else:
                        print(f"❌ Pas de données audio reçues")
                        return False
                
                else:
                    error_data = await response.json()
                    print(f"❌ Erreur synthèse (status: {response.status})")
                    print(f"   Détail: {error_data.get('detail', 'Erreur inconnue')}")
                    return False
        
        except Exception as e:
            print(f"❌ Erreur synthèse Jarvis: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Exécuter une série de tests complets"""
        print("🚀 === TEST COMPLET JARVIS VOICE PRESET ===\n")
        
        # Tests de base
        if not await self.test_service_health():
            return False
        
        if not await self.test_presets_available():
            return False
        
        if not await self.test_jarvis_phrases():
            return False
        
        # Tests de synthèse
        print(f"\n🎬 === TESTS DE SYNTHÈSE JARVIS ===")
        
        test_samples = [
            {
                "text": "Bonjour Monsieur. Tous les systèmes sont opérationnels.",
                "filename": "jarvis_greeting",
                "context": "greeting",
                "phrase_category": "greetings"
            },
            {
                "text": "Les systèmes sont nominaux à 98%.",
                "filename": "jarvis_status",
                "context": "system",
                "phrase_category": "status_reports"
            },
            {
                "text": "Je recommande une analyse complète des données avant de procéder.",
                "filename": "jarvis_recommendation",
                "context": "analysis",
                "phrase_category": "initiatives"
            },
            {
                "text": "Mission accomplie, Monsieur.",
                "filename": "jarvis_completion",
                "context": None,
                "phrase_category": "closings"
            },
            {
                "text": "Il semblerait qu'il y ait une anomalie dans le secteur 7. J'analyse la situation.",
                "filename": "jarvis_problem",
                "context": "analysis",
                "phrase_category": "errors"
            },
            {
                "text": "D'après mes calculs, la probabilité de succès est de 73.2%. Souhaitez-vous procéder?",
                "filename": "jarvis_calculation",
                "context": "calculation",
                "phrase_category": None
            }
        ]
        
        success_count = 0
        for i, sample in enumerate(test_samples, 1):
            print(f"\n--- Test {i}/{len(test_samples)} ---")
            if await self.synthesize_jarvis_sample(**sample):
                success_count += 1
            
            # Pause entre les tests
            await asyncio.sleep(0.5)
        
        # Résumé
        print(f"\n🏁 === RÉSUMÉ DES TESTS ===")
        print(f"Tests réussis: {success_count}/{len(test_samples)}")
        print(f"Fichiers générés dans: {OUTPUT_DIR.absolute()}")
        
        if success_count == len(test_samples):
            print("✅ Tous les tests sont passés avec succès!")
            print("\n🎉 Le preset vocal Jarvis est opérationnel!")
            print("\nPour écouter les échantillons:")
            for sample in test_samples:
                print(f"   {sample['filename']}.wav - {sample['text'][:30]}...")
        else:
            print(f"⚠️ {len(test_samples) - success_count} test(s) ont échoué")
        
        return success_count == len(test_samples)

async def main():
    """Point d'entrée principal"""
    async with JarvisVoiceTest() as tester:
        success = await tester.run_comprehensive_test()
        return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrompu par l'utilisateur")
        exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        exit(1)