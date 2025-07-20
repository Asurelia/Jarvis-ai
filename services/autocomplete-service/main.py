"""
🧠 Global Autocomplete Service - JARVIS 2025
Service d'autocomplétion globale intelligente avec détection de contexte
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Set
import uvicorn
import asyncio
import psutil
import time
import json
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import os
import platform
import logging
import httpx
import win32gui
import win32process
from collections import defaultdict, deque

# Configuration
SERVICE_PORT = 5007
API_VERSION = "2.0.0"
SYSTEM_OS = platform.system()

# Configuration intelligence
LEARNING_ENABLED = os.getenv("LEARNING_ENABLED", "true").lower() == "true"
CONTEXT_HISTORY_SIZE = int(os.getenv("CONTEXT_HISTORY_SIZE", "1000"))
SUGGESTION_LIMIT = int(os.getenv("SUGGESTION_LIMIT", "10"))

# Services JARVIS
BRAIN_API_URL = "http://brain-api:8080"
MCP_GATEWAY_URL = "http://mcp-gateway:5006"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="JARVIS Global Autocomplete Service",
    version=API_VERSION,
    description="Service d'autocomplétion globale intelligente avec IA"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContextType(str, Enum):
    TERMINAL = "terminal"
    CODE_EDITOR = "code_editor"
    BROWSER = "browser"
    TEXT_EDITOR = "text_editor"
    CHAT = "chat"
    EMAIL = "email"
    OFFICE = "office"
    UNKNOWN = "unknown"

class SuggestionType(str, Enum):
    COMMAND = "command"
    CODE = "code"
    TEXT = "text"
    FILE_PATH = "file_path"
    URL = "url"
    FUNCTION = "function"
    VARIABLE = "variable"
    SNIPPET = "snippet"

@dataclass
class ApplicationContext:
    process_name: str
    window_title: str
    context_type: ContextType
    language: Optional[str] = None
    project_path: Optional[str] = None
    file_extension: Optional[str] = None

@dataclass
class AutocompleteSuggestion:
    text: str
    type: SuggestionType
    confidence: float
    description: str
    insertText: str
    metadata: Dict[str, Any] = None

@dataclass
class UserPattern:
    context: ApplicationContext
    input_sequence: str
    completion: str
    frequency: int
    last_used: datetime

class ContextDetector:
    def __init__(self):
        self.app_patterns = {
            # Code editors
            'code.exe': ContextType.CODE_EDITOR,
            'cursor.exe': ContextType.CODE_EDITOR,
            'windsurf.exe': ContextType.CODE_EDITOR,
            'devenv.exe': ContextType.CODE_EDITOR,
            'idea64.exe': ContextType.CODE_EDITOR,
            'pycharm64.exe': ContextType.CODE_EDITOR,
            'notepad++.exe': ContextType.CODE_EDITOR,
            
            # Terminals
            'cmd.exe': ContextType.TERMINAL,
            'powershell.exe': ContextType.TERMINAL,
            'wt.exe': ContextType.TERMINAL,  # Windows Terminal
            'ubuntu.exe': ContextType.TERMINAL,
            'bash.exe': ContextType.TERMINAL,
            
            # Browsers
            'chrome.exe': ContextType.BROWSER,
            'firefox.exe': ContextType.BROWSER,
            'msedge.exe': ContextType.BROWSER,
            'brave.exe': ContextType.BROWSER,
            
            # Office
            'winword.exe': ContextType.OFFICE,
            'excel.exe': ContextType.OFFICE,
            'powerpnt.exe': ContextType.OFFICE,
            'onenote.exe': ContextType.OFFICE,
            
            # Text editors
            'notepad.exe': ContextType.TEXT_EDITOR,
            'wordpad.exe': ContextType.TEXT_EDITOR,
            
            # Chat/Communication
            'discord.exe': ContextType.CHAT,
            'teams.exe': ContextType.CHAT,
            'slack.exe': ContextType.CHAT,
            'telegram.exe': ContextType.CHAT,
        }
    
    def get_active_context(self) -> ApplicationContext:
        """Détecte le contexte de l'application active"""
        try:
            if SYSTEM_OS == "Windows":
                return self._get_windows_context()
            else:
                return self._get_unix_context()
        except Exception as e:
            logger.error(f"Context detection error: {e}")
            return ApplicationContext("unknown", "unknown", ContextType.UNKNOWN)
    
    def _get_windows_context(self) -> ApplicationContext:
        """Détecte le contexte sur Windows"""
        try:
            # Obtenir la fenêtre active
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            
            # Obtenir le processus
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name().lower()
            
            # Déterminer le type de contexte
            context_type = self.app_patterns.get(process_name, ContextType.UNKNOWN)
            
            # Analyser plus finement selon le type
            language = None
            file_extension = None
            project_path = None
            
            if context_type == ContextType.CODE_EDITOR:
                # Extraire l'extension du fichier depuis le titre
                if '.' in window_title:
                    parts = window_title.split('.')
                    if len(parts) > 1:
                        file_extension = '.' + parts[-1].split()[0]
                        language = self._get_language_from_extension(file_extension)
                
                # Tenter d'extraire le chemin du projet
                if '\\' in window_title or '/' in window_title:
                    project_path = self._extract_project_path(window_title)
            
            return ApplicationContext(
                process_name=process_name,
                window_title=window_title,
                context_type=context_type,
                language=language,
                project_path=project_path,
                file_extension=file_extension
            )
            
        except Exception as e:
            logger.error(f"Windows context detection error: {e}")
            return ApplicationContext("unknown", "unknown", ContextType.UNKNOWN)
    
    def _get_unix_context(self) -> ApplicationContext:
        """Détecte le contexte sur Unix/Linux/Mac"""
        # Implémentation simplifiée pour Unix
        return ApplicationContext("unknown", "unknown", ContextType.UNKNOWN)
    
    def _get_language_from_extension(self, extension: str) -> Optional[str]:
        """Détermine le langage de programmation depuis l'extension"""
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.sql': 'sql',
            '.sh': 'bash',
            '.ps1': 'powershell',
            '.bat': 'batch'
        }
        return lang_map.get(extension.lower())
    
    def _extract_project_path(self, window_title: str) -> Optional[str]:
        """Extrait le chemin du projet depuis le titre de la fenêtre"""
        # Logique d'extraction basique
        if ' - ' in window_title:
            parts = window_title.split(' - ')
            for part in parts:
                if '\\' in part or '/' in part:
                    return part.strip()
        return None

