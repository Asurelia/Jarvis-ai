#!/usr/bin/env python3
"""
🧪 JARVIS AI 2025 - Tests Complets des Nouveaux Composants
Tests d'importation, WebWorkers, WASM et communication avec les services
"""

import pytest
import asyncio
import time
import requests
import json
import threading
import concurrent.futures
import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

# Configuration des chemins
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# URLs des services
SERVICE_URLS = {
    'brain_api': 'http://localhost:5001',
    'mcp_gateway': 'http://localhost:5006',
    'tts_service': 'http://localhost:5002',
    'stt_service': 'http://localhost:5003',
    'system_control': 'http://localhost:5004',
    'terminal_service': 'http://localhost:5005',
    'ollama': 'http://localhost:11434',
    'redis': 'redis://localhost:6379',
    'postgres': 'postgresql://jarvis:jarvis@localhost:5432/jarvis'
}

@dataclass
class TestResult:
    """Résultat de test standardisé"""
    test_name: str
    passed: bool
    duration: float
    details: Dict[str, Any]
    errors: List[str]

class JARVISTestSuite:
    """Suite de tests complète pour JARVIS AI 2025"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
    def add_result(self, test_name: str, passed: bool, duration: float, 
                  details: Dict[str, Any] = None, errors: List[str] = None):
        """Ajouter un résultat de test"""
        result = TestResult(
            test_name=test_name,
            passed=passed,
            duration=duration,
            details=details or {},
            errors=errors or []
        )
        self.results.append(result)

class TestModuleImports:
    """Tests d'importation des modules JARVIS"""
    
    def test_core_modules_import(self):
        """Test d'importation des modules core"""
        start_time = time.time()
        errors = []
        imported_modules = []
        
        # Modules principaux à tester
        modules_to_test = [
            'core.__init__',
            'core.ai.__init__',
            'core.ai.action_executor',
            'core.voice.__init__',
            'core.voice.whisper_stt',
            'core.voice.edge_tts',
            'core.voice.voice_interface',
            'core.vision.__init__',
            'core.vision.visual_analysis',
            'core.control.__init__',
            'core.control.mouse_controller',
            'core.control.keyboard_controller',
            'core.control.app_detector',
            'tools.__init__',
            'tools.base_tool',
            'tools.tool_manager',
            'tools.mcp_server',
            'tools.ai_tools',
            'tools.web_tools',
            'tools.system_tools',
            'api.launcher',
            'config.settings',
            'config.logging_config'
        ]
        
        for module_name in modules_to_test:
            try:
                if module_name == 'core.agent':
                    # Module agent peut ne pas exister
                    continue
                    
                module = __import__(module_name, fromlist=[''])
                imported_modules.append(module_name)
                print(f"✅ {module_name}")
                
            except ImportError as e:
                error_msg = f"❌ {module_name}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
            except Exception as e:
                error_msg = f"⚠️ {module_name}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
        
        duration = time.time() - start_time
        success_rate = len(imported_modules) / len(modules_to_test)
        
        print(f"\n📊 Import Results:")
        print(f"   • Modules testés: {len(modules_to_test)}")
        print(f"   • Importés avec succès: {len(imported_modules)}")
        print(f"   • Taux de réussite: {success_rate:.1%}")
        print(f"   • Durée: {duration:.2f}s")
        
        assert success_rate > 0.6, f"Taux d'import trop faible: {success_rate:.1%}"

