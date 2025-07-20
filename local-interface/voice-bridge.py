"""
🎤 Voice Bridge Service - JARVIS 2025
Service local pour gestion audio avec accès microphone/speakers
Bridge entre interface web locale et services Docker
"""

from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import websockets
import json
import time
import threading
import queue
import numpy as np
import sounddevice as sd
import soundfile as sf
import wave
import io
import httpx
from datetime import datetime
import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import speech_recognition as sr
import pyttsx3
from pydantic import BaseModel

# Configuration
SERVICE_PORT = 3001
API_VERSION = "2.0.0"
CHUNK_SIZE = 1024
SAMPLE_RATE = 16000
CHANNELS = 1

# Services Docker (via réseau)
DOCKER_SERVICES = {
    "ai_pod": "http://localhost:8080",
    "audio_pod": "http://localhost:5002",  # TTS processing
    "control_pod": "http://localhost:5004",
    "integration_pod": "http://localhost:5006"
}

# Configuration audio
AUDIO_CONFIG = {
    "input_device": None,  # Auto-detect
    "output_device": None,  # Auto-detect
    "sample_rate": SAMPLE_RATE,
    "channels": CHANNELS,
    "chunk_size": CHUNK_SIZE
}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="JARVIS Voice Bridge",
    version=API_VERSION,
    description="Bridge vocal local avec accès matériel audio"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@dataclass
class AudioDeviceInfo:
    index: int
    name: str
    channels: int
    sample_rate: float
    is_input: bool
    is_output: bool

class VoiceRecognitionEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.continuous_listening = False
        
        # Calibrage du micro
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        logger.info("Voice recognition engine initialized")
    
    def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """Écoute ponctuelle avec timeout"""
        try:
            with self.microphone as source:
                logger.info("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            # Reconnaissance locale d'abord (rapide)
            try:
                text = self.recognizer.recognize_google(audio, language="fr-FR")
                logger.info(f"Recognized (Google): {text}")
                return text
            except sr.UnknownValueError:
                logger.warning("Speech not understood")
                return None
                
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout")
            return None
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return None
    
    async def listen_continuous(self, websocket: WebSocket):
        """Écoute continue avec streaming WebSocket"""
        self.continuous_listening = True
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio callback status: {status}")
            
            # Envoyer audio en continu
            audio_data = (indata[:, 0] * 32767).astype(np.int16)
            asyncio.create_task(self._send_audio_chunk(websocket, audio_data))
        
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                callback=audio_callback,
                blocksize=CHUNK_SIZE
            ):
                logger.info("Continuous listening started")
                while self.continuous_listening:
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Continuous listening error: {e}")
        finally:
            self.continuous_listening = False
            logger.info("Continuous listening stopped")
    
    async def _send_audio_chunk(self, websocket: WebSocket, audio_data: np.ndarray):
        """Envoie un chunk audio via WebSocket"""
        try:
            await websocket.send_json({
                "type": "audio_chunk",
                "data": audio_data.tolist(),
                "timestamp": time.time()
            })
        except Exception as e:
            logger.debug(f"WebSocket send error: {e}")
    
    def stop_listening(self):
        """Arrête l'écoute continue"""
        self.continuous_listening = False

class TextToSpeechEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.setup_voice()
        logger.info("TTS engine initialized")
    
    def setup_voice(self):
        """Configure la voix TTS"""
        voices = self.engine.getProperty('voices')
        
        # Chercher une voix française
        french_voice = None
        for voice in voices:
            if 'french' in voice.name.lower() or 'fr' in voice.id.lower():
                french_voice = voice
                break
        
        if french_voice:
            self.engine.setProperty('voice', french_voice.id)
            logger.info(f"French voice selected: {french_voice.name}")
        
        # Configuration voix
        self.engine.setProperty('rate', 180)  # Vitesse
        self.engine.setProperty('volume', 0.8)  # Volume
    
    def speak(self, text: str) -> bool:
        """Synthèse vocale locale"""
        try:
            logger.info(f"Speaking: {text[:50]}...")
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False
    
    async def speak_async(self, text: str) -> bool:
        """Synthèse vocale asynchrone"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.speak, text)

class DockerServiceClient:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def send_to_ai(self, message: str, context: Dict = None) -> Dict:
        """Envoie message au pod IA"""
        try:
            response = await self.http_client.post(
                f"{DOCKER_SERVICES['ai_pod']}/chat",
                json={
                    "message": message,
                    "context": context or {}
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"AI pod communication error: {e}")
            return {"error": str(e)}
    
    async def process_audio_remote(self, audio_data: bytes) -> Dict:
        """Traitement audio via pod audio"""
        try:
            files = {"audio": ("audio.wav", audio_data, "audio/wav")}
            response = await self.http_client.post(
                f"{DOCKER_SERVICES['audio_pod']}/transcribe",
                files=files
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Audio pod communication error: {e}")
            return {"error": str(e)}
    
    async def execute_system_action(self, action: str, params: Dict) -> Dict:
        """Exécute action via pod control"""
        try:
            response = await self.http_client.post(
                f"{DOCKER_SERVICES['control_pod']}/{action}",
                json=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Control pod communication error: {e}")
            return {"error": str(e)}
    
    async def close(self):
        await self.http_client.aclose()

# Instances globales
voice_recognition = VoiceRecognitionEngine()
tts_engine = TextToSpeechEngine()
docker_client = DockerServiceClient()

# Modèles Pydantic
class VoiceCommand(BaseModel):
    text: str
    confidence: Optional[float] = None
    language: str = "fr-FR"
    context: Optional[Dict] = None

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    speed: Optional[float] = None

class AudioDeviceRequest(BaseModel):
    input_device: Optional[int] = None
    output_device: Optional[int] = None

# Routes API
@app.get("/health")
async def health_check():
    """Vérification santé du bridge vocal"""
    return {
        "status": "healthy",
        "service": "Voice Bridge",
        "version": API_VERSION,
        "audio_devices": {
            "input_count": len(get_input_devices()),
            "output_count": len(get_output_devices())
        },
        "docker_services": DOCKER_SERVICES,
        "timestamp": time.time()
    }

@app.get("/audio/devices")
async def list_audio_devices():
    """Liste les périphériques audio disponibles"""
    devices = sd.query_devices()
    device_list = []
    
    for i, device in enumerate(devices):
        device_info = AudioDeviceInfo(
            index=i,
            name=device['name'],
            channels=device['max_input_channels'] if device['max_input_channels'] > 0 else device['max_output_channels'],
            sample_rate=device['default_samplerate'],
            is_input=device['max_input_channels'] > 0,
            is_output=device['max_output_channels'] > 0
        )
        device_list.append(device_info.__dict__)
    
    return {
        "success": True,
        "devices": device_list,
        "default_input": sd.default.device[0],
        "default_output": sd.default.device[1]
    }

@app.post("/audio/configure")
async def configure_audio_devices(request: AudioDeviceRequest):
    """Configure les périphériques audio"""
    try:
        if request.input_device is not None:
            sd.default.device[0] = request.input_device
            AUDIO_CONFIG["input_device"] = request.input_device
        
        if request.output_device is not None:
            sd.default.device[1] = request.output_device
            AUDIO_CONFIG["output_device"] = request.output_device
        
        return {
            "success": True,
            "message": "Audio devices configured",
            "config": AUDIO_CONFIG
        }
    except Exception as e:
        raise HTTPException(500, f"Audio configuration failed: {str(e)}")

@app.post("/voice/listen")
async def listen_once():
    """Écoute vocale ponctuelle"""
    try:
        text = voice_recognition.listen_once(timeout=10.0)
        
        if text:
            # Envoyer au pod IA pour traitement
            ai_response = await docker_client.send_to_ai(text, {
                "type": "voice_command",
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "recognized_text": text,
                "ai_response": ai_response,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "No speech recognized",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(500, f"Voice recognition failed: {str(e)}")

@app.post("/voice/speak")
async def speak_text(request: TTSRequest):
    """Synthèse vocale locale"""
    try:
        success = await tts_engine.speak_async(request.text)
        
        return {
            "success": success,
            "text": request.text,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Text-to-speech failed: {str(e)}")

@app.post("/voice/command")
async def process_voice_command(command: VoiceCommand):
    """Traite une commande vocale"""
    try:
        # Analyser la commande
        if "jarvis" in command.text.lower():
            # Commande pour JARVIS
            ai_response = await docker_client.send_to_ai(command.text, command.context)
            
            # Répondre vocalement
            if "response" in ai_response:
                await tts_engine.speak_async(ai_response["response"])
            
            return {
                "success": True,
                "command": command.text,
                "response": ai_response,
                "spoken": True
            }
        else:
            return {
                "success": False,
                "error": "Command not recognized as JARVIS command"
            }
            
    except Exception as e:
        raise HTTPException(500, f"Voice command processing failed: {str(e)}")

@app.websocket("/voice/stream")
async def voice_stream_websocket(websocket: WebSocket):
    """WebSocket pour streaming vocal continu"""
    await websocket.accept()
    logger.info("Voice streaming WebSocket connected")
    
    try:
        # Message de bienvenue
        await websocket.send_json({
            "type": "connected",
            "message": "Voice bridge connected",
            "capabilities": ["continuous_listening", "real_time_tts", "ai_integration"]
        })
        
        # Boucle de traitement
        listening_task = None
        
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "start_listening":
                    if not voice_recognition.continuous_listening:
                        listening_task = asyncio.create_task(
                            voice_recognition.listen_continuous(websocket)
                        )
                        await websocket.send_json({
                            "type": "listening_started",
                            "message": "Continuous listening activated"
                        })
                
                elif data.get("type") == "stop_listening":
                    if voice_recognition.continuous_listening:
                        voice_recognition.stop_listening()
                        if listening_task:
                            listening_task.cancel()
                        await websocket.send_json({
                            "type": "listening_stopped",
                            "message": "Continuous listening deactivated"
                        })
                
                elif data.get("type") == "speak":
                    text = data.get("text", "")
                    if text:
                        await tts_engine.speak_async(text)
                        await websocket.send_json({
                            "type": "speech_completed",
                            "text": text
                        })
                
                elif data.get("type") == "voice_command":
                    command_text = data.get("text", "")
                    if command_text:
                        # Traiter via IA
                        ai_response = await docker_client.send_to_ai(command_text)
                        await websocket.send_json({
                            "type": "ai_response",
                            "command": command_text,
                            "response": ai_response
                        })
                
                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except Exception as e:
                logger.error(f"WebSocket message processing error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if voice_recognition.continuous_listening:
            voice_recognition.stop_listening()
        logger.info("Voice streaming WebSocket disconnected")

# Fonctions utilitaires
def get_input_devices() -> List[Dict]:
    """Récupère les périphériques d'entrée audio"""
    devices = sd.query_devices()
    return [
        {"index": i, "name": device['name']}
        for i, device in enumerate(devices)
        if device['max_input_channels'] > 0
    ]

