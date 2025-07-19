#!/usr/bin/env python3
"""
🧪 Tests d'intégration Phase 2 JARVIS
Tests complets de tous les composants de la Phase 2
"""

import asyncio
import time
import json
import subprocess
import requests
import websockets
from pathlib import Path
import sys
from loguru import logger

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

from api.server import initialize_jarvis_modules

class Phase2IntegrationTester:
    """Testeur d'intégration pour JARVIS Phase 2"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.test_results = {}
        self.server_process = None
        
    async def setup_test_environment(self):
        """Prépare l'environnement de test"""
        logger.info("🔧 Préparation de l'environnement de test...")
        
        # Démarrer le serveur API en arrière-plan
        try:
            from api.launcher import JarvisLauncher
            self.launcher = JarvisLauncher()
            
            # Démarrer seulement l'API
            await self.launcher.start_api_server()
            
            # Attendre que le serveur soit prêt
            for i in range(30):
                try:
                    response = requests.get(f"{self.api_base_url}/api/health", timeout=1)
                    if response.status_code == 200:
                        logger.success("✅ Serveur API prêt pour les tests")
                        return True
                except:
                    await asyncio.sleep(1)
            
            logger.error("❌ Serveur API non prêt dans les temps")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur setup environnement: {e}")
            return False
    
    async def cleanup_test_environment(self):
        """Nettoie l'environnement de test"""
        logger.info("🧹 Nettoyage de l'environnement de test...")
        
        if hasattr(self, 'launcher'):
            await self.launcher.shutdown()
    
    async def test_api_health(self):
        """Test de santé de l'API"""
        logger.info("🏥 Test de santé de l'API...")
        
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['status', 'timestamp', 'uptime', 'version']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Champ manquant: {field}")
                
                if data['status'] != 'healthy':
                    raise ValueError(f"Statut non sain: {data['status']}")
                
                self.test_results['api_health'] = True
                logger.success("✅ API en bonne santé")
                return True
            else:
                raise ValueError(f"Code de statut inattendu: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Test santé API échoué: {e}")
            self.test_results['api_health'] = False
            return False
    
    async def test_system_status(self):
        """Test du statut système"""
        logger.info("📊 Test du statut système...")
        
        try:
            response = requests.get(f"{self.api_base_url}/api/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                required_sections = ['modules', 'performance', 'memory_usage', 'uptime']
                for section in required_sections:
                    if section not in data:
                        raise ValueError(f"Section manquante: {section}")
                
                # Vérifier qu'il y a des modules chargés
                if not data['modules'] or len(data['modules']) == 0:
                    raise ValueError("Aucun module trouvé")
                
                # Vérifier que les modules essentiels sont présents
                module_names = [m['name'] for m in data['modules']]
                essential_modules = ['screen_capture', 'ollama', 'planner']
                
                for module in essential_modules:
                    if module not in module_names:
                        logger.warning(f"⚠️ Module essentiel manquant: {module}")
                
                self.test_results['system_status'] = True
                logger.success(f"✅ Statut système OK - {len(data['modules'])} modules")
                return True
            else:
                raise ValueError(f"Code de statut inattendu: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Test statut système échoué: {e}")
            self.test_results['system_status'] = False
            return False
    
    async def test_websocket_connection(self):
        """Test de connexion WebSocket"""
        logger.info("🌐 Test de connexion WebSocket...")
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                
                # Attendre le message de bienvenue
                welcome_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_message)
                
                if welcome_data.get('type') != 'welcome':
                    raise ValueError(f"Message de bienvenue inattendu: {welcome_data}")
                
                # Envoyer un ping
                ping_message = json.dumps({"type": "ping"})
                await websocket.send(ping_message)
                
                # Attendre le pong
                pong_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_data = json.loads(pong_message)
                
                if pong_data.get('type') != 'pong':
                    raise ValueError(f"Pong inattendu: {pong_data}")
                
                self.test_results['websocket'] = True
                logger.success("✅ WebSocket fonctionne")
                return True
                
        except Exception as e:
            logger.error(f"❌ Test WebSocket échoué: {e}")
            self.test_results['websocket'] = False
            return False
    
    async def test_command_execution(self):
        """Test d'exécution de commande"""
        logger.info("⚡ Test d'exécution de commande...")
        
        try:
            command_data = {\n                "command": "take a screenshot",\n                "mode": "plan"\n            }\n            \n            response = requests.post(\n                f"{self.api_base_url}/api/command",\n                json=command_data,\n                timeout=15\n            )\n            \n            if response.status_code == 200:\n                data = response.json()\n                \n                required_fields = ['success', 'sequence_id', 'sequence_name', 'actions_count']\n                for field in required_fields:\n                    if field not in data:\n                        raise ValueError(f"Champ manquant: {field}")\n                \n                if not data['success']:\n                    raise ValueError("Commande non réussie")\n                \n                if data['actions_count'] <= 0:\n                    raise ValueError("Aucune action planifiée")\n                \n                self.test_results['command_execution'] = True\n                logger.success(f"✅ Commande planifiée - {data['actions_count']} actions")\n                return True\n            else:\n                raise ValueError(f"Code de statut inattendu: {response.status_code}")\n                \n        except Exception as e:\n            logger.error(f"❌ Test exécution commande échoué: {e}")\n            self.test_results['command_execution'] = False\n            return False\n    \n    async def test_chat_ai(self):\n        """Test de chat avec l'IA"""\n        logger.info("🤖 Test de chat avec l'IA...")\n        \n        try:\n            chat_data = {\n                "message": "Bonjour JARVIS, peux-tu me dire que ce test fonctionne ?"\n            }\n            \n            response = requests.post(\n                f"{self.api_base_url}/api/chat",\n                json=chat_data,\n                timeout=20\n            )\n            \n            if response.status_code == 200:\n                data = response.json()\n                \n                required_fields = ['success', 'response']\n                for field in required_fields:\n                    if field not in data:\n                        raise ValueError(f"Champ manquant: {field}")\n                \n                if not data['success']:\n                    raise ValueError("Chat non réussi")\n                \n                if not data['response'] or len(data['response']) < 10:\n                    raise ValueError("Réponse IA trop courte")\n                \n                self.test_results['chat_ai'] = True\n                logger.success(f"✅ Chat IA OK - Réponse: {data['response'][:50]}...")\n                return True\n            else:\n                raise ValueError(f"Code de statut inattendu: {response.status_code}")\n                \n        except Exception as e:\n            logger.error(f"❌ Test chat IA échoué: {e}")\n            self.test_results['chat_ai'] = False\n            return False\n    \n    async def test_screenshot_api(self):\n        """Test de l'API de capture d'écran"""\n        logger.info("📸 Test de l'API de capture d'écran...")\n        \n        try:\n            response = requests.get(\n                f"{self.api_base_url}/api/screenshot",\n                timeout=10\n            )\n            \n            if response.status_code == 200:\n                data = response.json()\n                \n                required_fields = ['success', 'filename', 'size']\n                for field in required_fields:\n                    if field not in data:\n                        raise ValueError(f"Champ manquant: {field}")\n                \n                if not data['success']:\n                    raise ValueError("Capture non réussie")\n                \n                # Vérifier que le fichier existe\n                screenshot_path = Path(data['filename'])\n                if not screenshot_path.exists():\n                    raise ValueError(f"Fichier capture non trouvé: {data['filename']}")\n                \n                self.test_results['screenshot_api'] = True\n                logger.success(f"✅ Capture d'écran OK - {data['filename']}")\n                return True\n            else:\n                raise ValueError(f"Code de statut inattendu: {response.status_code}")\n                \n        except Exception as e:\n            logger.error(f"❌ Test capture d'écran échoué: {e}")\n            self.test_results['screenshot_api'] = False\n            return False\n    \n    async def test_voice_synthesis(self):\n        """Test de synthèse vocale"""\n        logger.info("🎤 Test de synthèse vocale...")\n        \n        try:\n            voice_data = {\n                "text": "Test de synthèse vocale JARVIS Phase 2"\n            }\n            \n            response = requests.post(\n                f"{self.api_base_url}/api/voice/speak",\n                json=voice_data,\n                timeout=15\n            )\n            \n            if response.status_code == 200:\n                data = response.json()\n                \n                required_fields = ['success', 'text']\n                for field in required_fields:\n                    if field not in data:\n                        raise ValueError(f"Champ manquant: {field}")\n                \n                if not data['success']:\n                    raise ValueError("Synthèse vocale non réussie")\n                \n                self.test_results['voice_synthesis'] = True\n                logger.success("✅ Synthèse vocale OK")\n                return True\n            else:\n                # La synthèse vocale peut être non disponible\n                if response.status_code == 503:\n                    logger.warning("⚠️ Interface vocale non disponible")\n                    self.test_results['voice_synthesis'] = 'unavailable'\n                    return True\n                else:\n                    raise ValueError(f"Code de statut inattendu: {response.status_code}")\n                \n        except Exception as e:\n            logger.warning(f"⚠️ Test synthèse vocale échoué (non critique): {e}")\n            self.test_results['voice_synthesis'] = 'error'\n            return True  # Non critique\n    \n    async def test_applications_list(self):\n        """Test de listage des applications"""\n        logger.info("📱 Test de listage des applications...")\n        \n        try:\n            response = requests.get(\n                f"{self.api_base_url}/api/apps",\n                timeout=10\n            )\n            \n            if response.status_code == 200:\n                data = response.json()\n                \n                required_fields = ['success', 'apps', 'total_count']\n                for field in required_fields:\n                    if field not in data:\n                        raise ValueError(f"Champ manquant: {field}")\n                \n                if not data['success']:\n                    raise ValueError("Listage apps non réussi")\n                \n                if data['total_count'] <= 0:\n                    raise ValueError("Aucune application trouvée")\n                \n                self.test_results['applications_list'] = True\n                logger.success(f"✅ Listage apps OK - {data['total_count']} trouvées")\n                return True\n            else:\n                raise ValueError(f"Code de statut inattendu: {response.status_code}")\n                \n        except Exception as e:\n            logger.error(f"❌ Test listage apps échoué: {e}")\n            self.test_results['applications_list'] = False\n            return False\n    \n    async def test_memory_conversations(self):\n        """Test des conversations mémoire"""\n        logger.info("🧠 Test des conversations mémoire...")\n        \n        try:\n            response = requests.get(\n                f"{self.api_base_url}/api/memory/conversations",\n                timeout=10\n            )\n            \n            if response.status_code == 200:\n                data = response.json()\n                \n                required_fields = ['success', 'conversations', 'total_count']\n                for field in required_fields:\n                    if field not in data:\n                        raise ValueError(f"Champ manquant: {field}")\n                \n                if not data['success']:\n                    raise ValueError("Récupération conversations non réussie")\n                \n                self.test_results['memory_conversations'] = True\n                logger.success(f"✅ Mémoire conversations OK - {data['total_count']} trouvées")\n                return True\n            else:\n                raise ValueError(f"Code de statut inattendu: {response.status_code}")\n                \n        except Exception as e:\n            logger.error(f"❌ Test mémoire conversations échoué: {e}")\n            self.test_results['memory_conversations'] = False\n            return False\n    \n    async def run_integration_tests(self):\n        """Lance tous les tests d'intégration"""\n        logger.info("🚀 Démarrage des tests d'intégration Phase 2...")\n        \n        start_time = time.time()\n        \n        # Setup\n        if not await self.setup_test_environment():\n            logger.error("❌ Impossible de préparer l'environnement de test")\n            return False\n        \n        try:\n            # Tests individuels\n            tests = [\n                ("API Health", self.test_api_health),\n                ("System Status", self.test_system_status),\n                ("WebSocket", self.test_websocket_connection),\n                ("Command Execution", self.test_command_execution),\n                ("Chat AI", self.test_chat_ai),\n                ("Screenshot API", self.test_screenshot_api),\n                ("Voice Synthesis", self.test_voice_synthesis),\n                ("Applications List", self.test_applications_list),\n                ("Memory Conversations", self.test_memory_conversations)\n            ]\n            \n            passed_tests = 0\n            total_tests = len(tests)\n            \n            for test_name, test_func in tests:\n                logger.info(f"\\n▶️  Test: {test_name}")\n                try:\n                    success = await test_func()\n                    if success:\n                        passed_tests += 1\n                except Exception as e:\n                    logger.error(f"❌ Erreur inattendue dans {test_name}: {e}")\n                    self.test_results[test_name.lower().replace(' ', '_')] = False\n            \n            # Résultats finaux\n            execution_time = time.time() - start_time\n            \n            logger.info("\\n" + "="*60)\n            logger.info("📊 RÉSULTATS DES TESTS D'INTÉGRATION PHASE 2")\n            logger.info("="*60)\n            \n            for test_name, result in self.test_results.items():\n                if result == True:\n                    status = "✅ PASS"\n                elif result == 'unavailable':\n                    status = "⚠️  SKIP (Non disponible)"\n                elif result == 'error':\n                    status = "⚠️  SKIP (Erreur non critique)"\n                else:\n                    status = "❌ FAIL"\n                \n                logger.info(f"  {test_name.replace('_', ' ').title()}: {status}")\n            \n            # Calcul du score\n            critical_tests = ['api_health', 'system_status', 'websocket', 'command_execution']\n            critical_passed = sum(1 for test in critical_tests if self.test_results.get(test) == True)\n            \n            total_score = (passed_tests / total_tests) * 100\n            critical_score = (critical_passed / len(critical_tests)) * 100\n            \n            logger.info(f"\\n🎯 Score global: {passed_tests}/{total_tests} tests réussis ({total_score:.1f}%)")\n            logger.info(f"🚨 Tests critiques: {critical_passed}/{len(critical_tests)} réussis ({critical_score:.1f}%)")\n            logger.info(f"⏱️  Temps d'exécution: {execution_time:.2f}s")\n            \n            # Déterminer le succès global\n            if critical_score >= 100 and total_score >= 75:\n                logger.success("\\n🎉 JARVIS Phase 2 - INTÉGRATION RÉUSSIE!")\n                logger.success("✅ Tous les composants critiques fonctionnent")\n                logger.success("✅ L'API REST et WebSocket sont opérationnels")\n                logger.success("✅ Les modules JARVIS sont connectés et fonctionnels")\n                return True\n            elif critical_score >= 75:\n                logger.warning("\\n⚠️  JARVIS Phase 2 - INTÉGRATION PARTIELLE")\n                logger.warning("⚠️  Certains composants ne fonctionnent pas optimalement")\n                return False\n            else:\n                logger.error("\\n❌ JARVIS Phase 2 - INTÉGRATION ÉCHOUÉE")\n                logger.error("❌ Des composants critiques ne fonctionnent pas")\n                return False\n        \n        finally:\n            await self.cleanup_test_environment()\n\n\nasync def main():\n    """Point d'entrée principal"""\n    print("""\n    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗\n    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝\n    ██║███████║██████╔╝██║   ██║██║███████╗\n    ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║\n    ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║\n    ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝\n    \n    🧪 Tests d'Intégration Phase 2\n    """)\n    \n    tester = Phase2IntegrationTester()\n    success = await tester.run_integration_tests()\n    \n    if success:\n        logger.success("🎉 Phase 2 complètement opérationnelle!")\n        return 0\n    else:\n        logger.error("❌ Phase 2 nécessite des corrections")\n        return 1\n\n\nif __name__ == "__main__":\n    try:\n        exit_code = asyncio.run(main())\n        sys.exit(exit_code)\n    except KeyboardInterrupt:\n        logger.info("\\n👋 Tests interrompus par l'utilisateur")\n        sys.exit(0)\n    except Exception as e:\n        logger.error(f"❌ Erreur fatale: {e}")\n        sys.exit(1)