#!/usr/bin/env python3
"""
🛡️ Validateurs de sécurité pour JARVIS AI
Validation et sanitisation des inputs pour prévenir XSS, injection, etc.
"""

import re
import html
import unicodedata
import bleach
from typing import Any, Dict, List, Optional, Union
from pydantic import validator, BaseModel, Field
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Configuration de sécurité pour les validateurs"""
    
    # Longueurs maximales autorisées
    MAX_TEXT_LENGTH = 5000
    MAX_USERNAME_LENGTH = 50
    MAX_PASSWORD_LENGTH = 128
    MAX_EMAIL_LENGTH = 254
    MAX_URL_LENGTH = 2048
    MAX_FILENAME_LENGTH = 255
    
    # Patterns dangereux à détecter
    DANGEROUS_PATTERNS = [
        # JavaScript
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'setTimeout\s*\(',
        r'setInterval\s*\(',
        
        # SQL Injection
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\b(OR|AND)\s+\w+\s*=\s*\w+)',
        r'[\'"]\s*(OR|AND)\s+[\'"]\d+[\'"]\s*=\s*[\'"]\d+[\'"]',
        r'(\b(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)\b)',
        
        # Command Injection
        r'(\b(rm|del|format|shutdown|reboot|kill|ps|ls|cat|grep|find|wget|curl)\b)',
        r'[;&|`$(){}[\]\\]',
        
        # Path Traversal
        r'\.\./',
        r'\.\.\\',
        r'%2e%2e%2f',
        r'%2e%2e\\',
        
        # LDAP Injection
        r'[()&|!*]',
        
        # XML/XXE
        r'<!ENTITY',
        r'<!DOCTYPE',
        
        # Template Injection
        r'{{\s*.*\s*}}',
        r'{%\s*.*\s*%}',
    ]
    
    # Tags HTML autorisés (très restrictif)
    ALLOWED_HTML_TAGS = ['b', 'i', 'em', 'strong', 'p', 'br']
    ALLOWED_HTML_ATTRIBUTES = {}

class InputSanitizer:
    """Classe pour nettoyer et valider les inputs"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = SecurityConfig.MAX_TEXT_LENGTH) -> str:
        """Nettoie et valide un texte général"""
        if not isinstance(text, str):
            raise ValueError("L'input doit être une chaîne de caractères")
        
        # Vérifier la longueur
        if len(text) > max_length:
            raise ValueError(f"Texte trop long (max {max_length} caractères)")
        
        # Normaliser Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Échapper HTML par défaut
        text = html.escape(text)
        
        # Détecter les patterns dangereux
        InputSanitizer._check_dangerous_patterns(text)
        
        # Supprimer les caractères de contrôle dangereux
        text = InputSanitizer._remove_control_chars(text)
        
        return text.strip()
    
    @staticmethod
    def sanitize_html(html_input: str, max_length: int = SecurityConfig.MAX_TEXT_LENGTH) -> str:
        """Nettoie HTML avec whitelist restrictive"""
        if not isinstance(html_input, str):
            raise ValueError("L'input doit être une chaîne de caractères")
        
        if len(html_input) > max_length:
            raise ValueError(f"HTML trop long (max {max_length} caractères)")
        
        # Utiliser bleach pour nettoyer le HTML
        clean_html = bleach.clean(
            html_input,
            tags=SecurityConfig.ALLOWED_HTML_TAGS,
            attributes=SecurityConfig.ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )
        
        # Vérifications supplémentaires
        InputSanitizer._check_dangerous_patterns(clean_html)
        
        return clean_html
    
    @staticmethod
    def sanitize_username(username: str) -> str:
        """Valide et nettoie un nom d'utilisateur"""
        if not isinstance(username, str):
            raise ValueError("Le nom d'utilisateur doit être une chaîne")
        
        if len(username) > SecurityConfig.MAX_USERNAME_LENGTH:
            raise ValueError(f"Nom d'utilisateur trop long (max {SecurityConfig.MAX_USERNAME_LENGTH})")
        
        # Supprimer espaces en début/fin
        username = username.strip()
        
        # Vérifier format (lettres, chiffres, tirets, underscores seulement)
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("Nom d'utilisateur invalide (lettres, chiffres, _ et - seulement)")
        
        if len(username) < 3:
            raise ValueError("Nom d'utilisateur trop court (minimum 3 caractères)")
        
        return username.lower()
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Valide et nettoie une adresse email"""
        if not isinstance(email, str):
            raise ValueError("L'email doit être une chaîne")
        
        if len(email) > SecurityConfig.MAX_EMAIL_LENGTH:
            raise ValueError(f"Email trop long (max {SecurityConfig.MAX_EMAIL_LENGTH})")
        
        email = email.strip().lower()
        
        # Validation basique email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Format d'email invalide")
        
        return email
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Valide et nettoie une URL"""
        if not isinstance(url, str):
            raise ValueError("L'URL doit être une chaîne")
        
        if len(url) > SecurityConfig.MAX_URL_LENGTH:
            raise ValueError(f"URL trop longue (max {SecurityConfig.MAX_URL_LENGTH})")
        
        url = url.strip()
        
        # Vérifier protocole autorisé
        if not re.match(r'^https?://', url):
            raise ValueError("Seuls les protocols HTTP et HTTPS sont autorisés")
        
        # Vérifier qu'il n'y a pas de caractères dangereux
        dangerous_chars = ['<', '>', '"', "'", '`']
        if any(char in url for char in dangerous_chars):
            raise ValueError("URL contient des caractères dangereux")
        
        return url
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Valide et nettoie un nom de fichier"""
        if not isinstance(filename, str):
            raise ValueError("Le nom de fichier doit être une chaîne")
        
        if len(filename) > SecurityConfig.MAX_FILENAME_LENGTH:
            raise ValueError(f"Nom de fichier trop long (max {SecurityConfig.MAX_FILENAME_LENGTH})")
        
        filename = filename.strip()
        
        # Supprimer caractères dangereux
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\.\.', '', filename)  # Path traversal
        
        # Vérifier qu'il reste quelque chose
        if not filename or filename.startswith('.'):
            raise ValueError("Nom de fichier invalide")
        
        return filename
    
    @staticmethod
    def _check_dangerous_patterns(text: str):
        """Vérifie la présence de patterns dangereux"""
        text_lower = text.lower()
        
        for pattern in SecurityConfig.DANGEROUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Pattern dangereux détecté: {pattern}")
                raise ValueError("Contenu potentiellement dangereux détecté")
    
    @staticmethod
    def _remove_control_chars(text: str) -> str:
        """Supprime les caractères de contrôle dangereux"""
        # Garder seulement les caractères imprimables et espaces/newlines
        return ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

class SecureBaseModel(BaseModel):
    """Modèle Pydantic avec validation de sécurité intégrée"""
    
    class Config:
        # Validation stricte
        validate_assignment = True
        use_enum_values = True
        anystr_strip_whitespace = True

# Validateurs Pydantic pour types courants
def secure_text_validator(max_length: int = SecurityConfig.MAX_TEXT_LENGTH):
    """Crée un validateur pour texte sécurisé"""
    def validator_func(v):
        if v is None:
            return v
        return InputSanitizer.sanitize_text(str(v), max_length)
    return validator('*', allow_reuse=True)(validator_func)

def secure_html_validator(max_length: int = SecurityConfig.MAX_TEXT_LENGTH):
    """Crée un validateur pour HTML sécurisé"""
    def validator_func(v):
        if v is None:
            return v
        return InputSanitizer.sanitize_html(str(v), max_length)
    return validator('*', allow_reuse=True)(validator_func)

def secure_username_validator():
    """Crée un validateur pour nom d'utilisateur sécurisé"""
    def validator_func(v):
        if v is None:
            return v
        return InputSanitizer.sanitize_username(str(v))
    return validator('*', allow_reuse=True)(validator_func)

