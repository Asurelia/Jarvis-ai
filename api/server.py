#!/usr/bin/env python3
"""
🌐 JARVIS API Server - Interface REST pour connecter l'UI React au backend
Serveur FastAPI avec WebSocket pour communication temps réel
"""

import asyncio
import json
import logging
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger

# Import des modules JARVIS
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import JarvisAgent, create_agent
from core.vision.screen_capture import ScreenCapture
from core.vision.ocr_engine import OCREngine
from core.vision.visual_analysis import VisualAnalyzer
from core.control.mouse_controller import MouseController
from core.control.keyboard_controller import KeyboardController
from core.control.app_detector import AppDetector
from core.ai.ollama_service import OllamaService
from core.ai.action_planner import ActionPlanner, ActionSequence, Action
from core.ai.action_executor import ActionExecutor
from core.ai.memory_system import MemorySystem
from core.voice.voice_interface import VoiceInterface
from autocomplete.global_autocomplete import GlobalAutocomplete
from autocomplete.suggestion_engine import SuggestionEngine

# Modèles Pydantic pour l'API
class CommandRequest(BaseModel):
    command: str = Field(..., description="Commande en langage naturel")
    mode: str = Field(default="auto", description="Mode d'exécution: auto, plan, execute")

class ActionExecutionRequest(BaseModel):
    sequence_id: str = Field(..., description="ID de la séquence à exécuter")
    confirm: bool = Field(default=False, description="Confirmation d'exécution")

class ChatRequest(BaseModel):
    message: str = Field(..., description="Message pour l'IA")
    conversation_id: Optional[str] = Field(None, description="ID de conversation")

class VoiceCommandRequest(BaseModel):
    text: str = Field(..., description="Texte à synthétiser")
    voice: Optional[str] = Field(None, description="Voix à utiliser")

class ModuleStatus(BaseModel):
    name: str
    status: str
    details: Optional[Dict[str, Any]] = None
    last_update: datetime

class SystemStats(BaseModel):
    modules: List[ModuleStatus]
    performance: Dict[str, Any]
    memory_usage: Dict[str, Any]
    uptime: float

# Gestionnaire de WebSocket pour les connexions temps réel
class WebSocketManager:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.stats = {
            "connections": 0,
            "messages_sent": 0,
            "messages_received": 0
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        self.stats["connections"] += 1
        logger.info(f"📡 Nouvelle connexion WebSocket ({len(self.connections)} actives)")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
        logger.info(f"📡 Connexion WebSocket fermée ({len(self.connections)} actives)")

    async def broadcast(self, message: dict):
        """Diffuse un message à toutes les connexions actives"""
        if not self.connections:
            return

        dead_connections = []
        for connection in self.connections:
            try:
                await connection.send_json(message)
                self.stats["messages_sent"] += 1
            except Exception as e:
                logger.debug(f"Connexion WebSocket fermée: {e}")
                dead_connections.append(connection)

        # Nettoyer les connexions fermées
        for dead_connection in dead_connections:
            self.disconnect(dead_connection)

