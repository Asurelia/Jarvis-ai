"""
🔐 Security Validators for Brain API
Input validation and sanitization utilities
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Validateur de sécurité pour les entrées utilisateur"""
    
    # Patterns dangereux
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Scripts JavaScript
        r'javascript:',                # URLs JavaScript
        r'vbscript:',                 # URLs VBScript
        r'onload\s*=',                # Event handlers
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'eval\s*\(',                 # eval() calls
        r'setTimeout\s*\(',           # setTimeout calls
        r'setInterval\s*\(',          # setInterval calls
        r'document\.cookie',          # Cookie access
        r'document\.write',           # Document write
        r'innerHTML\s*=',             # innerHTML manipulation
        r'<iframe[^>]*>',             # iframes
        r'<object[^>]*>',             # objects
        r'<embed[^>]*>',              # embeds
        r'<form[^>]*>',               # forms
        r'<input[^>]*>',              # inputs
        r'<link[^>]*>',               # links
        r'<meta[^>]*>',               # meta tags
        r'<style[^>]*>',              # style tags
        r'expression\s*\(',           # CSS expressions
        r'@import',                   # CSS imports
        r'behavior\s*:',              # CSS behaviors
        r'-moz-binding',              # Mozilla bindings
        r'url\s*\(',                  # CSS URL functions
    ]
    
    # Caractères dangereux
    DANGEROUS_CHARS = ['<', '>', '"', "'", '&', '%', '\\', '/', ';', ':', '!']
    
    # Taille maximale des entrées
    MAX_INPUT_LENGTH = 10000
    MAX_QUERY_LENGTH = 1000
    MAX_USERNAME_LENGTH = 100
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """Nettoie le HTML de l'entrée utilisateur"""
        if not text:
            return ""
        
        # Échapper les caractères HTML
        sanitized = html.escape(text)
        
        # Supprimer les patterns dangereux
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized
    
    @classmethod
    def validate_input_length(cls, text: str, max_length: int = None) -> bool:
        """Valide la longueur de l'entrée"""
        if not text:
            return True
        
        max_len = max_length or cls.MAX_INPUT_LENGTH
        return len(text) <= max_len
    
    @classmethod
    def contains_dangerous_patterns(cls, text: str) -> bool:
        """Vérifie si le texte contient des patterns dangereux"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Pattern dangereux détecté: {pattern[:50]}...")
                return True
        
        return False
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Valide une URL"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # Vérifier le schéma
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Vérifier qu'il y a un netloc (domaine)
            if not parsed.netloc:
                return False
            
            # Vérifier les caractères dangereux
            if any(char in url for char in ['<', '>', '"', "'"]):
                return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def validate_username(cls, username: str) -> bool:
        """Valide un nom d'utilisateur"""
        if not username:
            return False
        
        # Longueur
        if not cls.validate_input_length(username, cls.MAX_USERNAME_LENGTH):
            return False
        
        # Pattern simple: lettres, chiffres, tirets et underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False
        
        # Pas de patterns dangereux
        if cls.contains_dangerous_patterns(username):
            return False
        
        return True
    
    @classmethod
    def sanitize_json_values(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoie récursivement les valeurs d'un dictionnaire JSON"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        
        for key, value in data.items():
            # Nettoyer la clé
            clean_key = cls.sanitize_html(str(key))
            
            if isinstance(value, str):
                # Nettoyer les chaînes
                sanitized[clean_key] = cls.sanitize_html(value)
            elif isinstance(value, dict):
                # Récursion pour les dictionnaires
                sanitized[clean_key] = cls.sanitize_json_values(value)
            elif isinstance(value, list):
                # Nettoyer les listes
                sanitized[clean_key] = [
                    cls.sanitize_html(str(item)) if isinstance(item, str)
                    else cls.sanitize_json_values(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                # Autres types
                sanitized[clean_key] = value
        
        return sanitized

def validate_chat_input(message: str) -> tuple[bool, str]:
    """
    Valide l'entrée d'un message de chat
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not message:
        return False, "Message vide"
    
    # Longueur
    if not SecurityValidator.validate_input_length(message, SecurityValidator.MAX_INPUT_LENGTH):
        return False, f"Message trop long (max {SecurityValidator.MAX_INPUT_LENGTH} caractères)"
    
    # Patterns dangereux
    if SecurityValidator.contains_dangerous_patterns(message):
        return False, "Message contient du contenu potentiellement dangereux"
    
    return True, ""

def sanitize_chat_message(message: str) -> str:
    """Nettoie un message de chat"""
    if not message:
        return ""
    
    return SecurityValidator.sanitize_html(message)

def validate_query_params(params: Dict[str, Any]) -> tuple[bool, str]:
    """
    Valide les paramètres de requête
    
    Returns:
        tuple: (is_valid, error_message)  
    """
    for key, value in params.items():
        if isinstance(value, str):
            # Longueur
            if not SecurityValidator.validate_input_length(value, SecurityValidator.MAX_QUERY_LENGTH):
                return False, f"Paramètre '{key}' trop long"
            
            # Patterns dangereux
            if SecurityValidator.contains_dangerous_patterns(value):
                return False, f"Paramètre '{key}' contient du contenu dangereux"
        
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    if not SecurityValidator.validate_input_length(item, SecurityValidator.MAX_QUERY_LENGTH):
                        return False, f"Élément de liste '{key}' trop long"
                        
                    if SecurityValidator.contains_dangerous_patterns(item):
                        return False, f"Élément de liste '{key}' contient du contenu dangereux"
    
    return True, ""

def get_client_ip(request) -> str:
    """Récupère l'IP du client en tenant compte des proxies"""
    # Vérifier les headers de proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Prendre la première IP (client original)
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # IP directe
    return request.client.host if request.client else "unknown"