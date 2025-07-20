"""
🎵 Audio API Routes - JARVIS Brain API
Endpoints pour gestion streaming audio et sessions
"""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles Pydantic
class AudioSessionConfig(BaseModel):
    direction: str = "bidirectional"  # input, output, bidirectional
    format: str = "wav"
    sample_rate: int = 16000
    channels: int = 1
    buffer_size: int = 1024
    target_latency_ms: float = 200.0

class AudioSessionResponse(BaseModel):
    session_id: str
    config: AudioSessionConfig
    timestamp: float

class AudioStatsResponse(BaseModel):
    session_id: str
    user_id: str
    duration: float
    buffer_level: int
    chunks_sent: int
    chunks_received: int
    bytes_transferred: int
    avg_chunk_latency: float
    quality_degradations: int

def get_audio_streamer():
    """Dépendance pour obtenir l'audio streamer"""
    from main import app_state
    return app_state.get("audio_streamer")

@router.get("/sessions", summary="Lister les sessions audio actives")
async def get_active_sessions(
    audio_streamer = Depends(get_audio_streamer)
) -> Dict[str, Any]:
    """Obtenir la liste des sessions audio actives"""
    
    if not audio_streamer:
        raise HTTPException(status_code=503, detail="Audio streamer non disponible")
    
    try:
        stats = audio_streamer.get_global_stats()
        
        return {
            "status": "success",
            "active_sessions": stats["active_sessions"],
            "sessions": stats["active_sessions_details"],
            "global_stats": {
                "avg_latency_ms": stats["avg_latency_ms"],
                "total_chunks_processed": stats["total_chunks_processed"],
                "throughput_kbps": stats["throughput_kbps"],
                "quality_score": stats["quality_score"]
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur sessions: {str(e)}")

@router.get("/sessions/{session_id}/stats", summary="Statistiques d'une session")
async def get_session_stats(
    session_id: str,
    audio_streamer = Depends(get_audio_streamer)
) -> AudioStatsResponse:
    """Obtenir les statistiques détaillées d'une session audio"""
    
    if not audio_streamer:
        raise HTTPException(status_code=503, detail="Audio streamer non disponible")
    
    try:
        stats = audio_streamer.get_session_stats(session_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail=f"Session {session_id} non trouvée")
        
        return AudioStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur stats session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur stats: {str(e)}")

@router.delete("/sessions/{session_id}", summary="Terminer une session audio")
async def end_audio_session(
    session_id: str,
    audio_streamer = Depends(get_audio_streamer)
) -> Dict[str, Any]:
    """Terminer manuellement une session de streaming audio"""
    
    if not audio_streamer:
        raise HTTPException(status_code=503, detail="Audio streamer non disponible")
    
    try:
        if session_id not in audio_streamer.active_sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} non trouvée")
        
        # Obtenir stats avant fermeture
        final_stats = audio_streamer.get_session_stats(session_id)
        
        # Terminer la session
        await audio_streamer.end_session(session_id)
        
        return {
            "status": "success",
            "message": f"Session {session_id} terminée",
            "final_stats": final_stats,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur fermeture session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur fermeture: {str(e)}")

@router.post("/test/upload", summary="Test upload audio")
async def test_audio_upload(
    audio_file: UploadFile = File(...),
    audio_streamer = Depends(get_audio_streamer)
) -> Dict[str, Any]:
    """
    Endpoint de test pour upload et traitement d'un fichier audio
    Utile pour tester le pipeline audio sans WebSocket
    """
    
    if not audio_streamer:
        raise HTTPException(status_code=503, detail="Audio streamer non disponible")
    
    try:
        # Vérifier le type de fichier
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Fichier audio requis")
        
        # Lire le fichier
        audio_data = await audio_file.read()
        
        # Traitement de base (simulation)
        file_info = {
            "filename": audio_file.filename,
            "content_type": audio_file.content_type,
            "size_bytes": len(audio_data),
            "duration_estimate": len(audio_data) / (16000 * 2),  # Estimation 16kHz 16-bit
        }
        
        logger.info(f"🎵 Test audio upload: {audio_file.filename} ({len(audio_data)} bytes)")
        
        return {
            "status": "success",
            "message": "Fichier audio traité avec succès",
            "file_info": file_info,
            "processed_at": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur test upload audio: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur traitement: {str(e)}")

@router.get("/config", summary="Configuration audio globale")
async def get_audio_config(
    audio_streamer = Depends(get_audio_streamer)
) -> Dict[str, Any]:
    """Obtenir la configuration audio actuelle"""
    
    if not audio_streamer:
        raise HTTPException(status_code=503, detail="Audio streamer non disponible")
    
    try:
        return {
            "status": "success",
            "config": audio_streamer.config,
            "optimizations": {
                "adaptive_buffering": audio_streamer.adaptive_buffering,
                "jitter_compensation": audio_streamer.jitter_compensation,
                "quality_adaptation": audio_streamer.quality_adaptation
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur config audio: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur config: {str(e)}")

@router.get("/health", summary="Santé du service audio")
async def audio_health_check(
    audio_streamer = Depends(get_audio_streamer)
) -> Dict[str, Any]:
    """Check de santé spécifique au streaming audio"""
    
    if not audio_streamer:
        return {
            "status": "unhealthy",
            "error": "Audio streamer non disponible",
            "timestamp": time.time()
        }
    
    try:
        stats = audio_streamer.get_global_stats()
        
        # Déterminer la santé
        is_healthy = (
            stats["avg_latency_ms"] <= audio_streamer.config["max_latency_ms"] and
            stats["quality_score"] >= 0.5
        )
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "active_sessions": stats["active_sessions"],
            "avg_latency_ms": stats["avg_latency_ms"],
            "quality_score": stats["quality_score"],
            "max_latency_threshold": audio_streamer.config["max_latency_ms"],
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur health check audio: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }