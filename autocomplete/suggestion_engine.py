"""
Moteur de suggestions intelligent pour l'autocomplétion JARVIS
Cache LRU, prédiction préemptive et apprentissage des patterns
"""
import asyncio
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
import string
import re
from pathlib import Path
from loguru import logger

@dataclass
class SuggestionContext:
    """Contexte pour une suggestion"""
    word: str
    app_name: str
    field_type: str
    language: str
    line_context: str
    previous_words: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

@dataclass
class Suggestion:
    """Représentation d'une suggestion"""
    text: str
    confidence: float
    source: str  # "ai", "cache", "patterns", "dictionary"
    context_score: float = 0.0
    usage_count: int = 0
    last_used: float = field(default_factory=time.time)
    
    @property
    def total_score(self) -> float:
        """Score total combiné"""
        recency_bonus = max(0, 1.0 - (time.time() - self.last_used) / 86400)  # Bonus sur 24h
        usage_bonus = min(0.3, self.usage_count * 0.01)  # Bonus usage plafonné
        
        return self.confidence + self.context_score + recency_bonus + usage_bonus

class LRUCache:
    """Cache LRU optimisé pour les suggestions"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, List[Suggestion]] = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_key(self, context: SuggestionContext) -> str:
        """Génère une clé de cache basée sur le contexte"""
        # Clé hiérarchique: app_type_word pour permettre des matches partiels
        return f"{context.app_name}:{context.field_type}:{context.word.lower()}"
    
    def get(self, context: SuggestionContext) -> Optional[List[Suggestion]]:
        """Récupère les suggestions du cache"""
        key = self._generate_key(context)
        
        if key in self.cache:
            # Déplacer en fin (LRU)
            suggestions = self.cache.pop(key)
            self.cache[key] = suggestions
            self.hit_count += 1
            
            # Mettre à jour les scores contextuels
            for suggestion in suggestions:
                suggestion.context_score = self._calculate_context_score(suggestion, context)
            
            return sorted(suggestions, key=lambda s: s.total_score, reverse=True)
        
        # Essayer des clés partielles
        partial_matches = self._find_partial_matches(context)
        if partial_matches:
            self.hit_count += 1
            return partial_matches
        
        self.miss_count += 1
        return None
    
    def _find_partial_matches(self, context: SuggestionContext) -> Optional[List[Suggestion]]:
        """Trouve des correspondances partielles dans le cache"""
        word = context.word.lower()
        app = context.app_name
        field_type = context.field_type
        
        matches = []
        
        # Chercher des suggestions pour des mots similaires
        for cached_key, suggestions in self.cache.items():
            cached_app, cached_type, cached_word = cached_key.split(':', 2)
            
            # Correspondance d'application et de type
            if cached_app == app and cached_type == field_type:
                # Le mot en cache commence par le mot actuel
                if cached_word.startswith(word) and len(cached_word) > len(word):
                    for suggestion in suggestions:
                        if suggestion.text.lower().startswith(word):
                            # Ajuster le score pour la correspondance partielle
                            suggestion.context_score = 0.8  # Score réduit pour correspondance partielle
                            matches.append(suggestion)
        
        if matches:
            return sorted(matches, key=lambda s: s.total_score, reverse=True)[:5]
        
        return None
    
    def put(self, context: SuggestionContext, suggestions: List[Suggestion]):
        """Ajoute des suggestions au cache"""
        key = self._generate_key(context)
        
        # Fusionner avec les suggestions existantes
        existing = self.cache.get(key, [])
        
        # Créer un dictionnaire pour éviter les doublons
        suggestion_dict = {s.text: s for s in existing}
        
        for new_suggestion in suggestions:
            if new_suggestion.text in suggestion_dict:
                # Mettre à jour la suggestion existante
                existing_suggestion = suggestion_dict[new_suggestion.text]
                existing_suggestion.confidence = max(existing_suggestion.confidence, new_suggestion.confidence)
                existing_suggestion.usage_count += 1
                existing_suggestion.last_used = time.time()
            else:
                suggestion_dict[new_suggestion.text] = new_suggestion
        
        # Garder les meilleures suggestions
        merged_suggestions = list(suggestion_dict.values())
        merged_suggestions.sort(key=lambda s: s.total_score, reverse=True)
        
        self.cache[key] = merged_suggestions[:10]  # Limite par clé
        
        # Nettoyer si nécessaire
        if len(self.cache) > self.max_size:
            # Supprimer les plus anciens
            for _ in range(len(self.cache) - int(self.max_size * 0.8)):
                self.cache.popitem(last=False)
    
    def _calculate_context_score(self, suggestion: Suggestion, context: SuggestionContext) -> float:
        """Calcule le score contextuel d'une suggestion"""
        score = 0.0
        
        # Bonus pour correspondance exacte du type de champ
        if suggestion.source == "patterns":
            score += 0.2
        
        # Bonus pour correspondance de longueur similaire
        length_diff = abs(len(suggestion.text) - len(context.word))
        if length_diff <= 2:
            score += 0.1
        
        # Bonus pour contexte de ligne similaire
        if context.line_context and len(context.line_context) > 10:
            # Simple heuristique basée sur les mots communs
            suggestion_words = set(suggestion.text.lower().split())
            context_words = set(context.line_context.lower().split())
            
            if suggestion_words & context_words:
                score += 0.15
        
        return min(score, 0.5)  # Plafonner le score contextuel
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "max_size": self.max_size
        }

