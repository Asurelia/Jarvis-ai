"""
🖥️ System Control Service - JARVIS 2025
Service de contrôle système sécurisé avec MCP integration
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
import uvicorn
import pyautogui
import keyboard
import pynput
from pynput import mouse, keyboard as pynput_keyboard
import pygetwindow as gw
import pyperclip
import psutil
import platform
import time
import json
import hashlib
import hmac
import secrets
import logging
import asyncio
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os
import threading
from dataclasses import dataclass
from enum import Enum

# Prometheus monitoring
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import structlog

# Configuration
SYSTEM_OS = platform.system()
SERVICE_PORT = 5004
API_VERSION = "2.0.0"

# Configuration sécurité
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "true").lower() == "true"
MAX_ACTIONS_PER_MINUTE = int(os.getenv("MAX_ACTIONS_PER_MINUTE", "60"))
EMERGENCY_KEY = "ctrl+shift+esc"

# Configuration PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# Logging sécurisé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/system-control.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="JARVIS System Control Service",
    version=API_VERSION,
    description="Service de contrôle système sécurisé avec MCP tools"
)

# CORS pour intégration browser/IDE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentification
security = HTTPBearer()

# Prometheus metrics
registry = CollectorRegistry()

# Métriques de contrôle système
system_actions = Counter(
    'system_control_actions_total',
    'Total system actions executed',
    ['action_type', 'status'],
    registry=registry
)

action_duration = Histogram(
    'system_control_action_duration_seconds',
    'Time taken to execute actions',
    ['action_type'],
    registry=registry
)

security_violations = Counter(
    'system_control_security_violations_total',
    'Total security violations detected',
    ['violation_type'],
    registry=registry
)

active_sessions = Gauge(
    'system_control_active_sessions',
    'Number of active control sessions',
    registry=registry
)

rate_limit_hits = Counter(
    'system_control_rate_limit_hits_total',
    'Total rate limit violations',
    registry=registry
)

memory_usage = Gauge(
    'system_control_memory_usage_bytes',
    'Memory usage of system control service',
    registry=registry
)

class ActionType(str, Enum):
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"
    KEYBOARD_TYPE = "keyboard_type"
    KEYBOARD_HOTKEY = "keyboard_hotkey"
    WINDOW_FOCUS = "window_focus"
    WINDOW_RESIZE = "window_resize"
    SCREENSHOT = "screenshot"
    CLIPBOARD_GET = "clipboard_get"
    CLIPBOARD_SET = "clipboard_set"
    APP_LAUNCH = "app_launch"

class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ActionLimit:
    max_per_minute: int
    security_level: SecurityLevel
    requires_confirmation: bool

# Configuration des limites par action
ACTION_LIMITS = {
    ActionType.MOUSE_CLICK: ActionLimit(30, SecurityLevel.MEDIUM, False),
    ActionType.MOUSE_MOVE: ActionLimit(60, SecurityLevel.LOW, False),
    ActionType.KEYBOARD_TYPE: ActionLimit(20, SecurityLevel.HIGH, True),
    ActionType.KEYBOARD_HOTKEY: ActionLimit(10, SecurityLevel.HIGH, True),
    ActionType.APP_LAUNCH: ActionLimit(5, SecurityLevel.CRITICAL, True),
}

class SecurityManager:
    def __init__(self):
        self.action_history = {}
        self.forbidden_zones = []
        self.emergency_stop = False
        self.setup_emergency_stop()
    
    def setup_emergency_stop(self):
        """Configure l'arrêt d'urgence"""
        def on_emergency():
            self.emergency_stop = True
            logger.critical("🚨 EMERGENCY STOP ACTIVATED!")
        
        keyboard.add_hotkey(EMERGENCY_KEY, on_emergency)
    
    def validate_action(self, action_type: ActionType, params: Dict) -> bool:
        """Valide si l'action est autorisée"""
        if self.emergency_stop:
            raise HTTPException(423, "Service in emergency stop mode")
        
        # Vérifier les limites de rate
        if not self._check_rate_limit(action_type):
            raise HTTPException(429, f"Rate limit exceeded for {action_type}")
        
        # Vérifier les zones interdites
        if action_type in [ActionType.MOUSE_CLICK, ActionType.MOUSE_MOVE]:
            if self._is_in_forbidden_zone(params.get('x', 0), params.get('y', 0)):
                raise HTTPException(403, "Action in forbidden zone")
        
        # Vérifier le contenu sensible
        if action_type == ActionType.KEYBOARD_TYPE:
            if self._contains_sensitive_content(params.get('text', '')):
                raise HTTPException(403, "Sensitive content detected")
        
        return True
    
    def _check_rate_limit(self, action_type: ActionType) -> bool:
        """Vérifie les limites de taux"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        if action_type not in self.action_history:
            self.action_history[action_type] = []
        
        # Nettoyer l'historique ancien
        self.action_history[action_type] = [
            timestamp for timestamp in self.action_history[action_type]
            if timestamp > minute_ago
        ]
        
        # Vérifier la limite
        limit = ACTION_LIMITS.get(action_type, ActionLimit(10, SecurityLevel.MEDIUM, False))
        if len(self.action_history[action_type]) >= limit.max_per_minute:
            return False
        
        # Enregistrer l'action
        self.action_history[action_type].append(now)
        return True
    
    def _is_in_forbidden_zone(self, x: int, y: int) -> bool:
        """Vérifie si les coordonnées sont dans une zone interdite"""
        for zone in self.forbidden_zones:
            if (zone['x1'] <= x <= zone['x2'] and 
                zone['y1'] <= y <= zone['y2']):
                return True
        return False
    
    def _contains_sensitive_content(self, text: str) -> bool:
        """Détecte le contenu sensible"""
        sensitive_patterns = [
            'password', 'secret', 'token', 'key', 'credential',
            'sudo', 'admin', 'root', 'rm -rf', 'del /f'
        ]
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in sensitive_patterns)

class ActionAuditor:
    def __init__(self):
        self.audit_file = "/app/logs/system-actions.audit"
    
    def log_action(self, action_type: str, params: Dict, success: bool, 
                   error: Optional[str] = None):
        """Enregistre l'action dans l'audit trail"""
        # Hash des paramètres sensibles
        safe_params = self._sanitize_params(params)
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "params": safe_params,
            "success": success,
            "error": error,
            "os": SYSTEM_OS,
            "sandbox_mode": SANDBOX_MODE
        }
        
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')
        
        logger.info(f"Action logged: {action_type} - Success: {success}")
    
    def _sanitize_params(self, params: Dict) -> Dict:
        """Nettoie les paramètres sensibles pour l'audit"""
        safe_params = params.copy()
        if 'text' in safe_params and len(safe_params['text']) > 10:
            # Hash des textes longs
            text_hash = hashlib.sha256(safe_params['text'].encode()).hexdigest()[:8]
            safe_params['text'] = f"[HASHED:{text_hash}]"
        return safe_params

