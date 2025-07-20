"""
💻 Terminal Service - JARVIS 2025
Service de terminal intelligent avec autocomplétion IA et sessions persistantes
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Set
import uvicorn
import asyncio
import subprocess
import os
import platform
import json
import time
import uuid
import shlex
import signal
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import logging
import threading
import queue
from dataclasses import dataclass, asdict
from enum import Enum
import re

# Configuration
SYSTEM_OS = platform.system()
SERVICE_PORT = 5005
API_VERSION = "2.0.0"
MAX_SESSIONS = int(os.getenv("MAX_TERMINAL_SESSIONS", "10"))
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

# Configuration sécurité
DANGEROUS_COMMANDS = {
    'rm', 'del', 'format', 'fdisk', 'mkfs', 'dd', 'sudo rm', 'sudo dd',
    'sudo fdisk', 'sudo mkfs', 'shutdown', 'reboot', 'halt', 'poweroff'
}

RESTRICTED_PATHS = {
    '/etc', '/boot', '/sys', '/proc', 'C:\\Windows', 'C:\\System32',
    '/usr/bin', '/usr/sbin', '/sbin', '/bin'
}

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="JARVIS Terminal Service",
    version=API_VERSION,
    description="Service de terminal intelligent avec IA et sécurité"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

class CommandType(str, Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    TERMINATED = "terminated"
    ERROR = "error"

@dataclass
class CommandHistory:
    command: str
    timestamp: datetime
    exit_code: int
    output: str
    working_dir: str
    execution_time: float

@dataclass
class AutocompleteOption:
    text: str
    type: str  # command, file, directory, option
    description: str
    confidence: float

class TerminalSession:
    def __init__(self, session_id: str, working_dir: str = None):
        self.session_id = session_id
        self.working_dir = working_dir or os.getcwd()
        self.status = SessionStatus.ACTIVE
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.history: List[CommandHistory] = []
        self.environment = dict(os.environ)
        self.process = None
        self.websocket_connections: Set[WebSocket] = set()
        
    def update_activity(self):
        self.last_activity = datetime.now()
        self.status = SessionStatus.ACTIVE
    
    def is_expired(self) -> bool:
        return (datetime.now() - self.last_activity).total_seconds() > SESSION_TIMEOUT * 60
    
    def add_to_history(self, command: str, exit_code: int, output: str, execution_time: float):
        entry = CommandHistory(
            command=command,
            timestamp=datetime.now(),
            exit_code=exit_code,
            output=output,
            working_dir=self.working_dir,
            execution_time=execution_time
        )
        self.history.append(entry)
        # Garder seulement les 100 dernières commandes
        if len(self.history) > 100:
            self.history = self.history[-100:]

class SecurityValidator:
    @staticmethod
    def classify_command(command: str) -> CommandType:
        """Classifie le niveau de dangerosité d'une commande"""
        command_lower = command.lower().strip()
        
        # Commandes bloquées
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in command_lower:
                return CommandType.BLOCKED
        
        # Commandes modérément risquées
        moderate_patterns = [
            r'sudo\s+', r'chmod\s+777', r'chown\s+', r'wget\s+', r'curl\s+.*\|\s*sh',
            r'pip\s+install', r'npm\s+install', r'git\s+clone'
        ]
        
        for pattern in moderate_patterns:
            if re.search(pattern, command_lower):
                return CommandType.MODERATE
        
        # Vérifier les chemins restreints
        for path in RESTRICTED_PATHS:
            if path.lower() in command_lower:
                return CommandType.DANGEROUS
        
        return CommandType.SAFE
    
    @staticmethod
    def validate_command(command: str, session: TerminalSession) -> bool:
        """Valide si une commande peut être exécutée"""
        command_type = SecurityValidator.classify_command(command)
        
        if command_type == CommandType.BLOCKED:
            raise HTTPException(403, f"Command blocked for security: {command}")
        
        if command_type == CommandType.DANGEROUS:
            logger.warning(f"Dangerous command attempted: {command}")
            # En mode production, on pourrait demander confirmation
            # return False
        
        return True

