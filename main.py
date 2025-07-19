#!/usr/bin/env python3
"""
🤖 JARVIS - Agent IA Autonome pour Windows
Script principal de démonstration et test

Usage:
    python main.py                    # Mode interactif
    python main.py --demo            # Mode démonstration
    python main.py --test            # Tests des modules
    python main.py --command "..."   # Commande directe
"""
import asyncio
import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Any
import json
from loguru import logger

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

# Imports des modules JARVIS
from core.agent import JarvisAgent, create_agent
from core.vision.screen_capture import ScreenCapture, quick_screenshot
from core.vision.ocr_engine import OCREngine, quick_ocr
from core.vision.visual_analysis import VisualAnalyzer, quick_screen_analysis
from core.control.mouse_controller import MouseController, quick_click
from core.control.keyboard_controller import KeyboardController, quick_type
from core.control.app_detector import AppDetector, get_current_app
from core.ai.ollama_service import OllamaService, quick_chat
from core.ai.action_planner import ActionPlanner, quick_plan
from config.amd_gpu import configure_amd_gpu, OLLAMA_CONFIG

class JarvisDemo:
    """Classe de démonstration de JARVIS"""
    
    def __init__(self):
        self.modules = {}
        self.agent = None
        
    async def initialize_all_modules(self):
        """Initialise tous les modules JARVIS"""
        logger.info("🚀 Initialisation complète de JARVIS...")
        
        try:
            # Configuration GPU AMD
            configure_amd_gpu()
            
            # Vision
            logger.info("📸 Initialisation des modules de vision...")
            self.modules['screen_capture'] = ScreenCapture()
            await self.modules['screen_capture'].initialize()
            
            self.modules['ocr'] = OCREngine()
            await self.modules['ocr'].initialize()
            
            self.modules['vision_analyzer'] = VisualAnalyzer()
            await self.modules['vision_analyzer'].initialize()
            
            # Contrôle
            logger.info("🎮 Initialisation des modules de contrôle...")
            self.modules['mouse'] = MouseController(sandbox_mode=True)
            await self.modules['mouse'].initialize()
            
            self.modules['keyboard'] = KeyboardController(sandbox_mode=True)
            await self.modules['keyboard'].initialize()
            
            self.modules['app_detector'] = AppDetector()
            await self.modules['app_detector'].initialize()
            
            # IA
            logger.info("🤖 Initialisation des modules IA...")
            self.modules['ollama'] = OllamaService()
            await self.modules['ollama'].initialize()
            
            self.modules['planner'] = ActionPlanner(self.modules['ollama'])
            
            # Agent principal
            logger.info("🎯 Création de l'agent JARVIS...")
            self.agent = await create_agent()
            
            logger.success("✅ JARVIS complètement initialisé et prêt!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    async def run_basic_tests(self):
        """Exécute les tests de base de tous les modules"""
        logger.info("🧪 Lancement des tests de base...")
        
        results = {}
        
        # Test capture d'écran
        try:
            logger.info("📸 Test capture d'écran...")
            screenshot = await self.modules['screen_capture'].capture()
            if screenshot:
                logger.success("✅ Capture d'écran OK")
                results['screenshot'] = True
                
                # Sauvegarder pour inspection
                screenshot.save("test_screenshot.png")
                logger.info("💾 Capture sauvée: test_screenshot.png")
            else:
                raise Exception("Capture échouée")
        except Exception as e:
            logger.error(f"❌ Test capture d'écran échoué: {e}")
            results['screenshot'] = False
        
        # Test OCR
        try:
            logger.info("🔍 Test OCR...")
            if results.get('screenshot') and 'screen_capture' in self.modules:
                screenshot = await self.modules['screen_capture'].capture()
                if screenshot:
                    ocr_result = await self.modules['ocr'].extract_text(screenshot.image, "auto")
                    if ocr_result.all_text:
                        logger.success(f"✅ OCR OK - {len(ocr_result.words)} mots détectés")
                        logger.info(f"📝 Texte échantillon: {ocr_result.all_text[:100]}...")
                        results['ocr'] = True
                    else:
                        logger.warning("⚠️  OCR OK mais aucun texte détecté")
                        results['ocr'] = True
        except Exception as e:
            logger.error(f"❌ Test OCR échoué: {e}")
            results['ocr'] = False
        
        # Test analyse visuelle
        try:
            logger.info("👁️  Test analyse visuelle...")
            if results.get('screenshot') and 'screen_capture' in self.modules:
                screenshot = await self.modules['screen_capture'].capture()
                if screenshot:
                    analysis = await self.modules['vision_analyzer'].analyze_screen(screenshot.image)
                    logger.success(f"✅ Analyse visuelle OK - {len(analysis.ui_elements)} éléments détectés")
                    logger.info(f"📋 Description: {analysis.description[:100]}...")
                    results['visual_analysis'] = True
        except Exception as e:
            logger.error(f"❌ Test analyse visuelle échoué: {e}")
            results['visual_analysis'] = False
        
        # Test détection d'applications
        try:
            logger.info("🔍 Test détection d'applications...")
            apps = await self.modules['app_detector'].get_running_applications()
            if apps:
                logger.success(f"✅ Détection apps OK - {len(apps)} applications trouvées")
                
                # Afficher les top 5
                for i, app in enumerate(apps[:5]):
                    status = "🟢" if app.is_active else "⚪"
                    logger.info(f"  {status} {app.name} ({app.memory_usage}MB)")
                
                results['app_detection'] = True
            else:
                raise Exception("Aucune application détectée")
        except Exception as e:
            logger.error(f"❌ Test détection apps échoué: {e}")
            results['app_detection'] = False
        
        # Test Ollama (si disponible)
        try:
            logger.info("🤖 Test Ollama...")
            if self.modules['ollama'].is_available:
                response = await self.modules['ollama'].chat("Bonjour JARVIS, réponds juste 'OK' pour le test")
                if response.success:
                    logger.success(f"✅ Ollama OK - Réponse: {response.content[:50]}...")
                    results['ollama'] = True
                else:
                    raise Exception(f"Erreur réponse: {response.error}")
            else:
                logger.warning("⚠️  Ollama non disponible")
                results['ollama'] = False
        except Exception as e:
            logger.error(f"❌ Test Ollama échoué: {e}")
            results['ollama'] = False
        
        # Test planification
        try:
            logger.info("📋 Test planification...")
            sequence = await self.modules['planner'].parse_natural_command("Take a screenshot")
            if sequence and sequence.actions:
                logger.success(f"✅ Planification OK - {len(sequence.actions)} actions planifiées")
                for i, action in enumerate(sequence.actions):
                    logger.info(f"  {i+1}. {action.type.value}: {action.description}")
                results['planning'] = True
            else:
                raise Exception("Aucune action planifiée")
        except Exception as e:
            logger.error(f"❌ Test planification échoué: {e}")
            results['planning'] = False
        
        # Résumé des tests
        logger.info("\n📊 RÉSUMÉ DES TESTS:")
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        logger.info(f"\n🎯 Score: {passed_tests}/{total_tests} tests réussis ({passed_tests/total_tests*100:.1f}%)")
        
        return results
    
    async def run_demo_sequence(self):
        """Exécute une séquence de démonstration"""
        logger.info("🎬 Lancement de la démonstration JARVIS...")
        
        try:
            # 1. Capture et analyse de l'écran actuel
            logger.info("📸 1. Capture et analyse de l'écran...")
            screenshot = await self.modules['screen_capture'].capture()
            if screenshot:
                analysis = await self.modules['vision_analyzer'].analyze_screen(screenshot.image)
                logger.info(f"📋 Analyse: {analysis.description[:200]}...")
                
                # OCR du texte visible
                ocr_result = await self.modules['ocr'].extract_text(screenshot.image)
                logger.info(f"📝 Texte détecté: {len(ocr_result.words)} mots")
            
            # 2. Détection des applications actives
            logger.info("🔍 2. Détection des applications...")
            active_app = await self.modules['app_detector'].get_active_application()
            if active_app:
                logger.info(f"📱 Application active: {active_app.name}")
                if active_app.main_window:
                    logger.info(f"🪟 Fenêtre: {active_app.main_window.title}")
            
            # 3. Planification d'une tâche simple
            logger.info("📋 3. Planification d'une tâche...")
            sequence = await self.modules['planner'].parse_natural_command(
                "Analyze the current screen and describe what I can do"
            )
            
            logger.info(f"📝 Séquence planifiée: {sequence.name}")
            for i, action in enumerate(sequence.actions[:3]):  # Montrer les 3 premières
                logger.info(f"  {i+1}. {action.type.value}: {action.description}")
            
            # 4. Test d'interaction IA (si disponible)
            if self.modules['ollama'].is_available:
                logger.info("🤖 4. Interaction avec l'IA...")
                
                # Analyser l'écran avec l'IA
                if screenshot:
                    import base64
                    import io
                    
                    # Convertir l'image en base64
                    buffer = io.BytesIO()
                    screenshot.image.save(buffer, format='PNG')
                    image_b64 = base64.b64encode(buffer.getvalue()).decode()
                    
                    ai_analysis = await self.modules['ollama'].analyze_screen(
                        image_b64, 
                        "Décris ce que tu vois et suggère des actions possibles"
                    )
                    
                    if ai_analysis.success:
                        logger.info(f"🧠 Analyse IA: {ai_analysis.content[:300]}...")
            
            logger.success("✅ Démonstration terminée avec succès!")
            
        except Exception as e:
            logger.error(f"❌ Erreur pendant la démonstration: {e}")
    
    async def interactive_mode(self):
        """Mode interactif avec l'utilisateur"""
        logger.info("🎮 Mode interactif JARVIS activé")
        logger.info("Tapez 'help' pour voir les commandes disponibles, 'quit' pour quitter")
        
        while True:
            try:
                # Prompt utilisateur
                command = input("\n🤖 JARVIS> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['quit', 'exit', 'q']:
                    logger.info("👋 Au revoir!")
                    break
                
                elif command.lower() == 'help':
                    self._show_help()
                
                elif command.lower() == 'status':
                    await self._show_status()
                
                elif command.lower() == 'screenshot':
                    await self._take_screenshot()
                
                elif command.lower() == 'analyze':
                    await self._analyze_current_screen()
                
                elif command.lower() == 'apps':
                    await self._show_running_apps()
                
                elif command.startswith('chat '):
                    await self._chat_with_ai(command[5:])
                
                elif command.startswith('plan '):
                    await self._plan_command(command[5:])
                
                else:
                    # Commande générale - essayer de la planifier et l'exécuter
                    await self._execute_natural_command(command)
                
            except KeyboardInterrupt:
                logger.info("\n👋 Arrêt demandé par l'utilisateur")
                break
            except Exception as e:
                logger.error(f"❌ Erreur: {e}")
    
    def _show_help(self):
        """Affiche l'aide"""
        help_text = """
🤖 COMMANDES JARVIS DISPONIBLES:

Commandes système:
  help                    - Affiche cette aide
  status                  - Statut des modules
  quit/exit/q            - Quitter JARVIS

Vision et analyse:
  screenshot             - Prendre une capture d'écran
  analyze                - Analyser l'écran actuel
  
Applications:
  apps                   - Lister les applications en cours

IA et planification:
  chat <message>         - Discuter avec JARVIS
  plan <commande>        - Planifier une commande
  
Commandes naturelles:
  Vous pouvez aussi donner des commandes en langage naturel:
  - "Take a screenshot"
  - "Open notepad"
  - "Search for Python on Google"
  - "Close the current window"
"""
        print(help_text)
    
    async def _show_status(self):
        """Affiche le statut des modules"""
        logger.info("📊 STATUT DES MODULES JARVIS:")
        
        for name, module in self.modules.items():
            status = "✅ OK" if module else "❌ ERREUR"
            
            # Informations spécifiques par module
            extra_info = ""
            
            if name == 'ollama' and module:
                extra_info = f" ({len(module.get_available_models())} modèles)"
            elif name == 'screen_capture' and module:
                info = module.get_screen_info()
                extra_info = f" ({len(info['monitors'])} moniteur(s))"
            elif name == 'app_detector' and module:
                stats = module.get_application_stats()
                extra_info = f" ({stats.get('total_applications', 0)} apps)"
            
            logger.info(f"  {name}: {status}{extra_info}")
    
    async def _take_screenshot(self):
        """Prend une capture d'écran"""
        try:
            logger.info("📸 Prise de capture d'écran...")
            screenshot = await self.modules['screen_capture'].capture()
            if screenshot:
                filename = f"jarvis_screenshot_{int(time.time())}.png"
                screenshot.save(filename)
                logger.success(f"✅ Capture sauvée: {filename}")
            else:
                logger.error("❌ Échec de la capture")
        except Exception as e:
            logger.error(f"❌ Erreur capture: {e}")
    
    async def _analyze_current_screen(self):
        """Analyse l'écran actuel"""
        try:
            logger.info("👁️  Analyse de l'écran...")
            screenshot = await self.modules['screen_capture'].capture()
            if screenshot:
                analysis = await self.modules['vision_analyzer'].analyze_screen(screenshot.image)
                
                logger.info(f"📋 Type de scène: {analysis.scene_type}")
                logger.info(f"📝 Description: {analysis.description}")
                logger.info(f"🔲 Éléments détectés: {len(analysis.ui_elements)}")
                
                if analysis.actions_suggested:
                    logger.info("💡 Actions suggérées:")
                    for action in analysis.actions_suggested[:3]:
                        logger.info(f"  - {action}")
            else:
                logger.error("❌ Impossible de capturer l'écran")
        except Exception as e:
            logger.error(f"❌ Erreur analyse: {e}")
    
    async def _show_running_apps(self):
        """Affiche les applications en cours"""
        try:
            logger.info("🔍 Applications en cours d'exécution:")
            apps = await self.modules['app_detector'].get_running_applications()
            
            for i, app in enumerate(apps[:10]):  # Top 10
                status = "🟢 ACTIVE" if app.is_active else "⚪"
                windows = f" ({len(app.windows)} fenêtres)" if app.windows else ""
                logger.info(f"  {status} {app.name} - {app.memory_usage}MB{windows}")
            
            if len(apps) > 10:
                logger.info(f"  ... et {len(apps) - 10} autres applications")
                
        except Exception as e:
            logger.error(f"❌ Erreur listage apps: {e}")
    
    async def _chat_with_ai(self, message: str):
        """Discute avec l'IA"""
        try:
            if not self.modules['ollama'].is_available:
                logger.warning("⚠️  Service Ollama non disponible")
                return
            
            logger.info(f"🤖 Discussion avec JARVIS: {message}")
            response = await self.modules['ollama'].chat(message)
            
            if response.success:
                logger.info(f"💬 JARVIS: {response.content}")
            else:
                logger.error(f"❌ Erreur IA: {response.error}")
        except Exception as e:
            logger.error(f"❌ Erreur chat: {e}")
    
    async def _plan_command(self, command: str):
        """Planifie une commande"""
        try:
            logger.info(f"📋 Planification: {command}")
            sequence = await self.modules['planner'].parse_natural_command(command)
            
            logger.info(f"📝 Séquence: {sequence.name}")
            logger.info(f"📃 Description: {sequence.description}")
            logger.info(f"🔢 Actions ({len(sequence.actions)}):")
            
            for i, action in enumerate(sequence.actions):
                logger.info(f"  {i+1}. {action.type.value}: {action.description}")
                if action.parameters:
                    logger.info(f"     Paramètres: {action.parameters}")
        except Exception as e:
            logger.error(f"❌ Erreur planification: {e}")
    
    async def _execute_natural_command(self, command: str):
        """Exécute une commande en langage naturel"""
        try:
            logger.info(f"🎯 Exécution de la commande: {command}")
            
            # Pour l'instant, juste planifier (l'exécution sera implémentée plus tard)
            sequence = await self.modules['planner'].parse_natural_command(command)
            
            logger.info(f"📋 Commande planifiée: {sequence.name}")
            logger.info(f"⚠️  Exécution automatique pas encore implémentée")
            logger.info("💡 Utilisez 'plan <commande>' pour voir le plan d'action")
            
        except Exception as e:
            logger.error(f"❌ Erreur exécution: {e}")

async def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="JARVIS - Agent IA Autonome")
    parser.add_argument('--demo', action='store_true', help='Mode démonstration')
    parser.add_argument('--test', action='store_true', help='Exécuter les tests')
    parser.add_argument('--command', type=str, help='Exécuter une commande directe')
    parser.add_argument('--config', type=str, help='Fichier de configuration')
    
    args = parser.parse_args()
    
    # Bannière de démarrage
    print("""
    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
    ██║███████║██████╔╝██║   ██║██║███████╗
    ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
    ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║
    ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
    
    🤖 Agent IA Autonome pour Windows
    Version 1.0.0 - Phase de développement
    """)
    
    # Initialisation
    demo = JarvisDemo()
    
    if not await demo.initialize_all_modules():
        logger.error("❌ Impossible d'initialiser JARVIS")
        return 1
    
    # Mode choisi
    if args.test:
        await demo.run_basic_tests()
    
    elif args.demo:
        await demo.run_demo_sequence()
    
    elif args.command:
        # Exécuter une commande directe
        try:
            sequence = await demo.modules['planner'].parse_natural_command(args.command)
            logger.info(f"📋 Commande planifiée: {sequence.name}")
            
            for i, action in enumerate(sequence.actions):
                logger.info(f"  {i+1}. {action.type.value}: {action.description}")
        except Exception as e:
            logger.error(f"❌ Erreur commande: {e}")
    
    else:
        # Mode interactif par défaut
        await demo.interactive_mode()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n👋 JARVIS arrêté par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)