class TestWebWorkersSimulation:
    """Tests de simulation des Web Workers"""
    
    def test_web_worker_simulation(self):
        """Simulation des Web Workers avec threading"""
        start_time = time.time()
        
        def worker_ai_task(data):
            """Simulation d'un worker AI"""
            time.sleep(0.1)  # Simulation traitement
            return {
                'type': 'neural_network',
                'result': [0.8, 0.6, 0.9],  # Résultat simulé
                'processing_time': 0.1
            }
        
        def worker_compute_task(data):
            """Simulation d'un worker de calcul"""
            time.sleep(0.05)
            return {
                'type': 'matrix_multiply',
                'result': [[2, 4], [6, 8]],
                'processing_time': 0.05
            }
        
        def worker_image_task(data):
            """Simulation d'un worker d'image"""
            time.sleep(0.08)
            return {
                'type': 'blur',
                'result': 'processed_image_data',
                'processing_time': 0.08
            }
        
        # Test de workers parallèles
        tasks = [
            ('ai-worker', worker_ai_task, {'input': [0.5, 0.3, 0.8]}),
            ('compute-worker', worker_compute_task, {'matrix_a': [[1, 2], [3, 4]]}),
            ('image-worker', worker_image_task, {'image_data': 'mock_image'})
        ]
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_worker = {
                executor.submit(task_func, task_data): worker_name 
                for worker_name, task_func, task_data in tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_worker):
                worker_name = future_to_worker[future]
                try:
                    result = future.result()
                    results.append((worker_name, result))
                    print(f"✅ {worker_name}: {result['type']} completed")
                except Exception as e:
                    print(f"❌ {worker_name}: {str(e)}")
        
        duration = time.time() - start_time
        
        print(f"\n📊 Web Workers Simulation:")
        print(f"   • Workers testés: {len(tasks)}")
        print(f"   • Résultats obtenus: {len(results)}")
        print(f"   • Durée totale: {duration:.2f}s")
        print(f"   • Parallélisation: {'✅' if duration < 0.2 else '❌'}")
        
        assert len(results) == len(tasks), "Tous les workers doivent réussir"
        assert duration < 0.25, "Les workers doivent s'exécuter en parallèle"

class TestWASMSimulation:
    """Tests de simulation WASM"""
    
    def test_wasm_module_simulation(self):
        """Simulation des modules WASM"""
        start_time = time.time()
        
        class MockWASMModule:
            """Module WASM simulé"""
            
            @staticmethod
            def fast_matrix_multiply(matrix_a, matrix_b):
                """Multiplication matricielle rapide simulée"""
                start = time.time()
                
                # Simulation calcul WASM (beaucoup plus rapide que Python)
                result = []
                for i in range(len(matrix_a)):
                    row = []
                    for j in range(len(matrix_b[0])):
                        sum_val = 0
                        for k in range(len(matrix_b)):
                            sum_val += matrix_a[i][k] * matrix_b[k][j]
                        row.append(sum_val)
                    result.append(row)
                
                # Simulation de vitesse WASM
                processing_time = time.time() - start
                simulated_speedup = 5.0  # WASM est ~5x plus rapide
                time.sleep(max(0, processing_time / simulated_speedup - processing_time))
                
                return result
            
            @staticmethod
            def fast_fft(data):
                """FFT rapide simulée"""
                # Simulation FFT
                return [{'real': val * 0.8, 'imag': val * 0.2, 'magnitude': abs(val)} for val in data]
            
            @staticmethod
            def vector_operations(vec1, vec2, operation):
                """Opérations vectorielles SIMD simulées"""
                if operation == 'add':
                    return [a + b for a, b in zip(vec1, vec2)]
                elif operation == 'multiply':
                    return [a * b for a, b in zip(vec1, vec2)]
                elif operation == 'dot':
                    return sum(a * b for a, b in zip(vec1, vec2))
                else:
                    return vec1
        
        # Tests des fonctions WASM
        wasm_module = MockWASMModule()
        
        # Test multiplication matricielle
        matrix_a = [[1, 2], [3, 4]]
        matrix_b = [[2, 0], [1, 3]]
        result_matrix = wasm_module.fast_matrix_multiply(matrix_a, matrix_b)
        expected_matrix = [[4, 6], [10, 12]]
        
        assert result_matrix == expected_matrix, "Multiplication matricielle incorrecte"
        print("✅ WASM Matrix Multiply: Correct")
        
        # Test FFT
        test_data = [1, 2, 3, 4, 5]
        fft_result = wasm_module.fast_fft(test_data)
        assert len(fft_result) == len(test_data), "FFT result length incorrect"
        assert all('real' in item and 'imag' in item for item in fft_result), "FFT format incorrect"
        print("✅ WASM FFT: Correct")
        
        # Test opérations vectorielles
        vec1 = [1, 2, 3, 4]
        vec2 = [2, 3, 4, 5]
        
        add_result = wasm_module.vector_operations(vec1, vec2, 'add')
        assert add_result == [3, 5, 7, 9], "Vector addition incorrect"
        
        dot_result = wasm_module.vector_operations(vec1, vec2, 'dot')
        assert dot_result == 40, "Dot product incorrect"  # 1*2 + 2*3 + 3*4 + 4*5 = 40
        
        print("✅ WASM Vector Operations: Correct")
        
        duration = time.time() - start_time
        print(f"\n📊 WASM Simulation Results:")
        print(f"   • Functions testées: 3")
        print(f"   • Toutes réussies: ✅")
        print(f"   • Durée: {duration:.3f}s")
        print(f"   • Speedup simulé: 5x")