class IntelligentAutocomplete:
    def __init__(self):
        self.command_cache = {}
        self.file_cache = {}
        self.load_common_commands()
    
    def load_common_commands(self):
        """Charge les commandes communes selon l'OS"""
        if SYSTEM_OS == "Windows":
            self.common_commands = [
                "dir", "cd", "copy", "move", "del", "type", "echo", "set",
                "cls", "md", "rd", "attrib", "find", "findstr", "tasklist",
                "taskkill", "systeminfo", "ipconfig", "ping", "tracert"
            ]
        else:
            self.common_commands = [
                "ls", "cd", "cp", "mv", "rm", "cat", "echo", "export",
                "clear", "mkdir", "rmdir", "chmod", "chown", "find", "grep",
                "ps", "kill", "top", "df", "du", "free", "uname", "whoami",
                "git", "python", "pip", "npm", "docker", "kubectl"
            ]
    
    def get_completions(self, partial_command: str, working_dir: str, 
                       session: TerminalSession) -> List[AutocompleteOption]:
        """Génère les suggestions d'autocomplétion"""
        options = []
        
        # Complétion de commandes
        if ' ' not in partial_command:
            command_options = self._complete_commands(partial_command)
            options.extend(command_options)
        
        # Complétion de fichiers/dossiers
        file_options = self._complete_files(partial_command, working_dir)
        options.extend(file_options)
        
        # Complétion basée sur l'historique
        history_options = self._complete_from_history(partial_command, session)
        options.extend(history_options)
        
        # Complétion intelligente basée sur le contexte
        smart_options = self._smart_completion(partial_command, session)
        options.extend(smart_options)
        
        # Trier par confiance et retourner les 10 meilleurs
        options.sort(key=lambda x: x.confidence, reverse=True)
        return options[:10]
    
    def _complete_commands(self, partial: str) -> List[AutocompleteOption]:
        """Autocomplétion des commandes"""
        options = []
        for cmd in self.common_commands:
            if cmd.startswith(partial.lower()):
                confidence = 0.9 if cmd == partial.lower() else 0.7
                options.append(AutocompleteOption(
                    text=cmd,
                    type="command",
                    description=f"Command: {cmd}",
                    confidence=confidence
                ))
        return options
    
    def _complete_files(self, partial: str, working_dir: str) -> List[AutocompleteOption]:
        """Autocomplétion des fichiers et dossiers"""
        options = []
        try:
            # Extraire le chemin partiel
            parts = partial.split()
            if len(parts) == 0:
                return options
            
            last_part = parts[-1]
            dir_path = working_dir
            
            if '/' in last_part or '\\' in last_part:
                dir_path = os.path.dirname(os.path.join(working_dir, last_part))
                file_prefix = os.path.basename(last_part)
            else:
                file_prefix = last_part
            
            if os.path.exists(dir_path):
                for item in os.listdir(dir_path):
                    if item.startswith(file_prefix):
                        item_path = os.path.join(dir_path, item)
                        is_dir = os.path.isdir(item_path)
                        
                        options.append(AutocompleteOption(
                            text=item + ('/' if is_dir else ''),
                            type="directory" if is_dir else "file",
                            description=f"{'Directory' if is_dir else 'File'}: {item}",
                            confidence=0.8
                        ))
        except Exception as e:
            logger.debug(f"File completion error: {e}")
        
        return options
    
    def _complete_from_history(self, partial: str, session: TerminalSession) -> List[AutocompleteOption]:
        """Autocomplétion basée sur l'historique"""
        options = []
        for entry in reversed(session.history[-20:]):  # 20 dernières commandes
            if entry.command.startswith(partial) and entry.command != partial:
                options.append(AutocompleteOption(
                    text=entry.command,
                    type="history",
                    description=f"From history: {entry.timestamp.strftime('%H:%M')}",
                    confidence=0.6
                ))
        return options
    
    def _smart_completion(self, partial: str, session: TerminalSession) -> List[AutocompleteOption]:
        """Autocomplétion intelligente basée sur le contexte"""
        options = []
        
        # Suggestions contextuelles
        if partial.startswith('git '):
            git_commands = ['add', 'commit', 'push', 'pull', 'status', 'log', 'branch']
            sub_cmd = partial[4:]
            for cmd in git_commands:
                if cmd.startswith(sub_cmd):
                    options.append(AutocompleteOption(
                        text=f"git {cmd}",
                        type="git_command",
                        description=f"Git command: {cmd}",
                        confidence=0.8
                    ))
        
        elif partial.startswith('docker '):
            docker_commands = ['run', 'build', 'pull', 'push', 'ps', 'logs', 'exec']
            sub_cmd = partial[7:]
            for cmd in docker_commands:
                if cmd.startswith(sub_cmd):
                    options.append(AutocompleteOption(
                        text=f"docker {cmd}",
                        type="docker_command",
                        description=f"Docker command: {cmd}",
                        confidence=0.8
                    ))
        
        return options

