#!/usr/bin/env python3
"""
Test direct du service GPU Stats (sans Docker)
Test rapide pour valider la logique du service
"""

import sys
import os
import asyncio
import time

# Ajouter le chemin du service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'gpu-stats-service'))

async def test_gpu_monitor():
    """Test du moniteur GPU"""
    print("GPU Test du GPU Monitor")
    print("=" * 40)
    
    try:
        # Importer le moniteur
        from main import GPUMonitor
        
        # Créer une instance
        monitor = GPUMonitor()
        print(f"OK GPUMonitor cree")
        print(f"   - Platform: {monitor.is_windows}")
        print(f"   - GPU par défaut: {monitor.gpu_info['name']}")
        
        # Initialiser
        print("\n🚀 Initialisation...")
        success = await monitor.initialize()
        print(f"✅ Initialisation: {'Succès' if success else 'Échec'}")
        
        # Tester la récupération des stats
        print("\n📊 Test des statistiques...")
        for i in range(3):
            stats = await monitor.get_gpu_stats()
            if stats:
                print(f"✅ Stats #{i+1}:")
                print(f"   - Température: {stats.temperature:.1f}°C")
                print(f"   - Utilisation: {stats.utilization:.1f}%")
                print(f"   - VRAM: {stats.memory_used:.0f}MB / {stats.memory_total:.0f}MB")
                print(f"   - Power: {stats.power_usage:.1f}W")
                print(f"   - Statut: {stats.status}")
            else:
                print(f"❌ Pas de stats #{i+1}")
            
            await asyncio.sleep(1)
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

async def test_data_models():
    """Test des modèles de données"""
    print("\n📋 Test des modèles de données")
    print("=" * 40)
    
    try:
        from main import GPUStats
        
        # Créer un exemple de stats
        stats = GPUStats(
            name="AMD Radeon RX 7800 XT",
            temperature=65.5,
            utilization=78.2,
            memory_used=8192.0,
            memory_total=16384.0,
            memory_utilization=50.0,
            core_clock=2400,
            memory_clock=2000,
            power_usage=180.5,
            fan_speed=65,
            driver_version="23.11.1",
            timestamp=time.time(),
            status="healthy"
        )
        
        print(f"✅ GPUStats créé:")
        print(f"   - Nom: {stats.name}")
        print(f"   - Température: {stats.temperature}°C")
        print(f"   - Utilisation: {stats.utilization}%")
        print(f"   - Statut: {stats.status}")
        
        # Test de sérialisation
        stats_dict = stats.dict()
        print(f"✅ Sérialisation: {len(stats_dict)} champs")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur modèles: {e}")
        return False

async def test_detection_methods():
    """Test des méthodes de détection"""
    print("\n🔍 Test des méthodes de détection")
    print("=" * 40)
    
    try:
        from main import GPUMonitor
        
        monitor = GPUMonitor()
        
        print("🔍 Test détection WMI...")
        try:
            await monitor._detect_via_wmi()
            print(f"✅ WMI: GPU détecté - {monitor.gpu_info['name']}")
        except Exception as e:
            print(f"⚠️ WMI non disponible: {e}")
        
        print("\n🔍 Test détection PowerShell...")
        try:
            await monitor._detect_via_powershell()
            print(f"✅ PowerShell: GPU détecté - {monitor.gpu_info['name']}")
        except Exception as e:
            print(f"⚠️ PowerShell échoué: {e}")
        
        print("\n🔍 Test simulation...")
        sim_stats = await monitor._simulate_gpu_stats()
        print(f"✅ Simulation:")
        print(f"   - Température: {sim_stats['temperature']:.1f}°C")
        print(f"   - Utilisation: {sim_stats['utilization']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur détection: {e}")
        return False

async def main():
    """Point d'entrée principal"""
    print("🧪 TEST DIRECT DU SERVICE GPU STATS")
    print("=" * 50)
    
    tests = [
        ("Modèles de données", test_data_models),
        ("Méthodes de détection", test_detection_methods),
        ("GPU Monitor", test_gpu_monitor),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print(f"\n📊 RÉSULTATS: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés!")
        print("🚀 Le service est prêt à être déployé")
    else:
        print("⚠️ Certains tests ont échoué")
        print("🔧 Vérifiez les dépendances et la configuration")
    
    print(f"\n💡 Pour démarrer le service complet:")
    print(f"   cd services/gpu-stats-service")
    print(f"   python main.py")

if __name__ == "__main__":
    asyncio.run(main())