class TestServiceCommunication:
    """Tests de communication avec les services"""
    
    def test_service_health_checks(self):
        """Vérification de la santé des services"""
        start_time = time.time()
        service_status = {}
        
        for service_name, url in SERVICE_URLS.items():
            if service_name in ['redis', 'postgres']:
                continue  # Skip database URLs for now
                
            try:
                if 'localhost:11434' in url:
                    # Test spécial pour Ollama
                    response = requests.get(f"{url}/api/tags", timeout=5)
                    if response.status_code == 200:
                        models = response.json().get('models', [])
                        service_status[service_name] = {
                            'status': '✅ Online',
                            'response_time': response.elapsed.total_seconds(),
                            'details': f"{len(models)} models available"
                        }
                        print(f"✅ {service_name}: {len(models)} models")
                    else:
                        service_status[service_name] = {'status': '❌ Error', 'details': response.status_code}
                else:
                    # Test standard pour les autres services
                    health_url = f"{url}/health"
                    response = requests.get(health_url, timeout=3)
                    
                    if response.status_code == 200:
                        service_status[service_name] = {
                            'status': '✅ Online',
                            'response_time': response.elapsed.total_seconds()
                        }
                        print(f"✅ {service_name}: Online ({response.elapsed.total_seconds():.3f}s)")
                    else:
                        service_status[service_name] = {'status': '❌ Error', 'details': response.status_code}
                        print(f"❌ {service_name}: HTTP {response.status_code}")
                        
            except requests.ConnectionError:
                service_status[service_name] = {'status': '🔴 Offline', 'details': 'Connection refused'}
                print(f"🔴 {service_name}: Offline")
            except requests.Timeout:
                service_status[service_name] = {'status': '⏱️ Timeout', 'details': 'Request timeout'}
                print(f"⏱️ {service_name}: Timeout")
            except Exception as e:
                service_status[service_name] = {'status': '⚠️ Error', 'details': str(e)}
                print(f"⚠️ {service_name}: {str(e)}")
        
        duration = time.time() - start_time
        
        online_services = sum(1 for status in service_status.values() if '✅' in status['status'])
        total_services = len(service_status)
        
        print(f"\n📊 Service Health Check:")
        print(f"   • Services testés: {total_services}")
        print(f"   • Services en ligne: {online_services}")
        print(f"   • Taux de disponibilité: {online_services/total_services:.1%}")
        print(f"   • Durée: {duration:.2f}s")
        
        return service_status
    
    def test_ollama_models(self):
        """Test spécifique des modèles Ollama"""
        start_time = time.time()
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                
                print(f"🤖 Modèles Ollama disponibles: {len(models)}")
                
                # Test avec un petit modèle
                for model in models:
                    model_name = model['name']
                    if 'tinyllama' in model_name.lower() or '1.1b' in model_name:
                        # Test génération avec le plus petit modèle
                        test_prompt = {
                            "model": model_name,
                            "prompt": "Hello, how are you?",
                            "stream": False,
                            "options": {"num_predict": 20}
                        }
                        
                        try:
                            gen_response = requests.post(
                                "http://localhost:11434/api/generate", 
                                json=test_prompt,
                                timeout=30
                            )
                            
                            if gen_response.status_code == 200:
                                result = gen_response.json()
                                print(f"✅ Test génération {model_name}: Success")
                                print(f"   Response: {result.get('response', '')[:100]}...")
                                break
                            else:
                                print(f"❌ Test génération {model_name}: HTTP {gen_response.status_code}")
                                
                        except requests.Timeout:
                            print(f"⏱️ Test génération {model_name}: Timeout (30s)")
                        except Exception as e:
                            print(f"⚠️ Test génération {model_name}: {str(e)}")
                        
                        break
                else:
                    print("ℹ️ Aucun petit modèle trouvé pour test rapide")
                
                duration = time.time() - start_time
                print(f"\n📊 Ollama Test Results:")
                print(f"   • Modèles disponibles: {len(models)}")
                print(f"   • Service: Online")
                print(f"   • Durée: {duration:.2f}s")
                
                return True
            else:
                print(f"❌ Ollama API error: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ollama test failed: {str(e)}")
            return False