class TerminalManager:
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}
        self.autocomplete = IntelligentAutocomplete()
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def create_session(self, working_dir: str = None) -> TerminalSession:
        """Crée une nouvelle session terminal"""
        if len(self.sessions) >= MAX_SESSIONS:
            # Nettoyer les sessions expirées
            self._cleanup_expired_sessions()
            if len(self.sessions) >= MAX_SESSIONS:
                raise HTTPException(429, "Maximum number of terminal sessions reached")
        
        session_id = str(uuid.uuid4())
        session = TerminalSession(session_id, working_dir)
        self.sessions[session_id] = session
        
        logger.info(f"Created terminal session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> TerminalSession:
        """Récupère une session par ID"""
        if session_id not in self.sessions:
            raise HTTPException(404, f"Terminal session not found: {session_id}")
        
        session = self.sessions[session_id]
        if session.is_expired():
            self.terminate_session(session_id)
            raise HTTPException(410, f"Terminal session expired: {session_id}")
        
        session.update_activity()
        return session
    
    def terminate_session(self, session_id: str):
        """Termine une session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.status = SessionStatus.TERMINATED
            
            # Fermer les connexions WebSocket
            for ws in session.websocket_connections.copy():
                try:
                    asyncio.create_task(ws.close())
                except:
                    pass
            
            # Tuer le processus s'il existe
            if session.process and session.process.poll() is None:
                try:
                    session.process.terminate()
                except:
                    pass
            
            del self.sessions[session_id]
            logger.info(f"Terminated terminal session: {session_id}")
    
    def _cleanup_expired_sessions(self):
        """Nettoie les sessions expirées"""
        while True:
            try:
                expired_sessions = [
                    sid for sid, session in self.sessions.items()
                    if session.is_expired()
                ]
                
                for session_id in expired_sessions:
                    self.terminate_session(session_id)
                
                time.sleep(60)  # Vérifier toutes les minutes
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                time.sleep(60)
    
    async def execute_command(self, session: TerminalSession, command: str) -> Dict:
        """Exécute une commande dans une session"""
        session.update_activity()
        
        # Validation de sécurité
        SecurityValidator.validate_command(command, session)
        
        start_time = time.time()
        
        try:
            # Préparation de la commande
            if SYSTEM_OS == "Windows":
                cmd_args = ["cmd", "/c", command]
            else:
                cmd_args = ["/bin/bash", "-c", command]
            
            # Exécution
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=session.working_dir,
                env=session.environment
            )
            
            stdout, _ = await process.communicate()
            execution_time = time.time() - start_time
            
            output = stdout.decode('utf-8', errors='replace')
            exit_code = process.returncode
            
            # Mise à jour du répertoire de travail si c'est une commande cd
            if command.strip().startswith('cd '):
                new_dir = command.strip()[3:].strip()
                if new_dir:
                    try:
                        new_path = os.path.abspath(os.path.join(session.working_dir, new_dir))
                        if os.path.exists(new_path) and os.path.isdir(new_path):
                            session.working_dir = new_path
                    except:
                        pass
            
            # Ajouter à l'historique
            session.add_to_history(command, exit_code, output, execution_time)
            
            # Notifier les connexions WebSocket
            await self._notify_websockets(session, {
                "type": "command_executed",
                "command": command,
                "output": output,
                "exit_code": exit_code,
                "execution_time": execution_time,
                "working_dir": session.working_dir
            })
            
            return {
                "success": True,
                "output": output,
                "exit_code": exit_code,
                "execution_time": execution_time,
                "working_dir": session.working_dir,
                "command": command
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            session.add_to_history(command, -1, error_msg, execution_time)
            
            logger.error(f"Command execution error: {e}")
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time,
                "command": command
            }
    
    async def _notify_websockets(self, session: TerminalSession, message: Dict):
        """Notifie toutes les connexions WebSocket d'une session"""
        if not session.websocket_connections:
            return
        
        disconnected = set()
        for ws in session.websocket_connections:
            try:
                await ws.send_json(message)
            except:
                disconnected.add(ws)
        
        # Nettoyer les connexions fermées
        for ws in disconnected:
            session.websocket_connections.discard(ws)

# Instance globale
terminal_manager = TerminalManager()

# Modèles Pydantic
class CreateSessionRequest(BaseModel):
    working_dir: Optional[str] = None

class ExecuteCommandRequest(BaseModel):
    command: str = Field(..., min_length=1, max_length=1000)

class AutocompleteRequest(BaseModel):
    partial_command: str = Field(..., max_length=200)

# Routes API
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Terminal Service",
        "version": API_VERSION,
        "os": SYSTEM_OS,
        "active_sessions": len(terminal_manager.sessions),
        "max_sessions": MAX_SESSIONS,
        "timestamp": time.time()
    }

