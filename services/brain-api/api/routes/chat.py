"""
💬 Routes de chat - JARVIS Brain API
Endpoints pour conversation et interaction utilisateur
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
import time
import uuid
import logging
import re
from utils.security_validators import (
    InputSanitizer, 
    SecureChatMessage, 
    SecurityValidationMiddleware,
    quick_sanitize
)

logger = logging.getLogger(__name__)

router = APIRouter()

# === MODÈLES DE DONNÉES ===

# Utilisation du modèle sécurisé
class ChatMessage(SecureChatMessage):
    """Modèle de message de chat avec validation de sécurité intégrée"""
    pass

class ChatResponse(BaseModel):
    response: str
    message_id: str
    user_id: Optional[str]
    execution_time: float
    steps_count: int
    confidence: float
    timestamp: float

class ConversationHistory(BaseModel):
    messages: List[Dict[str, Any]]
    total_count: int = Field(..., ge=0, le=10000)
    session_id: str = Field(..., min_length=1, max_length=50)
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("ID de session invalide")
        return v

# === ENDPOINTS ===

@router.post("/message", response_model=ChatResponse)
async def send_message(request: Request, message: ChatMessage) -> ChatResponse:
    """
    Envoyer un message à JARVIS et recevoir une réponse
    Avec validation de sécurité renforcée
    """
    start_time = time.time()
    message_id = str(uuid.uuid4())
    
    try:
        # Validation de sécurité de la requête
        content_length = request.headers.get('content-length')
        if content_length:
            SecurityValidationMiddleware.validate_request_size(int(content_length))
        
        SecurityValidationMiddleware.validate_headers(dict(request.headers))
        
        # Log sécurisé (pas de contenu sensible)
        safe_message_preview = message.message[:50] if len(message.message) > 50 else message.message
        logger.info(f"📨 Message reçu (longueur: {len(message.message)})")
        
        # Vérifications de sécurité supplémentaires
        if len(message.message.strip()) == 0:
            raise HTTPException(status_code=400, detail="Message vide")
        
        # Détection de contenu potentiellement malveillant
        suspicious_keywords = ['<script', 'javascript:', 'eval(', 'document.cookie']
        message_lower = message.message.lower()
        if any(keyword in message_lower for keyword in suspicious_keywords):
            logger.warning(f"Message potentiellement malveillant détecté de {message.user_id}")
            raise HTTPException(status_code=400, detail="Contenu non autorisé détecté")
        
        # Rate limiting basique (à améliorer avec Redis en production)
        # TODO: Implémenter rate limiting par utilisateur
        
        # Simulation traitement avec sécurité
        import asyncio
        await asyncio.sleep(0.2)  # Simule temps de traitement
        
        # Génération de réponse sécurisée
        response_text = generate_safe_response(message.message)
        
        execution_time = time.time() - start_time
        
        # Nettoyer la réponse avant de l'envoyer
        clean_response = InputSanitizer.sanitize_text(response_text)
        
        return ChatResponse(
            response=clean_response,
            message_id=message_id,
            user_id=message.user_id,
            execution_time=execution_time,
            steps_count=1,
            confidence=0.95,
            timestamp=time.time()
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Erreur de validation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erreur traitement message: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

def generate_safe_response(message: str) -> str:
    """Génère une réponse sécurisée basée sur le message"""
    message_clean = message.lower().strip()
    
    # Réponses prédéfinies sécurisées
    if "bonjour" in message_clean or "salut" in message_clean:
        return "Bonjour ! Je suis JARVIS, votre assistant IA. Comment puis-je vous aider aujourd'hui ?"
    elif "merci" in message_clean:
        return "Je vous en prie ! N'hésitez pas si vous avez d'autres questions."
    elif "temps" in message_clean or "heure" in message_clean:
        import datetime
        now = datetime.datetime.now()
        return f"Il est actuellement {now.strftime('%H:%M:%S')} le {now.strftime('%d/%m/%Y')}."
    elif "aide" in message_clean or "help" in message_clean:
        return "Je peux vous aider avec diverses tâches. Posez-moi vos questions et je ferai de mon mieux pour vous répondre."
    else:
        # Réponse générique sécurisée
        return "J'ai bien reçu votre message. Je traite votre demande avec mes capacités d'IA avancées."

@router.get("/history/{user_id}", response_model=ConversationHistory)
async def get_conversation_history(
    user_id: str, 
    session_id: Optional[str] = None,
    limit: int = Field(50, ge=1, le=100),  # Limiter pour éviter DoS
    offset: int = Field(0, ge=0)
) -> ConversationHistory:
    """
    Récupérer l'historique de conversation d'un utilisateur
    """
    try:
        # Validation de sécurité de l'user_id
        clean_user_id = quick_sanitize(user_id, "username")
        
        if session_id:
            clean_session_id = quick_sanitize(session_id, "text")
        else:
            clean_session_id = None
        
        # TODO: Intégrer avec Memory Manager
        # Pour l'instant, historique simulé avec données nettoyées
        
        messages = [
            {
                "id": str(uuid.uuid4()),
                "message": "Bonjour JARVIS",
                "response": "Bonjour ! Comment puis-je vous aider ?",
                "timestamp": time.time() - 3600,
                "user_id": clean_user_id
            },
            {
                "id": str(uuid.uuid4()),
                "message": "Quelle heure est-il ?",
                "response": "Il est 14:30",
                "timestamp": time.time() - 1800,
                "user_id": clean_user_id
            }
        ]
        
        return ConversationHistory(
            messages=messages[offset:offset+limit],
            total_count=len(messages),
            session_id=clean_session_id or str(uuid.uuid4())
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération historique: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.delete("/history/{user_id}")
async def clear_conversation_history(user_id: str, session_id: Optional[str] = None) -> Dict[str, str]:
    """
    Effacer l'historique de conversation d'un utilisateur
    """
    try:
        # TODO: Intégrer avec Memory Manager
        logger.info(f"🗑️ Suppression historique pour utilisateur: {user_id}")
        
        return {
            "status": "success",
            "message": f"Historique supprimé pour l'utilisateur {user_id}",
            "timestamp": str(time.time())
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur suppression historique: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/context/{user_id}")
async def get_user_context(user_id: str) -> Dict[str, Any]:
    """
    Récupérer le contexte complet d'un utilisateur
    """
    try:
        # TODO: Intégrer avec Memory Manager
        # Pour l'instant, contexte simulé
        
        context = {
            "user_id": user_id,
            "profile": {
                "name": f"User_{user_id[:8]}",
                "preferences": {"language": "fr", "timezone": "Europe/Paris"},
                "expertise_areas": ["programmation", "technologie"]
            },
            "recent_interactions": 15,
            "last_activity": time.time() - 300,
            "memory_summary": {
                "static_memories": 5,
                "dynamic_memories": 3,
                "episodic_memories": 25
            }
        }
        
        return context
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération contexte: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

class FeedbackRequest(BaseModel):
    message_id: str = Field(..., min_length=1, max_length=50)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    
    @validator('message_id')
    def validate_message_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("ID de message invalide")
        return v
    
    @validator('comment')
    def validate_comment(cls, v):
        if v is None:
            return v
        return InputSanitizer.sanitize_text(v)

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest) -> Dict[str, str]:
    """
    Soumettre un feedback sur une réponse
    """
    try:
        # Validation déjà effectuée par Pydantic
        
        # TODO: Enregistrer feedback pour améliorer le modèle
        logger.info(f"👍 Feedback reçu pour message {feedback.message_id}: {feedback.rating}/5")
        
        return {
            "status": "success",
            "message": "Feedback enregistré",
            "timestamp": str(time.time())
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")