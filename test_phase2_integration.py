#!/usr/bin/env python3
"""
🧪 Tests d'intégration JARVIS Phase 2
Tests complets de validation des fonctionnalités
"""

import asyncio
import sys
import time
import requests
from pathlib import Path
from loguru import logger

class Phase2IntegrationTester:
    """Testeur d'intégration pour JARVIS Phase 2"""
    
    def __init__(self):
        self.api_base_url = "http://127.0.0.1:8000"
        self.test_results = {}
        
    async def setup_test_environment(self):
        """Prépare l'environnement de test"""
        logger.info("🔧 Préparation de l'environnement de test...")
        
        # Vérifier que l'API est accessible
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
            if response.status_code == 200:
                logger.success("✅ API JARVIS accessible")
                return True
            else:
                logger.error("❌ API JARVIS non accessible")
                return False
        except Exception as e:
            logger.error(f"❌ Impossible de contacter l'API: {e}")
            return False
    
    async def test_api_health(self):
        """Test de santé de l'API"""
        logger.info("🏥 Test de santé de l'API...")
        
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.test_results['api_health'] = True
                    logger.success("✅ API en bonne santé")
                    return True
            
            self.test_results['api_health'] = False
            logger.error("❌ API en mauvaise santé")
            return False
            
        except Exception as e:
            logger.error(f"❌ Test santé API échoué: {e}")
            self.test_results['api_health'] = False
            return False
    
    async def test_system_status(self):
        """Test du statut système"""
        logger.info("💻 Test du statut système...")
        
        try:
            response = requests.get(f"{self.api_base_url}/api/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['success', 'system']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Champ manquant: {field}")
                
                self.test_results['system_status'] = True
                logger.success("✅ Statut système OK")
                return True
            else:
                raise ValueError(f"Code de statut inattendu: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Test statut système échoué: {e}")
            self.test_results['system_status'] = False
            return False
    
    async def test_command_execution(self):
        """Test d'exécution de commande"""
        logger.info("⚡ Test d'exécution de commande...")
        
        try:
            command_data = {
                "command": "take a screenshot",
                "mode": "plan"
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/command",
                json=command_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['success']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Champ manquant: {field}")
                
                if data.get('success'):
                    self.test_results['command_execution'] = True
                    logger.success("✅ Commande exécutée avec succès")
                    return True
                else:
                    raise ValueError("Commande non réussie")
            else:
                raise ValueError(f"Code de statut inattendu: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Test exécution commande échoué: {e}")
            self.test_results['command_execution'] = False
            return False
    
    async def test_screenshot_api(self):
        """Test de l'API de capture d'écran"""
        logger.info("📸 Test de l'API de capture d'écran...")
        
        try:
            response = requests.get(f"{self.api_base_url}/api/screenshot", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    self.test_results['screenshot_api'] = True
                    logger.success("✅ Capture d'écran OK")
                    return True
                else:
                    raise ValueError("Capture non réussie")
            else:
                raise ValueError(f"Code de statut inattendu: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Test capture d'écran échoué: {e}")
            self.test_results['screenshot_api'] = False
            return False
    
    async def cleanup_test_environment(self):
        """Nettoyage après tests"""
        logger.info("🧹 Nettoyage de l'environnement de test...")
        # Cleanup si nécessaire
        pass
    
    async def run_integration_tests(self):
        """Lance tous les tests d'intégration"""
        logger.info("🚀 Démarrage des tests d'intégration Phase 2...")
        
        start_time = time.time()
        
        # Setup
        if not await self.setup_test_environment():
            logger.error("❌ Impossible de préparer l'environnement de test")
            return False
        
        try:
            # Tests individuels
            tests = [
                ("API Health", self.test_api_health),
                ("System Status", self.test_system_status),
                ("Command Execution", self.test_command_execution),
                ("Screenshot API", self.test_screenshot_api),
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                logger.info(f"\n▶️  Test: {test_name}")
                try:
                    success = await test_func()
                    if success:
                        passed_tests += 1
                except Exception as e:
                    logger.error(f"❌ Erreur inattendue dans {test_name}: {e}")
                    self.test_results[test_name.lower().replace(' ', '_')] = False
            
            # Résultats finaux
            execution_time = time.time() - start_time
            
            logger.info("\n" + "="*60)
            logger.info("📊 RÉSULTATS DES TESTS D'INTÉGRATION PHASE 2")
            logger.info("="*60)
            
            for test_name, result in self.test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"  {test_name.replace('_', ' ').title()}: {status}")
            
            total_score = (passed_tests / total_tests) * 100
            
            logger.info(f"\n🎯 Score global: {passed_tests}/{total_tests} tests réussis ({total_score:.1f}%)")
            logger.info(f"⏱️  Temps d'exécution: {execution_time:.2f}s")
            
            # Déterminer le succès global
            if total_score >= 75:
                logger.success("\n🎉 JARVIS Phase 2 - INTÉGRATION RÉUSSIE!")
                return True
            else:
                logger.error("\n❌ JARVIS Phase 2 - INTÉGRATION ÉCHOUÉE")
                return False
        
        finally:
            await self.cleanup_test_environment()


async def main():
    """Point d'entrée principal"""
    print("""
    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
    ██║███████║██████╔╝██║   ██║██║███████╗
    ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
    ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║
    ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
    
    🧪 Tests d'Intégration Phase 2
    """)
    
    tester = Phase2IntegrationTester()
    success = await tester.run_integration_tests()
    
    if success:
        logger.success("🎉 Phase 2 complètement opérationnelle!")
        return 0
    else:
        logger.error("❌ Phase 2 nécessite des corrections")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n👋 Tests interrompus par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1) 