@app.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """Crée une nouvelle session terminal"""
    try:
        session = terminal_manager.create_session(request.working_dir)
        return {
            "success": True,
            "session_id": session.session_id,
            "working_dir": session.working_dir,
            "created_at": session.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to create session: {str(e)}")

@app.get("/sessions")
async def list_sessions():
    """Liste toutes les sessions actives"""
    sessions_info = []
    for session in terminal_manager.sessions.values():
        sessions_info.append({
            "session_id": session.session_id,
            "status": session.status.value,
            "working_dir": session.working_dir,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "command_count": len(session.history)
        })
    
    return {
        "success": True,
        "sessions": sessions_info,
        "total": len(sessions_info)
    }

@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Récupère les informations d'une session"""
    session = terminal_manager.get_session(session_id)
    
    return {
        "success": True,
        "session_id": session.session_id,
        "status": session.status.value,
        "working_dir": session.working_dir,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "command_count": len(session.history),
        "recent_history": [
            {
                "command": entry.command,
                "timestamp": entry.timestamp.isoformat(),
                "exit_code": entry.exit_code,
                "execution_time": entry.execution_time
            }
            for entry in session.history[-10:]  # 10 dernières commandes
        ]
    }

@app.delete("/sessions/{session_id}")
async def terminate_session(session_id: str):
    """Termine une session"""
    terminal_manager.terminate_session(session_id)
    return {"success": True, "message": f"Session {session_id} terminated"}

@app.post("/sessions/{session_id}/execute")
async def execute_command(session_id: str, request: ExecuteCommandRequest):
    """Exécute une commande dans une session"""
    session = terminal_manager.get_session(session_id)
    result = await terminal_manager.execute_command(session, request.command)
    return result

@app.post("/sessions/{session_id}/autocomplete")
async def get_autocomplete(session_id: str, request: AutocompleteRequest):
    """Récupère les suggestions d'autocomplétion"""
    session = terminal_manager.get_session(session_id)
    
    options = terminal_manager.autocomplete.get_completions(
        request.partial_command,
        session.working_dir,
        session
    )
    
    return {
        "success": True,
        "partial_command": request.partial_command,
        "suggestions": [asdict(option) for option in options]
    }

@app.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket pour communication temps réel avec une session"""
    await websocket.accept()
    
    try:
        session = terminal_manager.get_session(session_id)
        session.websocket_connections.add(websocket)
        
        logger.info(f"WebSocket connected to session {session_id}")
        
        # Message de bienvenue
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "working_dir": session.working_dir,
            "message": f"Connected to terminal session {session_id}"
        })
        
        while True:
            # Recevoir les messages du client
            data = await websocket.receive_json()
            
            if data.get("type") == "execute_command":
                command = data.get("command", "")
                if command:
                    result = await terminal_manager.execute_command(session, command)
                    await websocket.send_json({
                        "type": "command_result",
                        **result
                    })
            
            elif data.get("type") == "autocomplete":
                partial = data.get("partial_command", "")
                if partial:
                    options = terminal_manager.autocomplete.get_completions(
                        partial, session.working_dir, session
                    )
                    await websocket.send_json({
                        "type": "autocomplete_result",
                        "suggestions": [asdict(option) for option in options]
                    })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if session_id in terminal_manager.sessions:
            session = terminal_manager.sessions[session_id]
            session.websocket_connections.discard(websocket)

if __name__ == "__main__":
    logger.info(f"Starting Terminal Service on port {SERVICE_PORT}")
    logger.info(f"OS: {SYSTEM_OS}, Max sessions: {MAX_SESSIONS}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=False
    )