    async def send_to_client(self, websocket: WebSocket, message: dict):
        """Envoie un message à un client spécifique"""
        try:
            await websocket.send_json(message)
            self.stats["messages_sent"] += 1
        except Exception as e:
            logger.debug(f"Erreur envoi WebSocket: {e}")
            self.disconnect(websocket)

# Application FastAPI
app = FastAPI(
    title="JARVIS API",
    description="API REST pour l'interface utilisateur JARVIS",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configuration CORS pour permettre les requêtes depuis l'interface React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestionnaire WebSocket global
websocket_manager = WebSocketManager()

# Variables globales pour les modules JARVIS
jarvis_modules: Dict[str, Any] = {}
jarvis_agent: Optional[JarvisAgent] = None
server_start_time = time.time()

# === ENDPOINTS API REST ===

@app.get("/api/health")
async def health_check():
    """Vérification de santé du serveur"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - server_start_time,
        "version": "1.0.0"
    }

@app.get("/api/status", response_model=SystemStats)
async def get_system_status():
    """Obtient le statut de tous les modules JARVIS"""
    try:
        modules_status = []
        
        for name, module in jarvis_modules.items():
            status = "active" if module else "error"
            details = {}
            
            # Informations spécifiques par module
            if name == "ollama" and module:
                details = {
                    "models": len(module.get_available_models()) if hasattr(module, 'get_available_models') else 0,
                    "is_available": getattr(module, 'is_available', False)
                }
            elif name == "screen_capture" and module:
                details = {
                    "monitors": len(module.get_screen_info()['monitors']) if hasattr(module, 'get_screen_info') else 0
                }
            elif name == "memory" and module:
                details = {
                    "collections": 5,  # Nombre de collections ChromaDB
                    "conversations": getattr(module, 'conversation_count', 0)
                }
            
            modules_status.append(ModuleStatus(
                name=name,
                status=status,
                details=details,
                last_update=datetime.now()
            ))
        
        # Statistiques de performance
        performance = {
            "websocket_connections": len(websocket_manager.connections),
            "messages_sent": websocket_manager.stats["messages_sent"],
            "modules_loaded": len([m for m in jarvis_modules.values() if m])
        }
        
        memory_usage = {
            "python_process": "N/A",  # À implémenter si nécessaire
            "total_modules": len(jarvis_modules)
        }
        
        return SystemStats(
            modules=modules_status,
            performance=performance,
            memory_usage=memory_usage,
            uptime=time.time() - server_start_time
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération statut: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/command")
async def execute_command(request: CommandRequest, background_tasks: BackgroundTasks):
    """Exécute une commande en langage naturel"""
    try:
        if not jarvis_modules.get("planner"):
            raise HTTPException(status_code=503, detail="Module de planification non disponible")
        
        logger.info(f"🎯 Commande reçue: {request.command}")
        
        # Planifier la commande
        sequence = await jarvis_modules["planner"].parse_natural_command(request.command)
        
        if not sequence or not sequence.actions:
            raise HTTPException(status_code=400, detail="Impossible de planifier cette commande")
        
        # Diffuser la planification via WebSocket
        await websocket_manager.broadcast({
            "type": "command_planned",
            "data": {
                "sequence_id": sequence.id,
                "name": sequence.name,
                "description": sequence.description,
                "actions_count": len(sequence.actions),
                "timestamp": datetime.now().isoformat()
            }
        })
        
        response = {
            "success": True,
            "sequence_id": sequence.id,
            "sequence_name": sequence.name,
            "description": sequence.description,
            "actions_count": len(sequence.actions),
            "actions": [
                {
                    "type": action.type.value,
                    "description": action.description,
                    "parameters": action.parameters
                }
                for action in sequence.actions
            ]
        }
        
        # Si mode auto ou execute, exécuter directement
        if request.mode in ["auto", "execute"] and jarvis_modules.get("executor"):
            background_tasks.add_task(execute_sequence_async, sequence.id, sequence)
            response["execution_started"] = True
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur exécution commande: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_sequence_async(sequence_id: str, sequence: ActionSequence):
    """Exécute une séquence d'actions en arrière-plan"""
    try:
        if not jarvis_modules.get("executor"):
            await websocket_manager.broadcast({
                "type": "execution_error",
                "data": {
                    "sequence_id": sequence_id,
                    "error": "Exécuteur non disponible",
                    "timestamp": datetime.now().isoformat()
                }
            })
            return
        
        # Notifier le début d'exécution
        await websocket_manager.broadcast({
            "type": "execution_started",
            "data": {
                "sequence_id": sequence_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Exécuter la séquence
        result = await jarvis_modules["executor"].execute_sequence(sequence)
        
        # Notifier le résultat
        await websocket_manager.broadcast({
            "type": "execution_completed",
            "data": {
                "sequence_id": sequence_id,
                "success": result["success"],
                "actions_executed": result.get("actions_executed", 0),
                "execution_time": result.get("execution_time", 0),
                "error": result.get("error"),
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur exécution séquence {sequence_id}: {e}")
        await websocket_manager.broadcast({
            "type": "execution_error",
            "data": {
                "sequence_id": sequence_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        })

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """Discussion avec l'IA JARVIS"""
    try:
        if not jarvis_modules.get("ollama"):
            raise HTTPException(status_code=503, detail="Service IA non disponible")
        
        logger.info(f"💬 Chat: {request.message}")
        
        # Démarrer ou continuer une conversation
        conversation_id = request.conversation_id
        if jarvis_modules.get("memory") and not conversation_id:
            conversation_id = jarvis_modules["memory"].start_conversation({"mode": "chat"})
        
        # Enregistrer le message utilisateur
        if jarvis_modules.get("memory") and conversation_id:
            jarvis_modules["memory"].add_message_to_conversation(conversation_id, "user", request.message)
        
        # Obtenir la réponse de l'IA
        response = await jarvis_modules["ollama"].chat(request.message)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"Erreur IA: {response.error}")
        
        # Enregistrer la réponse
        if jarvis_modules.get("memory") and conversation_id:
            jarvis_modules["memory"].add_message_to_conversation(conversation_id, "assistant", response.content)
        
        # Diffuser la réponse via WebSocket
        await websocket_manager.broadcast({
            "type": "chat_response",
            "data": {
                "message": response.content,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return {
            "success": True,
            "response": response.content,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/speak")
async def speak_text(request: VoiceCommandRequest):
    """Synthèse vocale du texte"""
    try:
        if not jarvis_modules.get("voice"):
            raise HTTPException(status_code=503, detail="Interface vocale non disponible")
        
        logger.info(f"🎤 Synthèse: {request.text[:50]}...")
        
        # Synthétiser le texte
        await jarvis_modules["voice"].speak(request.text)
        
        return {
            "success": True,
            "text": request.text,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur synthèse vocale: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/screenshot")
async def take_screenshot():
    """Prend une capture d'écran"""
    try:
        if not jarvis_modules.get("screen_capture"):
            raise HTTPException(status_code=503, detail="Module capture non disponible")
        
        logger.info("📸 Capture d'écran demandée")
        
        screenshot = await jarvis_modules["screen_capture"].capture()
        if not screenshot:
            raise HTTPException(status_code=500, detail="Échec de la capture")
        
        # Sauvegarder temporairement
        timestamp = int(time.time())
        filename = f"screenshot_{timestamp}.png"
        screenshot.save(filename)
        
        # Diffuser la notification
        await websocket_manager.broadcast({
            "type": "screenshot_taken",
            "data": {
                "filename": filename,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return {
            "success": True,
            "filename": filename,
            "size": {
                "width": screenshot.image.width,
                "height": screenshot.image.height
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur capture: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/apps")
async def get_running_applications():
    """Obtient la liste des applications en cours"""
    try:
        if not jarvis_modules.get("app_detector"):
            raise HTTPException(status_code=503, detail="Détecteur d'apps non disponible")
        
        apps = await jarvis_modules["app_detector"].get_running_applications()
        
        apps_data = []
        for app in apps[:20]:  # Top 20
            apps_data.append({
                "name": app.name,
                "is_active": app.is_active,
                "memory_usage": app.memory_usage,
                "windows_count": len(app.windows) if app.windows else 0,
                "main_window_title": app.main_window.title if app.main_window else None
            })
        
        return {
            "success": True,
            "apps": apps_data,
            "total_count": len(apps),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur listage apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/conversations")
async def get_conversations():
    """Obtient l'historique des conversations"""
    try:
        if not jarvis_modules.get("memory"):
            raise HTTPException(status_code=503, detail="Système mémoire non disponible")
        
        # Pour l'instant, retourner un exemple
        # TODO: Implémenter la récupération réelle depuis ChromaDB
        conversations = [
            {
                "id": "conv_1",
                "summary": "Discussion sur la capture d'écran",
                "message_count": 5,
                "created_at": "2024-01-20T10:30:00Z",
                "last_activity": "2024-01-20T10:35:00Z"
            }
        ]
        
        return {
            "success": True,
            "conversations": conversations,
            "total_count": len(conversations),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === WEBSOCKET ENDPOINT ===

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour communication temps réel"""
    await websocket_manager.connect(websocket)
    
    try:
        # Envoyer un message de bienvenue
        await websocket_manager.send_to_client(websocket, {
            "type": "welcome",
            "data": {
                "message": "Connexion JARVIS établie",
                "timestamp": datetime.now().isoformat(),
                "server_version": "1.0.0"
            }
        })
        
        # Écouter les messages du client
        while True:
            try:
                data = await websocket.receive_json()
                websocket_manager.stats["messages_received"] += 1
                
                # Traiter les différents types de messages
                message_type = data.get("type")
                
                if message_type == "ping":
                    await websocket_manager.send_to_client(websocket, {
                        "type": "pong",
                        "data": {"timestamp": datetime.now().isoformat()}
                    })
                
                elif message_type == "subscribe_status":
                    # Envoyer le statut actuel
                    status = await get_system_status()
                    await websocket_manager.send_to_client(websocket, {
                        "type": "status_update",
                        "data": status.dict()
                    })
                
                elif message_type == "command":
                    # Traiter une commande via WebSocket
                    command = data.get("data", {}).get("command")
                    if command:
                        # Ici on pourrait traiter la commande...
                        await websocket_manager.send_to_client(websocket, {
                            "type": "command_received",
                            "data": {"command": command, "status": "processing"}
                        })
                
            except Exception as e:
                logger.debug(f"Erreur traitement message WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("Cliente WebSocket déconnecté")
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
    finally:
        websocket_manager.disconnect(websocket)

# === INITIALISATION DES MODULES JARVIS ===

async def initialize_jarvis_modules():
    """Initialise tous les modules JARVIS pour l'API"""
    logger.info("🚀 Initialisation des modules JARVIS pour l'API...")
    
    try:
        # Vision
        logger.info("📸 Initialisation modules vision...")
        jarvis_modules['screen_capture'] = ScreenCapture()
        await jarvis_modules['screen_capture'].initialize()
        
        jarvis_modules['ocr'] = OCREngine()
        await jarvis_modules['ocr'].initialize()
        
        jarvis_modules['vision_analyzer'] = VisualAnalyzer()
        await jarvis_modules['vision_analyzer'].initialize()
        
        # Contrôle
        logger.info("🎮 Initialisation modules contrôle...")
        jarvis_modules['mouse'] = MouseController(sandbox_mode=True)
        await jarvis_modules['mouse'].initialize()
        
        jarvis_modules['keyboard'] = KeyboardController(sandbox_mode=True)
        await jarvis_modules['keyboard'].initialize()
        
        jarvis_modules['app_detector'] = AppDetector()
        await jarvis_modules['app_detector'].initialize()
        
        # IA
        logger.info("🤖 Initialisation modules IA...")
        jarvis_modules['ollama'] = OllamaService()
        await jarvis_modules['ollama'].initialize()
        
        jarvis_modules['planner'] = ActionPlanner(jarvis_modules['ollama'])
        
        # Mémoire
        logger.info("🧠 Initialisation système mémoire...")
        jarvis_modules['memory'] = MemorySystem()
        memory_initialized = await jarvis_modules['memory'].initialize()
        if memory_initialized and jarvis_modules.get('ollama'):
            jarvis_modules['memory'].set_ollama_service(jarvis_modules['ollama'])
        
        # Exécuteur
        logger.info("⚡ Initialisation exécuteur...")
        jarvis_modules['executor'] = ActionExecutor()
        await jarvis_modules['executor'].initialize(jarvis_modules)
        
        # Interface vocale
        logger.info("🎤 Initialisation interface vocale...")
        try:
            jarvis_modules['voice'] = VoiceInterface()
            await jarvis_modules['voice'].initialize()
        except Exception as e:
            logger.warning(f"Interface vocale non disponible: {e}")
            jarvis_modules['voice'] = None
        
        # Autocomplétion
        logger.info("⚡ Initialisation autocomplétion...")
        try:
            jarvis_modules['suggestion_engine'] = SuggestionEngine(jarvis_modules['ollama'])
            await jarvis_modules['suggestion_engine'].initialize()
            
            jarvis_modules['autocomplete'] = GlobalAutocomplete()
            await jarvis_modules['autocomplete'].initialize()
        except Exception as e:
            logger.warning(f"Autocomplétion non disponible: {e}")
            jarvis_modules['autocomplete'] = None
        
        logger.success("✅ Modules JARVIS initialisés pour l'API!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation modules: {e}")
        return False

# === ÉVÉNEMENTS DE DÉMARRAGE/ARRÊT ===

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage du serveur"""
    logger.info("🌐 Démarrage du serveur API JARVIS...")
    
    # Créer le répertoire API s'il n'existe pas
    Path(__file__).parent.mkdir(exist_ok=True)
    
    # Initialiser les modules JARVIS
    success = await initialize_jarvis_modules()
    if not success:
        logger.error("❌ Impossible d'initialiser JARVIS")
    else:
        logger.success("✅ Serveur API JARVIS prêt!")

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage à l'arrêt du serveur"""
    logger.info("🔄 Arrêt du serveur API JARVIS...")
    
    # Fermer les connexions WebSocket
    for connection in websocket_manager.connections:
        try:
            await connection.close()
        except:
            pass
    
    # Nettoyer les modules si nécessaire
    for name, module in jarvis_modules.items():
        if hasattr(module, 'shutdown'):
            try:
                await module.shutdown()
            except:
                pass
    
    logger.info("👋 Serveur API JARVIS arrêté")

# === POINT D'ENTRÉE ===

def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Lance le serveur API"""
    logger.info(f"🚀 Lancement serveur API JARVIS sur http://{host}:{port}")
    
    uvicorn.run(
        "api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Serveur API JARVIS")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute")
    parser.add_argument("--port", type=int, default=8000, help="Port d'écoute")
    parser.add_argument("--reload", action="store_true", help="Mode développement avec rechargement automatique")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, reload=args.reload)