# Instances globales
security_manager = SecurityManager()
auditor = ActionAuditor()

class SystemController:
    def __init__(self):
        self.screen_size = pyautogui.size()
        logger.info(f"Screen size detected: {self.screen_size}")
    
    def move_mouse(self, x: int, y: int, duration: float = 0.5) -> Dict:
        """Déplace la souris"""
        try:
            # Validation des coordonnées
            if not (0 <= x <= self.screen_size.width and 0 <= y <= self.screen_size.height):
                raise ValueError(f"Coordinates out of bounds: ({x}, {y})")
            
            pyautogui.moveTo(x, y, duration=duration)
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            raise HTTPException(500, f"Mouse move failed: {str(e)}")
    
    def click_mouse(self, x: int, y: int, button: str = "left", clicks: int = 1) -> Dict:
        """Clique avec la souris"""
        try:
            pyautogui.click(x, y, clicks=clicks, button=button)
            return {"success": True, "x": x, "y": y, "button": button, "clicks": clicks}
        except Exception as e:
            raise HTTPException(500, f"Mouse click failed: {str(e)}")
    
    def scroll_mouse(self, x: int, y: int, scroll_amount: int) -> Dict:
        """Scroll avec la souris"""
        try:
            pyautogui.scroll(scroll_amount, x=x, y=y)
            return {"success": True, "scroll_amount": scroll_amount}
        except Exception as e:
            raise HTTPException(500, f"Mouse scroll failed: {str(e)}")
    
    def type_text(self, text: str, interval: float = 0.05) -> Dict:
        """Tape du texte"""
        try:
            pyautogui.write(text, interval=interval)
            return {"success": True, "length": len(text)}
        except Exception as e:
            raise HTTPException(500, f"Text typing failed: {str(e)}")
    
    def press_hotkey(self, keys: List[str]) -> Dict:
        """Presse une combinaison de touches"""
        try:
            pyautogui.hotkey(*keys)
            return {"success": True, "keys": keys}
        except Exception as e:
            raise HTTPException(500, f"Hotkey failed: {str(e)}")
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> Dict:
        """Prend une capture d'écran"""
        try:
            timestamp = int(time.time())
            filename = f"/app/cache/screenshot_{timestamp}.png"
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            screenshot.save(filename)
            return {"success": True, "filename": filename, "timestamp": timestamp}
        except Exception as e:
            raise HTTPException(500, f"Screenshot failed: {str(e)}")
    
    def get_clipboard(self) -> Dict:
        """Récupère le contenu du presse-papiers"""
        try:
            content = pyperclip.paste()
            return {"success": True, "content": content, "length": len(content)}
        except Exception as e:
            raise HTTPException(500, f"Clipboard get failed: {str(e)}")
    
    def set_clipboard(self, content: str) -> Dict:
        """Définit le contenu du presse-papiers"""
        try:
            pyperclip.copy(content)
            return {"success": True, "length": len(content)}
        except Exception as e:
            raise HTTPException(500, f"Clipboard set failed: {str(e)}")
    
    def get_windows(self) -> List[Dict]:
        """Liste les fenêtres ouvertes"""
        try:
            windows = []
            for window in gw.getAllWindows():
                if window.title:  # Ignorer les fenêtres sans titre
                    windows.append({
                        "title": window.title,
                        "x": window.left,
                        "y": window.top,
                        "width": window.width,
                        "height": window.height,
                        "active": window.isActive
                    })
            return windows
        except Exception as e:
            logger.warning(f"Window enumeration failed: {e}")
            return []
    
    def focus_window(self, title: str) -> Dict:
        """Met le focus sur une fenêtre"""
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                raise ValueError(f"Window not found: {title}")
            
            window = windows[0]
            window.activate()
            return {"success": True, "title": title}
        except Exception as e:
            raise HTTPException(500, f"Window focus failed: {str(e)}")

