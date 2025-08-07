#!/usr/bin/env python3
"""
🎮 Ollama AMD RX 7800 XT Optimizer
Script d'optimisation automatique pour modèles IA sur AMD RX 7800 XT
"""

import os
import json
import subprocess
import time
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OllamaAMDOptimizer:
    """Optimiseur Ollama pour AMD RX 7800 XT"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config/ollama/amd-rx7800xt-config.json"
        self.ollama_url = "http://localhost:11434"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Charger configuration AMD RX 7800 XT"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config non trouvée: {self.config_path}, utilisation valeurs par défaut")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut AMD RX 7800 XT"""
        return {
            "models": {
                "llama3.2:3b": {
                    "quantization": "Q4_K_M",
                    "vram_usage_mb": 2800,
                    "gpu_layers": -1
                },
                "gpt-oss-20b": {
                    "quantization": "Q4_K_M", 
                    "vram_usage_mb": 12288,
                    "gpu_layers": -1
                }
            },
            "rocm_settings": {
                "hip_visible_devices": "0",
                "rocr_visible_devices": "0"
            }
        }
    
    def setup_rocm_environment(self) -> bool:
        """Configuration environnement ROCm pour AMD"""
        logger.info("🔧 Configuration environnement ROCm...")
        
        rocm_env = self.config.get("rocm_settings", {})
        
        env_vars = {
            "HIP_VISIBLE_DEVICES": rocm_env.get("hip_visible_devices", "0"),
            "ROCR_VISIBLE_DEVICES": rocm_env.get("rocr_visible_devices", "0"), 
            "HIP_FORCE_DEV_KERNARG": rocm_env.get("hip_force_dev_kernarg", "1"),
            "AMD_LOG_LEVEL": rocm_env.get("amd_log_level", "2"),
            "HIP_LAUNCH_BLOCKING": rocm_env.get("hip_launch_blocking", "0"),
            "HSA_ENABLE_INTERRUPT": rocm_env.get("hsa_enable_interrupt", "0"),
            "HIP_DEVICE_ORDER": rocm_env.get("hip_device_order", "PCI_BUS_ID")
        }
        
        for var, value in env_vars.items():
            os.environ[var] = str(value)
            logger.info(f"   {var} = {value}")
        
        return True
    
    def check_gpu_status(self) -> Dict[str, Any]:
        """Vérification état GPU AMD"""
        try:
            # Utiliser rocm-smi pour info GPU
            result = subprocess.run(
                ["rocm-smi", "--showmeminfo", "vram", "--json"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                gpu_info = json.loads(result.stdout)
                return {
                    "available": True,
                    "memory_info": gpu_info,
                    "temperature": self._get_gpu_temperature(),
                    "utilization": self._get_gpu_utilization()
                }
            else:
                logger.warning("rocm-smi non disponible, tentative alternative...")
                return {"available": False, "reason": "rocm-smi_unavailable"}
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout rocm-smi")
            return {"available": False, "reason": "timeout"}
        except Exception as e:
            logger.error(f"Erreur vérification GPU: {e}")
            return {"available": False, "reason": str(e)}
    
    def _get_gpu_temperature(self) -> Optional[float]:
        """Récupérer température GPU"""
        try:
            result = subprocess.run(
                ["rocm-smi", "--showtemp", "--json"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                temp_data = json.loads(result.stdout)
                # Parser température selon format rocm-smi
                return temp_data.get("card0", {}).get("Temperature (Sensor edge) (C)", 0)
        except:
            pass
        return None
    
    def _get_gpu_utilization(self) -> Optional[float]:
        """Récupérer utilisation GPU"""
        try:
            result = subprocess.run(
                ["rocm-smi", "--showuse", "--json"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                use_data = json.loads(result.stdout)
                return use_data.get("card0", {}).get("GPU use (%)", 0)
        except:
            pass
        return None
    
    def optimize_model_config(self, model_name: str) -> Dict[str, Any]:
        """Optimiser configuration modèle pour AMD RX 7800 XT"""
        models_config = self.config.get("models", {})
        
        if model_name not in models_config:
            logger.warning(f"Modèle {model_name} non configuré, utilisation config par défaut")
            return self._get_default_model_config(model_name)
        
        base_config = models_config[model_name]
        
        # Optimisations spécifiques AMD RX 7800 XT
        optimizations = {
            "num_ctx": base_config.get("context_length", 8192),
            "num_batch": base_config.get("batch_size", 512),
            "num_gqa": 8,  # Grouped Query Attention optimisé RDNA3
            "num_gpu": base_config.get("gpu_layers", -1),
            "num_thread": base_config.get("num_threads", 16),
            "num_predict": base_config.get("n_predict", 2048),
            
            # Mémoire optimisée 16GB VRAM
            "mmap": base_config.get("mmap", True),
            "mlock": base_config.get("mlock", True),
            "numa": base_config.get("numa", False),
            "low_vram": base_config.get("low_vram", False),
            "f16_kv": base_config.get("f16_kv", True),
            
            # Performance RDNA3
            "flash_attn": base_config.get("flash_attention", True),
            "rope_frequency_base": base_config.get("rope_frequency_base", 10000.0),
            "rope_frequency_scale": base_config.get("rope_frequency_scale", 1.0),
            
            # Génération
            "temperature": base_config.get("temperature", 0.7),
            "top_p": base_config.get("top_p", 0.9),
            "top_k": base_config.get("top_k", 40),
            "repeat_penalty": base_config.get("repeat_penalty", 1.1),
            "seed": base_config.get("seed", -1),
        }
        
        # Ajustements spécifiques modèle
        if "gpt-oss-20b" in model_name.lower():
            optimizations.update({
                "num_batch": 256,  # Batch réduit pour gros modèle
                "num_thread": 20,  # Plus de threads
                "num_predict": 4096,  # Contexte étendu
                "group_attention": True
            })
        elif "llama3.2:3b" in model_name.lower():
            optimizations.update({
                "num_batch": 512,  # Batch élevé pour petit modèle
                "num_thread": 12,
                "num_predict": 2048
            })
        
        return optimizations
    
    def _get_default_model_config(self, model_name: str) -> Dict[str, Any]:
        """Configuration par défaut modèle"""
        return {
            "num_ctx": 8192,
            "num_batch": 512, 
            "num_gpu": -1,
            "mmap": True,
            "mlock": True,
            "f16_kv": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40
        }
    
    def pull_model_optimized(self, model_name: str) -> bool:
        """Télécharger et configurer modèle optimisé"""
        logger.info(f"📥 Téléchargement modèle {model_name}...")
        
        try:
            # Pull modèle via API Ollama
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=1800  # 30min timeout
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                print(f"\r{data['status']}", end="", flush=True)
                        except:
                            pass
                
                print(f"\n✅ Modèle {model_name} téléchargé")
                return True
            else:
                logger.error(f"❌ Erreur téléchargement: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur pull modèle: {e}")
            return False
    
    def create_optimized_modelfile(self, model_name: str, output_path: str = None) -> str:
        """Créer Modelfile optimisé pour AMD RX 7800 XT"""
        
        if not output_path:
            output_path = f"config/ollama/{model_name.replace(':', '_')}_amd_optimized.Modelfile"
        
        # Configuration optimisée
        config = self.optimize_model_config(model_name)
        
        # Template Modelfile
        modelfile_content = f"""# Modelfile optimisé AMD RX 7800 XT pour {model_name}
FROM {model_name}

# Paramètres mémoire optimisés 16GB VRAM  
PARAMETER num_ctx {config['num_ctx']}
PARAMETER num_batch {config['num_batch']}
PARAMETER num_gpu {config['num_gpu']}
PARAMETER num_thread {config['num_thread']}
PARAMETER num_predict {config['num_predict']}

# Optimisations RDNA3
PARAMETER mmap {str(config['mmap']).lower()}
PARAMETER mlock {str(config['mlock']).lower()}
PARAMETER numa {str(config['numa']).lower()}
PARAMETER low_vram {str(config['low_vram']).lower()}
PARAMETER f16_kv {str(config['f16_kv']).lower()}

# Génération optimisée
PARAMETER temperature {config['temperature']}
PARAMETER top_p {config['top_p']}
PARAMETER top_k {config['top_k']}
PARAMETER repeat_penalty {config['repeat_penalty']}

# RoPE optimisé
PARAMETER rope_frequency_base {config['rope_frequency_base']}
PARAMETER rope_frequency_scale {config['rope_frequency_scale']}

# Prompt système optimisé
SYSTEM \"\"\"Tu es JARVIS, un assistant IA avancé optimisé pour AMD RX 7800 XT. 
Tu réponds de manière précise, efficace et adaptée au contexte technique.
\"\"\"
"""
        
        # Créer dossier si nécessaire
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire Modelfile
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)
        
        logger.info(f"📝 Modelfile créé: {output_path}")
        return output_path
    
    def create_optimized_model(self, model_name: str, optimized_name: str = None) -> bool:
        """Créer modèle optimisé depuis Modelfile"""
        
        if not optimized_name:
            optimized_name = f"{model_name.replace(':', '_')}_amd_optimized"
        
        # Créer Modelfile optimisé
        modelfile_path = self.create_optimized_modelfile(model_name)
        
        try:
            logger.info(f"🔨 Création modèle optimisé {optimized_name}...")
            
            # Créer modèle via API Ollama
            with open(modelfile_path, 'r', encoding='utf-8') as f:
                modelfile_content = f.read()
            
            response = requests.post(
                f"{self.ollama_url}/api/create",
                json={
                    "name": optimized_name,
                    "modelfile": modelfile_content
                },
                stream=True,
                timeout=600  # 10min timeout
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                print(f"\r{data['status']}", end="", flush=True)
                        except:
                            pass
                
                print(f"\n✅ Modèle optimisé {optimized_name} créé")
                return True
            else:
                logger.error(f"❌ Erreur création modèle: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur création modèle optimisé: {e}")
            return False
    
    def benchmark_model(self, model_name: str, num_tests: int = 5) -> Dict[str, Any]:
        """Benchmark performance modèle"""
        logger.info(f"📊 Benchmark {model_name} ({num_tests} tests)...")
        
        test_prompt = "Explain the concept of artificial intelligence in a comprehensive but concise manner."
        
        results = {
            "model": model_name,
            "tests": [],
            "avg_response_time": 0,
            "avg_tokens_per_second": 0,
            "success_rate": 0
        }
        
        successful_tests = 0
        total_response_time = 0
        total_tokens = 0
        
        for i in range(num_tests):
            logger.info(f"  Test {i+1}/{num_tests}")
            
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": test_prompt,
                        "stream": False
                    },
                    timeout=120
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", "")
                    tokens = len(response_text.split())  # Approximation
                    tokens_per_second = tokens / response_time if response_time > 0 else 0
                    
                    test_result = {
                        "test_id": i + 1,
                        "response_time": response_time,
                        "tokens": tokens,
                        "tokens_per_second": tokens_per_second,
                        "success": True
                    }
                    
                    successful_tests += 1
                    total_response_time += response_time
                    total_tokens += tokens
                    
                    logger.info(f"    ✅ {response_time:.2f}s, {tokens_per_second:.1f} tok/s")
                else:
                    test_result = {
                        "test_id": i + 1,
                        "error": f"HTTP {response.status_code}",
                        "success": False
                    }
                    logger.info(f"    ❌ HTTP {response.status_code}")
                
                results["tests"].append(test_result)
                
            except Exception as e:
                test_result = {
                    "test_id": i + 1,
                    "error": str(e),
                    "success": False
                }
                results["tests"].append(test_result)
                logger.info(f"    ❌ {str(e)}")
        
        # Calcul moyennes
        if successful_tests > 0:
            results["avg_response_time"] = total_response_time / successful_tests
            results["avg_tokens_per_second"] = total_tokens / total_response_time
            results["success_rate"] = successful_tests / num_tests
        
        logger.info(f"📈 Résultats benchmark {model_name}:")
        logger.info(f"   Taux succès: {results['success_rate']*100:.1f}%")
        logger.info(f"   Temps moyen: {results['avg_response_time']:.2f}s")
        logger.info(f"   Tokens/sec: {results['avg_tokens_per_second']:.1f}")
        
        return results
    
    def full_optimization_workflow(self, models: List[str]) -> Dict[str, Any]:
        """Workflow complet d'optimisation"""
        logger.info("🚀 Démarrage workflow optimisation AMD RX 7800 XT")
        
        results = {
            "gpu_status": None,
            "models": {},
            "benchmarks": {},
            "success": False
        }
        
        # 1. Configuration environnement ROCm
        if not self.setup_rocm_environment():
            logger.error("❌ Échec configuration ROCm")
            return results
        
        # 2. Vérification GPU
        gpu_status = self.check_gpu_status()
        results["gpu_status"] = gpu_status
        
        if not gpu_status.get("available", False):
            logger.warning("⚠️ GPU non détecté, continuation avec configuration CPU")
        
        # 3. Traitement de chaque modèle
        for model_name in models:
            logger.info(f"🔧 Optimisation {model_name}...")
            
            model_results = {"pulled": False, "optimized": False, "benchmark": None}
            
            # Pull modèle si nécessaire
            if self.pull_model_optimized(model_name):
                model_results["pulled"] = True
                
                # Créer version optimisée
                optimized_name = f"{model_name.replace(':', '_')}_amd_optimized"
                if self.create_optimized_model(model_name, optimized_name):
                    model_results["optimized"] = True
                    
                    # Benchmark
                    benchmark = self.benchmark_model(optimized_name, 3)
                    model_results["benchmark"] = benchmark
                    results["benchmarks"][optimized_name] = benchmark
            
            results["models"][model_name] = model_results
        
        # 4. Résumé final
        successful_models = sum(1 for r in results["models"].values() if r["optimized"])
        total_models = len(models)
        
        results["success"] = successful_models == total_models
        
        logger.info(f"✅ Optimisation terminée: {successful_models}/{total_models} modèles")
        
        return results

def main():
    parser = argparse.ArgumentParser(description="Optimiseur Ollama AMD RX 7800 XT")
    parser.add_argument("--config", help="Chemin fichier configuration")
    parser.add_argument("--models", nargs="+", default=["llama3.2:3b", "gpt-oss-20b"],
                       help="Liste des modèles à optimiser")
    parser.add_argument("--benchmark-only", action="store_true",
                       help="Seulement benchmark, pas d'optimisation")
    parser.add_argument("--setup-only", action="store_true", 
                       help="Seulement setup environnement ROCm")
    
    args = parser.parse_args()
    
    optimizer = OllamaAMDOptimizer(args.config)
    
    if args.setup_only:
        optimizer.setup_rocm_environment()
        gpu_status = optimizer.check_gpu_status()
        print(f"GPU Status: {json.dumps(gpu_status, indent=2)}")
        return
    
    if args.benchmark_only:
        for model in args.models:
            results = optimizer.benchmark_model(model)
            print(f"\nBenchmark {model}:")
            print(json.dumps(results, indent=2))
        return
    
    # Workflow complet
    results = optimizer.full_optimization_workflow(args.models)
    
    # Sauvegarder résultats
    output_file = f"optimization_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📊 Résultats sauvés: {output_file}")

if __name__ == "__main__":
    main()