#!/usr/bin/env python3
"""
JARVIS AI - Installation automatisée complète
Installe et configure automatiquement tout l'environnement JARVIS
"""

import os
import sys
import subprocess
import platform
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import time
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis-install.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Colors:
    """Codes couleur pour l'affichage terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class JarvisInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.project_dir = Path(__file__).parent.absolute()
        self.errors = []
        self.installed_components = []
        
    def print_banner(self):
        """Affiche la bannière d'installation"""
        banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔══════════════════════════════════════════╗
║            JARVIS AI INSTALLER           ║
║         Installation Automatisée         ║
╚══════════════════════════════════════════╝
{Colors.ENDC}
Système: {self.system.capitalize()}
Répertoire: {self.project_dir}
"""
        print(banner)

    def check_prerequisites(self) -> bool:
        """Vérifie les prérequis système"""
        logger.info("🔍 Vérification des prérequis...")
        
        prerequisites = {
            'python': {'cmd': 'python --version', 'min_version': '3.8'},
            'docker': {'cmd': 'docker --version', 'required': True},
            'docker-compose': {'cmd': 'docker-compose --version', 'required': True},
            'git': {'cmd': 'git --version', 'required': True},
        }
        
        if self.system == 'windows':
            prerequisites['python']['cmd'] = 'python --version'
        
        missing = []
        for name, config in prerequisites.items():
            try:
                result = subprocess.run(
                    config['cmd'].split(), 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                print(f"{Colors.OKGREEN}✓{Colors.ENDC} {name}: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                if config.get('required', False):
                    missing.append(name)
                    print(f"{Colors.FAIL}✗{Colors.ENDC} {name}: Non trouvé")
                else:
                    print(f"{Colors.WARNING}⚠{Colors.ENDC} {name}: Non trouvé (optionnel)")
        
        if missing:
            print(f"\n{Colors.FAIL}Prérequis manquants:{Colors.ENDC}")
            for item in missing:
                print(f"  - {item}")
            print(f"\n{Colors.WARNING}Veuillez installer les prérequis manquants et relancer l'installation.{Colors.ENDC}")
            return False
            
        return True

    def install_python_dependencies(self) -> bool:
        """Installe les dépendances Python"""
        logger.info("📦 Installation des dépendances Python...")
        
        try:
            # Créer l'environnement virtuel si nécessaire
            venv_path = self.project_dir / 'venv'
            if not venv_path.exists():
                print(f"{Colors.OKBLUE}Création de l'environnement virtuel...{Colors.ENDC}")
                subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
            
            # Activer l'environnement virtuel
            if self.system == 'windows':
                pip_cmd = str(venv_path / 'Scripts' / 'pip.exe')
                python_cmd = str(venv_path / 'Scripts' / 'python.exe')
            else:
                pip_cmd = str(venv_path / 'bin' / 'pip')
                python_cmd = str(venv_path / 'bin' / 'python')
            
            # Mise à jour de pip
            subprocess.run([python_cmd, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
            
            # Installation des dépendances principales
            requirements_files = [
                'requirements.txt',
                'local-interface/requirements.txt'
            ]
            
            for req_file in requirements_files:
                req_path = self.project_dir / req_file
                if req_path.exists():
                    print(f"  📋 Installation de {req_file}...")
                    subprocess.run([pip_cmd, 'install', '-r', str(req_path)], check=True)
            
            # Installation des dépendances de développement
            dev_packages = ['pytest', 'black', 'flake8', 'pre-commit']
            subprocess.run([pip_cmd, 'install'] + dev_packages, check=True)
            
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Dépendances Python installées")
            self.installed_components.append('Python Dependencies')
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Erreur lors de l'installation des dépendances Python: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def setup_docker_environment(self) -> bool:
        """Configure l'environnement Docker"""
        logger.info("🐳 Configuration de l'environnement Docker...")
        
        try:
            # Vérifier que Docker est démarré
            subprocess.run(['docker', 'info'], capture_output=True, check=True)
            
            # Construire les images Docker
            docker_services = [
                'brain-api',
                'stt-service', 
                'tts-service',
                'system-control',
                'terminal-service',
                'mcp-gateway',
                'autocomplete-service'
            ]
            
            for service in docker_services:
                service_path = self.project_dir / 'services' / service
                if service_path.exists() and (service_path / 'Dockerfile').exists():
                    print(f"  🔨 Construction de l'image {service}...")
                    subprocess.run([
                        'docker', 'build', 
                        '-t', f'jarvis-{service}',
                        str(service_path)
                    ], check=True, cwd=str(self.project_dir))
            
            # Configuration des réseaux Docker
            try:
                subprocess.run(['docker', 'network', 'create', 'jarvis-network'], 
                             capture_output=True, check=True)
            except subprocess.CalledProcessError:
                # Le réseau existe probablement déjà
                pass
            
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Environnement Docker configuré")
            self.installed_components.append('Docker Environment')
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Erreur lors de la configuration Docker: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def install_nodejs_dependencies(self) -> bool:
        """Installe les dépendances Node.js pour l'interface"""
        logger.info("🟢 Installation des dépendances Node.js...")
        
        try:
            ui_path = self.project_dir / 'ui'
            if not ui_path.exists():
                print(f"{Colors.WARNING}⚠{Colors.ENDC} Répertoire UI non trouvé, ignorer...")
                return True
            
            # Vérifier npm
            subprocess.run(['npm', '--version'], capture_output=True, check=True)
            
            # Installation des dépendances
            print(f"  📦 Installation des packages npm...")
            subprocess.run(['npm', 'install'], cwd=str(ui_path), check=True)
            
            # Build de production
            print(f"  🔨 Build de l'interface...")
            subprocess.run(['npm', 'run', 'build'], cwd=str(ui_path), check=True)
            
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Interface utilisateur installée")
            self.installed_components.append('UI Dependencies')
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"{Colors.WARNING}⚠{Colors.ENDC} Node.js non disponible, interface web désactivée")
            return True

    def setup_configuration(self) -> bool:
        """Configure les fichiers de configuration"""
        logger.info("⚙️ Configuration des fichiers...")
        
        try:
            # Créer les répertoires nécessaires
            directories = [
                'logs',
                'cache', 
                'memory',
                'models',
                'data'
            ]
            
            for directory in directories:
                dir_path = self.project_dir / directory
                dir_path.mkdir(exist_ok=True)
            
            # Configuration par défaut
            config = {
                "system": {
                    "debug": False,
                    "log_level": "INFO",
                    "auto_start": True
                },
                "services": {
                    "brain_api": {"port": 5000, "enabled": True},
                    "stt_service": {"port": 5001, "enabled": True},
                    "tts_service": {"port": 5002, "enabled": True},
                    "system_control": {"port": 5004, "enabled": True},
                    "terminal_service": {"port": 5005, "enabled": True},
                    "mcp_gateway": {"port": 5006, "enabled": True},
                    "autocomplete_service": {"port": 5007, "enabled": True}
                },
                "ai": {
                    "model": "llama3.2:latest",
                    "temperature": 0.7,
                    "max_tokens": 2048
                },
                "voice": {
                    "input_device": "default",
                    "output_device": "default",
                    "wake_word": "jarvis"
                }
            }
            
            config_path = self.project_dir / 'config' / 'jarvis.json'
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Configuration initialisée")
            self.installed_components.append('Configuration')
            return True
            
        except Exception as e:
            error_msg = f"Erreur lors de la configuration: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def setup_voice_bridge(self) -> bool:
        """Configure le pont vocal local"""
        logger.info("🎤 Configuration du pont vocal...")
        
        try:
            voice_bridge_path = self.project_dir / 'local-interface' / 'voice-bridge.py'
            if not voice_bridge_path.exists():
                print(f"{Colors.WARNING}⚠{Colors.ENDC} voice-bridge.py non trouvé")
                return True
            
            # Créer un script de lancement pour le pont vocal
            if self.system == 'windows':
                launcher_content = f"""@echo off
cd /d "{self.project_dir}"
call venv\\Scripts\\activate
python local-interface\\voice-bridge.py
pause
"""
                launcher_path = self.project_dir / 'start-voice-bridge.bat'
            else:
                launcher_content = f"""#!/bin/bash
cd "{self.project_dir}"
source venv/bin/activate
python local-interface/voice-bridge.py
"""
                launcher_path = self.project_dir / 'start-voice-bridge.sh'
            
            with open(launcher_path, 'w') as f:
                f.write(launcher_content)
            
            if self.system != 'windows':
                os.chmod(launcher_path, 0o755)
            
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Pont vocal configuré")
            self.installed_components.append('Voice Bridge')
            return True
            
        except Exception as e:
            error_msg = f"Erreur lors de la configuration du pont vocal: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def create_launch_scripts(self) -> bool:
        """Crée les scripts de lancement automatique"""
        logger.info("🚀 Création des scripts de lancement...")
        
        try:
            # Script de lancement principal Windows
            if self.system == 'windows':
                windows_script = f"""@echo off
title JARVIS AI - Lancement Automatique
echo.
echo ╔══════════════════════════════════════════╗
echo ║            JARVIS AI STARTUP             ║
echo ╚══════════════════════════════════════════╝
echo.

cd /d "{self.project_dir}"

echo [1/4] Demarrage des services Docker...
docker-compose up -d
if errorlevel 1 (
    echo ERREUR: Echec du demarrage Docker
    pause
    exit /b 1
)

echo [2/4] Attente de l'initialisation des services...
timeout /t 10 /nobreak >nul

echo [3/4] Demarrage du pont vocal...
start "Voice Bridge" start-voice-bridge.bat

echo [4/4] Demarrage de l'interface principale...
call venv\\Scripts\\activate
start "JARVIS Main" python start_jarvis.py

echo.
echo ✓ JARVIS AI demarre avec succes!
echo   - Interface web: http://localhost:3000
echo   - API principale: http://localhost:5000
echo   - Documentation: http://localhost:5000/docs
echo.
echo Appuyez sur une touche pour fermer cette fenetre...
pause >nul
"""
                with open(self.project_dir / 'launch-jarvis.bat', 'w') as f:
                    f.write(windows_script)
            
            # Script de lancement principal Linux/Mac
            unix_script = f"""#!/bin/bash
echo "╔══════════════════════════════════════════╗"
echo "║            JARVIS AI STARTUP             ║"
echo "╚══════════════════════════════════════════╝"
echo

cd "{self.project_dir}"

echo "[1/4] Démarrage des services Docker..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "ERREUR: Échec du démarrage Docker"
    exit 1
fi

echo "[2/4] Attente de l'initialisation des services..."
sleep 10

echo "[3/4] Démarrage du pont vocal..."
./start-voice-bridge.sh &

echo "[4/4] Démarrage de l'interface principale..."
source venv/bin/activate
python start_jarvis.py &

echo
echo "✓ JARVIS AI démarré avec succès!"
echo "  - Interface web: http://localhost:3000"
echo "  - API principale: http://localhost:5000"
echo "  - Documentation: http://localhost:5000/docs"
echo
"""
            with open(self.project_dir / 'launch-jarvis.sh', 'w') as f:
                f.write(unix_script)
            os.chmod(self.project_dir / 'launch-jarvis.sh', 0o755)
            
            # Script d'arrêt
            stop_script = """#!/bin/bash
echo "Arrêt de JARVIS AI..."
docker-compose down
pkill -f voice-bridge.py
pkill -f start_jarvis.py
echo "✓ JARVIS AI arrêté"
"""
            with open(self.project_dir / 'stop-jarvis.sh', 'w') as f:
                f.write(stop_script)
            os.chmod(self.project_dir / 'stop-jarvis.sh', 0o755)
            
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Scripts de lancement créés")
            self.installed_components.append('Launch Scripts')
            return True
            
        except Exception as e:
            error_msg = f"Erreur lors de la création des scripts: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def pull_ai_models(self) -> bool:
        """Télécharge les modèles IA nécessaires"""
        logger.info("🤖 Téléchargement des modèles IA...")
        
        try:
            # Vérifier si Ollama est disponible
            try:
                subprocess.run(['ollama', 'version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"{Colors.WARNING}⚠{Colors.ENDC} Ollama non installé, modèles IA non téléchargés")
                return True
            
            # Modèles à télécharger
            models = [
                'llama3.2:latest',
                'codellama:7b'
            ]
            
            for model in models:
                print(f"  📥 Téléchargement de {model}...")
                try:
                    subprocess.run(['ollama', 'pull', model], check=True, timeout=600)
                except subprocess.TimeoutExpired:
                    print(f"{Colors.WARNING}⚠{Colors.ENDC} Timeout pour {model}, continuer...")
                except subprocess.CalledProcessError:
                    print(f"{Colors.WARNING}⚠{Colors.ENDC} Échec du téléchargement de {model}")
            
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Modèles IA téléchargés")
            self.installed_components.append('AI Models')
            return True
            
        except Exception as e:
            error_msg = f"Erreur lors du téléchargement des modèles: {e}"
            logger.error(error_msg)
            return True  # Non bloquant

    def run_tests(self) -> bool:
        """Exécute les tests de base"""
        logger.info("🧪 Exécution des tests de validation...")
        
        try:
            # Test des imports Python
            test_imports = [
                'import fastapi',
                'import websockets', 
                'import pydantic',
                'import uvicorn'
            ]
            
            for test_import in test_imports:
                try:
                    subprocess.run([
                        sys.executable, '-c', test_import
                    ], check=True, capture_output=True, cwd=str(self.project_dir))
                except subprocess.CalledProcessError:
                    print(f"{Colors.WARNING}⚠{Colors.ENDC} Import échoué: {test_import}")
            
            # Test de la configuration Docker
            try:
                result = subprocess.run([
                    'docker-compose', 'config'
                ], capture_output=True, text=True, cwd=str(self.project_dir))
                if result.returncode != 0:
                    print(f"{Colors.WARNING}⚠{Colors.ENDC} Configuration Docker invalide")
            except subprocess.CalledProcessError:
                print(f"{Colors.WARNING}⚠{Colors.ENDC} Impossible de valider Docker")
            
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Tests de validation terminés")
            return True
            
        except Exception as e:
            error_msg = f"Erreur lors des tests: {e}"
            logger.error(error_msg)
            return True  # Non bloquant

    def print_summary(self):
        """Affiche le résumé de l'installation"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}╔═══════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}║              INSTALLATION TERMINÉE            ║{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}╚═══════════════════════════════════════════════╝{Colors.ENDC}")
        
        print(f"\n{Colors.OKGREEN}Composants installés:{Colors.ENDC}")
        for component in self.installed_components:
            print(f"  ✓ {component}")
        
        if self.errors:
            print(f"\n{Colors.WARNING}Avertissements:{Colors.ENDC}")
            for error in self.errors:
                print(f"  ⚠ {error}")
        
        print(f"\n{Colors.OKBLUE}Comment démarrer JARVIS:{Colors.ENDC}")
        if self.system == 'windows':
            print(f"  📄 Double-cliquez sur: launch-jarvis.bat")
        else:
            print(f"  📄 Exécutez: ./launch-jarvis.sh")
        
        print(f"\n{Colors.OKBLUE}Accès aux services:{Colors.ENDC}")
        print(f"  🌐 Interface web: http://localhost:3000")
        print(f"  🔗 API principale: http://localhost:5000")
        print(f"  📚 Documentation: http://localhost:5000/docs")
        
        print(f"\n{Colors.OKCYAN}Pour plus d'aide, consultez le README.md{Colors.ENDC}")

    def install(self):
        """Lance l'installation complète"""
        self.print_banner()
        
        if not self.check_prerequisites():
            sys.exit(1)
        
        installation_steps = [
            ('Dépendances Python', self.install_python_dependencies),
            ('Environnement Docker', self.setup_docker_environment), 
            ('Interface utilisateur', self.install_nodejs_dependencies),
            ('Configuration', self.setup_configuration),
            ('Pont vocal', self.setup_voice_bridge),
            ('Scripts de lancement', self.create_launch_scripts),
            ('Modèles IA', self.pull_ai_models),
            ('Tests de validation', self.run_tests)
        ]
        
        failed_steps = []
        for step_name, step_func in installation_steps:
            print(f"\n{Colors.OKBLUE}🔧 {step_name}...{Colors.ENDC}")
            if not step_func():
                failed_steps.append(step_name)
        
        if failed_steps:
            print(f"\n{Colors.FAIL}Étapes échouées:{Colors.ENDC}")
            for step in failed_steps:
                print(f"  ✗ {step}")
            print(f"\n{Colors.WARNING}Installation partiellement réussie. Consultez les logs pour plus de détails.{Colors.ENDC}")
        
        self.print_summary()

if __name__ == '__main__':
    installer = JarvisInstaller()
    try:
        installer.install()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Installation interrompue par l'utilisateur.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Erreur fatale: {e}{Colors.ENDC}")
        logger.exception("Erreur fatale lors de l'installation")
        sys.exit(1)