# Middleware de validation des requêtes
class SecurityValidationMiddleware:
    """Middleware pour valider toutes les requêtes entrantes"""
    
    @staticmethod
    def validate_request_size(content_length: Optional[int], max_size: int = 10 * 1024 * 1024):
        """Valide la taille de la requête (max 10MB par défaut)"""
        if content_length and content_length > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"Requête trop volumineuse (max {max_size} bytes)"
            )
    
    @staticmethod
    def validate_headers(headers: Dict[str, str]):
        """Valide les headers de la requête"""
        dangerous_headers = [
            'x-forwarded-host',
            'x-original-url', 
            'x-rewrite-url'
        ]
        
        for header in dangerous_headers:
            if header in headers:
                logger.warning(f"Header potentiellement dangereux: {header}")
    
    @staticmethod
    def validate_json_payload(payload: Dict[str, Any], max_depth: int = 10):
        """Valide un payload JSON"""
        def check_depth(obj, current_depth=0):
            if current_depth > max_depth:
                raise ValueError("Structure JSON trop profonde")
            
            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, current_depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, current_depth + 1)
        
        check_depth(payload)

# Classes de modèles sécurisés pré-configurés
class SecureChatMessage(SecureBaseModel):
    """Modèle sécurisé pour les messages de chat"""
    message: str = Field(..., max_length=SecurityConfig.MAX_TEXT_LENGTH)
    user_id: Optional[str] = Field(None, max_length=50)
    session_id: Optional[str] = Field(None, max_length=50)
    context: Optional[Dict[str, Any]] = Field(None)
    
    @validator('message')
    def validate_message(cls, v):
        return InputSanitizer.sanitize_text(v)
    
    @validator('user_id', 'session_id')
    def validate_ids(cls, v):
        if v is None:
            return v
        # Validation UUID ou alphanumerique
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("ID invalide")
        return v

