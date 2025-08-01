"""
🎤 STT Service - JARVIS v2.0
Service de reconnaissance vocale avec Whisper
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
import uvicorn
import whisper
import numpy as np
import io
import time
import asyncio
import json
import torch
import torchaudio
import soundfile as sf
from typing import Optional, Dict, Any
from pathlib import Path
import tempfile
import os
from loguru import logger

# Prometheus monitoring
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
import structlog

# Configuration
MODEL_NAME = os.getenv("STT_MODEL", "base")
def get_optimal_device():
    """Détection GPU optimale AMD/NVIDIA"""
    if torch.cuda.is_available():
        try:
            device_name = torch.cuda.get_device_name(0)
            if 'AMD' in device_name or 'Radeon' in device_name:
                logger.info("🔴 GPU AMD détecté pour STT")
                return "cuda"  # ROCm utilise l'API CUDA
            elif 'NVIDIA' in device_name:
                logger.info("🟢 GPU NVIDIA détecté pour STT")
                return "cuda"
        except Exception as e:
            logger.warning(f"⚠️ Erreur détection GPU: {e}")
        return "cuda"
    return "cpu"

DEVICE = get_optimal_device()
SAMPLE_RATE = 16000
CHUNK_LENGTH = 30  # seconds

# Initialize FastAPI
app = FastAPI(
    title="JARVIS STT Service", 
    version="2.0.0",
    description="Service de reconnaissance vocale temps réel avec Whisper"
)

# Prometheus metrics
registry = CollectorRegistry()

# Métriques de transcription
stt_requests = Counter(
    'stt_requests_total', 
    'Total STT requests', 
    ['method', 'status'],
    registry=registry
)

stt_duration = Histogram(
    'stt_transcription_duration_seconds',
    'Time spent transcribing audio',
    ['model', 'language'],
    registry=registry
)

stt_audio_duration = Histogram(
    'stt_audio_duration_seconds',
    'Duration of processed audio files',
    ['language'],
    registry=registry
)

# Métriques de performance
stt_model_load_time = Gauge(
    'stt_model_load_time_seconds',
    'Time taken to load the STT model',
    registry=registry
)

stt_active_connections = Gauge(
    'stt_websocket_active_connections',
    'Number of active WebSocket connections',
    registry=registry
)

stt_memory_usage = Gauge(
    'stt_memory_usage_bytes',
    'Memory usage of STT service',
    registry=registry
)

# Métriques d'erreur
stt_errors = Counter(
    'stt_errors_total',
    'Total STT errors',
    ['error_type'],
    registry=registry
)

# Global model instance
whisper_model = None

class STTService:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Charger le modèle Whisper"""
        try:
            logger.info(f"Chargement du modèle Whisper {MODEL_NAME} sur {DEVICE}")
            start_time = time.time()
            
            self.model = whisper.load_model(MODEL_NAME, device=DEVICE)
            
            load_time = time.time() - start_time
            stt_model_load_time.set(load_time)
            
            logger.success(f"Modèle {MODEL_NAME} chargé avec succès en {load_time:.2f}s")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            stt_errors.labels(error_type='model_loading').inc()
            raise
    
    def transcribe_audio(self, audio_data: np.ndarray, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcrire l'audio avec Whisper"""
        start_time = time.time()
        audio_duration = len(audio_data) / SAMPLE_RATE
        
        try:
            # Options de transcription
            options = {
                "language": language,
                "task": "transcribe",
                "fp16": DEVICE == "cuda" and 'AMD' not in torch.cuda.get_device_name(0) if DEVICE == "cuda" else False,
                "verbose": False
            }
            
            # Transcription
            result = self.model.transcribe(audio_data, **options)
            
            # Métriques
            transcription_time = time.time() - start_time
            detected_language = result.get("language", language or "unknown")
            
            stt_duration.labels(model=MODEL_NAME, language=detected_language).observe(transcription_time)
            stt_audio_duration.labels(language=detected_language).observe(audio_duration)
            
            return {
                "text": result["text"].strip(),
                "language": detected_language,
                "segments": result.get("segments", []),
                "duration": audio_duration
            }
        except Exception as e:
            logger.error(f"Erreur de transcription: {e}")
            stt_errors.labels(error_type='transcription').inc()
            raise

    def process_audio_file(self, audio_bytes: bytes, format: str = "wav") -> np.ndarray:
        """Convertir les bytes audio en array numpy"""
        try:
            # Lire l'audio
            audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
            
            # Convertir en mono si nécessaire
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Resampler si nécessaire
            if sample_rate != SAMPLE_RATE:
                audio_tensor = torch.from_numpy(audio_data).float()
                resampler = torchaudio.transforms.Resample(sample_rate, SAMPLE_RATE)
                audio_data = resampler(audio_tensor).numpy()
            
            return audio_data.astype(np.float32)
        except Exception as e:
            logger.error(f"Erreur de traitement audio: {e}")
            raise

# Initialiser le service
stt_service = STTService()

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    logger.info("STT Service démarré")
    logger.info(f"Modèle: {MODEL_NAME}, Device: {DEVICE}")

@app.get("/health")
async def health_check():
    """Vérification de santé du service"""
    return {
        "status": "healthy",
        "service": "STT Service", 
        "version": "2.0.0",
        "model": MODEL_NAME,
        "device": DEVICE,
        "timestamp": time.time()
    }

@app.get("/metrics")
async def get_metrics():
    """Endpoint Prometheus pour les métriques"""
    # Mise à jour des métriques de mémoire
    import psutil
    process = psutil.Process()
    stt_memory_usage.set(process.memory_info().rss)
    
    return Response(
        generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/models")
async def list_models():
    """Liste des modèles disponibles"""
    return {
        "current_model": MODEL_NAME,
        "available_models": ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        "device": DEVICE
    }

@app.get("/languages")
async def list_languages():
    """Liste des langues supportées"""
    return {
        "languages": whisper.tokenizer.LANGUAGES,
        "default": "auto"
    }

@app.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = None,
    detect_language: bool = True
):
    """Transcrire un fichier audio en texte"""
    try:
        stt_requests.labels(method='transcribe', status='started').inc()
        
        # Vérifier le type de fichier
        if not audio.content_type.startswith("audio/"):
            stt_requests.labels(method='transcribe', status='error').inc()
            raise HTTPException(400, "Le fichier doit être un fichier audio")
        
        # Lire le fichier
        audio_bytes = await audio.read()
        
        # Traiter l'audio
        audio_data = stt_service.process_audio_file(audio_bytes)
        
        # Détecter la langue si demandé
        if detect_language and not language:
            # Détecter sur les 30 premières secondes
            sample = audio_data[:SAMPLE_RATE * 30]
            detected = stt_service.model.detect_language(sample)
            language = max(detected, key=detected.get)
            logger.info(f"Langue détectée: {language}")
        
        # Transcrire
        result = stt_service.transcribe_audio(audio_data, language)
        
        stt_requests.labels(method='transcribe', status='success').inc()
        
        return {
            "status": "success",
            "filename": audio.filename,
            "transcription": result["text"],
            "language": result["language"],
            "duration": result["duration"],
            "segments": result["segments"],
            "timestamp": time.time()
        }
        
    except Exception as e:
        stt_requests.labels(method='transcribe', status='error').inc()
        logger.error(f"Erreur de transcription: {e}")
        raise HTTPException(500, f"Erreur de transcription: {str(e)}")

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket pour transcription en temps réel"""
    await websocket.accept()
    stt_active_connections.inc()
    logger.info("Nouvelle connexion WebSocket STT")
    
    try:
        audio_buffer = []
        
        while True:
            # Recevoir les données audio
            data = await websocket.receive_bytes()
            
            # Ajouter au buffer
            audio_buffer.extend(data)
            
            # Si on a assez de données (chunk de 1 seconde)
            if len(audio_buffer) >= SAMPLE_RATE * 2:  # 2 bytes per sample
                # Convertir en numpy array
                audio_chunk = np.frombuffer(bytes(audio_buffer[:SAMPLE_RATE * 2]), dtype=np.int16)
                audio_chunk = audio_chunk.astype(np.float32) / 32768.0
                
                # Transcrire le chunk
                try:
                    result = stt_service.transcribe_audio(audio_chunk)
                    
                    # Envoyer le résultat
                    await websocket.send_json({
                        "type": "transcription",
                        "text": result["text"],
                        "timestamp": time.time(),
                        "is_final": False
                    })
                except Exception as e:
                    logger.error(f"Erreur de transcription chunk: {e}")
                    stt_errors.labels(error_type='websocket_transcription').inc()
                
                # Vider le buffer traité
                audio_buffer = audio_buffer[SAMPLE_RATE * 2:]
                
    except WebSocketDisconnect:
        stt_active_connections.dec()
        logger.info("Déconnexion WebSocket STT")
    except Exception as e:
        stt_active_connections.dec()
        stt_errors.labels(error_type='websocket_error').inc()
        logger.error(f"Erreur WebSocket: {e}")
        await websocket.close()

@app.post("/detect-language")
async def detect_language(audio: UploadFile = File(...)):
    """Détecter la langue d'un fichier audio"""
    try:
        # Lire et traiter l'audio
        audio_bytes = await audio.read()
        audio_data = stt_service.process_audio_file(audio_bytes)
        
        # Détecter la langue sur les 30 premières secondes
        sample = audio_data[:SAMPLE_RATE * 30]
        detected = stt_service.model.detect_language(sample)
        
        # Trier par probabilité
        sorted_langs = sorted(detected.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "status": "success",
            "filename": audio.filename,
            "detected_language": sorted_langs[0][0],
            "confidence": sorted_langs[0][1],
            "all_probabilities": dict(sorted_langs[:5])  # Top 5
        }
        
    except Exception as e:
        logger.error(f"Erreur de détection de langue: {e}")
        raise HTTPException(500, f"Erreur: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=5003, 
        reload=False,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
        }
    )