class LearningEngine:
    def __init__(self):
        self.user_patterns: Dict[str, UserPattern] = {}
        self.context_suggestions: Dict[str, List[AutocompleteSuggestion]] = defaultdict(list)
        self.recent_inputs = deque(maxlen=CONTEXT_HISTORY_SIZE)
        self.load_patterns()
    
    def learn_pattern(self, context: ApplicationContext, input_text: str, completion: str):
        """Apprend un nouveau pattern d'utilisation"""
        if not LEARNING_ENABLED:
            return
        
        pattern_key = f"{context.context_type}:{context.process_name}:{input_text}"
        
        if pattern_key in self.user_patterns:
            pattern = self.user_patterns[pattern_key]
            pattern.frequency += 1
            pattern.last_used = datetime.now()
        else:
            pattern = UserPattern(
                context=context,
                input_sequence=input_text,
                completion=completion,
                frequency=1,
                last_used=datetime.now()
            )
            self.user_patterns[pattern_key] = pattern
        
        # Ajouter à l'historique récent
        self.recent_inputs.append({
            'context': context,
            'input': input_text,
            'completion': completion,
            'timestamp': datetime.now()
        })
        
        # Sauvegarder périodiquement
        if len(self.user_patterns) % 50 == 0:
            self.save_patterns()
    
    def get_learned_suggestions(self, context: ApplicationContext, input_text: str) -> List[AutocompleteSuggestion]:
        """Récupère les suggestions basées sur l'apprentissage"""
        suggestions = []
        
        # Recherche par similarité dans les patterns
        for pattern_key, pattern in self.user_patterns.items():
            if (pattern.context.context_type == context.context_type and
                pattern.input_sequence.startswith(input_text) and
                len(pattern.input_sequence) > len(input_text)):
                
                confidence = min(0.9, pattern.frequency * 0.1)
                
                suggestion = AutocompleteSuggestion(
                    text=pattern.completion,
                    type=SuggestionType.TEXT,
                    confidence=confidence,
                    description=f"Learned pattern (used {pattern.frequency} times)",
                    insertText=pattern.completion
                )
                suggestions.append(suggestion)
        
        # Trier par confiance et fréquence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:5]  # Top 5 suggestions apprises
    
    def save_patterns(self):
        """Sauvegarde les patterns appris"""
        try:
            patterns_data = {}
            for key, pattern in self.user_patterns.items():
                patterns_data[key] = {
                    'context': asdict(pattern.context),
                    'input_sequence': pattern.input_sequence,
                    'completion': pattern.completion,
                    'frequency': pattern.frequency,
                    'last_used': pattern.last_used.isoformat()
                }
            
            with open('/app/cache/learned_patterns.json', 'w') as f:
                json.dump(patterns_data, f, indent=2)
            
            logger.info(f"Saved {len(patterns_data)} learned patterns")
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def load_patterns(self):
        """Charge les patterns sauvegardés"""
        try:
            if os.path.exists('/app/cache/learned_patterns.json'):
                with open('/app/cache/learned_patterns.json', 'r') as f:
                    patterns_data = json.load(f)
                
                for key, data in patterns_data.items():
                    context = ApplicationContext(**data['context'])
                    pattern = UserPattern(
                        context=context,
                        input_sequence=data['input_sequence'],
                        completion=data['completion'],
                        frequency=data['frequency'],
                        last_used=datetime.fromisoformat(data['last_used'])
                    )
                    self.user_patterns[key] = pattern
                
                logger.info(f"Loaded {len(patterns_data)} learned patterns")
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")

