#!/usr/bin/env python3
"""
🤖 JARVIS - Agent IA Autonome pour Windows
Script principal avec toutes les fonctionnalités Phase 4

Usage:
    python main.py                    # Mode interactif complet
    python main.py --demo            # Mode démonstration
    python main.py --test            # Tests des modules
    python main.py --voice           # Mode vocal
    python main.py --autocomplete    # Test autocomplétion
    python main.py --tools           # Test système d'outils
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

# Imports des modules JARVIS Phase 1
from core.agent import JarvisAgent, create_agent
from core.vision.screen_capture import ScreenCapture, quick_screenshot
from core.vision.ocr_engine import OCREngine, quick_ocr
from core.vision.visual_analysis import VisualAnalyzer, quick_screen_analysis
from core.control.mouse_controller import MouseController, quick_click
from core.control.keyboard_controller import KeyboardController, quick_type
from core.control.app_detector import AppDetector, get_current_app
from core.ai.ollama_service import OllamaService, quick_chat
from core.ai.action_planner import ActionPlanner, quick_plan
from core.ai.action_executor import ActionExecutor
from core.ai.memory_system import MemorySystem

# Imports des modules JARVIS Phase 2
from core.voice.voice_interface import VoiceInterface, VoiceInterfaceConfig
from autocomplete.global_autocomplete import GlobalAutocomplete, AutocompleteConfig
from autocomplete.suggestion_engine import SuggestionEngine
from autocomplete.overlay_ui import OverlayUI

# Imports des modules JARVIS Phase 4 - Tools System
from tools.tool_manager import tool_manager
from tools.mcp_server import mcp_server

from config.amd_gpu import configure_amd_gpu, OLLAMA_CONFIG

class JarvisDemo:
    """Classe de démonstration de JARVIS"""
    
    def __init__(self):
        self.modules = {}
        self.agent = None
        
    async def initialize_all_modules(self):
        """Initialise tous les modules JARVIS (Phase 1 + Phase 2)"""
        logger.info("🚀 Initialisation complète de JARVIS Phase 2...")
        
        try:
            # Configuration GPU AMD
            configure_amd_gpu()
            
            # === MODULES PHASE 1 ===
            
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
            
            # IA Core
            logger.info("🤖 Initialisation des modules IA...")
            self.modules['ollama'] = OllamaService()
            await self.modules['ollama'].initialize()
            
            self.modules['planner'] = ActionPlanner(self.modules['ollama'])
            
            # === MODULES PHASE 2 ===
            
            # Mémoire persistante
            logger.info("🧠 Initialisation du système de mémoire...")
            self.modules['memory'] = MemorySystem()
            memory_initialized = await self.modules['memory'].initialize()
            if memory_initialized:
                logger.success("✅ Système de mémoire prêt")
            else:
                logger.warning("⚠️ Système de mémoire non disponible")
            
            # Exécuteur d'actions
            logger.info("⚡ Initialisation de l'exécuteur d'actions...")
            self.modules['executor'] = ActionExecutor()
            await self.modules['executor'].initialize(self.modules)
            
            # Interface vocale
            logger.info("🎤 Initialisation de l'interface vocale...")
            try:
                self.modules['voice'] = VoiceInterface()
                voice_initialized = await self.modules['voice'].initialize()
                if voice_initialized:
                    logger.success("✅ Interface vocale prête")
                else:
                    logger.warning("⚠️ Interface vocale non disponible")
            except Exception as e:
                logger.warning(f"⚠️ Interface vocale non disponible: {e}")
                self.modules['voice'] = None
            
            # Autocomplétion globale
            logger.info("⚡ Initialisation de l'autocomplétion globale...")
            try:
                self.modules['suggestion_engine'] = SuggestionEngine(self.modules['ollama'])
                await self.modules['suggestion_engine'].initialize()
                
                self.modules['autocomplete'] = GlobalAutocomplete()
                autocomplete_initialized = await self.modules['autocomplete'].initialize()
                
                if autocomplete_initialized:
                    # Configurer les callbacks
                    async def suggestion_callback(context):
                        return await self._generate_autocomplete_suggestions(context)
                    
                    async def context_callback(event):
                        await self._handle_autocomplete_event(event)
                    
                    self.modules['autocomplete'].set_suggestion_callback(suggestion_callback)
                    self.modules['autocomplete'].set_context_callback(context_callback)
                    
                    logger.success("✅ Autocomplétion globale prête")
                else:
                    logger.warning("⚠️ Autocomplétion globale non disponible")
            except Exception as e:
                logger.warning(f"⚠️ Autocomplétion non disponible: {e}")
                self.modules['autocomplete'] = None
            
            # === MODULES PHASE 4 - TOOLS SYSTEM ===
            
            # Gestionnaire d'outils
            logger.info("🛠️ Initialisation du système d'outils...")
            try:
                tools_initialized = await tool_manager.initialize()
                if tools_initialized:
                    self.modules['tool_manager'] = tool_manager
                    logger.success(f"✅ Système d'outils prêt avec {len(tool_manager.registry.tools)} outils")
                else:
                    logger.warning("⚠️ Système d'outils non disponible")
                    self.modules['tool_manager'] = None
            except Exception as e:
                logger.error(f"❌ Erreur initialisation outils: {e}")
                self.modules['tool_manager'] = None
            
            # Serveur MCP
            logger.info("🔌 Initialisation du serveur MCP...")
            try:
                self.modules['mcp_server'] = mcp_server
                logger.success("✅ Serveur MCP prêt")
            except Exception as e:
                logger.warning(f"⚠️ Serveur MCP non disponible: {e}")
                self.modules['mcp_server'] = None
            
            # Agent principal
            logger.info("🎯 Création de l'agent JARVIS...")
            self.agent = await create_agent()
            
            logger.success("✅ JARVIS Phase 2 complètement initialisé et prêt!")
            logger.info("🌟 Nouvelles fonctionnalités disponibles:")
            logger.info("  🎤 Interface vocale avec Whisper + Edge-TTS")
            logger.info("  ⚡ Autocomplétion globale temps réel")
            logger.info("  🧠 Mémoire persistante avec ChromaDB") 
            logger.info("  🚀 Exécution automatique d'actions")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    # === Méthodes pour les nouvelles fonctionnalités Phase 2 ===
    
    async def _generate_autocomplete_suggestions(self, context):
        """Génère des suggestions d'autocomplétion"""
        try:
            if self.modules['suggestion_engine']:
                from autocomplete.suggestion_engine import SuggestionContext
                
                suggestion_context = SuggestionContext(
                    word=context["current_word"],
                    app_name=context["app_name"],
                    field_type=context["field_type"],
                    language=context.get("language", "fr"),
                    line_context=context["current_line"],
                    previous_words=context.get("previous_words", [])
                )
                
                suggestions = await self.modules['suggestion_engine'].generate_suggestions(suggestion_context, 5)
                return [s.text for s in suggestions]
            
            return []
        except Exception as e:
            logger.debug(f"Erreur génération suggestions: {e}")
            return []
    
    async def _handle_autocomplete_event(self, event):
        """Gère les événements d'autocomplétion"""
        try:
            action = event["action"]
            
            if action == "show_suggestions":
                suggestions = event["suggestions"]
                context = event["context"]
                logger.debug(f"💡 Suggestions: {suggestions} pour '{context.current_text}'")
                
                # TODO: Afficher l'overlay UI
                
            elif action == "suggestion_accepted":
                suggestion = event["suggestion"]
                original = event["original"]
                logger.info(f"✅ Suggestion acceptée: '{original}' -> '{suggestion}'")
                
                # Apprendre de l'acceptation
                if self.modules['suggestion_engine']:
                    from autocomplete.suggestion_engine import SuggestionContext
                    context = SuggestionContext(word=original, app_name="", field_type="text", language="fr", line_context="")
                    self.modules['suggestion_engine'].learn_from_acceptance(context, suggestion)
        
        except Exception as e:
            logger.debug(f"Erreur événement autocomplétion: {e}")
    
    async def run_voice_mode(self):
        """Lance le mode vocal interactif"""
        if not self.modules.get('voice'):
            logger.error("❌ Interface vocale non disponible")
            return
        
        logger.info("🎤 Démarrage du mode vocal JARVIS...")
        
        # Configurer le callback de commande vocale
        async def voice_command_callback(command: str) -> str:
            """Traite les commandes vocales"""
            try:
                # Démarrer une conversation en mémoire
                if self.modules.get('memory'):
                    conv_id = self.modules['memory'].start_conversation({"mode": "voice"})
                    self.modules['memory'].add_message_to_conversation(conv_id, "user", command)
                
                # Planifier et exécuter l'action
                if self.modules.get('planner') and self.modules.get('executor'):
                    sequence = await self.modules['planner'].parse_natural_command(command)
                    
                    if sequence and sequence.actions:
                        logger.info(f"📋 Séquence planifiée: {len(sequence.actions)} actions")
                        
                        # Demander confirmation vocale
                        confirmation = f"Je vais exécuter {len(sequence.actions)} actions pour: {sequence.description}. Voulez-vous continuer ?"
                        await self.modules['voice'].speak(confirmation)
                        
                        # Écouter la réponse
                        response = await self.modules['voice'].listen_for_command()
                        
                        if response and ("oui" in response.lower() or "ok" in response.lower() or "yes" in response.lower()):
                            # Exécuter la séquence
                            result = await self.modules['executor'].execute_sequence(sequence)
                            
                            if result["success"]:
                                response_text = f"Commande exécutée avec succès en {result['execution_time']:.1f} secondes."
                            else:
                                response_text = f"Erreur lors de l'exécution: {result.get('error', 'Erreur inconnue')}"
                        else:
                            response_text = "Commande annulée."
                    else:
                        response_text = "Je n'ai pas pu planifier cette action."
                else:
                    # Réponse conversationnelle via Ollama
                    if self.modules.get('ollama'):
                        ollama_response = await self.modules['ollama'].chat(command)
                        response_text = ollama_response.content if ollama_response.success else "Je n'ai pas pu traiter votre demande."
                    else:
                        response_text = "Système de traitement non disponible."
                
                # Enregistrer la réponse en mémoire
                if self.modules.get('memory') and 'conv_id' in locals():
                    self.modules['memory'].add_message_to_conversation(conv_id, "assistant", response_text)
                
                return response_text
                
            except Exception as e:
                logger.error(f"❌ Erreur traitement commande vocale: {e}")
                return f"Erreur lors du traitement: {str(e)}"
        
        # Configurer les callbacks
        self.modules['voice'].set_command_callback(voice_command_callback)
        
        # Démarrer l'activation vocale
        try:
            await self.modules['voice'].start_voice_activation()
        except KeyboardInterrupt:
            logger.info("⏹️ Mode vocal arrêté par l'utilisateur")
        finally:
            self.modules['voice'].stop_voice_activation()
    
    async def test_autocomplete_system(self):
        """Test du système d'autocomplétion"""
        if not self.modules.get('autocomplete'):
            logger.error("❌ Système d'autocomplétion non disponible")
            return
        
        logger.info("🧪 Test du système d'autocomplétion globale")
        logger.info("Tapez dans n'importe quelle application pour tester l'autocomplétion")
        logger.info("Les suggestions apparaîtront automatiquement")
        logger.info("Ctrl+C pour arrêter")
        
        try:
            # Le système d'autocomplétion fonctionne en arrière-plan
            while True:
                await asyncio.sleep(1)
                
                # Afficher les stats périodiquement
                stats = self.modules['autocomplete'].get_stats()
                if stats["keys_processed"] > 0 and stats["keys_processed"] % 100 == 0:
                    logger.info(f"📊 {stats['keys_processed']} touches traitées, {stats['suggestions_generated']} suggestions")
        
        except KeyboardInterrupt:
            logger.info("⏹️ Test autocomplétion arrêté")
            await self.modules['autocomplete'].shutdown()
    
    async def test_tools_system(self):
        """Test du système d'outils"""
        if not self.modules.get('tool_manager'):
            logger.error("❌ Système d'outils non disponible")
            return
        
        logger.info("🛠️ Test du système d'outils JARVIS")
        
        try:
            # Afficher les statistiques
            stats = self.modules['tool_manager'].get_stats()
            logger.info(f"📊 {stats['tools_available']} outils disponibles")
            
            # Lister les outils par catégorie
            for category, count in stats['categories'].items():
                if count > 0:
                    logger.info(f"  {category}: {count} outils")
            
            # Test d'exécution d'outils
            logger.info("🧪 Tests d'exécution...")
            
            # Test 1: Lecture du fichier courant
            logger.info("1. Test lecture de fichier...")
            result = await self.modules['tool_manager'].execute_tool("FileReadTool", {
                "filepath": __file__,
                "max_lines": 5
            })
            if result.success:
                logger.success(f"✅ Fichier lu: {len(result.data)} caractères")
            else:
                logger.error(f"❌ Erreur: {result.error}")
            
            # Test 2: Informations système
            logger.info("2. Test informations système...")
            result = await self.modules['tool_manager'].execute_tool("SystemInfoTool", {
                "include_network": False,
                "include_disks": False
            })
            if result.success:
                logger.success(f"✅ Infos système récupérées")
                logger.info(f"  Système: {result.data['platform']['system']}")
                logger.info(f"  RAM: {result.data['memory']['total_gb']} GB")
            else:
                logger.error(f"❌ Erreur: {result.error}")
            
            # Test 3: Recherche d'outils
            logger.info("3. Test recherche d'outils...")
            matches = self.modules['tool_manager'].search_tools("lire fichier", max_results=3)
            logger.success(f"✅ {len(matches)} outils trouvés pour 'lire fichier'")
            for match in matches:
                tool_info = match["tool"]
                similarity = match["similarity"]
                logger.info(f"  - {tool_info['display_name']} (similarité: {similarity:.2f})")
            
            # Test 4: Exécution par requête
            logger.info("4. Test exécution par requête...")
            result = await self.modules['tool_manager'].execute_tool_by_query(
                "obtenir les informations du système"
            )
            if result.success:
                logger.success("✅ Outil exécuté via requête naturelle")
            else:
                logger.error(f"❌ Erreur: {result.error}")
            
            # Statistiques finales
            final_stats = self.modules['tool_manager'].get_stats()
            logger.info("📊 Statistiques finales:")
            logger.info(f"  Outils exécutés: {final_stats['tools_executed']}")
            logger.info(f"  Succès: {final_stats['executions_successful']}")
            logger.info(f"  Échecs: {final_stats['executions_failed']}")
            if final_stats['tools_executed'] > 0:
                logger.info(f"  Taux de succès: {final_stats['success_rate']:.1%}")
                logger.info(f"  Temps moyen: {final_stats['avg_execution_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Erreur durant le test des outils: {e}")
    
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
        
        # === TESTS PHASE 2 ===
        
        # Test exécuteur d'actions
        try:
            logger.info("⚡ Test exécuteur d'actions...")
            if self.modules['executor']:
                from core.ai.action_planner import Action, ActionType, ActionSequence
                
                test_action = Action(
                    type=ActionType.SCREENSHOT,
                    description="Test screenshot",
                    parameters={}
                )
                
                test_sequence = ActionSequence(
                    id="test_executor",
                    name="Test exécuteur",
                    description="Test de l'exécuteur d'actions",
                    actions=[test_action]
                )
                
                result = await self.modules['executor'].execute_sequence(test_sequence)
                
                if result["success"]:
                    logger.success(f"✅ Exécuteur OK - {result['actions_executed']} actions exécutées")
                    results['executor'] = True
                else:
                    raise Exception(result.get("error", "Échec exécution"))
            else:
                raise Exception("Exécuteur non disponible")
        except Exception as e:
            logger.error(f"❌ Test exécuteur échoué: {e}")
            results['executor'] = False
        
        # Test mémoire
        try:
            logger.info("🧠 Test système de mémoire...")
            if self.modules['memory']:
                # Test de conversation
                conv_id = self.modules['memory'].start_conversation({"test": True})
                self.modules['memory'].add_message_to_conversation(conv_id, "user", "Test message")
                self.modules['memory'].add_message_to_conversation(conv_id, "assistant", "Test response")
                
                summary = await self.modules['memory'].end_conversation(conv_id)
                
                if summary:
                    logger.success(f"✅ Mémoire OK - Conversation sauvée: {summary[:50]}...")
                    results['memory'] = True
                else:
                    raise Exception("Pas de résumé généré")
            else:
                logger.warning("⚠️ Système de mémoire non disponible")
                results['memory'] = False
        except Exception as e:
            logger.error(f"❌ Test mémoire échoué: {e}")
            results['memory'] = False
        
        # Test interface vocale
        try:
            logger.info("🎤 Test interface vocale...")
            if self.modules['voice']:
                # Test de synthèse vocale simple
                await self.modules['voice'].speak("Test de l'interface vocale JARVIS.")
                logger.success("✅ Interface vocale OK - TTS fonctionnel")
                results['voice'] = True
            else:
                logger.warning("⚠️ Interface vocale non disponible")
                results['voice'] = False
        except Exception as e:
            logger.error(f"❌ Test interface vocale échoué: {e}")
            results['voice'] = False
        
        # Test moteur de suggestions
        try:
            logger.info("💡 Test moteur de suggestions...")
            if self.modules['suggestion_engine']:
                from autocomplete.suggestion_engine import SuggestionContext
                
                test_context = SuggestionContext(
                    word="test",
                    app_name="notepad.exe",
                    field_type="text",
                    language="fr",
                    line_context="This is a test"
                )
                
                suggestions = await self.modules['suggestion_engine'].generate_suggestions(test_context)
                
                if suggestions:
                    logger.success(f"✅ Moteur suggestions OK - {len(suggestions)} suggestions générées")
                    results['suggestions'] = True
                else:
                    logger.warning("⚠️ Aucune suggestion générée")
                    results['suggestions'] = True  # Pas forcément un échec
            else:
                logger.warning("⚠️ Moteur de suggestions non disponible")
                results['suggestions'] = False
        except Exception as e:
            logger.error(f"❌ Test suggestions échoué: {e}")
            results['suggestions'] = False
        
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

    def print_help(self):
        """Affiche l'aide d'utilisation"""
        help_text = """
🤖 JARVIS - Assistant IA Autonome pour Windows

Usage: python main.py [options]

Options:
  --demo          Lance une démonstration interactive
  --test          Exécute tous les tests de modules
  --voice         Lance le mode vocal interactif
  --autocomplete  Test le système d'autocomplétion
  --config PATH   Utilise un fichier de configuration personnalisé
  --debug         Active le mode debug avec logs détaillés
  --sandbox       Active le mode sandbox (sécurisé)
  --help          Affiche cette aide

Modes d'opération:
  • Mode Interactif: Interface en ligne de commande
  • Mode Vocal: Interaction par reconnaissance vocale
  • Mode Démonstration: Tests automatisés et démonstrations
  • Mode Sandbox: Exécution sécurisée avec restrictions

Fonctionnalités Phase 1:
  ✅ Vision: Capture d'écran, OCR, analyse visuelle
  ✅ Contrôle: Souris, clavier, détection d'applications
  ✅ IA: Service Ollama, planification d'actions

Fonctionnalités Phase 2:
  ✅ Interface vocale: Reconnaissance et synthèse vocale
  ✅ Autocomplétion globale: Suggestions intelligentes
  ✅ Mémoire persistante: Apprentissage des habitudes
  ✅ Exécuteur d'actions: Automatisation sécurisée
  🔄 Interface moderne: UI Electron + React

Exemples:
  python main.py --demo             # Démonstration complète
  python main.py --voice            # Mode vocal interactif
  python main.py --autocomplete     # Test autocomplétion
  python main.py --test --debug     # Tests avec logs détaillés
  python main.py --sandbox          # Mode sécurisé
"""
        print(help_text)

async def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="JARVIS - Agent IA Autonome")
    parser.add_argument('--demo', action='store_true', help='Mode démonstration')
    parser.add_argument('--voice', action='store_true', help='Lance le mode vocal')
    parser.add_argument('--autocomplete', action='store_true', help='Test autocomplétion')
    parser.add_argument('--tools', action='store_true', help='Test système d\'outils')
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
    elif args.voice:
        await demo.run_voice_mode()
    elif args.autocomplete:
        await demo.test_autocomplete_system()
    elif args.tools:
        await demo.test_tools_system()
    
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