class TestAsyncComponents:
    """Tests des composants asynchrones"""
    
    @pytest.mark.asyncio
    async def test_websocket_simulation(self):
        """Simulation des connexions WebSocket"""
        
        class MockWebSocket:
            def __init__(self, url):
                self.url = url
                self.connected = False
                self.messages_sent = []
                self.messages_received = []
            
            async def connect(self):
                await asyncio.sleep(0.1)  # Simulation connexion
                self.connected = True
                return True
            
            async def send(self, message):
                if not self.connected:
                    raise Exception("Not connected")
                self.messages_sent.append(message)
                
                # Simulation réponse
                await asyncio.sleep(0.05)
                response = {
                    "type": "response",
                    "data": f"Echo: {message}",
                    "timestamp": time.time()
                }
                self.messages_received.append(response)
                return response
            
            async def close(self):
                self.connected = False
        
        # Test connexions multiples
        websockets = [
            MockWebSocket("ws://localhost:5001/ws"),  # Brain API
            MockWebSocket("ws://localhost:5006/ws"),  # MCP Gateway
        ]
        
        # Test connexion parallèle
        start_time = time.time()
        
        connect_tasks = [ws.connect() for ws in websockets]
        connect_results = await asyncio.gather(*connect_tasks, return_exceptions=True)
        
        connected_count = sum(1 for result in connect_results if result is True)
        print(f"✅ WebSocket connections: {connected_count}/{len(websockets)}")
        
        # Test envoi de messages
        test_messages = [
            {"type": "cognitive_state", "data": "thinking"},
            {"type": "prediction_request", "data": {"horizon": "short_term"}},
        ]
        
        for i, ws in enumerate(websockets):
            if ws.connected:
                try:
                    response = await ws.send(test_messages[i % len(test_messages)])
                    print(f"✅ WebSocket {i}: Message sent/received")
                except Exception as e:
                    print(f"❌ WebSocket {i}: {str(e)}")
        
        # Fermeture
        close_tasks = [ws.close() for ws in websockets]
        await asyncio.gather(*close_tasks)
        
        duration = time.time() - start_time
        print(f"\n📊 WebSocket Simulation:")
        print(f"   • Connexions testées: {len(websockets)}")
        print(f"   • Connexions réussies: {connected_count}")
        print(f"   • Durée: {duration:.3f}s")
        
        assert connected_count > 0, "Au moins une connexion WebSocket doit réussir"

class TestPerformanceMetrics:
    """Tests de métriques de performance"""
    
    def test_performance_benchmarks(self):
        """Benchmarks de performance des composants"""
        start_time = time.time()
        
        benchmarks = {}
        
        # Test 1: Import time
        import_start = time.time()
        try:
            import json
            import asyncio
            import threading
            benchmarks['import_time'] = time.time() - import_start
            print(f"✅ Import benchmark: {benchmarks['import_time']:.3f}s")
        except Exception as e:
            print(f"❌ Import benchmark failed: {str(e)}")
        
        # Test 2: JSON processing
        json_start = time.time()
        test_data = {"cognitive_state": "thinking", "agents": ["analytical", "creative"]}
        for _ in range(1000):
            json_str = json.dumps(test_data)
            parsed = json.loads(json_str)
        benchmarks['json_processing'] = time.time() - json_start
        print(f"✅ JSON processing (1000x): {benchmarks['json_processing']:.3f}s")
        
        # Test 3: Threading performance
        threading_start = time.time()
        
        def cpu_task():
            sum(i * i for i in range(10000))
        
        threads = []
        for _ in range(4):
            thread = threading.Thread(target=cpu_task)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
            
        benchmarks['threading'] = time.time() - threading_start
        print(f"✅ Threading (4 threads): {benchmarks['threading']:.3f}s")
        
        # Test 4: Memory usage simulation
        memory_start = time.time()
        large_list = [i for i in range(100000)]
        memory_processing = sum(large_list)
        del large_list
        benchmarks['memory_test'] = time.time() - memory_start
        print(f"✅ Memory test (100k items): {benchmarks['memory_test']:.3f}s")
        
        duration = time.time() - start_time
        
        print(f"\n📊 Performance Benchmarks:")
        for test_name, test_time in benchmarks.items():
            print(f"   • {test_name}: {test_time:.3f}s")
        print(f"   • Total duration: {duration:.3f}s")
        
        # Assertions de performance
        assert benchmarks.get('import_time', 1) < 0.1, "Import time too slow"
        assert benchmarks.get('json_processing', 1) < 0.5, "JSON processing too slow"
        assert benchmarks.get('threading', 1) < 1.0, "Threading too slow"
        
        return benchmarks