class IntelligentAutocomplete:
    def __init__(self):
        self.context_detector = ContextDetector()
        self.learning_engine = LearningEngine()
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def get_suggestions(self, input_text: str, max_suggestions: int = SUGGESTION_LIMIT) -> List[AutocompleteSuggestion]:
        """Génère des suggestions d'autocomplétion intelligentes"""
        context = self.context_detector.get_active_context()
        suggestions = []
        
        # 1. Suggestions apprises
        learned_suggestions = self.learning_engine.get_learned_suggestions(context, input_text)
        suggestions.extend(learned_suggestions)
        
        # 2. Suggestions contextuelles
        context_suggestions = await self._get_context_suggestions(context, input_text)
        suggestions.extend(context_suggestions)
        
        # 3. Suggestions IA
        if len(suggestions) < max_suggestions:
            ai_suggestions = await self._get_ai_suggestions(context, input_text)
            suggestions.extend(ai_suggestions)
        
        # Déduplication et tri
        unique_suggestions = self._deduplicate_suggestions(suggestions)
        unique_suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_suggestions[:max_suggestions]
    
    async def _get_context_suggestions(self, context: ApplicationContext, input_text: str) -> List[AutocompleteSuggestion]:
        """Génère des suggestions basées sur le contexte"""
        suggestions = []
        
        if context.context_type == ContextType.TERMINAL:
            suggestions.extend(self._get_terminal_suggestions(input_text))
        elif context.context_type == ContextType.CODE_EDITOR:
            suggestions.extend(await self._get_code_suggestions(context, input_text))
        elif context.context_type == ContextType.BROWSER:
            suggestions.extend(self._get_browser_suggestions(input_text))
        
        return suggestions
    
    def _get_terminal_suggestions(self, input_text: str) -> List[AutocompleteSuggestion]:
        """Suggestions pour terminal"""
        common_commands = [
            "ls", "cd", "mkdir", "rmdir", "cp", "mv", "rm", "cat", "grep", "find",
            "git", "python", "pip", "npm", "docker", "kubectl", "ssh", "scp",
            "ps", "kill", "top", "htop", "df", "du", "free", "uname", "whoami"
        ]
        
        suggestions = []
        for cmd in common_commands:
            if cmd.startswith(input_text.lower()):
                suggestions.append(AutocompleteSuggestion(
                    text=cmd,
                    type=SuggestionType.COMMAND,
                    confidence=0.8,
                    description=f"Terminal command: {cmd}",
                    insertText=cmd
                ))
        
        return suggestions
    
    async def _get_code_suggestions(self, context: ApplicationContext, input_text: str) -> List[AutocompleteSuggestion]:
        """Suggestions pour éditeur de code"""
        suggestions = []
        
        if context.language:
            # Suggestions spécifiques au langage
            if context.language == 'python':
                python_keywords = [
                    "def", "class", "import", "from", "if", "elif", "else",
                    "for", "while", "try", "except", "finally", "with", "as",
                    "return", "yield", "break", "continue", "pass", "raise"
                ]
                
                for keyword in python_keywords:
                    if keyword.startswith(input_text.lower()):
                        suggestions.append(AutocompleteSuggestion(
                            text=keyword,
                            type=SuggestionType.CODE,
                            confidence=0.7,
                            description=f"Python keyword: {keyword}",
                            insertText=keyword
                        ))
            
            elif context.language == 'javascript':
                js_keywords = [
                    "function", "const", "let", "var", "if", "else", "for",
                    "while", "do", "switch", "case", "break", "continue",
                    "return", "try", "catch", "finally", "throw", "async", "await"
                ]
                
                for keyword in js_keywords:
                    if keyword.startswith(input_text.lower()):
                        suggestions.append(AutocompleteSuggestion(
                            text=keyword,
                            type=SuggestionType.CODE,
                            confidence=0.7,
                            description=f"JavaScript keyword: {keyword}",
                            insertText=keyword
                        ))
        
        return suggestions
    
    def _get_browser_suggestions(self, input_text: str) -> List[AutocompleteSuggestion]:
        """Suggestions pour navigateur"""
        if input_text.startswith('http'):
            return [AutocompleteSuggestion(
                text="https://",
                type=SuggestionType.URL,
                confidence=0.9,
                description="HTTPS URL",
                insertText="https://"
            )]
        return []
    
    async def _get_ai_suggestions(self, context: ApplicationContext, input_text: str) -> List[AutocompleteSuggestion]:
        """Suggestions générées par IA"""
        try:
            # Appel au brain-api pour suggestions IA
            response = await self.http_client.post(
                f"{BRAIN_API_URL}/chat",
                json={
                    "message": f"Provide autocompletion suggestions for: '{input_text}' in context: {context.context_type.value}",
                    "context": {
                        "type": "autocomplete",
                        "application": context.process_name,
                        "language": context.language
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                # Parser la réponse IA pour extraire les suggestions
                # Format attendu: liste de suggestions
                return self._parse_ai_suggestions(result.get('response', ''))
        except Exception as e:
            logger.debug(f"AI suggestions error: {e}")
        
        return []
    
    def _parse_ai_suggestions(self, ai_response: str) -> List[AutocompleteSuggestion]:
        """Parse la réponse IA pour extraire les suggestions"""
        # Implémentation basique - peut être améliorée
        suggestions = []
        lines = ai_response.split('\n')
        
        for line in lines[:5]:  # Max 5 suggestions IA
            line = line.strip()
            if line and not line.startswith('#'):
                suggestions.append(AutocompleteSuggestion(
                    text=line,
                    type=SuggestionType.TEXT,
                    confidence=0.6,
                    description="AI generated suggestion",
                    insertText=line
                ))
        
        return suggestions
    
    def _deduplicate_suggestions(self, suggestions: List[AutocompleteSuggestion]) -> List[AutocompleteSuggestion]:
        """Élimine les suggestions dupliquées"""
        seen = set()
        unique = []
        
        for suggestion in suggestions:
            key = (suggestion.text, suggestion.type)
            if key not in seen:
                seen.add(key)
                unique.append(suggestion)
        
        return unique
    
    async def close(self):
        """Ferme les ressources"""
        await self.http_client.aclose()

# Instance globale
autocomplete_engine = IntelligentAutocomplete()

# Modèles Pydantic
class AutocompleteRequest(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=200)
    max_suggestions: int = Field(SUGGESTION_LIMIT, ge=1, le=20)
    context_override: Optional[Dict[str, Any]] = None

class LearnPatternRequest(BaseModel):
    input_text: str
    completion: str
    context_info: Optional[Dict[str, Any]] = None

# Routes API
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Global Autocomplete Service",
        "version": API_VERSION,
        "os": SYSTEM_OS,
        "learning_enabled": LEARNING_ENABLED,
        "patterns_learned": len(autocomplete_engine.learning_engine.user_patterns),
        "timestamp": time.time()
    }

@app.post("/autocomplete")
async def get_autocomplete(request: AutocompleteRequest):
    """Récupère les suggestions d'autocomplétion"""
    try:
        suggestions = await autocomplete_engine.get_suggestions(
            request.input_text,
            request.max_suggestions
        )
        
        return {
            "success": True,
            "input_text": request.input_text,
            "suggestions": [asdict(s) for s in suggestions],
            "count": len(suggestions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        raise HTTPException(500, f"Failed to get suggestions: {str(e)}")

@app.get("/context")
async def get_current_context():
    """Récupère le contexte actuel de l'application"""
    context = autocomplete_engine.context_detector.get_active_context()
    return {
        "success": True,
        "context": asdict(context),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/learn")
async def learn_pattern(request: LearnPatternRequest):
    """Apprend un nouveau pattern d'utilisation"""
    if not LEARNING_ENABLED:
        raise HTTPException(400, "Learning is disabled")
    
    context = autocomplete_engine.context_detector.get_active_context()
    autocomplete_engine.learning_engine.learn_pattern(
        context,
        request.input_text,
        request.completion
    )
    
    return {
        "success": True,
        "message": "Pattern learned successfully",
        "patterns_count": len(autocomplete_engine.learning_engine.user_patterns)
    }

@app.get("/patterns")
async def get_learned_patterns():
    """Récupère les patterns appris"""
    patterns = []
    for pattern in autocomplete_engine.learning_engine.user_patterns.values():
        patterns.append({
            "context_type": pattern.context.context_type.value,
            "input_sequence": pattern.input_sequence,
            "completion": pattern.completion,
            "frequency": pattern.frequency,
            "last_used": pattern.last_used.isoformat()
        })
    
    return {
        "success": True,
        "patterns": patterns,
        "total": len(patterns)
    }

@app.delete("/patterns")
async def clear_learned_patterns():
    """Efface tous les patterns appris"""
    autocomplete_engine.learning_engine.user_patterns.clear()
    try:
        os.remove('/app/cache/learned_patterns.json')
    except FileNotFoundError:
        pass
    
    return {
        "success": True,
        "message": "All learned patterns cleared"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour autocomplétion temps réel"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "autocomplete":
                input_text = data.get("input_text", "")
                max_suggestions = data.get("max_suggestions", SUGGESTION_LIMIT)
                
                if input_text:
                    suggestions = await autocomplete_engine.get_suggestions(
                        input_text, max_suggestions
                    )
                    
                    await websocket.send_json({
                        "type": "suggestions",
                        "input_text": input_text,
                        "suggestions": [asdict(s) for s in suggestions]
                    })
            
            elif data.get("type") == "learn":
                input_text = data.get("input_text", "")
                completion = data.get("completion", "")
                
                if input_text and completion and LEARNING_ENABLED:
                    context = autocomplete_engine.context_detector.get_active_context()
                    autocomplete_engine.learning_engine.learn_pattern(
                        context, input_text, completion
                    )
                    
                    await websocket.send_json({
                        "type": "learned",
                        "success": True
                    })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        pass

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage à l'arrêt"""
    autocomplete_engine.learning_engine.save_patterns()
    await autocomplete_engine.close()

if __name__ == "__main__":
    logger.info(f"Starting Global Autocomplete Service on port {SERVICE_PORT}")
    logger.info(f"Learning enabled: {LEARNING_ENABLED}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=False
    )