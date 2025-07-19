#!/usr/bin/env python3
"""
🚀 JARVIS Launcher - Démarre l'API et l'interface utilisateur
Orchestre le démarrage de tous les composants de JARVIS Phase 2
"""

import asyncio
import subprocess
import sys
import time
import signal
import os
import threading
from pathlib import Path
from typing import Optional, List
import psutil
from loguru import logger

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.server import run_server


class JarvisLauncher:
    """Gestionnaire de lancement et d'arrêt de JARVIS"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.api_thread: Optional[threading.Thread] = None
        self.shutdown_requested = False
        
        # Configuration
        self.api_host = "127.0.0.1"
        self.api_port = 8000
        self.ui_dev_port = 3000
        
        # Chemins
        self.project_root = Path(__file__).parent.parent
        self.ui_path = self.project_root / "ui"
        
    def setup_signal_handlers(self):
        """Configure les gestionnaires de signaux pour un arrêt propre"""
        def signal_handler(signum, frame):
            logger.info(f"Signal {signum} reçu, arrêt en cours...")
            self.shutdown_requested = True
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def check_dependencies(self) -> bool:
        """Vérifie que toutes les dépendances sont disponibles"""
        logger.info("🔍 Vérification des dépendances...")
        
        # Vérifier Python et modules
        try:
            import fastapi
            import uvicorn
            import websockets
            logger.success("✅ Modules Python OK")
        except ImportError as e:
            logger.error(f"❌ Module Python manquant: {e}")
            return False
        
        # Vérifier Node.js et npm (pour l'interface)
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.success(f"✅ Node.js OK: {result.stdout.strip()}")
            else:
                logger.warning("⚠️ Node.js non disponible (interface web uniquement)")
        except FileNotFoundError:
            logger.warning("⚠️ Node.js non trouvé (interface web uniquement)")
        
        # Vérifier les répertoires
        if not self.ui_path.exists():
            logger.error(f"❌ Répertoire UI non trouvé: {self.ui_path}")
            return False
        
        if not (self.ui_path / "package.json").exists():
            logger.error("❌ package.json non trouvé dans le répertoire UI")
            return False
        
        logger.success("✅ Toutes les dépendances sont disponibles")
        return True
    
    def install_ui_dependencies(self) -> bool:
        """Installe les dépendances de l'interface utilisateur"""
        logger.info("📦 Installation des dépendances UI...")
        
        try:
            # Vérifier si node_modules existe déjà
            if (self.ui_path / "node_modules").exists():
                logger.info("📦 Dépendances UI déjà installées")
                return True
            
            # Installer avec npm
            process = subprocess.run(
                ["npm", "install"],
                cwd=self.ui_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if process.returncode == 0:
                logger.success("✅ Dépendances UI installées")
                return True
            else:
                logger.error(f"❌ Erreur installation UI: {process.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout lors de l'installation des dépendances UI")
            return False
        except FileNotFoundError:
            logger.warning("⚠️ npm non trouvé, interface Electron non disponible")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur installation dépendances: {e}")
            return False
    
    def start_api_server(self):
        """Démarre le serveur API en arrière-plan"""
        logger.info(f"🌐 Démarrage du serveur API sur {self.api_host}:{self.api_port}")
        
        def run_api():
            try:
                run_server(host=self.api_host, port=self.api_port, reload=False)
            except Exception as e:
                logger.error(f"❌ Erreur serveur API: {e}")
        
        self.api_thread = threading.Thread(target=run_api, daemon=True)
        self.api_thread.start()
        
        # Attendre que le serveur soit prêt
        for i in range(30):  # Attendre max 30 secondes
            try:
                import requests
                response = requests.get(f"http://{self.api_host}:{self.api_port}/api/health", timeout=1)
                if response.status_code == 200:
                    logger.success("✅ Serveur API prêt")
                    return True
            except:
                pass
            time.sleep(1)
        
        logger.error("❌ Serveur API n'a pas démarré dans les temps")
        return False
    
    def start_ui_dev_server(self) -> bool:
        """Démarre le serveur de développement React"""
        logger.info(f"🎨 Démarrage du serveur UI de développement sur port {self.ui_dev_port}")
        
        try:
            # Définir les variables d'environnement pour React
            env = os.environ.copy()
            env.update({
                "REACT_APP_API_URL": f"http://{self.api_host}:{self.api_port}",
                "REACT_APP_WS_URL": f"ws://{self.api_host}:{self.api_port}/ws",
                "PORT": str(self.ui_dev_port),
                "BROWSER": "none"  # Ne pas ouvrir automatiquement le navigateur
            })
            
            # Démarrer le serveur de développement
            process = subprocess.Popen(
                ["npm", "start"],
                cwd=self.ui_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append(process)
            
            # Attendre que le serveur soit prêt
            logger.info("⏳ Attente du démarrage du serveur UI...")
            for i in range(60):  # Attendre max 60 secondes
                try:
                    import requests
                    response = requests.get(f"http://localhost:{self.ui_dev_port}", timeout=1)
                    if response.status_code == 200:
                        logger.success("✅ Serveur UI prêt")
                        return True
                except:
                    pass
                time.sleep(1)
            
            logger.error("❌ Serveur UI n'a pas démarré dans les temps")
            return False
            
        except FileNotFoundError:
            logger.warning("⚠️ npm non trouvé, impossible de démarrer le serveur UI")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur démarrage serveur UI: {e}")
            return False
    
    def start_electron_app(self) -> bool:
        """Démarre l'application Electron"""
        logger.info("🖥️ Démarrage de l'application Electron...")
        
        try:
            # Vérifier si Electron est installé
            electron_path = self.ui_path / "node_modules" / ".bin" / "electron"
            if not electron_path.exists():
                logger.error("❌ Electron non installé")
                return False
            
            # Démarrer Electron
            process = subprocess.Popen(
                ["npm", "run", "electron"],
                cwd=self.ui_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append(process)
            logger.success("✅ Application Electron démarrée")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage Electron: {e}")
            return False
    
    def open_browser(self):
        """Ouvre le navigateur avec l'interface web"""
        logger.info("🌐 Ouverture du navigateur...")
        
        import webbrowser
        url = f"http://localhost:{self.ui_dev_port}"
        
        try:
            webbrowser.open(url)
            logger.success(f"✅ Navigateur ouvert: {url}")
        except Exception as e:
            logger.warning(f"⚠️ Impossible d'ouvrir le navigateur: {e}")
            logger.info(f"🔗 Ouvrez manuellement: {url}")
    
    async def shutdown(self):
        """Arrêt propre de tous les services"""
        if self.shutdown_requested:
            return
        
        self.shutdown_requested = True
        logger.info("🔄 Arrêt de JARVIS en cours...")
        
        # Arrêter tous les processus
        for process in self.processes:
            try:
                if process.poll() is None:  # Processus encore en vie
                    logger.info(f"🛑 Arrêt du processus {process.pid}")
                    process.terminate()
                    
                    # Attendre l'arrêt gracieux
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"⚠️ Forçage de l'arrêt du processus {process.pid}")
                        process.kill()
                        process.wait()
            except Exception as e:
                logger.warning(f"⚠️ Erreur arrêt processus: {e}")
        
        # Nettoyer la liste des processus
        self.processes.clear()
        
        logger.success("✅ JARVIS arrêté proprement")
    
    async def run(self, mode: str = "full"):
        """Lance JARVIS dans le mode spécifié"""
        logger.info("🚀 Démarrage de JARVIS Phase 2...")
        
        # Vérifications préliminaires
        if not self.check_dependencies():
            logger.error("❌ Dépendances manquantes")
            return False
        
        # Installer les dépendances UI si nécessaire
        if mode in ["full", "electron", "web"] and not self.install_ui_dependencies():
            logger.warning("⚠️ Impossible d'installer les dépendances UI")
            if mode in ["electron", "web"]:
                return False
        
        # Démarrer le serveur API
        if not self.start_api_server():
            logger.error("❌ Impossible de démarrer le serveur API")
            return False
        
        # Démarrer selon le mode
        if mode == "api":
            logger.success("✅ JARVIS API démarré en mode serveur uniquement")
            logger.info(f"🔗 API disponible sur: http://{self.api_host}:{self.api_port}")
            logger.info(f"📖 Documentation: http://{self.api_host}:{self.api_port}/api/docs")
            
        elif mode == "web":
            # Mode web avec serveur de développement
            if self.start_ui_dev_server():
                self.open_browser()
                logger.success("✅ JARVIS démarré en mode web")
                logger.info(f"🔗 Interface: http://localhost:{self.ui_dev_port}")
            else:
                logger.error("❌ Impossible de démarrer l'interface web")
                return False
        
        elif mode == "electron":
            # Mode Electron
            if self.start_ui_dev_server() and self.start_electron_app():
                logger.success("✅ JARVIS démarré en mode Electron")
            else:
                logger.error("❌ Impossible de démarrer l'application Electron")
                return False
        
        elif mode == "full":
            # Mode complet avec options
            if self.start_ui_dev_server():
                logger.info("🎯 Choisissez votre interface:")
                logger.info("  1. Navigateur web")
                logger.info("  2. Application Electron")
                logger.info("  3. Les deux")
                
                choice = input("Votre choix (1-3): ").strip()
                
                if choice in ["1", "3"]:
                    self.open_browser()
                
                if choice in ["2", "3"]:
                    self.start_electron_app()
                
                logger.success("✅ JARVIS démarré en mode complet")
            else:
                logger.error("❌ Impossible de démarrer l'interface")
                return False
        
        else:
            logger.error(f"❌ Mode inconnu: {mode}")
            return False
        
        # Boucle principale - attendre l'arrêt
        try:
            while not self.shutdown_requested:
                await asyncio.sleep(1)
                
                # Vérifier que les processus sont toujours en vie
                for process in self.processes[:]:  # Copie pour éviter les modifications concurrent
                    if process.poll() is not None:
                        logger.warning(f"⚠️ Processus {process.pid} s'est arrêté")
                        self.processes.remove(process)
        
        except KeyboardInterrupt:
            logger.info("⏹️ Arrêt demandé par l'utilisateur")
        
        finally:
            await self.shutdown()
        
        return True


async def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS Phase 2 Launcher")
    parser.add_argument(
        "--mode", 
        choices=["api", "web", "electron", "full"],
        default="full",
        help="Mode de démarrage (défaut: full)"
    )
    parser.add_argument(
        "--api-host",
        default="127.0.0.1",
        help="Adresse d'écoute de l'API (défaut: 127.0.0.1)"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="Port d'écoute de l'API (défaut: 8000)"
    )
    
    args = parser.parse_args()
    
    # Bannière
    print("""
    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
    ██║███████║██████╔╝██║   ██║██║███████╗
    ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
    ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║
    ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
    
    🤖 Assistant IA Autonome - Phase 2
    Mode: {args.mode} | API: {args.api_host}:{args.api_port}
    """)
    
    # Créer et lancer JARVIS
    launcher = JarvisLauncher()
    launcher.api_host = args.api_host
    launcher.api_port = args.api_port
    launcher.setup_signal_handlers()
    
    success = await launcher.run(args.mode)
    
    if success:
        logger.success("👋 JARVIS arrêté avec succès")
        return 0
    else:
        logger.error("❌ JARVIS s'est arrêté avec des erreurs")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n👋 Arrêt demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)