#!/usr/bin/env python3
"""
🚀 Script de démarrage simple pour JARVIS Phase 2
Point d'entrée unique pour démarrer JARVIS avec tous ses composants
"""

import asyncio
import sys
import argparse
from pathlib import Path
from loguru import logger

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

from api.launcher import JarvisLauncher

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="🤖 JARVIS Phase 2 - Assistant IA Autonome",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python start_jarvis.py                    # Démarrage complet interactif
  python start_jarvis.py --mode web         # Interface web uniquement  
  python start_jarvis.py --mode api         # API uniquement
  python start_jarvis.py --mode electron    # Application Electron
  python start_jarvis.py --test             # Tests d'intégration
        """
    )
    
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
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Lancer les tests d'intégration"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Mode debug avec logs détaillés"
    )
    
    args = parser.parse_args()
    
    # Configuration des logs
    if args.debug:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
    
    # Bannière
    print("""
    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
    ██║███████║██████╔╝██║   ██║██║███████╗
    ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
    ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║
    ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
    
    🤖 Assistant IA Autonome - Phase 2 COMPLÈTE
    """)
    
    async def run_app():
        if args.test:
            # Lancer les tests d'intégration
            logger.info("🧪 Lancement des tests d'intégration...")
            
            try:
                from test_phase2_integration import Phase2IntegrationTester
                tester = Phase2IntegrationTester()
                success = await tester.run_integration_tests()
                return 0 if success else 1
            except ImportError as e:
                logger.error(f"❌ Impossible d'importer les tests: {e}")
                return 1
        else:
            # Lancer JARVIS normalement
            logger.info(f"🚀 Démarrage de JARVIS en mode {args.mode}...")
            
            launcher = JarvisLauncher()
            launcher.api_host = args.api_host
            launcher.api_port = args.api_port
            launcher.setup_signal_handlers()
            
            try:
                success = await launcher.run(args.mode)
                return 0 if success else 1
            except Exception as e:
                logger.error(f"❌ Erreur démarrage JARVIS: {e}")
                return 1
    
    try:
        exit_code = asyncio.run(run_app())
        
        if exit_code == 0:
            logger.success("👋 JARVIS arrêté avec succès")
        else:
            logger.error("❌ JARVIS s'est arrêté avec des erreurs")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("\n👋 Arrêt demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()