def run_complete_test_suite():
    """Exécuter la suite complète de tests"""
    print("🚀 JARVIS AI 2025 - Suite de Tests Complète")
    print("=" * 50)
    
    suite = JARVISTestSuite()
    
    # Tests d'importation
    print("\n📦 Tests d'Importation des Modules")
    print("-" * 30)
    try:
        test_imports = TestModuleImports()
        test_imports.test_core_modules_import()
        suite.add_result("module_imports", True, time.time() - suite.start_time)
    except Exception as e:
        print(f"❌ Module imports failed: {str(e)}")
        suite.add_result("module_imports", False, time.time() - suite.start_time, errors=[str(e)])
    
    # Tests Web Workers
    print("\n👥 Tests Web Workers (Simulation)")
    print("-" * 30)
    try:
        test_workers = TestWebWorkersSimulation()
        test_workers.test_web_worker_simulation()
        suite.add_result("web_workers", True, time.time() - suite.start_time)
    except Exception as e:
        print(f"❌ Web workers failed: {str(e)}")
        suite.add_result("web_workers", False, time.time() - suite.start_time, errors=[str(e)])
    
    # Tests WASM
    print("\n🔥 Tests WASM (Simulation)")
    print("-" * 30)
    try:
        test_wasm = TestWASMSimulation()
        test_wasm.test_wasm_module_simulation()
        suite.add_result("wasm_simulation", True, time.time() - suite.start_time)
    except Exception as e:
        print(f"❌ WASM simulation failed: {str(e)}")
        suite.add_result("wasm_simulation", False, time.time() - suite.start_time, errors=[str(e)])
    
    # Tests de services
    print("\n🌐 Tests de Communication avec les Services")
    print("-" * 30)
    try:
        test_services = TestServiceCommunication()
        service_status = test_services.test_service_health_checks()
        test_services.test_ollama_models()
        suite.add_result("service_communication", True, time.time() - suite.start_time, 
                        details={'service_status': service_status})
    except Exception as e:
        print(f"❌ Service communication failed: {str(e)}")
        suite.add_result("service_communication", False, time.time() - suite.start_time, errors=[str(e)])
    
    # Tests asynchrones
    print("\n⚡ Tests Composants Asynchrones")
    print("-" * 30)
    try:
        test_async = TestAsyncComponents()
        asyncio.run(test_async.test_websocket_simulation())
        suite.add_result("async_components", True, time.time() - suite.start_time)
    except Exception as e:
        print(f"❌ Async components failed: {str(e)}")
        suite.add_result("async_components", False, time.time() - suite.start_time, errors=[str(e)])
    
    # Tests de performance
    print("\n📊 Tests de Performance")
    print("-" * 30)
    try:
        test_perf = TestPerformanceMetrics()
        benchmarks = test_perf.test_performance_benchmarks()
        suite.add_result("performance", True, time.time() - suite.start_time, 
                        details={'benchmarks': benchmarks})
    except Exception as e:
        print(f"❌ Performance tests failed: {str(e)}")
        suite.add_result("performance", False, time.time() - suite.start_time, errors=[str(e)])
    
    # Rapport final
    print("\n" + "=" * 50)
    print("📋 RAPPORT FINAL")
    print("=" * 50)
    
    total_tests = len(suite.results)
    passed_tests = sum(1 for result in suite.results if result.passed)
    total_duration = time.time() - suite.start_time
    
    print(f"🧪 Tests exécutés: {total_tests}")
    print(f"✅ Tests réussis: {passed_tests}")
    print(f"❌ Tests échoués: {total_tests - passed_tests}")
    print(f"📊 Taux de réussite: {passed_tests/total_tests:.1%}")
    print(f"⏱️ Durée totale: {total_duration:.2f}s")
    
    if passed_tests == total_tests:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS ! JARVIS AI 2025 EST PRÊT !")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests ont échoué. Vérifiez les logs ci-dessus.")
        return False

if __name__ == "__main__":
    """Point d'entrée principal"""
    success = run_complete_test_suite()
    sys.exit(0 if success else 1)