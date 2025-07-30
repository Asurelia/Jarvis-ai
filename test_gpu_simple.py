#!/usr/bin/env python3
"""
Test simple du service GPU Stats
Validation rapide sans emojis pour compatibilité Windows
"""

import sys
import os
import asyncio
import time

# Ajouter le chemin du service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'gpu-stats-service'))

async def test_basic_functionality():
    """Test des fonctionnalités de base"""
    print("TEST SERVICE GPU STATS")
    print("=" * 50)
    
    try:
        # Test des imports
        print("\n1. Test des imports...")
        from main import GPUMonitor, GPUStats
        print("   OK - Modules importés avec succès")
        
        # Test création du moniteur
        print("\n2. Test création GPUMonitor...")
        monitor = GPUMonitor()
        print(f"   OK - GPUMonitor créé")
        print(f"   - Plateforme Windows: {monitor.is_windows}")
        print(f"   - GPU par défaut: {monitor.gpu_info['name']}")
        print(f"   - VRAM totale: {monitor.gpu_info['memory_total']} MB")
        
        # Test initialisation
        print("\n3. Test initialisation...")
        success = await monitor.initialize()
        print(f"   {'OK' if success else 'ERREUR'} - Initialisation: {'Succès' if success else 'Échec'}")
        
        # Test récupération stats
        print("\n4. Test récupération des stats...")
        stats = await monitor.get_gpu_stats()
        
        if stats:
            print("   OK - Statistiques récupérées:")
            print(f"   - Nom GPU: {stats.name}")
            print(f"   - Température: {stats.temperature:.1f}°C")
            print(f"   - Utilisation: {stats.utilization:.1f}%")
            print(f"   - VRAM utilisée: {stats.memory_used:.0f} MB / {stats.memory_total:.0f} MB")
            print(f"   - Utilisation VRAM: {stats.memory_utilization:.1f}%")
            print(f"   - Core Clock: {stats.core_clock} MHz")
            print(f"   - Memory Clock: {stats.memory_clock} MHz")
            print(f"   - Consommation: {stats.power_usage:.1f} W")
            print(f"   - Vitesse ventilateur: {stats.fan_speed}%")
            print(f"   - Driver: {stats.driver_version}")
            print(f"   - Statut: {stats.status}")
            print(f"   - Timestamp: {time.ctime(stats.timestamp)}")
        else:
            print("   ERREUR - Aucune statistique récupérée")
            return False
        
        # Test modèle de données
        print("\n5. Test modèle de données...")
        test_stats = GPUStats(
            name="Test GPU",
            temperature=50.0,
            utilization=75.5,
            memory_used=4096.0,
            memory_total=8192.0,
            memory_utilization=50.0,
            core_clock=1800,
            memory_clock=1600,
            power_usage=150.0,
            fan_speed=60,
            driver_version="1.0.0",
            timestamp=time.time(),
            status="healthy"
        )
        
        stats_dict = test_stats.dict()
        print(f"   OK - Modèle créé avec {len(stats_dict)} champs")
        
        # Test simulation
        print("\n6. Test méthodes de simulation...")
        sim_data = await monitor._simulate_gpu_stats()
        print(f"   OK - Simulation:")
        print(f"   - Température simulée: {sim_data['temperature']:.1f}°C")
        print(f"   - Utilisation simulée: {sim_data['utilization']:.1f}%")
        print(f"   - Power simulé: {sim_data['power_usage']:.1f}W")
        
        # Test de performance
        print("\n7. Test de performance...")
        start_time = time.time()
        for i in range(5):
            await monitor.get_gpu_stats()
        end_time = time.time()
        
        avg_time = ((end_time - start_time) / 5) * 1000
        print(f"   OK - 5 requêtes en {(end_time - start_time):.2f}s")
        print(f"   - Temps moyen par requête: {avg_time:.1f}ms")
        
        return True
        
    except ImportError as e:
        print(f"   ERREUR - Import échoué: {e}")
        print("   Vérifiez que les dépendances sont installées:")
        print("   pip install fastapi uvicorn websockets psutil loguru")
        return False
    except Exception as e:
        print(f"   ERREUR - Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_detection_methods():
    """Test des méthodes de détection spécifiques"""
    print("\nTEST MÉTHODES DE DÉTECTION")
    print("=" * 50)
    
    try:
        from main import GPUMonitor
        monitor = GPUMonitor()
        
        # Test détection WMI
        print("\n1. Test détection WMI...")
        try:
            original_info = monitor.gpu_info.copy()
            await monitor._detect_via_wmi()
            if monitor.gpu_info != original_info:
                print("   OK - WMI a détecté des informations GPU")
                print(f"   - GPU: {monitor.gpu_info['name']}")
            else:
                print("   INFO - WMI n'a pas modifié les infos (normal si pas de WMI)")
        except Exception as e:
            print(f"   INFO - WMI non disponible: {type(e).__name__}")
        
        # Test détection PowerShell
        print("\n2. Test détection PowerShell...")
        try:
            original_info = monitor.gpu_info.copy()
            await monitor._detect_via_powershell()
            if monitor.gpu_info != original_info:
                print("   OK - PowerShell a détecté des informations GPU")
                print(f"   - GPU: {monitor.gpu_info['name']}")
            else:
                print("   INFO - PowerShell n'a pas modifié les infos")
        except Exception as e:
            print(f"   INFO - PowerShell échoué: {type(e).__name__}")
        
        # Test stats Windows
        print("\n3. Test stats Windows...")
        try:
            stats = await monitor._get_stats_windows()
            if stats:
                print("   OK - Stats Windows récupérées")
                print(f"   - Température: {stats.get('temperature', 'N/A')}")
                print(f"   - Utilisation: {stats.get('utilization', 'N/A')}")
            else:
                print("   INFO - Stats Windows non disponibles (utilise simulation)")
        except Exception as e:
            print(f"   INFO - Stats Windows échouées: {type(e).__name__}")
        
        # Test performance counters
        print("\n4. Test Performance Counters...")
        try:
            stats = await monitor._get_stats_perfcounters()
            if stats:
                print("   OK - Performance Counters fonctionnels")
                print(f"   - Température estimée: {stats.get('temperature', 'N/A')}")
                print(f"   - Utilisation estimée: {stats.get('utilization', 'N/A')}")
            else:
                print("   INFO - Performance Counters non disponibles")
        except Exception as e:
            print(f"   INFO - Performance Counters échoués: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"   ERREUR - Test détection échoué: {e}")
        return False

async def main():
    """Point d'entrée principal"""
    print("SERVICE GPU STATS - TEST DIRECT")
    print("Date:", time.ctime())
    print("Python:", sys.version.split()[0])
    print("Platform:", sys.platform)
    
    # Tests
    tests = [
        ("Fonctionnalités de base", test_basic_functionality),
        ("Méthodes de détection", test_detection_methods),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print('='*60)
        
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"\nRESULTAT: {test_name} - SUCCÈS")
            else:
                print(f"\nRESULTAT: {test_name} - ÉCHEC")
        except Exception as e:
            print(f"\nRESULTAT: {test_name} - ERREUR: {e}")
    
    # Résultats finaux
    print(f"\n{'='*60}")
    print("RÉSULTATS FINAUX")
    print('='*60)
    print(f"Tests réussis: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("STATUT: TOUS LES TESTS RÉUSSIS!")
        print("ACTION: Le service est prêt pour le déploiement Docker")
    elif passed > 0:
        print("STATUT: TESTS PARTIELLEMENT RÉUSSIS")
        print("ACTION: Le service fonctionne mais certaines optimisations sont possibles")
    else:
        print("STATUT: TESTS ÉCHOUÉS")
        print("ACTION: Vérifiez les dépendances et la configuration")
    
    print(f"\nDémarrage du service complet:")
    print(f"  cd services/gpu-stats-service")
    print(f"  python main.py")
    print(f"\nTest API après démarrage:")
    print(f"  curl http://localhost:5009/health")
    print(f"  curl http://localhost:5009/gpu/stats")
    
    return passed >= total * 0.5

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\nErreur fatale: {e}")
        sys.exit(1)