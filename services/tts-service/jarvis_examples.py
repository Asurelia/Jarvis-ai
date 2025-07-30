#!/usr/bin/env python3
"""
🎭 Exemples d'utilisation - JARVIS Voice Preset
Exemples pratiques d'utilisation du preset vocal Jarvis
"""

import requests
import json
import base64
from pathlib import Path

# Configuration
TTS_SERVICE_URL = "http://localhost:5002"
OUTPUT_DIR = Path("examples_output")
OUTPUT_DIR.mkdir(exist_ok=True)

def test_basic_jarvis():
    """Test basique du preset Jarvis"""
    print("🤖 Test basique Jarvis...")
    
    payload = {
        "text": "Bonjour Monsieur. Comment puis-je vous assister aujourd'hui ?",
        "context": "greeting"
    }
    
    response = requests.post(f"{TTS_SERVICE_URL}/api/tts/jarvis", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        audio_bytes = base64.b64decode(data['audio'])
        
        with open(OUTPUT_DIR / "basic_jarvis.wav", 'wb') as f:
            f.write(audio_bytes)
        
        print(f"✅ Audio sauvé: {OUTPUT_DIR / 'basic_jarvis.wav'}")
        print(f"   Texte original: {data['original_text']}")
        print(f"   Texte amélioré: {data['enhanced_text']}")
    else:
        print(f"❌ Erreur: {response.status_code}")

def test_jarvis_with_categories():
    """Test avec différentes catégories de phrases"""
    print("\n🎭 Test avec catégories de phrases...")
    
    categories = [
        ("greetings", "Initialisation des systèmes en cours."),
        ("confirmations", "Lancement de l'analyse des données."),
        ("status_reports", "Scan de sécurité terminé."),
        ("initiatives", "optimiser les performances du système."),
        ("closings", "Analyse terminée avec succès.")
    ]
    
    for category, text in categories:
        payload = {
            "text": text,
            "phrase_category": category
        }
        
        response = requests.post(f"{TTS_SERVICE_URL}/api/tts/jarvis", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            audio_bytes = base64.b64decode(data['audio'])
            
            filename = f"jarvis_{category}.wav"
            with open(OUTPUT_DIR / filename, 'wb') as f:
                f.write(audio_bytes)
            
            print(f"✅ {filename} - '{data['enhanced_text']}'")
        else:
            print(f"❌ Erreur {category}: {response.status_code}")

def test_contextual_responses():
    """Test des réponses contextuelles"""
    print("\n🧠 Test réponses contextuelles...")
    
    contexts = [
        ("weather", "Il fait 22 degrés avec un ciel dégagé."),
        ("time", "15h42 et 30 secondes."),
        ("calculation", "La racine carrée de 256 est 16."),
        ("analysis", "les données montrent une tendance positive.")
    ]
    
    for context, text in contexts:
        payload = {
            "text": text,
            "context": context
        }
        
        response = requests.post(f"{TTS_SERVICE_URL}/api/tts/jarvis", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            audio_bytes = base64.b64decode(data['audio'])
            
            filename = f"jarvis_context_{context}.wav"
            with open(OUTPUT_DIR / filename, 'wb') as f:
                f.write(audio_bytes)
            
            print(f"✅ {filename}")
            print(f"   Contexte: {context}")
            print(f"   Résultat: '{data['enhanced_text']}'")
        else:
            print(f"❌ Erreur contexte {context}: {response.status_code}")

def test_regular_vs_jarvis():
    """Comparaison voix normale vs Jarvis"""
    print("\n⚖️ Comparaison normale vs Jarvis...")
    
    text = "Les diagnostics système sont terminés. Aucune anomalie détectée."
    
    # Voix normale
    normal_payload = {
        "text": text,
        "voice_id": "french_male"
    }
    
    response = requests.post(f"{TTS_SERVICE_URL}/api/synthesize", json=normal_payload)
    if response.status_code == 200:
        data = response.json()
        audio_bytes = base64.b64decode(data['audio'])
        
        with open(OUTPUT_DIR / "comparison_normal.wav", 'wb') as f:
            f.write(audio_bytes)
        print("✅ Voix normale sauvée")
    
    # Voix Jarvis
    jarvis_payload = {
        "text": text,
        "context": "system"
    }
    
    response = requests.post(f"{TTS_SERVICE_URL}/api/tts/jarvis", json=jarvis_payload)
    if response.status_code == 200:
        data = response.json()
        audio_bytes = base64.b64decode(data['audio'])
        
        with open(OUTPUT_DIR / "comparison_jarvis.wav", 'wb') as f:
            f.write(audio_bytes)
        print("✅ Voix Jarvis sauvée")
        print(f"   Effets: {data.get('voice_effects', 'none')}")

def list_available_phrases():
    """Lister toutes les phrases disponibles"""
    print("\n📋 Phrases Jarvis disponibles...")
    
    response = requests.get(f"{TTS_SERVICE_URL}/api/jarvis/phrases")
    
    if response.status_code == 200:
        data = response.json()
        phrases = data['phrases']
        
        print(f"📊 {data['total_phrases']} phrases dans {len(phrases)} catégories:\n")
        
        for category, phrase_list in phrases.items():
            print(f"🏷️ {category.upper()} ({len(phrase_list)} phrases):")
            for phrase in phrase_list:
                print(f"   • {phrase}")
            print()
    else:
        print(f"❌ Erreur récupération phrases: {response.status_code}")

def demo_advanced_scenarios():
    """Scénarios avancés d'utilisation"""
    print("\n🎬 Scénarios avancés...")
    
    scenarios = [
        {
            "name": "Rapport de mission",
            "text": "Mission de surveillance terminée. 47 anomalies détectées et corrigées automatiquement.",
            "context": "system",
            "phrase_category": "status_reports"
        },
        {
            "name": "Alerte sécurité",
            "text": "Tentative d'intrusion détectée sur le port 443. Activation des contre-mesures.",
            "context": "analysis",
            "phrase_category": "errors"
        },
        {
            "name": "Recommandation stratégique",
            "text": "analyser les tendances du marché avant d'investir dans ce secteur.",
            "context": "recommendation",
            "phrase_category": "initiatives"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🎭 Scénario: {scenario['name']}")
        
        payload = {
            "text": scenario['text'],
            "context": scenario.get('context'),
            "phrase_category": scenario.get('phrase_category')
        }
        
        response = requests.post(f"{TTS_SERVICE_URL}/api/tts/jarvis", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            audio_bytes = base64.b64decode(data['audio'])
            
            filename = f"scenario_{scenario['name'].lower().replace(' ', '_')}.wav"
            with open(OUTPUT_DIR / filename, 'wb') as f:
                f.write(audio_bytes)
            
            print(f"✅ {filename}")
            print(f"   '{data['enhanced_text']}'")
        else:
            print(f"❌ Erreur: {response.status_code}")

if __name__ == "__main__":
    print("🚀 === EXEMPLES JARVIS VOICE PRESET ===\n")
    
    try:
        # Vérifier que le service est accessible
        response = requests.get(f"{TTS_SERVICE_URL}/health")
        if response.status_code != 200:
            print(f"❌ Service TTS non accessible à {TTS_SERVICE_URL}")
            exit(1)
        
        print(f"✅ Service TTS accessible")
        print(f"📁 Sortie dans: {OUTPUT_DIR.absolute()}\n")
        
        # Exécuter les tests
        test_basic_jarvis()
        test_jarvis_with_categories()
        test_contextual_responses()
        test_regular_vs_jarvis()
        demo_advanced_scenarios()
        list_available_phrases()
        
        print(f"\n🎉 Tous les exemples générés dans {OUTPUT_DIR.absolute()}")
        print("\n🎧 Pour écouter les fichiers audio:")
        for wav_file in OUTPUT_DIR.glob("*.wav"):
            print(f"   {wav_file.name}")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter au service TTS à {TTS_SERVICE_URL}")
        print("   Assurez-vous que le service est démarré avec: python main.py")
    except Exception as e:
        print(f"❌ Erreur: {e}")