class SecureUserInput(SecureBaseModel):
    """Modèle sécurisé pour les inputs utilisateur génériques"""
    username: Optional[str] = Field(None, max_length=SecurityConfig.MAX_USERNAME_LENGTH)
    email: Optional[str] = Field(None, max_length=SecurityConfig.MAX_EMAIL_LENGTH)
    text_content: Optional[str] = Field(None, max_length=SecurityConfig.MAX_TEXT_LENGTH)
    
    @validator('username')
    def validate_username(cls, v):
        if v is None:
            return v
        return InputSanitizer.sanitize_username(v)
    
    @validator('email')
    def validate_email(cls, v):
        if v is None:
            return v
        return InputSanitizer.sanitize_email(v)
    
    @validator('text_content')
    def validate_text(cls, v):
        if v is None:
            return v
        return InputSanitizer.sanitize_text(v)

# Fonction utilitaire pour validation rapide
def quick_sanitize(value: Any, input_type: str = "text") -> Any:
    """Fonction rapide pour nettoyer un input selon son type"""
    if value is None:
        return None
    
    try:
        if input_type == "text":
            return InputSanitizer.sanitize_text(str(value))
        elif input_type == "html":
            return InputSanitizer.sanitize_html(str(value))
        elif input_type == "username":
            return InputSanitizer.sanitize_username(str(value))
        elif input_type == "email":
            return InputSanitizer.sanitize_email(str(value))
        elif input_type == "url":
            return InputSanitizer.sanitize_url(str(value))
        elif input_type == "filename":
            return InputSanitizer.sanitize_filename(str(value))
        else:
            return InputSanitizer.sanitize_text(str(value))
    except ValueError as e:
        logger.warning(f"Validation échouée pour {input_type}: {e}")
        raise HTTPException(status_code=400, detail=str(e))