class PatternLearner:
    """Apprend les patterns de frappe de l'utilisateur"""
    
    def __init__(self):
        self.patterns = defaultdict(lambda: defaultdict(int))  # app -> {word: count}
        self.transitions = defaultdict(lambda: defaultdict(int))  # word -> {next_word: count}
        self.field_patterns = defaultdict(lambda: defaultdict(int))  # field_type -> {word: count}
        
    def learn_pattern(self, context: SuggestionContext, accepted_suggestion: str):
        """Apprend un nouveau pattern à partir d'une suggestion acceptée"""
        app = context.app_name
        field_type = context.field_type
        word = context.word
        
        # Enregistrer le pattern par application
        self.patterns[app][accepted_suggestion] += 1
        
        # Enregistrer le pattern par type de champ
        self.field_patterns[field_type][accepted_suggestion] += 1
        
        # Enregistrer les transitions de mots
        if context.previous_words:
            prev_word = context.previous_words[-1]
            self.transitions[prev_word][accepted_suggestion] += 1
    
    def get_pattern_suggestions(self, context: SuggestionContext, max_suggestions: int = 5) -> List[Suggestion]:
        """Génère des suggestions basées sur les patterns appris"""
        suggestions = []
        word = context.word.lower()
        
        # Suggestions basées sur l'application
        app_patterns = self.patterns.get(context.app_name, {})
        for pattern, count in app_patterns.items():
            if pattern.lower().startswith(word) and len(pattern) > len(word):
                confidence = min(0.9, count / 100.0)  # Normaliser
                suggestion = Suggestion(
                    text=pattern,
                    confidence=confidence,
                    source="patterns",
                    usage_count=count
                )
                suggestions.append(suggestion)
        
        # Suggestions basées sur le type de champ
        field_patterns = self.field_patterns.get(context.field_type, {})
        for pattern, count in field_patterns.items():
            if pattern.lower().startswith(word) and len(pattern) > len(word):
                # Éviter les doublons
                if not any(s.text == pattern for s in suggestions):
                    confidence = min(0.8, count / 50.0)
                    suggestion = Suggestion(
                        text=pattern,
                        confidence=confidence,
                        source="patterns",
                        usage_count=count
                    )
                    suggestions.append(suggestion)
        
        # Suggestions basées sur les transitions
        if context.previous_words:
            prev_word = context.previous_words[-1]
            transitions = self.transitions.get(prev_word, {})
            
            for next_word, count in transitions.items():
                if next_word.lower().startswith(word) and len(next_word) > len(word):
                    if not any(s.text == next_word for s in suggestions):
                        confidence = min(0.85, count / 20.0)
                        suggestion = Suggestion(
                            text=next_word,
                            confidence=confidence,
                            source="patterns",
                            usage_count=count
                        )
                        suggestions.append(suggestion)
        
        # Trier par score et limiter
        suggestions.sort(key=lambda s: s.total_score, reverse=True)
        return suggestions[:max_suggestions]
    
    def save_patterns(self, filepath: str):
        """Sauvegarde les patterns appris"""
        try:
            data = {
                "patterns": dict(self.patterns),
                "transitions": dict(self.transitions),
                "field_patterns": dict(self.field_patterns)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Patterns sauvegardés: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde patterns: {e}")
    
    def load_patterns(self, filepath: str):
        """Charge les patterns depuis un fichier"""
        try:
            if not Path(filepath).exists():
                logger.info("📁 Aucun fichier de patterns existant")
                return
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.patterns = defaultdict(lambda: defaultdict(int), data.get("patterns", {}))
            self.transitions = defaultdict(lambda: defaultdict(int), data.get("transitions", {}))
            self.field_patterns = defaultdict(lambda: defaultdict(int), data.get("field_patterns", {}))
            
            total_patterns = sum(len(patterns) for patterns in self.patterns.values())
            logger.success(f"📚 {total_patterns} patterns chargés depuis {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement patterns: {e}")

class DictionarySuggestions:
    """Générateur de suggestions basé sur un dictionnaire"""
    
    def __init__(self):
        self.dictionaries = {
            "fr": set(),
            "en": set()
        }
        self.loaded = False
    
    def load_dictionaries(self):
        """Charge les dictionnaires de base"""
        try:
            # Dictionnaire français de base
            french_words = [
                "bonjour", "merci", "comment", "pourquoi", "parce", "toujours",
                "jamais", "peut-être", "certainement", "probablement", "évidemment",
                "naturellement", "effectivement", "absolument", "exactement",
                "simplement", "rapidement", "facilement", "difficilement",
                "application", "ordinateur", "internet", "navigation", "recherche",
                "fichier", "dossier", "document", "télécharger", "installer"
            ]
            
            # Dictionnaire anglais de base
            english_words = [
                "hello", "thank", "thanks", "please", "welcome", "application",
                "computer", "internet", "website", "download", "install",
                "document", "folder", "search", "navigation", "function",
                "development", "programming", "software", "hardware", "system"
            ]
            
            self.dictionaries["fr"].update(french_words)
            self.dictionaries["en"].update(english_words)
            
            self.loaded = True
            logger.info(f"📖 Dictionnaires chargés: {len(french_words)} mots FR, {len(english_words)} mots EN")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement dictionnaires: {e}")
    
    def get_dictionary_suggestions(self, context: SuggestionContext, max_suggestions: int = 3) -> List[Suggestion]:
        """Génère des suggestions basées sur le dictionnaire"""
        if not self.loaded:
            return []
        
        suggestions = []
        word = context.word.lower()
        language = context.language
        
        if language in self.dictionaries:
            dictionary = self.dictionaries[language]
            
            for dict_word in dictionary:
                if dict_word.startswith(word) and len(dict_word) > len(word):
                    # Calculer la confiance basée sur la fréquence d'usage supposée
                    confidence = 0.6 if len(dict_word) - len(word) <= 3 else 0.4
                    
                    suggestion = Suggestion(
                        text=dict_word,
                        confidence=confidence,
                        source="dictionary"
                    )
                    suggestions.append(suggestion)
        
        # Trier par longueur (préférer les completions plus courtes)
        suggestions.sort(key=lambda s: len(s.text))
        return suggestions[:max_suggestions]

class SuggestionEngine:
    """Moteur de suggestions principal"""
    
    def __init__(self, ollama_service=None, cache_size: int = 1000):
        self.ollama_service = ollama_service
        self.cache = LRUCache(cache_size)
        self.pattern_learner = PatternLearner()
        self.dictionary = DictionarySuggestions()
        
        # Configuration
        self.patterns_file = "cache/suggestion_patterns.json"
        
        # Statistiques
        self.stats = {
            "suggestions_generated": 0,
            "ai_suggestions": 0,
            "cache_suggestions": 0,
            "pattern_suggestions": 0,
            "dictionary_suggestions": 0
        }
        
        logger.info("💡 Moteur de suggestions initialisé")
    
    async def initialize(self):
        """Initialise le moteur de suggestions"""
        try:
            # Créer le dossier cache
            Path("cache").mkdir(exist_ok=True)
            
            # Charger les patterns
            self.pattern_learner.load_patterns(self.patterns_file)
            
            # Charger les dictionnaires
            self.dictionary.load_dictionaries()
            
            logger.success("✅ Moteur de suggestions prêt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation moteur: {e}")
            return False
    
    async def generate_suggestions(self, context: SuggestionContext, max_suggestions: int = 5) -> List[Suggestion]:
        """Génère des suggestions pour un contexte donné"""
        self.stats["suggestions_generated"] += 1
        
        all_suggestions = []
        
        # 1. Vérifier le cache
        cached_suggestions = self.cache.get(context)
        if cached_suggestions:
            all_suggestions.extend(cached_suggestions[:3])
            self.stats["cache_suggestions"] += 1
        
        # 2. Générer avec les patterns appris
        pattern_suggestions = self.pattern_learner.get_pattern_suggestions(context, 3)
        if pattern_suggestions:
            all_suggestions.extend(pattern_suggestions)
            self.stats["pattern_suggestions"] += 1
        
        # 3. Générer avec le dictionnaire
        dict_suggestions = self.dictionary.get_dictionary_suggestions(context, 2)
        if dict_suggestions:
            all_suggestions.extend(dict_suggestions)
            self.stats["dictionary_suggestions"] += 1
        
        # 4. Générer avec l'IA si disponible et si pas assez de suggestions
        if len(all_suggestions) < max_suggestions and self.ollama_service:
            ai_suggestions = await self._generate_ai_suggestions(context, max_suggestions - len(all_suggestions))
            if ai_suggestions:
                all_suggestions.extend(ai_suggestions)
                self.stats["ai_suggestions"] += 1
        
        # Éliminer les doublons et trier par score
        unique_suggestions = self._deduplicate_suggestions(all_suggestions)
        unique_suggestions.sort(key=lambda s: s.total_score, reverse=True)
        
        # Limiter et mettre en cache
        final_suggestions = unique_suggestions[:max_suggestions]
        
        if final_suggestions:
            self.cache.put(context, final_suggestions)
        
        logger.debug(f"💡 {len(final_suggestions)} suggestions générées pour '{context.word}'")
        return final_suggestions
    
    async def _generate_ai_suggestions(self, context: SuggestionContext, max_suggestions: int) -> List[Suggestion]:
        """Génère des suggestions avec l'IA"""
        try:
            # Préparer le prompt pour l'autocomplétion
            prompt = f"""Complète le mot '{context.word}' dans ce contexte:
Application: {context.app_name}
Type de champ: {context.field_type}
Contexte: {context.line_context}

Donne {max_suggestions} suggestions de complétion naturelles et utiles.
Format: suggestion1,suggestion2,suggestion3
Seulement les completions, pas d'explication."""
            
            response = await self.ollama_service.autocomplete_text(context.word, prompt)
            
            if response.success and response.content:
                # Parser les suggestions
                suggestions_text = response.content.strip()
                suggestion_texts = [s.strip() for s in suggestions_text.split(',')]
                
                suggestions = []
                for text in suggestion_texts:
                    if text and len(text) > len(context.word):
                        suggestion = Suggestion(
                            text=text,
                            confidence=0.8,  # Confiance élevée pour l'IA
                            source="ai"
                        )
                        suggestions.append(suggestion)
                
                return suggestions
            
        except Exception as e:
            logger.debug(f"Erreur génération IA: {e}")
        
        return []
    
    def _deduplicate_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Élimine les doublons en gardant les meilleures"""
        seen = {}
        
        for suggestion in suggestions:
            text_lower = suggestion.text.lower()
            
            if text_lower not in seen or suggestion.total_score > seen[text_lower].total_score:
                seen[text_lower] = suggestion
        
        return list(seen.values())
    
    def learn_from_acceptance(self, context: SuggestionContext, accepted_suggestion: str):
        """Apprend d'une suggestion acceptée"""
        try:
            # Enseigner au pattern learner
            self.pattern_learner.learn_pattern(context, accepted_suggestion)
            
            # Sauvegarder périodiquement
            if self.stats["suggestions_generated"] % 50 == 0:
                self.save_patterns()
            
            logger.debug(f"📚 Pattern appris: '{context.word}' -> '{accepted_suggestion}'")
            
        except Exception as e:
            logger.error(f"❌ Erreur apprentissage: {e}")
    
    def save_patterns(self):
        """Sauvegarde les patterns appris"""
        self.pattern_learner.save_patterns(self.patterns_file)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du moteur"""
        stats = self.stats.copy()
        stats["cache"] = self.cache.get_stats()
        
        # Calculer les pourcentages
        total = stats["suggestions_generated"]
        if total > 0:
            stats["ai_percentage"] = stats["ai_suggestions"] / total
            stats["cache_percentage"] = stats["cache_suggestions"] / total
            stats["pattern_percentage"] = stats["pattern_suggestions"] / total
            stats["dictionary_percentage"] = stats["dictionary_suggestions"] / total
        
        return stats
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.stats = {
            "suggestions_generated": 0,
            "ai_suggestions": 0,
            "cache_suggestions": 0,
            "pattern_suggestions": 0,
            "dictionary_suggestions": 0
        }
        logger.info("📊 Statistiques moteur remises à zéro")

# Fonctions utilitaires
async def test_suggestion_engine(ollama_service=None) -> bool:
    """Test du moteur de suggestions"""
    try:
        engine = SuggestionEngine(ollama_service)
        
        if not await engine.initialize():
            return False
        
        # Contextes de test
        test_contexts = [
            SuggestionContext(
                word="bonjour",
                app_name="notepad.exe",
                field_type="text",
                language="fr",
                line_context="Salut, bonjour"
            ),
            SuggestionContext(
                word="appl",
                app_name="chrome.exe",
                field_type="text",
                language="fr",
                line_context="L'appl"
            ),
            SuggestionContext(
                word="dev",
                app_name="vscode.exe",
                field_type="code",
                language="en",
                line_context="function dev"
            )
        ]
        
        for i, context in enumerate(test_contexts):
            logger.info(f"🧪 Test {i+1}: '{context.word}' dans {context.app_name}")
            
            suggestions = await engine.generate_suggestions(context)
            
            if suggestions:
                logger.info(f"💡 Suggestions générées:")
                for j, suggestion in enumerate(suggestions):
                    logger.info(f"  {j+1}. {suggestion.text} (score: {suggestion.total_score:.2f}, source: {suggestion.source})")
                
                # Simuler l'acceptation de la première suggestion
                engine.learn_from_acceptance(context, suggestions[0].text)
            else:
                logger.warning("⚠️ Aucune suggestion générée")
        
        # Afficher les statistiques
        stats = engine.get_stats()
        logger.info(f"📊 Statistiques finales:")
        logger.info(f"  - Total: {stats['suggestions_generated']}")
        logger.info(f"  - Cache: {stats['cache_suggestions']}")
        logger.info(f"  - Patterns: {stats['pattern_suggestions']}")
        logger.info(f"  - Dictionnaire: {stats['dictionary_suggestions']}")
        logger.info(f"  - IA: {stats['ai_suggestions']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test moteur: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_suggestion_engine())