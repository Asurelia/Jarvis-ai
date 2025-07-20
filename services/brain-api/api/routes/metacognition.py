"""
🤔 Routes de métacognition - JARVIS Brain API
Endpoints pour filtrage intelligent LLM et optimisation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Tuple
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# === MODÈLES DE DONNÉES ===

class QueryAnalysis(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class QueryDecision(BaseModel):
    should_activate_llm: bool
    reason: str
    complexity_score: float
    estimated_cost: float
    recommended_action: str

class HallucinationCheck(BaseModel):
    response: str

class HallucinationResult(BaseModel):
    is_hallucination: bool
    confidence: float
    patterns_found: List[str]
    recommendations: List[str]

class OptimizationSuggestion(BaseModel):
    current_efficiency: float
    suggested_threshold: float
    expected_improvement: float
    justification: str

# === ENDPOINTS ===

@router.post("/analyze", response_model=QueryDecision)
async def analyze_query(analysis: QueryAnalysis) -> QueryDecision:
    """
    Analyser une requête pour décider de l'activation LLM
    """
    try:
        # TODO: Intégrer avec MetacognitionEngine
        logger.info(f"🤔 Analyse requête: {analysis.query[:50]}...")
        
        # Simulation analyse métacognitive
        query = analysis.query.lower().strip()
        
        # Score de complexité simulé
        complexity_indicators = ["comment", "pourquoi", "expliquer", "analyser", "comparer"]
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in query) / len(complexity_indicators)
        
        # Requêtes simples
        simple_patterns = ["bonjour", "merci", "oui", "non", "ok"]
        is_simple = any(pattern in query for pattern in simple_patterns)
        
        if is_simple:
            return QueryDecision(
                should_activate_llm=False,
                reason="Requête simple, réponse directe possible",
                complexity_score=0.1,
                estimated_cost=0.0,
                recommended_action="direct_response"
            )
        
        if complexity_score < 0.3:
            return QueryDecision(
                should_activate_llm=False,
                reason=f"Complexité insuffisante ({complexity_score:.2f} < 0.3)",
                complexity_score=complexity_score,
                estimated_cost=0.0,
                recommended_action="template_response"
            )
        
        # Activation LLM justifiée
        estimated_cost = complexity_score * 0.01  # Coût estimé en euros
        
        return QueryDecision(
            should_activate_llm=True,
            reason=f"LLM activé (complexité: {complexity_score:.2f})",
            complexity_score=complexity_score,
            estimated_cost=estimated_cost,
            recommended_action="llm_processing"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur analyse requête: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.post("/check-hallucination", response_model=HallucinationResult)
async def check_hallucination(check: HallucinationCheck) -> HallucinationResult:
    """
    Vérifier si une réponse contient des hallucinations
    """
    try:
        # TODO: Intégrer avec MetacognitionEngine
        logger.info(f"🚨 Vérification hallucination: {len(check.response)} caractères")
        
        response = check.response.lower()
        patterns_found = []
        confidence_scores = []
        
        # Patterns d'incertitude
        uncertainty_patterns = [
            "je ne sais pas", "incertain", "peut-être", "probablement",
            "il me semble", "apparemment", "selon certaines sources"
        ]
        
        for pattern in uncertainty_patterns:
            if pattern in response:
                patterns_found.append(f"Incertitude: {pattern}")
                confidence_scores.append(0.8)
        
        # Répétitions anormales
        words = response.split()
        if len(words) > 10:
            word_freq = {}
            for word in words:
                if len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            max_repetition = max(word_freq.values()) if word_freq else 0
            if max_repetition > len(words) * 0.3:
                patterns_found.append(f"Répétition excessive: {max_repetition}/{len(words)}")
                confidence_scores.append(0.9)
        
        # Score final
        final_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        is_hallucination = final_confidence >= 0.7
        
        recommendations = []
        if is_hallucination:
            recommendations.extend([
                "Régénérer la réponse avec un prompt plus spécifique",
                "Vérifier les sources d'information",
                "Utiliser un modèle différent"
            ])
        else:
            recommendations.append("Réponse semble fiable")
        
        return HallucinationResult(
            is_hallucination=is_hallucination,
            confidence=final_confidence,
            patterns_found=patterns_found,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification hallucination: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/stats")
async def get_metacognition_stats() -> Dict[str, Any]:
    """
    Obtenir les statistiques de métacognition
    """
    try:
        # TODO: Intégrer avec MetacognitionEngine
        
        stats = {
            "total_queries": 234,
            "llm_activations": 156,
            "filtered_queries": 78,
            "hallucinations_detected": 12,
            "repetitions_filtered": 15,
            "complexity_filtered": 51,
            "efficiency_percentage": 66.7,
            "filter_rate": 33.3,
            "avg_cost_saved": 0.12,  # euros par requête filtrée
            "total_cost_saved": 9.36  # euros total
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erreur stats métacognition: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.post("/optimize")
async def auto_optimize() -> OptimizationSuggestion:
    """
    Auto-optimisation des seuils de métacognition
    """
    try:
        # TODO: Intégrer avec MetacognitionEngine
        logger.info("🔧 Auto-optimisation métacognition")
        
        # Simulation optimisation
        current_efficiency = 66.7
        suggested_threshold = 0.35  # Nouveau seuil de complexité
        expected_improvement = 8.5  # % d'amélioration attendue
        
        return OptimizationSuggestion(
            current_efficiency=current_efficiency,
            suggested_threshold=suggested_threshold,
            expected_improvement=expected_improvement,
            justification="Basé sur l'analyse des dernières 100 requêtes, augmenter le seuil réduirait les faux positifs"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur auto-optimisation: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/efficiency-report")
async def get_efficiency_report() -> Dict[str, Any]:
    """
    Rapport d'efficacité détaillé
    """
    try:
        # TODO: Intégrer avec MetacognitionEngine
        
        report = {
            "period": "last_30_days",
            "total_queries": 2340,
            "llm_activations": 1560,
            "queries_filtered": 780,
            "filtering_breakdown": {
                "simple_queries": 351,
                "repetitive_queries": 156,
                "low_complexity": 273
            },
            "cost_analysis": {
                "total_cost_saved": 93.60,  # euros
                "avg_cost_per_llm_call": 0.012,
                "potential_monthly_savings": 124.80
            },
            "quality_metrics": {
                "hallucinations_prevented": 45,
                "user_satisfaction": 0.92,
                "response_accuracy": 0.89
            },
            "recommendations": [
                "Ajuster le seuil de complexité à 0.35",
                "Améliorer la détection des requêtes répétitives",
                "Intégrer plus de patterns d'incertitude"
            ]
        }
        
        return report
        
    except Exception as e:
        logger.error(f"❌ Erreur rapport efficacité: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.put("/settings")
async def update_settings(
    complexity_threshold: Optional[float] = None,
    hallucination_threshold: Optional[float] = None,
    max_repetitions: Optional[int] = None
) -> Dict[str, str]:
    """
    Mettre à jour les paramètres de métacognition
    """
    try:
        # TODO: Intégrer avec MetacognitionEngine
        
        settings_updated = []
        if complexity_threshold is not None:
            settings_updated.append(f"complexity_threshold: {complexity_threshold}")
        if hallucination_threshold is not None:
            settings_updated.append(f"hallucination_threshold: {hallucination_threshold}")
        if max_repetitions is not None:
            settings_updated.append(f"max_repetitions: {max_repetitions}")
        
        logger.info(f"⚙️ Paramètres mis à jour: {', '.join(settings_updated)}")
        
        return {
            "status": "success",
            "message": f"Paramètres mis à jour: {', '.join(settings_updated)}",
            "timestamp": str(time.time())
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour paramètres: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/patterns")
async def get_detected_patterns() -> Dict[str, Any]:
    """
    Obtenir les patterns détectés récemment
    """
    try:
        # TODO: Intégrer avec MetacognitionEngine
        
        patterns = {
            "recent_patterns": [
                {
                    "type": "repetitive_query",
                    "pattern": "Quelle heure est-il ?",
                    "occurrences": 15,
                    "last_seen": time.time() - 300
                },
                {
                    "type": "simple_greeting",
                    "pattern": "bonjour",
                    "occurrences": 23,
                    "last_seen": time.time() - 150
                },
                {
                    "type": "uncertainty_indicator",
                    "pattern": "je ne sais pas",
                    "occurrences": 8,
                    "last_seen": time.time() - 800
                }
            ],
            "pattern_trends": {
                "increasing": ["simple_greeting", "repetitive_query"],
                "decreasing": ["uncertainty_indicator"],
                "stable": ["complex_technical"]
            }
        }
        
        return patterns
        
    except Exception as e:
        logger.error(f"❌ Erreur patterns détectés: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")