def get_output_devices() -> List[Dict]:
    """Récupère les périphériques de sortie audio"""
    devices = sd.query_devices()
    return [
        {"index": i, "name": device['name']}
        for i, device in enumerate(devices)
        if device['max_output_channels'] > 0
    ]

# Interface web statique
@app.get("/", response_class=HTMLResponse)
async def serve_interface():
    """Interface web pour contrôle vocal"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JARVIS Voice Bridge</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
            .connected { background: #0d7377; }
            .disconnected { background: #d32f2f; }
            .listening { background: #f57c00; }
            button { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
            .primary { background: #1976d2; color: white; }
            .success { background: #388e3c; color: white; }
            .warning { background: #f57c00; color: white; }
            .danger { background: #d32f2f; color: white; }
            #output { background: #2a2a2a; padding: 15px; border-radius: 5px; min-height: 200px; overflow-y: auto; }
            .log-entry { margin: 5px 0; padding: 5px; border-left: 3px solid #1976d2; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 JARVIS Voice Bridge</h1>
            <div id="status" class="status disconnected">🔴 Déconnecté</div>
            
            <div>
                <button onclick="connect()" class="primary">Se connecter</button>
                <button onclick="startListening()" class="success">🎤 Écouter</button>
                <button onclick="stopListening()" class="warning">⏹️ Arrêter</button>
                <button onclick="testTTS()" class="primary">🗣️ Test TTS</button>
            </div>
            
            <div>
                <h3>Commande Rapide</h3>
                <input type="text" id="commandInput" placeholder="Tapez votre commande..." style="width: 70%; padding: 10px;">
                <button onclick="sendCommand()" class="success">Envoyer</button>
            </div>
            
            <div>
                <h3>Sortie / Logs</h3>
                <div id="output"></div>
            </div>
        </div>

        <script>
            let ws = null;
            let isListening = false;

            function log(message, type = 'info') {
                const output = document.getElementById('output');
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;
                output.appendChild(entry);
                output.scrollTop = output.scrollHeight;
            }

            function updateStatus(status, className) {
                const statusEl = document.getElementById('status');
                statusEl.textContent = status;
                statusEl.className = `status ${className}`;
            }

            function connect() {
                if (ws) ws.close();
                
                ws = new WebSocket('ws://localhost:3001/voice/stream');
                
                ws.onopen = () => {
                    updateStatus('🟢 Connecté', 'connected');
                    log('Connecté au Voice Bridge');
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    log(`Reçu: ${data.type} - ${data.message || JSON.stringify(data)}`);
                    
                    if (data.type === 'ai_response' && data.response.response) {
                        // Auto-speak AI response
                        speak(data.response.response);
                    }
                };
                
                ws.onclose = () => {
                    updateStatus('🔴 Déconnecté', 'disconnected');
                    log('Connexion fermée');
                };
                
                ws.onerror = (error) => {
                    log(`Erreur WebSocket: ${error}`, 'error');
                };
            }

            function startListening() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({type: 'start_listening'}));
                    updateStatus('🟠 En écoute...', 'listening');
                    isListening = true;
                    log('Écoute continue activée');
                }
            }

            function stopListening() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({type: 'stop_listening'}));
                    updateStatus('🟢 Connecté', 'connected');
                    isListening = false;
                    log('Écoute continue désactivée');
                }
            }

            function speak(text) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({type: 'speak', text: text}));
                    log(`TTS: ${text}`);
                }
            }

            function testTTS() {
                speak('Bonjour, je suis JARVIS, votre assistant IA. Système vocal opérationnel.');
            }

            function sendCommand() {
                const input = document.getElementById('commandInput');
                const command = input.value.trim();
                
                if (command && ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'voice_command',
                        text: command
                    }));
                    log(`Commande envoyée: ${command}`);
                    input.value = '';
                }
            }

            // Auto-connect on page load
            window.onload = () => {
                setTimeout(connect, 500);
            };

            // Enter key for command input
            document.getElementById('commandInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendCommand();
            });
        </script>
    </body>
    </html>
    """

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage à l'arrêt"""
    voice_recognition.stop_listening()
    await docker_client.close()

if __name__ == "__main__":
    logger.info(f"Starting JARVIS Voice Bridge on port {SERVICE_PORT}")
    logger.info("Local audio access enabled")
    
    uvicorn.run(
        "voice-bridge:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=False
    )