# Instance du contrôleur
controller = SystemController()

# Modèles Pydantic
class MouseMoveRequest(BaseModel):
    x: int = Field(..., ge=0, description="Coordonnée X")
    y: int = Field(..., ge=0, description="Coordonnée Y")
    duration: float = Field(0.5, ge=0, le=5, description="Durée du mouvement")

class MouseClickRequest(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    button: str = Field("left", regex="^(left|right|middle)$")
    clicks: int = Field(1, ge=1, le=5)

class MouseScrollRequest(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    scroll_amount: int = Field(..., ge=-10, le=10)

class TypeTextRequest(BaseModel):
    text: str = Field(..., max_length=1000)
    interval: float = Field(0.05, ge=0, le=1)

class HotkeyRequest(BaseModel):
    keys: List[str] = Field(..., min_items=1, max_items=5)

class ClipboardSetRequest(BaseModel):
    content: str = Field(..., max_length=10000)

class WindowFocusRequest(BaseModel):
    title: str = Field(..., min_length=1)

# Configuration JWT
import jwt
from datetime import datetime, timedelta
import secrets

# Clé secrète pour JWT - doit être la même que brain-api
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    logger.error("🚨 ERREUR SÉCURITÉ: JWT_SECRET_KEY manquante!")
    raise ValueError("JWT_SECRET_KEY doit être configurée dans les variables d'environnement")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Liste des tokens révoqués (en production, utiliser Redis)
revoked_tokens = set()

class JWTError(Exception):
    pass

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Créer un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Vérifier et décoder un token JWT"""
    try:
        # Vérifier si le token est révoqué
        if token in revoked_tokens:
            raise JWTError("Token révoqué")
        
        # Décoder le token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Vérifications supplémentaires
        if "exp" not in payload:
            raise JWTError("Token sans expiration")
        
        if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
            raise JWTError("Token expiré")
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise JWTError("Token expiré")
    except jwt.InvalidTokenError:
        raise JWTError("Token invalide")
    except Exception as e:
        raise JWTError(f"Erreur validation token: {str(e)}")

# Middleware de sécurité
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Vérification d'authentification JWT avec sécurité renforcée"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Token d'authentification requis",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Extraire le token
        token = credentials.credentials
        
        # Vérifier le token
        payload = verify_jwt_token(token)
        
        # Vérifications de sécurité supplémentaires
        required_fields = ["sub", "permissions", "iat"]
        for field in required_fields:
            if field not in payload:
                raise JWTError(f"Champ requis manquant: {field}")
        
        # Vérifier les permissions pour le contrôle système
        permissions = payload.get("permissions", [])
        if "system_control" not in permissions:
            raise HTTPException(
                status_code=403,
                detail="Permissions insuffisantes pour le contrôle système"
            )
        
        # Log de l'accès (sans les données sensibles)
        logger.info(f"Accès autorisé - Utilisateur: {payload.get('sub')} - Permissions: {permissions}")
        
        return {
            "user_id": payload.get("sub"),
            "permissions": permissions,
            "token_issued": payload.get("iat")
        }
    
    except JWTError as e:
        logger.warning(f"Échec authentification JWT: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentification échouée: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Erreur verification token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur interne d'authentification"
        )

# Modèles pour l'authentification
class AuthRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    permissions: Optional[List[str]] = Field(default=["system_control"])

class PasswordManager:
    """Gestion sécurisée des mots de passe avec PBKDF2 et salt"""
    
    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
        """Hash un mot de passe avec PBKDF2 et retourne (hash, salt)"""
        if salt is None:
            salt = secrets.token_bytes(32)  # 256-bit salt
        
        # PBKDF2 avec SHA-256, 100000 itérations (recommandé OWASP)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        
        # Encode en base64 pour stockage
        pwdhash_b64 = pwdhash.hex()
        salt_b64 = salt.hex()
        
        return pwdhash_b64, salt_b64
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
        """Vérifie un mot de passe contre son hash"""
        try:
            salt = bytes.fromhex(stored_salt)
            stored_hash_bytes = bytes.fromhex(stored_hash)
            
            # Recalculer le hash avec le même salt
            pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            
            # Comparaison sécurisée contre timing attacks
            return hmac.compare_digest(pwdhash, stored_hash_bytes)
        except Exception as e:
            logger.error(f"Erreur vérification mot de passe: {e}")
            return False
    
    @staticmethod
    def get_secure_credentials() -> dict:
        """Récupère les credentials sécurisés depuis les variables d'environnement"""
        credentials = {}
        
        # Utilisateur JARVIS
        jarvis_user = os.getenv("SYSTEM_CONTROL_JARVIS_USER", "jarvis")
        jarvis_pwd_hash = os.getenv("SYSTEM_CONTROL_JARVIS_PASSWORD_HASH")
        jarvis_pwd_salt = os.getenv("SYSTEM_CONTROL_JARVIS_PASSWORD_SALT")
        
        if jarvis_pwd_hash and jarvis_pwd_salt:
            credentials[jarvis_user] = {
                "hash": jarvis_pwd_hash,
                "salt": jarvis_pwd_salt
            }
        
        # Utilisateur Admin
        admin_user = os.getenv("SYSTEM_CONTROL_ADMIN_USER", "admin")
        admin_pwd_hash = os.getenv("SYSTEM_CONTROL_ADMIN_PASSWORD_HASH")
        admin_pwd_salt = os.getenv("SYSTEM_CONTROL_ADMIN_PASSWORD_SALT")
        
        if admin_pwd_hash and admin_pwd_salt:
            credentials[admin_user] = {
                "hash": admin_pwd_hash,
                "salt": admin_pwd_salt
            }
        
        return credentials

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    permissions: List[str]

# Routes d'authentification
@app.post("/auth/login", response_model=TokenResponse)
async def login(auth_request: AuthRequest):
    """Authentification et génération de token JWT avec hashage sécurisé"""
    # Récupération des credentials hashés
    valid_users = PasswordManager.get_secure_credentials()
    
    # Vérifier que les credentials sont configurés
    if not valid_users:
        logger.error("🚨 ERREUR SÉCURITÉ: Aucun credential hashé configuré!")
        raise HTTPException(
            status_code=500,
            detail="Configuration de sécurité incomplète - credentials manquants"
        )
    
    # Vérification de l'utilisateur
    if auth_request.username not in valid_users:
        # Délai artifiel pour éviter les attaques par timing
        await asyncio.sleep(0.5)
        raise HTTPException(
            status_code=401,
            detail="Identifiants invalides"
        )
    
    user_creds = valid_users[auth_request.username]
    
    # Vérification du mot de passe avec hash sécurisé
    if not PasswordManager.verify_password(
        auth_request.password, 
        user_creds["hash"], 
        user_creds["salt"]
    ):
        # Log de la tentative d'accès
        logger.warning(f"Tentative de connexion échouée pour {auth_request.username}")
        raise HTTPException(
            status_code=401,
            detail="Identifiants invalides"
        )
    
    # Vérifier les permissions demandées
    allowed_permissions = ["system_control", "mouse", "keyboard", "clipboard", "window"]
    requested_permissions = auth_request.permissions or ["system_control"]
    
    for perm in requested_permissions:
        if perm not in allowed_permissions:
            raise HTTPException(
                status_code=400,
                detail=f"Permission non autorisée: {perm}"
            )
    
    # Créer le token
    token_data = {
        "sub": auth_request.username,
        "permissions": requested_permissions,
        "type": "access_token"
    }
    
    expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
    access_token = create_access_token(data=token_data, expires_delta=expires_delta)
    
    logger.info(f"Token généré pour {auth_request.username} avec permissions {requested_permissions}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        permissions=requested_permissions
    )

@app.post("/auth/revoke")
async def revoke_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Révoquer un token JWT"""
    token = credentials.credentials
    revoked_tokens.add(token)
    
    logger.info("Token révoqué")
    return {"message": "Token révoqué avec succès"}

@app.get("/auth/verify")
async def verify_current_token(user_data: dict = Depends(verify_token)):
    """Vérifier le token actuel"""
    return {
        "valid": True,
        "user_id": user_data["user_id"],
        "permissions": user_data["permissions"],
        "token_issued": user_data["token_issued"]
    }

# Routes API
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "System Control Service",
        "version": API_VERSION,
        "os": SYSTEM_OS,
        "sandbox_mode": SANDBOX_MODE,
        "emergency_stop": security_manager.emergency_stop,
        "screen_size": controller.screen_size,
        "timestamp": time.time(),
        "authentication": "JWT enabled"
    }

@app.get("/metrics")
async def get_metrics():
    """Endpoint Prometheus pour les métriques"""
    # Mise à jour des métriques système
    process = psutil.Process()
    memory_usage.set(process.memory_info().rss)
    
    return Response(
        generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )

@app.post("/mouse/move")
async def move_mouse(request: MouseMoveRequest, _: bool = Depends(verify_token)):
    security_manager.validate_action(ActionType.MOUSE_MOVE, request.dict())
    
    try:
        result = controller.move_mouse(request.x, request.y, request.duration)
        auditor.log_action("mouse_move", request.dict(), True)
        return result
    except Exception as e:
        auditor.log_action("mouse_move", request.dict(), False, str(e))
        raise

@app.post("/mouse/click")
async def click_mouse(request: MouseClickRequest, _: bool = Depends(verify_token)):
    security_manager.validate_action(ActionType.MOUSE_CLICK, request.dict())
    
    try:
        result = controller.click_mouse(
            request.x, request.y, request.button, request.clicks
        )
        auditor.log_action("mouse_click", request.dict(), True)
        return result
    except Exception as e:
        auditor.log_action("mouse_click", request.dict(), False, str(e))
        raise

@app.post("/mouse/scroll")
async def scroll_mouse(request: MouseScrollRequest, _: bool = Depends(verify_token)):
    security_manager.validate_action(ActionType.MOUSE_SCROLL, request.dict())
    
    try:
        result = controller.scroll_mouse(request.x, request.y, request.scroll_amount)
        auditor.log_action("mouse_scroll", request.dict(), True)
        return result
    except Exception as e:
        auditor.log_action("mouse_scroll", request.dict(), False, str(e))
        raise

@app.post("/keyboard/type")
async def type_text(request: TypeTextRequest, _: bool = Depends(verify_token)):
    security_manager.validate_action(ActionType.KEYBOARD_TYPE, request.dict())
    
    try:
        result = controller.type_text(request.text, request.interval)
        auditor.log_action("keyboard_type", {"length": len(request.text)}, True)
        return result
    except Exception as e:
        auditor.log_action("keyboard_type", request.dict(), False, str(e))
        raise

@app.post("/keyboard/hotkey")
async def press_hotkey(request: HotkeyRequest, _: bool = Depends(verify_token)):
    security_manager.validate_action(ActionType.KEYBOARD_HOTKEY, request.dict())
    
    try:
        result = controller.press_hotkey(request.keys)
        auditor.log_action("keyboard_hotkey", request.dict(), True)
        return result
    except Exception as e:
        auditor.log_action("keyboard_hotkey", request.dict(), False, str(e))
        raise

@app.post("/screenshot")
async def take_screenshot(_: bool = Depends(verify_token)):
    security_manager.validate_action(ActionType.SCREENSHOT, {})
    
    try:
        result = controller.take_screenshot()
        auditor.log_action("screenshot", {}, True)
        return result
    except Exception as e:
        auditor.log_action("screenshot", {}, False, str(e))
        raise

@app.get("/clipboard")
async def get_clipboard(_: bool = Depends(verify_token)):
    security_manager.validate_action(ActionType.CLIPBOARD_GET, {})
    
    try:
        result = controller.get_clipboard()
        auditor.log_action("clipboard_get", {"length": result.get("length", 0)}, True)
        return result
    except Exception as e:
        auditor.log_action("clipboard_get", {}, False, str(e))
        raise

@app.post("/clipboard")
async def set_clipboard(request: ClipboardSetRequest, _: bool = Depends(verify_token)):
    security_manager.validate_action(ActionType.CLIPBOARD_SET, request.dict())
    
    try:
        result = controller.set_clipboard(request.content)
        auditor.log_action("clipboard_set", {"length": len(request.content)}, True)
        return result
    except Exception as e:
        auditor.log_action("clipboard_set", request.dict(), False, str(e))
        raise

@app.get("/windows")
async def list_windows(_: bool = Depends(verify_token)):
    try:
        windows = controller.get_windows()
        return {"success": True, "windows": windows, "count": len(windows)}
    except Exception as e:
        raise HTTPException(500, f"Window listing failed: {str(e)}")

@app.post("/windows/focus")
async def focus_window(request: WindowFocusRequest, _: bool = Depends(verify_token)):
    security_manager.validate_action(ActionType.WINDOW_FOCUS, request.dict())
    
    try:
        result = controller.focus_window(request.title)
        auditor.log_action("window_focus", request.dict(), True)
        return result
    except Exception as e:
        auditor.log_action("window_focus", request.dict(), False, str(e))
        raise

@app.post("/security/emergency-stop")
async def emergency_stop():
    """Arrêt d'urgence du service"""
    security_manager.emergency_stop = True
    logger.critical("🚨 Emergency stop activated via API")
    return {"success": True, "message": "Emergency stop activated"}

@app.post("/security/reset")
async def reset_security(_: bool = Depends(verify_token)):
    """Reset du système de sécurité"""
    security_manager.emergency_stop = False
    security_manager.action_history.clear()
    logger.info("Security system reset")
    return {"success": True, "message": "Security system reset"}

@app.get("/security/status")
async def security_status(_: bool = Depends(verify_token)):
    """État du système de sécurité"""
    return {
        "emergency_stop": security_manager.emergency_stop,
        "sandbox_mode": SANDBOX_MODE,
        "action_limits": {k.value: v.__dict__ for k, v in ACTION_LIMITS.items()},
        "recent_actions": {
            k.value: len(v) for k, v in security_manager.action_history.items()
        }
    }

if __name__ == "__main__":
    logger.info(f"Starting System Control Service on port {SERVICE_PORT}")
    logger.info(f"OS: {SYSTEM_OS}, Sandbox: {SANDBOX_MODE}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=False,
        log_config=None  # Utilise notre config logging
    )