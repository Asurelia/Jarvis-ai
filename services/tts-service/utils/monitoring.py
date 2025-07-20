"""
📊 Monitoring & Metrics - TTS Service
Métriques Prometheus pour le service TTS
"""

import logging
from prometheus_client import Counter, Histogram, Gauge
import time

logger = logging.getLogger(__name__)

# Métriques TTS
TTS_REQUESTS = Counter(
    'jarvis_tts_requests_total',
    'Total des requêtes TTS',
    ['voice_id', 'language', 'streaming']
)

TTS_DURATION = Histogram(
    'jarvis_tts_duration_seconds',
    'Durée de synthèse TTS',
    ['voice_id', 'language']
)

TTS_TEXT_LENGTH = Histogram(
    'jarvis_tts_text_length_chars',
    'Longueur du texte synthétisé',
    buckets=[10, 50, 100, 500, 1000, 5000]
)

ACTIVE_STREAMS = Gauge(
    'jarvis_tts_active_streams',
    'Nombre de streams audio actifs'
)

AUDIO_CHUNKS_SENT = Counter(
    'jarvis_tts_audio_chunks_sent_total',
    'Total des chunks audio envoyés'
)

VOICE_CLONES = Counter(
    'jarvis_tts_voice_clones_total',
    'Total des voix clonées',
    ['status']
)

TTS_ERRORS = Counter(
    'jarvis_tts_errors_total',
    'Total des erreurs TTS',
    ['error_type']
)

# Fonctions d'enregistrement
def setup_metrics():
    """Initialiser les métriques"""
    logger.info("📊 Métriques TTS initialisées")

def record_tts_request(
    voice_id: str,
    language: str,
    text_length: int,
    duration: float,
    streaming: bool = False
):
    """Enregistrer une requête TTS"""
    try:
        TTS_REQUESTS.labels(
            voice_id=voice_id,
            language=language,
            streaming=str(streaming)
        ).inc()
        
        TTS_DURATION.labels(
            voice_id=voice_id,
            language=language
        ).observe(duration)
        
        TTS_TEXT_LENGTH.observe(text_length)
        
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement métriques TTS: {e}")

def record_stream_activity(active_count: int):
    """Enregistrer l'activité des streams"""
    try:
        ACTIVE_STREAMS.set(active_count)
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement streams: {e}")

def record_audio_chunk():
    """Enregistrer l'envoi d'un chunk audio"""
    try:
        AUDIO_CHUNKS_SENT.inc()
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement chunk: {e}")

def record_voice_clone(success: bool):
    """Enregistrer un clonage de voix"""
    try:
        status = "success" if success else "failure"
        VOICE_CLONES.labels(status=status).inc()
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement clonage: {e}")

def record_tts_error(error_type: str):
    """Enregistrer une erreur TTS"""
    try:
        TTS_ERRORS.labels(error_type=error_type).inc()
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement erreur: {e}")