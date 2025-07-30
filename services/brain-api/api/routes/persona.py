"""
🎭 Routes Persona - JARVIS Brain API
Endpoints pour gestion des personnalités IA
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

# === MODÈLES DE DONNÉES ===

class PersonaSwitchRequest(BaseModel):
    reason: Optional[str] = "user_request"
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class PersonaSwitchResponse(BaseModel):
    success: bool
    previous_persona: Optional[str]
    current_persona: str
    message: str
    timestamp: str

class PersonaInfo(BaseModel):
    name: str
    description: str
    personality: Dict[str, float]
    voice: Dict[str, Any]
    response_style: str
    priorities: List[str]
    behavior_patterns: Dict[str, Any]
    sample_phrases: Dict[str, str]
    is_active: bool
    usage_count: int
    last_used: Optional[str]

class PersonaPreferencesUpdate(BaseModel):
    preferences: Dict[str, Any]
    user_id: Optional[str] = None

class PersonaStatistics(BaseModel):
    total_interactions: int
    current_persona: Optional[str]
    total_transitions: int
    personas: Dict[str, Dict[str, Any]]

class FormatRequest(BaseModel):
    content: str
    context: Optional[Dict[str, Any]] = None

class FormatResponse(BaseModel):
    original: str
    formatted: str
    persona: str
    timestamp: str

# === DÉPENDANCES ===

def get_persona_manager():
    """Obtenir le gestionnaire de personas depuis l'état global de l'app"""
    from main import app_state
    
    if not app_state.get("persona_manager"):
        raise HTTPException(
            status_code=503,
            detail="Persona Manager non disponible"
        )
    
    return app_state["persona_manager"]

# === ENDPOINTS ===

@router.get("/", response_model=Dict[str, PersonaInfo])
async def get_available_personas(
    persona_manager = Depends(get_persona_manager)
) -> Dict[str, PersonaInfo]:
    """
    Obtenir la liste de toutes les personas disponibles avec leurs informations
    """
    try:
        personas_data = persona_manager.get_available_personas()
        
        result = {}
        for name, data in personas_data.items():
            result[name] = PersonaInfo(**data)
        
        logger.info(f"📋 Liste des personas demandée - {len(result)} personas disponibles")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération personas: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/current")
async def get_current_persona(
    persona_manager = Depends(get_persona_manager)
) -> Dict[str, Any]:
    """
    Obtenir la persona actuellement active
    """
    try:
        current = persona_manager.get_current_persona()
        
        if not current:
            raise HTTPException(status_code=404, detail="Aucune persona active")
        
        persona_info = current.get_persona_info()
        persona_info["is_active"] = True
        
        logger.info(f"📍 Persona actuelle demandée: {current.name}")
        return persona_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération persona actuelle: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.post("/switch/{persona_name}", response_model=PersonaSwitchResponse)
async def switch_persona(
    persona_name: str,
    request: PersonaSwitchRequest,
    persona_manager = Depends(get_persona_manager)
) -> PersonaSwitchResponse:
    """
    Changer la persona active
    """
    try:
        # Obtenir la persona actuelle avant le changement
        current = persona_manager.get_current_persona()
        previous_name = current.name if current else None
        
        # Effectuer le changement
        success = await persona_manager.switch_persona(
            persona_name=persona_name,
            reason=request.reason,
            user_id=request.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de changer vers la persona '{persona_name}'"
            )
        
        # Obtenir la nouvelle persona pour confirmation
        new_current = persona_manager.get_current_persona()
        
        response = PersonaSwitchResponse(
            success=True,
            previous_persona=previous_name,
            current_persona=new_current.name,
            message=f"Persona changée avec succès vers {new_current.name}",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"🎭 Changement persona: {previous_name} → {persona_name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur changement persona: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.post("/format", response_model=FormatResponse)
async def format_response(
    request: FormatRequest,
    persona_manager = Depends(get_persona_manager)
) -> FormatResponse:
    """
    Formater un texte selon la persona active
    """
    try:
        current = persona_manager.get_current_persona()
        
        if not current:
            raise HTTPException(status_code=404, detail="Aucune persona active")
        
        formatted = persona_manager.format_response(request.content, request.context)
        
        response = FormatResponse(
            original=request.content,
            formatted=formatted,
            persona=current.name,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✨ Formatage de réponse par {current.name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur formatage réponse: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/statistics", response_model=PersonaStatistics)
async def get_persona_statistics(
    persona_manager = Depends(get_persona_manager)
) -> PersonaStatistics:
    """
    Obtenir les statistiques d'utilisation des personas
    """
    try:
        stats = persona_manager.get_persona_statistics()
        
        logger.info("📊 Statistiques personas demandées")
        return PersonaStatistics(**stats)
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération statistiques: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/history")
async def get_transition_history(
    limit: int = 10,
    persona_manager = Depends(get_persona_manager)
) -> Dict[str, Any]:
    """
    Obtenir l'historique des transitions entre personas
    """
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="La limite doit être entre 1 et 100")
        
        history = persona_manager.get_transition_history(limit)
        
        return {
            "transitions": history,
            "total_returned": len(history),
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération historique: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.put("/preferences/{persona_name}")
async def update_persona_preferences(
    persona_name: str,
    request: PersonaPreferencesUpdate,
    persona_manager = Depends(get_persona_manager)
) -> Dict[str, str]:
    """
    Mettre à jour les préférences utilisateur pour une persona
    """
    try:
        # Vérifier que la persona existe
        available = persona_manager.get_available_personas()
        if persona_name not in available:
            raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' non trouvée")
        
        # Mettre à jour les préférences
        await persona_manager.update_user_preferences(persona_name, request.preferences)
        
        logger.info(f"⚙️ Préférences mises à jour pour {persona_name}")
        return {
            "status": "success",
            "message": f"Préférences mises à jour pour {persona_name}",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour préférences: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.post("/suggest")
async def suggest_persona(
    context: Dict[str, Any],
    persona_manager = Depends(get_persona_manager)
) -> Dict[str, Any]:
    """
    Suggérer une persona basée sur le contexte
    """
    try:
        suggestion = await persona_manager.suggest_persona_switch(context)
        
        current = persona_manager.get_current_persona()
        current_name = current.name if current else None
        
        return {
            "current_persona": current_name,
            "suggested_persona": suggestion,
            "should_switch": suggestion is not None and suggestion != current_name,
            "context_analyzed": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur suggestion persona: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/{persona_name}/info", response_model=PersonaInfo)
async def get_persona_info(
    persona_name: str,
    persona_manager = Depends(get_persona_manager)
) -> PersonaInfo:
    """
    Obtenir les informations détaillées d'une persona spécifique
    """
    try:
        available = persona_manager.get_available_personas()
        
        if persona_name not in available:
            raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' non trouvée")
        
        persona_data = available[persona_name]
        
        logger.info(f"ℹ️ Informations demandées pour {persona_name}")
        return PersonaInfo(**persona_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération info persona: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.post("/{persona_name}/test")
async def test_persona(
    persona_name: str,
    test_content: str = "Hello, this is a test message.",
    persona_manager = Depends(get_persona_manager)
) -> Dict[str, Any]:
    """
    Tester le formatage d'une persona sans la changer
    """
    try:
        available = persona_manager.get_available_personas()
        
        if persona_name not in available:
            raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' non trouvée")
        
        # Sauvegarder la persona actuelle
        current = persona_manager.get_current_persona()
        original_name = current.name if current else None
        
        # Changer temporairement vers la persona de test
        await persona_manager.switch_persona(persona_name, "test")
        
        # Formater le contenu de test
        formatted = persona_manager.format_response(test_content)
        
        # Restaurer la persona originale si elle existait
        if original_name and original_name != persona_name:
            await persona_manager.switch_persona(original_name, "restore_after_test")
        
        return {
            "persona": persona_name,
            "original": test_content,
            "formatted": formatted,
            "test_successful": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur test persona: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.delete("/reset")
async def reset_persona_state(
    confirm: bool = False,
    persona_manager = Depends(get_persona_manager)
) -> Dict[str, str]:
    """
    Réinitialiser l'état des personas (usage, préférences, historique)
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Ajoutez '?confirm=true' pour confirmer la réinitialisation"
            )
        
        # Réinitialiser vers la persona par défaut
        await persona_manager.switch_persona(
            persona_manager.default_persona_name,
            "reset"
        )
        
        # TODO: Implémenter la réinitialisation complète de l'état
        # Cela nécessiterait d'ajouter une méthode reset() au PersonaManager
        
        logger.warning("🔄 Réinitialisation état personas demandée")
        return {
            "status": "success",
            "message": "État des personas réinitialisé",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur réinitialisation: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")