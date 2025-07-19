#!/usr/bin/env python3
"""
🛠️ Script d'installation automatique JARVIS Phase 2
Installe et configure automatiquement tous les composants
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Optional, List
import urllib.request
import zipfile
import json

class JarvisInstaller:
    """Installateur automatique pour JARVIS"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.project_root = Path(__file__).parent
        self.python_executable = sys.executable
        self.errors = []
        self.warnings = []
        
        # Versions recommandées
        self.versions = {
            "python": "3.11.0",
            "node": "18.0.0",
            "npm": "9.0.0"
        }
    
    def print_banner(self):
        """Affiche la bannière d'installation"""
        print("""
    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
    ██║███████║██████╔╝██║   ██║██║███████╗
    ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
    ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║
    ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
    
    🛠️  Installation Automatique JARVIS Phase 2
    """)
    
    def run_command(self, command: List[str], cwd: Optional[Path] = None, 
                   capture_output: bool = False, check: bool = True) -> subprocess.CompletedProcess:
        """Exécute une commande avec gestion d'erreurs"""
        try:
            print(f"🔧 Exécution: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=capture_output,
                text=True,
                check=check
            )
            
            if capture_output and result.stdout:
                print(f"📤 Sortie: {result.stdout.strip()}")
            
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Erreur commande: {' '.join(command)}"
            if e.stderr:
                error_msg += f"\\n{e.stderr}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            if check:
                raise
            return e
        except FileNotFoundError:
            error_msg = f"Commande non trouvée: {command[0]}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            if check:
                raise
            return None
    
    def check_python_version(self) -> bool:
        """Vérifie la version de Python"""
        print("🐍 Vérification de Python...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 11):
            self.errors.append(f"Python 3.11+ requis, trouvé {version.major}.{version.minor}")
            return False
        
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} OK")
        return True
    
    def check_node_npm(self) -> bool:
        """Vérifie Node.js et npm"""
        print("📦 Vérification de Node.js et npm...")
        
        try:
            # Vérifier Node.js
            result = self.run_command(["node", "--version"], capture_output=True, check=False)
            if result and result.returncode == 0:
                node_version = result.stdout.strip()
                print(f"✅ Node.js {node_version} trouvé")
            else:
                self.warnings.append("Node.js non trouvé - interface web non disponible")
                return False
            
            # Vérifier npm
            result = self.run_command(["npm", "--version"], capture_output=True, check=False)
            if result and result.returncode == 0:
                npm_version = result.stdout.strip()
                print(f"✅ npm {npm_version} trouvé")
                return True
            else:
                self.warnings.append("npm non trouvé - interface web non disponible")
                return False
                
        except Exception as e:
            self.warnings.append(f"Erreur vérification Node.js/npm: {e}")
            return False
    
    def check_ollama(self) -> bool:
        """Vérifie Ollama"""
        print("🤖 Vérification d'Ollama...")
        
        try:
            result = self.run_command(["ollama", "--version"], capture_output=True, check=False)
            if result and result.returncode == 0:
                print("✅ Ollama trouvé")
                
                # Vérifier les modèles recommandés
                models_to_check = ["llama3.2:3b", "llava:7b"]
                for model in models_to_check:
                    result = self.run_command(["ollama", "list"], capture_output=True, check=False)
                    if result and model in result.stdout:
                        print(f"✅ Modèle {model} disponible")
                    else:
                        print(f"⚠️ Modèle {model} non trouvé - sera installé plus tard")
                
                return True
            else:
                self.warnings.append("Ollama non trouvé - certaines fonctionnalités IA non disponibles")
                return False
                
        except Exception as e:
            self.warnings.append(f"Erreur vérification Ollama: {e}")
            return False
    
    def check_tesseract(self) -> bool:
        """Vérifie Tesseract OCR"""
        print("👁️ Vérification de Tesseract OCR...")
        
        try:
            result = self.run_command(["tesseract", "--version"], capture_output=True, check=False)
            if result and result.returncode == 0:
                print("✅ Tesseract OCR trouvé")
                return True
            else:
                self.warnings.append("Tesseract OCR non trouvé - OCR non disponible")
                return False
                
        except Exception as e:
            self.warnings.append(f"Erreur vérification Tesseract: {e}")
            return False
    
    def create_virtual_environment(self) -> bool:
        """Crée l'environnement virtuel Python"""
        print("🐍 Création de l'environnement virtuel...")
        
        venv_path = self.project_root / "venv"
        
        if venv_path.exists():
            print("✅ Environnement virtuel existe déjà")
            return True
        
        try:
            self.run_command([self.python_executable, "-m", "venv", "venv"])
            print("✅ Environnement virtuel créé")
            return True
        except Exception as e:
            self.errors.append(f"Erreur création environnement virtuel: {e}")
            return False
    
    def install_python_dependencies(self) -> bool:
        """Installe les dépendances Python"""
        print("📦 Installation des dépendances Python...")
        
        venv_path = self.project_root / "venv"
        
        if self.system == "windows":
            pip_executable = venv_path / "Scripts" / "pip.exe"
        else:
            pip_executable = venv_path / "bin" / "pip"
        
        if not pip_executable.exists():
            self.errors.append("pip non trouvé dans l'environnement virtuel")
            return False
        
        try:
            # Mettre à jour pip
            self.run_command([str(pip_executable), "install", "--upgrade", "pip"])
            
            # Installer les dépendances
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                self.run_command([str(pip_executable), "install", "-r", str(requirements_file)])
                print("✅ Dépendances Python installées")
                return True
            else:
                self.errors.append("Fichier requirements.txt non trouvé")
                return False
                
        except Exception as e:
            self.errors.append(f"Erreur installation dépendances Python: {e}")
            return False
    
    def install_node_dependencies(self) -> bool:
        """Installe les dépendances Node.js"""
        print("📦 Installation des dépendances Node.js...")
        
        ui_path = self.project_root / "ui"
        package_json = ui_path / "package.json"
        
        if not package_json.exists():
            self.warnings.append("package.json non trouvé - interface web non disponible")
            return False
        
        try:
            self.run_command(["npm", "install"], cwd=ui_path)
            print("✅ Dépendances Node.js installées")
            return True
        except Exception as e:
            self.warnings.append(f"Erreur installation dépendances Node.js: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Crée les répertoires nécessaires"""
        print("📁 Création des répertoires...")
        
        directories = [
            "logs",
            "memory",
            "memory/chroma",
            "screenshots",
            "exports",
            "temp"
        ]
        
        try:
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Répertoire créé: {directory}")
            
            return True
        except Exception as e:
            self.errors.append(f"Erreur création répertoires: {e}")
            return False
    
    def setup_configuration(self) -> bool:
        """Configure les fichiers de configuration"""
        print("⚙️ Configuration...")
        
        try:
            # Copier .env.example vers .env si n'existe pas
            env_example = self.project_root / ".env.example"
            env_file = self.project_root / ".env"
            
            if env_example.exists() and not env_file.exists():
                shutil.copy2(env_example, env_file)
                print("✅ Fichier .env créé depuis .env.example")
            
            # Créer gitignore si nécessaire
            gitignore = self.project_root / ".gitignore"
            if not gitignore.exists():
                gitignore_content = \"\"\"# JARVIS .gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/

# JARVIS specific
.env
logs/
memory/
screenshots/
temp/
*.log

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
\"\"\"
                with open(gitignore, "w", encoding="utf-8") as f:
                    f.write(gitignore_content)
                print("✅ .gitignore créé")
            
            return True
        except Exception as e:
            self.errors.append(f"Erreur configuration: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Lance les tests d'intégration"""
        print("🧪 Lancement des tests...")
        
        try:
            venv_path = self.project_root / "venv"
            
            if self.system == "windows":
                python_executable = venv_path / "Scripts" / "python.exe"
            else:
                python_executable = venv_path / "bin" / "python"
            
            if not python_executable.exists():
                python_executable = self.python_executable
            
            # Lancer les tests avec timeout
            result = self.run_command(
                [str(python_executable), "start_jarvis.py", "--test"],
                check=False
            )
            
            if result and result.returncode == 0:
                print("✅ Tests d'intégration réussis")
                return True
            else:
                self.warnings.append("Tests d'intégration échoués - vérifiez la configuration")
                return False
                
        except Exception as e:
            self.warnings.append(f"Erreur tests: {e}")
            return False
    
    def print_summary(self):
        """Affiche le résumé de l'installation"""
        print("\\n" + "="*60)
        print("📋 RÉSUMÉ DE L'INSTALLATION")
        print("="*60)
        
        if not self.errors:
            print("🎉 Installation réussie !")
            print("\\n🚀 Pour démarrer JARVIS :")
            print("   python start_jarvis.py")
            print("\\n🌐 Interfaces disponibles :")
            print("   • Interface web: http://localhost:3000")
            print("   • API: http://localhost:8000/api/docs")
            
            if self.warnings:
                print("\\n⚠️ Avertissements :")
                for warning in self.warnings:
                    print(f"   • {warning}")
        else:
            print("❌ Installation échouée")
            print("\\n❌ Erreurs :")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings and not self.errors:
            print("\\n💡 Installation partielle - certaines fonctionnalités peuvent être limitées")
    
    def install(self, run_tests: bool = True) -> bool:
        """Lance l'installation complète"""
        self.print_banner()
        
        steps = [
            ("Vérification Python", self.check_python_version),
            ("Vérification Node.js/npm", self.check_node_npm),
            ("Vérification Ollama", self.check_ollama),
            ("Vérification Tesseract", self.check_tesseract),
            ("Création environnement virtuel", self.create_virtual_environment),
            ("Installation dépendances Python", self.install_python_dependencies),
            ("Installation dépendances Node.js", self.install_node_dependencies),
            ("Création répertoires", self.create_directories),
            ("Configuration", self.setup_configuration),
        ]
        
        if run_tests:
            steps.append(("Tests d'intégration", self.run_tests))
        
        print(f"🔧 Début de l'installation ({len(steps)} étapes)\\n")
        
        for i, (step_name, step_function) in enumerate(steps, 1):
            print(f"[{i}/{len(steps)}] {step_name}...")
            try:
                success = step_function()
                if success:
                    print(f"✅ {step_name} terminé\\n")
                else:
                    print(f"⚠️ {step_name} avec avertissements\\n")
            except Exception as e:
                print(f"❌ {step_name} échoué: {e}\\n")
                self.errors.append(f"{step_name}: {e}")
        
        self.print_summary()
        return len(self.errors) == 0


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Installation automatique JARVIS Phase 2")
    parser.add_argument("--no-tests", action="store_true", help="Ignorer les tests d'intégration")
    parser.add_argument("--force", action="store_true", help="Forcer l'installation même en cas d'erreurs")
    
    args = parser.parse_args()
    
    installer = JarvisInstaller()
    success = installer.install(run_tests=not args.no_tests)
    
    if success:
        print("\\n🎉 Installation terminée avec succès !")
        print("\\nPour démarrer JARVIS :")
        print("  python start_jarvis.py")
        return 0
    else:
        if args.force:
            print("\\n⚠️ Installation forcée malgré les erreurs")
            return 0
        else:
            print("\\n❌ Installation échouée")
            print("\\nUtilisez --force pour ignorer les erreurs")
            return 1


if __name__ == "__main__":
    sys.exit(main())