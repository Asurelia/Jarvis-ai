"""
🤔 Module Métacognition - JARVIS Brain API
Filtrage intelligent LLM et détection d'hallucinations
"""

import asyncio
import re
import time
from typing import Dict, List, Optional, Tuple
import logging
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MetacognitionEngine:
    """
    Moteur de métacognition pour filtrage intelligent des requêtes LLM
    Implémente la logique "penser à penser" pour optimiser l'utilisation du LLM
    """
    
    def __init__(self, hallucination_threshold: float = 0.7, complexity_min_score: float = 0.3):
        self.hallucination_threshold = hallucination_threshold
        self.complexity_min_score = complexity_min_score
        
        # Statistiques d'utilisation
        self.stats = {
            "total_queries": 0,
            "llm_activations": 0,
            "filtered_queries": 0,
            "hallucinations_detected": 0,
            "repetitions_filtered": 0,
            "complexity_filtered": 0
        }
        
        # Historique pour détection de patterns
        self.query_history = deque(maxlen=100)
        self.repetition_tracker = defaultdict(int)
        self.response_quality_history = deque(maxlen=50)
        
        # Patterns de détection
        self.hallucination_patterns = [
            r'\b(?:je ne sais pas|incertain|peut-être|probablement)\b',
            r'\b(?:il me semble|il semblerait|apparemment)\b',
            r'\b(?:selon certaines sources|d\'après|il paraît)\b',
            r'(?:[A-Z]{3,}\s*){3,}',  # Séquences de mots en majuscules
            r'(?:\w+\s*){20,}',  # Phrases très longues
        ]
        
        self.complexity_indicators = [
            r'\b(?:analyser|analyser|comparer|évaluer|synthétiser)\b',
            r'\b(?:pourquoi|comment|quand|où|qui|quoi)\b',
            r'\b(?:expliquer|détailler|décrire|justifier)\b',
            r'\b(?:algorithme|programme|code|fonction|méthode)\b',
            r'\b(?:problème|solution|stratégie|approche)\b'
        ]
        
        self.simple_queries = [
            r'^\s*(?:bonjour|salut|hello|hi)\s*[!.?]*\s*$',
            r'^\s*(?:merci|thanks|thank you)\s*[!.?]*\s*$',
            r'^\s*(?:oui|non|yes|no|ok|okay)\s*[!.?]*\s*$',
            r'^\s*(?:ça va|comment allez-vous|how are you)\s*[?]*\s*$'
        ]
        
        logger.info("🤔 Métacognition Engine initialisé")
    
    async def initialize(self):
        """Initialisation asynchrone du moteur"""
        logger.info("🚀 Initialisation Métacognition Engine...")
        
        # Chargement des modèles de détection (simulation)
        await asyncio.sleep(0.1)
        
        logger.info("✅ Métacognition Engine prêt")
    
    async def shutdown(self):
        """Arrêt propre du moteur"""
        logger.info("🛑 Arrêt Métacognition Engine...")
        self._log_final_stats()
    
    def should_activate_llm(self, query: str, context: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Décision principale : faut-il activer le LLM pour cette requête ?
        
        Returns:
            Tuple[bool, str]: (should_activate, reason)
        """
        self.stats["total_queries"] += 1
        query_clean = query.strip().lower()
        
        # 1. Requêtes simples (pas besoin LLM)
        if self._is_simple_query(query_clean):
            self.stats["complexity_filtered"] += 1
            return False, "Requête simple, réponse directe possible"
        
        # 2. Détection de répétitions
        if self._is_repetitive_query(query_clean):
            self.stats["repetitions_filtered"] += 1
            return False, "Requête répétitive détectée"
        
        # 3. Vérification complexité minimum
        complexity_score = self._calculate_complexity_score(query_clean)
        if complexity_score < self.complexity_min_score:
            self.stats["complexity_filtered"] += 1
            return False, f"Complexité insuffisante ({complexity_score:.2f} < {self.complexity_min_score})"
        
        # 4. Vérification contexte utilisateur
        if context and not self._should_engage_with_context(context):
            return False, "Contexte utilisateur ne nécessite pas LLM"
        
        # 5. Activation LLM justifiée
        self.stats["llm_activations"] += 1
        self._update_query_history(query_clean)
        
        return True, f"LLM activé (complexité: {complexity_score:.2f})"
    
    def detect_hallucination(self, response: str) -> Tuple[bool, float, List[str]]:
        """
        Détecter les hallucinations dans une réponse LLM
        
        Returns:
            Tuple[bool, float, List[str]]: (is_hallucination, confidence, patterns_found)
        """
        response_clean = response.strip().lower()
        patterns_found = []
        confidence_scores = []
        
        # Vérification patterns d'incertitude
        for pattern in self.hallucination_patterns:
            matches = re.findall(pattern, response_clean, re.IGNORECASE)
            if matches:
                patterns_found.append(f"Incertitude: {pattern}")
                confidence_scores.append(0.8)
        
        # Vérification répétitions anormales
        words = response_clean.split()
        if len(words) > 10:
            word_freq = defaultdict(int)
            for word in words:
                if len(word) > 3:  # Mots significatifs seulement
                    word_freq[word] += 1
            
            # Détecter répétitions excessives
            max_repetition = max(word_freq.values()) if word_freq else 0
            if max_repetition > len(words) * 0.3:  # Plus de 30% de répétition
                patterns_found.append(f"Répétition excessive: {max_repetition}/{len(words)}")
                confidence_scores.append(0.9)
        
        # Vérification cohérence structurelle
        sentences = response.split('.')
        if len(sentences) > 3:
            # Phrases très courtes ou très longues
            avg_length = np.mean([len(s.split()) for s in sentences if s.strip()])
            if avg_length < 3 or avg_length > 50:
                patterns_found.append(f"Structure anormale: {avg_length:.1f} mots/phrase")
                confidence_scores.append(0.6)
        
        # Calcul score final
        final_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        is_hallucination = final_confidence >= self.hallucination_threshold
        
        if is_hallucination:
            self.stats["hallucinations_detected"] += 1
            logger.warning(f"🚨 Hallucination détectée (conf: {final_confidence:.2f}): {patterns_found}")
        
        return is_hallucination, final_confidence, patterns_found
    
    def _is_simple_query(self, query: str) -> bool:
        """Vérifier si la requête est simple (salutations, confirmations, etc.)"""
        for pattern in self.simple_queries:
            if re.match(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _is_repetitive_query(self, query: str) -> bool:
        """Détecter si la requête est répétitive"""
        self.repetition_tracker[query] += 1
        
        # Plus de 3 fois la même requête = répétitif
        if self.repetition_tracker[query] > 3:
            return True
        
        # Vérifier similarité avec historique récent
        for historical_query in list(self.query_history)[-10:]:
            similarity = self._calculate_similarity(query, historical_query)
            if similarity > 0.8:  # 80% de similarité
                return True
        
        return False
    
    def _calculate_complexity_score(self, query: str) -> float:
        """Calculer le score de complexité d'une requête"""
        score = 0.0
        
        # Longueur (plus c'est long, plus c'est complexe)
        length_score = min(len(query.split()) / 20.0, 1.0)
        score += length_score * 0.3
        
        # Mots de complexité
        complexity_matches = 0
        for pattern in self.complexity_indicators:
            complexity_matches += len(re.findall(pattern, query, re.IGNORECASE))
        
        complexity_score = min(complexity_matches / 3.0, 1.0)
        score += complexity_score * 0.5
        
        # Questions (mots interrogatifs)
        question_words = ['quoi', 'qui', 'quand', 'où', 'comment', 'pourquoi', 'what', 'who', 'when', 'where', 'how', 'why']
        question_score = sum(1 for word in question_words if word in query) / len(question_words)
        score += question_score * 0.2
        
        return min(score, 1.0)
    
    def _should_engage_with_context(self, context: Dict) -> bool:
        """Décider si le contexte justifie l'engagement du LLM"""
        # Vérifier l'humeur/état de l'utilisateur
        user_mood = context.get('user_mood', 'neutral')
        if user_mood in ['frustrated', 'urgent']:
            return True
        
        # Vérifier l'historique récent
        recent_interactions = context.get('recent_interactions', 0)
        if recent_interactions > 10:  # Utilisateur très actif
            return False  # Éviter la surcharge
        
        # Vérifier le type de requête
        request_type = context.get('request_type', 'general')
        high_priority_types = ['task_execution', 'problem_solving', 'learning']
        
        return request_type in high_priority_types
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculer similarité simple entre deux textes"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _update_query_history(self, query: str):
        """Mettre à jour l'historique des requêtes"""
        self.query_history.append({
            'query': query,
            'timestamp': time.time()
        })
    
    def get_stats(self) -> Dict:
        """Obtenir les statistiques d'utilisation"""
        efficiency = (self.stats["llm_activations"] / self.stats["total_queries"]) * 100 if self.stats["total_queries"] > 0 else 0
        
        return {
            **self.stats,
            "efficiency_percentage": round(efficiency, 2),
            "filter_rate": round((self.stats["filtered_queries"] / self.stats["total_queries"]) * 100, 2) if self.stats["total_queries"] > 0 else 0
        }
    
    def _log_final_stats(self):
        """Logger les statistiques finales"""
        stats = self.get_stats()
        logger.info(f"📊 Métacognition Stats - Efficience: {stats['efficiency_percentage']}%, "
                   f"Requêtes filtrées: {stats['filter_rate']}%, "
                   f"Hallucinations: {stats['hallucinations_detected']}")
    
    async def self_optimize(self):
        """Auto-optimisation des seuils basée sur l'historique"""
        if len(self.response_quality_history) < 10:
            return
        
        # Analyser la qualité des réponses récentes
        avg_quality = np.mean(self.response_quality_history)
        
        # Ajuster les seuils selon la performance
        if avg_quality < 0.6:  # Qualité faible
            self.complexity_min_score *= 1.1  # Plus strict
            self.hallucination_threshold *= 0.9  # Plus sensible
        elif avg_quality > 0.8:  # Haute qualité
            self.complexity_min_score *= 0.95  # Moins strict
            self.hallucination_threshold *= 1.05  # Moins sensible
        
        # Garder dans les limites
        self.complexity_min_score = np.clip(self.complexity_min_score, 0.1, 0.8)
        self.hallucination_threshold = np.clip(self.hallucination_threshold, 0.3, 0.95)
        
        logger.info(f"🔧 Auto-optimisation: complexity={self.complexity_min_score:.2f}, "
                   f"hallucination={self.hallucination_threshold:.2f}")