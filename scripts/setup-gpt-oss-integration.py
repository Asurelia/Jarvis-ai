#!/usr/bin/env python3
"""
🚀 Setup GPT-OSS 20B Integration for JARVIS AI
Script d'installation et configuration complète pour intégration GPT-OSS 20B
"""

import os
import sys
import json
import subprocess
import asyncio
import argparse
import requests
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JarvisGPTOSSSetup:
    """Installation et configuration GPT-OSS 20B pour JARVIS"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.ollama_url = "http://localhost:11434"
        self.gateway_url = "http://localhost:5010"
        
        self.setup_steps = [
            "check_prerequisites",
            "setup_rocm_environment", 
            "install_dependencies",
            "pull_models",
            "optimize_configurations",
            "start_services",
            "run_validation",
            "generate_documentation"
        ]
        
        self.status = {step: False for step in self.setup_steps}
        
    def print_header(self):
        """Afficher header setup"""
        print("\n" + "="*70)
        print("🤖 JARVIS AI - GPT-OSS 20B Integration Setup")
        print("   Optimisé pour AMD RX 7800 XT (16GB VRAM)")
        print("="*70)
        
    def print_step(self, step: str, description: str):
        """Afficher étape courante"""
        print(f"\n🔧 [{step.upper()}] {description}")
        print("-" * 50)
    
    def check_prerequisites(self) -> bool:
        """Vérifier prérequis système"""
        self.print_step("check_prerequisites", "Vérification prérequis système")
        
        checks = {
            "python_version": False,
            "docker": False,
            "rocm": False,
            "gpu": False,
            "disk_space": False
        }
        
        # Python version
        if sys.version_info >= (3, 8):
            checks["python_version"] = True
            logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        else:
            logger.error(f"❌ Python >= 3.8 requis, trouvé {sys.version}")
        
        # Docker
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                checks["docker"] = True
                logger.info(f"✅ Docker détecté: {result.stdout.strip()}")
            else:
                logger.error("❌ Docker non disponible")
        except Exception as e:
            logger.error(f"❌ Erreur vérification Docker: {e}")
        
        # ROCm
        try:
            result = subprocess.run(["rocm-smi", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                checks["rocm"] = True
                logger.info("✅ ROCm détecté")
            else:
                logger.warning("⚠️  ROCm non détecté, performance GPU limitée")
        except Exception:
            logger.warning("⚠️  rocm-smi non trouvé")
        
        # GPU AMD
        try:
            result = subprocess.run(["rocm-smi", "--showproductname"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and "RX 7800 XT" in result.stdout:
                checks["gpu"] = True
                logger.info("✅ AMD RX 7800 XT détecté")
            else:
                logger.warning("⚠️  AMD RX 7800 XT non détecté spécifiquement")
        except Exception:
            # Fallback avec GPUtil
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    if gpu.memoryTotal >= 15000:  # Au moins 15GB VRAM
                        checks["gpu"] = True
                        logger.info(f"✅ GPU détecté: {gpu.name} ({gpu.memoryTotal}MB VRAM)")
                    else:
                        logger.warning(f"⚠️  GPU VRAM insuffisante: {gpu.memoryTotal}MB < 16GB requis")
            except ImportError:
                logger.warning("⚠️  Impossible de détecter GPU")
        
        # Espace disque (minimum 50GB)
        try:
            import shutil
            free_space_gb = shutil.disk_usage(self.project_root).free // (1024**3)
            if free_space_gb >= 50:
                checks["disk_space"] = True
                logger.info(f"✅ Espace disque: {free_space_gb}GB disponible")
            else:
                logger.error(f"❌ Espace disque insuffisant: {free_space_gb}GB < 50GB requis")
        except Exception as e:
            logger.warning(f"⚠️  Impossible de vérifier espace disque: {e}")
        
        # Résumé prérequis
        passed_checks = sum(checks.values())
        total_checks = len(checks)
        
        print(f"\n📊 Prérequis: {passed_checks}/{total_checks} validés")
        for check, status in checks.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {check}")
        
        success = passed_checks >= 3  # Au minimum Python, Docker, espace disque
        self.status["check_prerequisites"] = success
        return success
    
    def setup_rocm_environment(self) -> bool:
        """Configuration environnement ROCm"""
        self.print_step("setup_rocm_environment", "Configuration environnement ROCm")
        
        try:
            # Variables d'environnement ROCm optimisées
            rocm_env = {
                "HIP_VISIBLE_DEVICES": "0",
                "ROCR_VISIBLE_DEVICES": "0",
                "HIP_FORCE_DEV_KERNARG": "1",
                "AMD_LOG_LEVEL": "2",
                "HIP_LAUNCH_BLOCKING": "0",
                "HSA_ENABLE_INTERRUPT": "0",
                "HIP_DEVICE_ORDER": "PCI_BUS_ID",
                "ROCM_PATH": "/opt/rocm",
                "GPU_DEVICE_ORDINAL": "0",
                "GPU_MAX_HW_QUEUES": "4"
            }
            
            # Créer script d'environnement
            env_script_path = self.project_root / "scripts" / "rocm-env.sh"
            env_script_path.parent.mkdir(exist_ok=True)
            
            with open(env_script_path, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# ROCm Environment Configuration for AMD RX 7800 XT\n\n")
                
                for var, value in rocm_env.items():
                    f.write(f"export {var}={value}\n")
                    # Définir aussi pour session courante
                    os.environ[var] = value
                
                f.write("\necho '🔴 ROCm Environment configured for AMD RX 7800 XT'\n")
            
            # Rendre exécutable
            os.chmod(env_script_path, 0o755)
            
            logger.info(f"✅ Script ROCm créé: {env_script_path}")
            
            # Créer aussi version Windows .bat
            bat_script_path = self.project_root / "scripts" / "rocm-env.bat"
            with open(bat_script_path, 'w') as f:
                f.write("@echo off\n")
                f.write("REM ROCm Environment Configuration for AMD RX 7800 XT\n\n")
                
                for var, value in rocm_env.items():
                    f.write(f"set {var}={value}\n")
                
                f.write("\necho ROCm Environment configured for AMD RX 7800 XT\n")
            
            logger.info(f"✅ Script ROCm Windows créé: {bat_script_path}")
            
            self.status["setup_rocm_environment"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration ROCm: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Installation dépendances Python"""
        self.print_step("install_dependencies", "Installation dépendances Python")
        
        try:
            # Dépendances spécifiques pour LLM Gateway
            gateway_deps = [
                "aiohttp>=3.8.0",
                "fastapi>=0.104.0", 
                "uvicorn>=0.24.0",
                "pydantic>=2.4.0",
                "psutil>=5.9.0",
                "GPUtil>=1.4.0",
                "structlog>=22.1.0",
                "prometheus-client>=0.17.0"
            ]
            
            # Créer requirements pour gateway
            gateway_req_path = self.project_root / "services" / "llm-gateway" / "requirements.txt"
            gateway_req_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(gateway_req_path, 'w') as f:
                for dep in gateway_deps:
                    f.write(f"{dep}\n")
            
            logger.info(f"✅ Requirements LLM Gateway créés: {gateway_req_path}")
            
            # Installer dépendances
            pip_cmd = [sys.executable, "-m", "pip", "install", "-r", str(gateway_req_path)]
            result = subprocess.run(pip_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ Dépendances LLM Gateway installées")
                self.status["install_dependencies"] = True
                return True
            else:
                logger.error(f"❌ Erreur installation dépendances: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur installation dépendances: {e}")
            return False
    
    def pull_models(self) -> bool:
        """Téléchargement modèles Ollama"""
        self.print_step("pull_models", "Téléchargement modèles IA")
        
        models = [
            ("llama3.2:3b", "Modèle léger pour requêtes simples"),
            ("gpt-oss-20b", "Modèle lourd pour requêtes complexes")
        ]
        
        try:
            # Vérifier Ollama disponible
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code != 200:
                logger.error(f"❌ Ollama non disponible sur {self.ollama_url}")
                return False
            
            existing_models = [m['name'] for m in response.json().get('models', [])]
            logger.info(f"📦 Modèles existants: {existing_models}")
            
            # Télécharger modèles manquants
            for model, description in models:
                if model in existing_models:
                    logger.info(f"✅ {model} déjà disponible")
                    continue
                
                logger.info(f"📥 Téléchargement {model} - {description}")
                
                # Pull via API
                pull_response = requests.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": model},
                    stream=True,
                    timeout=1800  # 30 min max
                )
                
                if pull_response.status_code == 200:
                    for line in pull_response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "status" in data:
                                    print(f"\r   {data['status']}", end="", flush=True)
                            except:
                                pass
                    print(f"\n✅ {model} téléchargé")
                else:
                    logger.error(f"❌ Erreur téléchargement {model}: {pull_response.status_code}")
                    return False
            
            self.status["pull_models"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur téléchargement modèles: {e}")
            return False
    
    def optimize_configurations(self) -> bool:
        """Optimisation configurations modèles"""
        self.print_step("optimize_configurations", "Optimisation configurations")
        
        try:
            # Utiliser l'optimiseur Ollama
            optimizer_path = self.project_root / "scripts" / "ollama-amd-optimizer.py"
            
            if optimizer_path.exists():
                logger.info("🔧 Exécution optimiseur AMD...")
                
                # Lancer optimiseur
                result = subprocess.run([
                    sys.executable, str(optimizer_path),
                    "--models", "llama3.2:3b", "gpt-oss-20b"
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    logger.info("✅ Optimisations appliquées")
                else:
                    logger.warning(f"⚠️  Optimiseur retourné: {result.stderr}")
            else:
                logger.warning("⚠️  Optimiseur non trouvé, configuration manuelle")
            
            # Créer docker-compose pour LLM Gateway
            self._create_gateway_docker_compose()
            
            self.status["optimize_configurations"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur optimisation: {e}")
            return False
    
    def _create_gateway_docker_compose(self):
        """Créer docker-compose pour LLM Gateway"""
        compose_content = """
version: '3.8'

services:
  llm-gateway:
    build: ./services/llm-gateway
    container_name: jarvis-llm-gateway
    ports:
      - "5010:5010"
    environment:
      - HIP_VISIBLE_DEVICES=0
      - ROCR_VISIBLE_DEVICES=0
      - HIP_FORCE_DEV_KERNARG=1
      - GPU_OPTIMIZATION=true
    volumes:
      - ./config/ollama:/app/config
    networks:
      - jarvis-ai-network
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5010/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  jarvis-ai-network:
    external: true
"""
        
        compose_path = self.project_root / "docker-compose.llm-gateway.yml"
        with open(compose_path, 'w') as f:
            f.write(compose_content.strip())
        
        logger.info(f"✅ Docker Compose LLM Gateway créé: {compose_path}")
    
    def start_services(self) -> bool:
        """Démarrage services"""
        self.print_step("start_services", "Démarrage services")
        
        try:
            # Démarrer LLM Gateway
            gateway_compose = self.project_root / "docker-compose.llm-gateway.yml"
            
            if gateway_compose.exists():
                logger.info("🚀 Démarrage LLM Gateway...")
                
                result = subprocess.run([
                    "docker-compose", "-f", str(gateway_compose), "up", "-d"
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    logger.info("✅ LLM Gateway démarré")
                    
                    # Attendre service ready
                    for attempt in range(30):
                        try:
                            response = requests.get(f"{self.gateway_url}/api/health", timeout=5)
                            if response.status_code == 200:
                                logger.info("✅ LLM Gateway opérationnel")
                                break
                        except:
                            pass
                        
                        time.sleep(2)
                    else:
                        logger.warning("⚠️  LLM Gateway santé non confirmée")
                else:
                    logger.error(f"❌ Erreur démarrage Gateway: {result.stderr}")
                    return False
            
            self.status["start_services"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage services: {e}")
            return False
    
    def run_validation(self) -> bool:
        """Validation installation"""
        self.print_step("run_validation", "Validation installation")
        
        try:
            # Test santé gateway
            response = requests.get(f"{self.gateway_url}/api/health", timeout=10)
            if response.status_code != 200:
                logger.error("❌ Gateway non accessible")
                return False
            
            health_data = response.json()
            logger.info(f"✅ Gateway santé: {health_data.get('status')}")
            
            # Test modèles disponibles
            response = requests.get(f"{self.gateway_url}/api/models", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                logger.info(f"✅ Modèles configurés: {len(models_data.get('models', {}))}")
            
            # Test requête simple
            test_response = requests.post(
                f"{self.gateway_url}/api/chat",
                json={
                    "messages": [{"role": "user", "content": "Hello, test GPT-OSS integration"}],
                    "stream": False
                },
                timeout=60
            )
            
            if test_response.status_code == 200:
                logger.info("✅ Test chat réussi")
                
                # Analyser réponse
                data = test_response.json()
                if "metadata" in data:
                    model_used = data["metadata"].get("model_used", "unknown")
                    logger.info(f"   Modèle utilisé: {model_used}")
            else:
                logger.error(f"❌ Test chat échoué: {test_response.status_code}")
                return False
            
            self.status["run_validation"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur validation: {e}")
            return False
    
    def generate_documentation(self) -> bool:
        """Génération documentation"""
        self.print_step("generate_documentation", "Génération documentation")
        
        try:
            doc_content = f"""# GPT-OSS 20B Integration - JARVIS AI

## ✅ Installation Complétée

Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
Système: AMD RX 7800 XT optimisé

## 🚀 Services Actifs

- **LLM Gateway**: http://localhost:5010
- **Ollama**: http://localhost:11434
- **Brain API**: http://localhost:8080

## 🤖 Modèles Disponibles

- **llama3.2:3b**: Modèle léger pour requêtes simples
- **gpt-oss-20b**: Modèle lourd pour requêtes complexes

## 📊 Configuration Optimisée

### ROCm Environment
```bash
source scripts/rocm-env.sh  # Linux/Mac
scripts/rocm-env.bat        # Windows
```

### Docker Services
```bash
# Démarrer LLM Gateway
docker-compose -f docker-compose.llm-gateway.yml up -d

# Voir logs
docker-compose -f docker-compose.llm-gateway.yml logs -f
```

### Tests Performance
```bash
# Benchmarks complets
python tests/performance/test_llm_gateway_benchmarks.py

# Tests manuels
curl -X POST http://localhost:5010/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{{"messages": [{{"role": "user", "content": "Test GPT-OSS"}}], "stream": false}}'
```

## 🔧 Monitoring GPU

- Métriques: http://localhost:5010/api/metrics
- Santé: http://localhost:5010/api/health
- ROCm: `rocm-smi --showmeminfo vram --showtemp`

## ⚡ Performance Attendue

- Requêtes simples: ~2-5s (llama3.2:3b)
- Requêtes complexes: ~10-30s (gpt-oss-20b)  
- Switching automatique selon complexité

## 🚨 Troubleshooting

### GPU Non Détecté
```bash
rocm-smi --showproductname
export HIP_VISIBLE_DEVICES=0
```

### VRAM Insuffisante
- Vérifier utilisation: `rocm-smi --showmeminfo vram`
- Réduire batch size dans configuration
- Utiliser quantization Q4_K_M

### Gateway Non Accessible
```bash
docker-compose -f docker-compose.llm-gateway.yml restart
docker logs jarvis-llm-gateway
```

## 📞 Support

- Logs: `docker-compose logs`
- Issues: Vérifier configurations dans config/ollama/
- Performance: Ajuster seuils dans LLM Gateway
"""
            
            doc_path = self.project_root / "GPT-OSS-INTEGRATION-GUIDE.md"
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            logger.info(f"✅ Documentation générée: {doc_path}")
            
            self.status["generate_documentation"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur génération doc: {e}")
            return False
    
    def run_full_setup(self) -> bool:
        """Exécution complète du setup"""
        self.print_header()
        
        success_count = 0
        
        for step_name in self.setup_steps:
            step_method = getattr(self, step_name)
            
            try:
                if step_method():
                    success_count += 1
                    logger.info(f"✅ {step_name} RÉUSSI")
                else:
                    logger.error(f"❌ {step_name} ÉCHOUÉ")
            except Exception as e:
                logger.error(f"❌ {step_name} EXCEPTION: {e}")
        
        # Résumé final
        print("\n" + "="*70)
        print("📊 RÉSULTATS INSTALLATION")
        print("="*70)
        
        for step_name in self.setup_steps:
            status_icon = "✅" if self.status[step_name] else "❌"
            print(f"{status_icon} {step_name}")
        
        success_rate = success_count / len(self.setup_steps)
        print(f"\n🎯 Taux succès: {success_count}/{len(self.setup_steps)} ({success_rate*100:.1f}%)")
        
        if success_rate >= 0.8:  # 80% minimum
            print("\n🎉 INSTALLATION GPT-OSS RÉUSSIE!")
            print("   Votre JARVIS AI est prêt avec GPT-OSS 20B")
            print("   Guide: GPT-OSS-INTEGRATION-GUIDE.md")
            return True
        else:
            print("\n⚠️  INSTALLATION INCOMPLÈTE")
            print("   Vérifiez les erreurs ci-dessus")
            return False

def main():
    parser = argparse.ArgumentParser(description="Setup GPT-OSS 20B pour JARVIS AI")
    parser.add_argument("--project-root", help="Racine projet JARVIS")
    parser.add_argument("--skip-validation", action="store_true", help="Ignorer validation")
    parser.add_argument("--only-step", help="Exécuter seulement une étape spécifique")
    
    args = parser.parse_args()
    
    setup = JarvisGPTOSSSetup(args.project_root)
    
    if args.only_step:
        if hasattr(setup, args.only_step):
            step_method = getattr(setup, args.only_step)
            success = step_method()
            sys.exit(0 if success else 1)
        else:
            logger.error(f"Étape inconnue: {args.only_step}")
            sys.exit(1)
    
    success = setup.run_full_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()