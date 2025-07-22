#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS AI 2025 - Tests Simples (Compatible Windows)
"""

import sys
import time
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_basic_imports():
    """Test d'importation des modules de base"""
    print("Test d'importation des modules de base...")
    
    modules_ok = 0
    modules_total = 0
    
    basic_modules = ['json', 'threading', 'asyncio', 'requests']
    
    for module_name in basic_modules:
        modules_total += 1
        try:
            __import__(module_name)
            print(f"  OK: {module_name}")
            modules_ok += 1
        except ImportError as e:
            print(f"  ERREUR: {module_name} - {e}")
    
    print(f"Modules importes: {modules_ok}/{modules_total}")
    return modules_ok, modules_total

def test_ollama_connection():
    """Test de connexion à Ollama"""
    print("\nTest de connexion Ollama...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"  OK: Ollama actif - {len(models)} modeles disponibles")
            
            # Afficher quelques modèles
            for i, model in enumerate(models[:3]):
                name = model.get('name', 'Unknown')
                size_gb = model.get('size', 0) / (1024**3)
                print(f"    - {name} ({size_gb:.1f}GB)")
                
            return True, len(models)
        else:
            print(f"  ERREUR: HTTP {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"  ERREUR: {e}")
        return False, 0

def test_threading_performance():
    """Test de performance des threads"""
    print("\nTest de performance threading...")
    
    import threading
    import concurrent.futures
    
    def cpu_task(n):
        return sum(i * i for i in range(n))
    
    # Test séquentiel
    start_time = time.time()
    seq_results = [cpu_task(10000) for _ in range(4)]
    seq_duration = time.time() - start_time
    
    # Test parallèle
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        parallel_results = list(executor.map(cpu_task, [10000] * 4))
    parallel_duration = time.time() - start_time
    
    speedup = seq_duration / parallel_duration
    
    print(f"  Sequentiel: {seq_duration:.3f}s")
    print(f"  Parallele: {parallel_duration:.3f}s")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup > 1.0, speedup

def test_json_processing():
    """Test de traitement JSON"""
    print("\nTest de traitement JSON...")
    
    import json
    
    test_data = {
        "cognitive_state": "thinking",
        "agents": ["analytical", "creative", "synthesizer"],
        "predictions": [
            {"action": "save_file", "confidence": 0.85, "time": 300},
            {"action": "check_email", "confidence": 0.67, "time": 600}
        ],
        "neural_activity": 0.73
    }
    
    start_time = time.time()
    
    # Test sérialisation/désérialisation multiple
    for i in range(1000):
        json_str = json.dumps(test_data)
        parsed_data = json.loads(json_str)
    
    duration = time.time() - start_time
    
    print(f"  1000 operations JSON: {duration:.3f}s")
    print(f"  Performance: {1000/duration:.0f} ops/sec")
    
    return duration < 0.5, duration

def test_file_system():
    """Test du système de fichiers"""
    print("\nTest du systeme de fichiers...")
    
    ui_components = [
        'ui/src/components/CognitiveIntelligenceModule.js',
        'ui/src/components/PredictionSystem.js', 
        'ui/src/components/NeuralInterface.js',
        'ui/src/components/PerformanceMonitor.js',
        'ui/src/utils/PerformanceOptimizer.js'
    ]
    
    existing_files = 0
    total_files = len(ui_components)
    
    for file_path in ui_components:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            print(f"  OK: {file_path} ({size_kb:.1f}KB)")
            existing_files += 1
        else:
            print(f"  MANQUANT: {file_path}")
    
    print(f"Fichiers trouves: {existing_files}/{total_files}")
    return existing_files, total_files

def run_simple_tests():
    """Exécuter tous les tests simples"""
    print("JARVIS AI 2025 - Tests Rapides")
    print("=" * 40)
    
    results = {}
    start_time = time.time()
    
    # Test 1: Imports
    modules_ok, modules_total = test_basic_imports()
    results['imports'] = modules_ok == modules_total
    
    # Test 2: Ollama
    ollama_ok, models_count = test_ollama_connection()
    results['ollama'] = ollama_ok
    
    # Test 3: Threading
    threading_ok, speedup = test_threading_performance()
    results['threading'] = threading_ok
    
    # Test 4: JSON
    json_ok, json_duration = test_json_processing()
    results['json'] = json_ok
    
    # Test 5: Files
    files_found, files_total = test_file_system()
    results['files'] = files_found == files_total
    
    # Résumé
    total_duration = time.time() - start_time
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print("\n" + "=" * 40)
    print("RESUME DES TESTS")
    print("=" * 40)
    
    for test_name, passed in results.items():
        status = "PASSE" if passed else "ECHEC"
        print(f"  {test_name.upper()}: {status}")
    
    print(f"\nTests passes: {passed_tests}/{total_tests}")
    print(f"Taux de reussite: {passed_tests/total_tests:.1%}")
    print(f"Duree totale: {total_duration:.2f}s")
    
    if passed_tests == total_tests:
        print("\nTOUS LES TESTS SONT PASSES! JARVIS est pret.")
        return True
    else:
        print(f"\n{total_tests - passed_tests} tests ont echoue.")
        return False

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)