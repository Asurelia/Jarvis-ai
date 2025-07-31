#!/usr/bin/env python3
"""
🔒 Tests unitaires critiques pour la Sécurité
Tests pour l'authentification, validation, JWT, CORS, protection contre injections
"""

import pytest
import asyncio
import time
import jwt
import json
import hashlib
import secrets
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, Request
from datetime import datetime, timedelta

# Import des modules de sécurité à tester
import sys
import os

# Mock des modules de sécurité
class MockSecurityManager:
    """Mock du gestionnaire de sécurité pour les tests"""
    
    def __init__(self):
        self.secret_key = "mock-test-secret"
        self.jwt_algorithm = "HS256"
        self.token_expiry = 3600  # 1 hour
        
    def generate_jwt_token(self, user_data, expires_in=None):
        """Génère un token JWT"""
        if expires_in is None:
            expires_in = self.token_expiry
            
        payload = {
            "user_id": user_data.get("id"),
            "username": user_data.get("username"),
            "role": user_data.get("role", "user"),
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)  # JWT ID unique
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
    
    def verify_jwt_token(self, token):
        """Vérifie un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            return {"valid": True, "payload": payload}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
    
    def hash_password(self, password):
        """Hash un mot de passe"""
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    def verify_password(self, password, password_hash):
        """Vérifie un mot de passe"""
        try:
            salt, stored_hash = password_hash.split(':')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return pwd_hash.hex() == stored_hash
        except:
            return False


class TestJWTAuthentication:
    """Tests pour l'authentification JWT"""
    
    @pytest.fixture
    def security_manager(self):
        """Fixture pour créer un gestionnaire de sécurité"""
        return MockSecurityManager()

    def test_jwt_token_generation(self, security_manager):
        """Test la génération de tokens JWT"""
        user_data = {
            "id": "user123",
            "username": "testuser",
            "role": "admin"
        }
        
        token = security_manager.generate_jwt_token(user_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Vérifier que le token peut être décodé
        verification = security_manager.verify_jwt_token(token)
        assert verification["valid"] is True
        assert verification["payload"]["user_id"] == "user123"
        assert verification["payload"]["username"] == "testuser"
        assert verification["payload"]["role"] == "admin"

    def test_jwt_token_expiration(self, security_manager):
        """Test l'expiration des tokens JWT"""
        user_data = {"id": "user123", "username": "testuser"}
        
        # Générer un token qui expire immédiatement
        token = security_manager.generate_jwt_token(user_data, expires_in=-1)
        
        time.sleep(1)  # Attendre un peu
        
        verification = security_manager.verify_jwt_token(token)
        assert verification["valid"] is False
        assert "expired" in verification["error"].lower()

    def test_jwt_token_invalid_signature(self, security_manager):
        """Test la détection de signatures invalides"""
        user_data = {"id": "user123", "username": "testuser"}
        
        token = security_manager.generate_jwt_token(user_data)
        
        # Modifier le token pour corrompre la signature
        corrupted_token = token[:-10] + "corrupted"
        
        verification = security_manager.verify_jwt_token(corrupted_token)
        assert verification["valid"] is False
        assert "invalid" in verification["error"].lower()

    def test_jwt_token_missing_claims(self, security_manager):
        """Test la gestion de claims manquants"""
        incomplete_user_data = {"username": "testuser"}  # Manque l'ID
        
        token = security_manager.generate_jwt_token(incomplete_user_data)
        verification = security_manager.verify_jwt_token(token)
        
        assert verification["valid"] is True
        assert verification["payload"]["user_id"] is None
        assert verification["payload"]["username"] == "testuser"

    def test_jwt_token_role_based_access(self, security_manager):
        """Test l'accès basé sur les rôles"""
        admin_user = {"id": "admin1", "username": "admin", "role": "admin"}
        user_user = {"id": "user1", "username": "user", "role": "user"}
        
        admin_token = security_manager.generate_jwt_token(admin_user)
        user_token = security_manager.generate_jwt_token(user_user)
        
        admin_verification = security_manager.verify_jwt_token(admin_token)
        user_verification = security_manager.verify_jwt_token(user_token)
        
        assert admin_verification["payload"]["role"] == "admin"
        assert user_verification["payload"]["role"] == "user"


class TestPasswordSecurity:
    """Tests pour la sécurité des mots de passe"""
    
    @pytest.fixture
    def security_manager(self):
        return MockSecurityManager()

    def test_password_hashing(self, security_manager):
        """Test le hachage des mots de passe"""
        password = "test_password_123"
        
        password_hash = security_manager.hash_password(password)
        
        assert password_hash is not None
        assert password != password_hash
        assert ":" in password_hash  # Format salt:hash
        assert len(password_hash) > 64  # Au moins 32 chars salt + 64 chars hash

    def test_password_verification_correct(self, security_manager):
        """Test la vérification avec le bon mot de passe"""
        password = "correct_password_456"
        
        password_hash = security_manager.hash_password(password)
        verification = security_manager.verify_password(password, password_hash)
        
        assert verification is True

    def test_password_verification_incorrect(self, security_manager):
        """Test la vérification avec un mauvais mot de passe"""
        correct_password = "correct_password_456"
        wrong_password = "wrong_password_789"
        
        password_hash = security_manager.hash_password(correct_password)
        verification = security_manager.verify_password(wrong_password, password_hash)
        
        assert verification is False

    def test_password_hash_uniqueness(self, security_manager):
        """Test que les hashs sont uniques même pour le même mot de passe"""
        password = "same_password"
        
        hash1 = security_manager.hash_password(password)
        hash2 = security_manager.hash_password(password)
        
        assert hash1 != hash2  # Les salts doivent être différents
        
        # Mais les deux doivent être valides
        assert security_manager.verify_password(password, hash1) is True
        assert security_manager.verify_password(password, hash2) is True

    def test_password_hash_malformed(self, security_manager):
        """Test la gestion de hashs malformés"""
        password = "test_password"
        malformed_hash = "this_is_not_a_valid_hash"
        
        verification = security_manager.verify_password(password, malformed_hash)
        assert verification is False


class TestInputValidation:
    """Tests pour la validation des entrées"""
    
    def test_sql_injection_detection(self):
        """Test la détection d'injections SQL"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin' --",
            "' UNION SELECT * FROM passwords --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        def is_sql_injection(input_string):
            """Fonction simple de détection d'injection SQL"""
            dangerous_keywords = [
                'DROP', 'DELETE', 'INSERT', 'UPDATE', 'UNION', 
                'SELECT', 'CREATE', 'ALTER', 'EXEC', 'EXECUTE',
                '--', ';', '/*', '*/', 'xp_', 'sp_'
            ]
            
            input_upper = input_string.upper()
            return any(keyword in input_upper for keyword in dangerous_keywords)
        
        for malicious_input in malicious_inputs:
            assert is_sql_injection(malicious_input) is True, f"Failed to detect: {malicious_input}"
        
        # Test avec des entrées légitimes
        legitimate_inputs = ["john.doe", "user@email.com", "My password123", "Search term"]
        for legitimate_input in legitimate_inputs:
            assert is_sql_injection(legitimate_input) is False, f"False positive: {legitimate_input}"

    def test_xss_prevention(self):
        """Test la prévention d'attaques XSS"""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src='x' onerror='alert(1)'>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
            "<svg onload=alert(1)>",
            "<body onload=alert('XSS')>"
        ]
        
        def sanitize_html_input(input_string):
            """Fonction simple de nettoyage HTML"""
            import html
            import re
            
            # Échapper les caractères HTML
            sanitized = html.escape(input_string)
            
            # Supprimer les balises script et autres dangereuses
            dangerous_tags = r'<(script|iframe|object|embed|form|meta|link|style)[^>]*>.*?</\1>'
            sanitized = re.sub(dangerous_tags, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            
            # Supprimer les attributs d'événements JavaScript
            event_attributes = r'\s*on\w+\s*=\s*["\'][^"\']*["\']'
            sanitized = re.sub(event_attributes, '', sanitized, flags=re.IGNORECASE)
            
            # Supprimer javascript: URLs
            sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
            
            return sanitized
        
        for malicious_input in malicious_inputs:
            sanitized = sanitize_html_input(malicious_input)
            assert "<script>" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert "alert(" not in sanitized

    def test_command_injection_prevention(self):
        """Test la prévention d'injections de commandes"""
        malicious_inputs = [
            "test; rm -rf /",
            "test && cat /etc/passwd",
            "test | nc -l 1234",
            "test `whoami`",
            "test $(ls -la)",
            "test; python -c 'import os; os.system(\"rm -rf /\")'",
            "test & ping google.com"
        ]
        
        def is_command_injection(input_string):
            """Fonction simple de détection d'injection de commandes"""
            dangerous_chars = [';', '&&', '||', '|', '`', '$', '&', '>', '<', '*']
            dangerous_commands = ['rm', 'del', 'format', 'fdisk', 'nc', 'netcat', 'wget', 'curl']
            
            for char in dangerous_chars:
                if char in input_string:
                    return True
            
            input_lower = input_string.lower()
            for command in dangerous_commands:
                if command in input_lower:
                    return True
            
            return False
        
        for malicious_input in malicious_inputs:
            assert is_command_injection(malicious_input) is True, f"Failed to detect: {malicious_input}"

    def test_path_traversal_prevention(self):
        """Test la prévention de path traversal"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2froot%2f.ssh%2fid_rsa",
            "....//....//....//etc//passwd",
            "/var/www/../../etc/passwd",
            "file:///etc/passwd",
            "\\..\\..\\..\\.ssh\\id_rsa"
        ]
        
        def is_path_traversal(path):
            """Fonction simple de détection de path traversal"""
            import urllib.parse
            
            # Décoder l'URL
            decoded_path = urllib.parse.unquote(path)
            
            # Rechercher des patterns dangereux
            dangerous_patterns = ['../', '..\\', '....', '%2e%2e', 'file://', '\\..\\']
            
            for pattern in dangerous_patterns:
                if pattern in decoded_path.lower():
                    return True
            
            return False
        
        for malicious_path in malicious_paths:
            assert is_path_traversal(malicious_path) is True, f"Failed to detect: {malicious_path}"

    def test_input_length_validation(self):
        """Test la validation de longueur des entrées"""
        def validate_input_length(input_string, min_length=1, max_length=255):
            """Valide la longueur d'une entrée"""
            if not isinstance(input_string, str):
                return False
            
            length = len(input_string)
            return min_length <= length <= max_length
        
        # Tests de longueurs valides
        assert validate_input_length("test") is True
        assert validate_input_length("a" * 255) is True
        assert validate_input_length("valid input", min_length=5, max_length=20) is True
        
        # Tests de longueurs invalides
        assert validate_input_length("") is False  # Trop court
        assert validate_input_length("a" * 256) is False  # Trop long
        assert validate_input_length("abc", min_length=5) is False  # Trop court pour min
        assert validate_input_length("too long input", max_length=10) is False  # Trop long pour max

    def test_email_validation(self):
        """Test la validation d'emails"""
        import re
        
        def validate_email(email):
            """Valide un email avec regex simple"""
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, email) is not None
        
        # Emails valides
        valid_emails = [
            "user@example.com",
            "test.email@domain.co.uk",
            "user+tag@example.org",
            "123@example.com"
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True, f"Valid email rejected: {email}"
        
        # Emails invalides
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user..double.dot@example.com",
            "user@.example.com",
            "user@example.",
            "<script>alert('xss')</script>@example.com"
        ]
        
        for email in invalid_emails:
            assert validate_email(email) is False, f"Invalid email accepted: {email}"


class TestCORSConfiguration:
    """Tests pour la configuration CORS"""
    
    def test_cors_allowed_origins(self):
        """Test la configuration des origines autorisées"""
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://jarvis.example.com"
        ]
        
        def is_origin_allowed(origin, allowed_list):
            """Vérifie si une origine est autorisée"""
            return origin in allowed_list
        
        # Test origines autorisées
        for origin in allowed_origins:
            assert is_origin_allowed(origin, allowed_origins) is True
        
        # Test origines non autorisées
        forbidden_origins = [
            "http://malicious.com",
            "https://evil.example.com",
            "ftp://localhost:3000",
            "javascript:alert('xss')"
        ]
        
        for origin in forbidden_origins:
            assert is_origin_allowed(origin, allowed_origins) is False

    def test_cors_preflight_handling(self):
        """Test la gestion des requêtes preflight CORS"""
        def handle_preflight_request(origin, method, headers):
            """Simule la gestion d'une requête preflight"""
            allowed_origins = ["http://localhost:3000", "https://jarvis.example.com"]
            allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            allowed_headers = ["Authorization", "Content-Type", "Accept"]
            
            if origin not in allowed_origins:
                return {"allowed": False, "error": "Origin not allowed"}
            
            if method not in allowed_methods:
                return {"allowed": False, "error": "Method not allowed"}
            
            for header in headers:
                if header not in allowed_headers:
                    return {"allowed": False, "error": f"Header {header} not allowed"}
            
            return {"allowed": True}
        
        # Test requête preflight valide
        result = handle_preflight_request(
            "http://localhost:3000",
            "POST",
            ["Content-Type", "Authorization"]
        )
        assert result["allowed"] is True
        
        # Test origine non autorisée
        result = handle_preflight_request(
            "http://malicious.com",
            "POST",
            ["Content-Type"]
        )
        assert result["allowed"] is False
        assert "Origin not allowed" in result["error"]
        
        # Test méthode non autorisée
        result = handle_preflight_request(
            "http://localhost:3000",
            "PATCH",
            ["Content-Type"]
        )
        assert result["allowed"] is False
        assert "Method not allowed" in result["error"]


class TestRateLimiting:
    """Tests pour la limitation de taux"""
    
    def test_rate_limiting_basic(self):
        """Test la limitation de taux basique"""
        class RateLimiter:
            def __init__(self, max_requests=10, window_seconds=60):
                self.max_requests = max_requests
                self.window_seconds = window_seconds
                self.requests = {}
            
            def is_allowed(self, client_id):
                now = time.time()
                
                # Nettoyer les anciennes requêtes
                if client_id in self.requests:
                    self.requests[client_id] = [
                        req_time for req_time in self.requests[client_id]
                        if now - req_time < self.window_seconds
                    ]
                else:
                    self.requests[client_id] = []
                
                # Vérifier la limite
                if len(self.requests[client_id]) >= self.max_requests:
                    return False
                
                # Ajouter la requête actuelle
                self.requests[client_id].append(now)
                return True
        
        limiter = RateLimiter(max_requests=3, window_seconds=10)
        
        # Test requêtes dans la limite
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        
        # Test dépassement de limite
        assert limiter.is_allowed("client1") is False
        
        # Test client différent
        assert limiter.is_allowed("client2") is True

    def test_rate_limiting_by_ip(self):
        """Test la limitation par adresse IP"""
        def get_client_ip(request_headers):
            """Extrait l'IP client des headers"""
            # Vérifier les headers de proxy en premier
            forwarded_for = request_headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            
            real_ip = request_headers.get("X-Real-IP")
            if real_ip:
                return real_ip
            
            # IP par défaut si pas trouvée
            return request_headers.get("Remote-Addr", "127.0.0.1")
        
        # Test extraction IP normale
        headers1 = {"Remote-Addr": "192.168.1.100"}
        ip1 = get_client_ip(headers1)
        assert ip1 == "192.168.1.100"
        
        # Test avec proxy
        headers2 = {"X-Forwarded-For": "203.0.113.1, 192.168.1.100", "Remote-Addr": "192.168.1.100"}
        ip2 = get_client_ip(headers2)
        assert ip2 == "203.0.113.1"
        
        # Test avec X-Real-IP
        headers3 = {"X-Real-IP": "203.0.113.2", "Remote-Addr": "192.168.1.100"}
        ip3 = get_client_ip(headers3)
        assert ip3 == "203.0.113.2"


class TestSessionManagement:
    """Tests pour la gestion de sessions"""
    
    def test_session_creation(self):
        """Test la création de sessions"""
        class SessionManager:
            def __init__(self):
                self.sessions = {}
                self.session_timeout = 3600  # 1 hour
            
            def create_session(self, user_id):
                session_id = secrets.token_hex(32)
                session_data = {
                    "user_id": user_id,
                    "created_at": time.time(),
                    "last_activity": time.time(),
                    "active": True
                }
                self.sessions[session_id] = session_data
                return session_id
            
            def get_session(self, session_id):
                if session_id not in self.sessions:
                    return None
                
                session = self.sessions[session_id]
                
                # Vérifier l'expiration
                if time.time() - session["last_activity"] > self.session_timeout:
                    session["active"] = False
                    return None
                
                # Mettre à jour l'activité
                session["last_activity"] = time.time()
                return session
            
            def destroy_session(self, session_id):
                if session_id in self.sessions:
                    del self.sessions[session_id]
                    return True
                return False
        
        manager = SessionManager()
        
        # Test création
        session_id = manager.create_session("user123")
        assert session_id is not None
        assert len(session_id) == 64  # 32 bytes hex = 64 chars
        
        # Test récupération
        session = manager.get_session(session_id)
        assert session is not None
        assert session["user_id"] == "user123"
        assert session["active"] is True
        
        # Test session inexistante
        fake_session = manager.get_session("fake_session_id")
        assert fake_session is None
        
        # Test destruction
        destroyed = manager.destroy_session(session_id)
        assert destroyed is True
        
        # Vérifier que la session n'existe plus
        session_after_destroy = manager.get_session(session_id)
        assert session_after_destroy is None

    def test_session_timeout(self):
        """Test l'expiration de sessions"""
        class SessionManager:
            def __init__(self, timeout=1):  # 1 seconde pour le test
                self.sessions = {}
                self.session_timeout = timeout
            
            def create_session(self, user_id):
                session_id = secrets.token_hex(16)
                self.sessions[session_id] = {
                    "user_id": user_id,
                    "last_activity": time.time(),
                    "active": True
                }
                return session_id
            
            def get_session(self, session_id):
                if session_id not in self.sessions:
                    return None
                
                session = self.sessions[session_id]
                
                if time.time() - session["last_activity"] > self.session_timeout:
                    session["active"] = False
                    return None
                
                session["last_activity"] = time.time()
                return session
        
        manager = SessionManager(timeout=1)
        
        # Créer une session
        session_id = manager.create_session("user123")
        
        # Vérifier qu'elle est active
        session = manager.get_session(session_id)
        assert session is not None
        
        # Attendre l'expiration
        time.sleep(1.1)
        
        # Vérifier qu'elle a expiré
        expired_session = manager.get_session(session_id)
        assert expired_session is None


class TestAuditLogging:
    """Tests pour la journalisation d'audit"""
    
    def test_security_event_logging(self):
        """Test la journalisation d'événements de sécurité"""
        class SecurityAuditor:
            def __init__(self):
                self.events = []
            
            def log_event(self, event_type, user_id, ip_address, details=None):
                event = {
                    "timestamp": time.time(),
                    "event_type": event_type,
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "details": details or {},
                    "severity": self._get_severity(event_type)
                }
                self.events.append(event)
                return event
            
            def _get_severity(self, event_type):
                severity_map = {
                    "login_success": "info",
                    "login_failure": "warning",
                    "password_change": "info",
                    "account_locked": "warning",
                    "suspicious_activity": "critical",
                    "privilege_escalation": "critical",
                    "data_access": "info"
                }
                return severity_map.get(event_type, "info")
            
            def get_events_by_user(self, user_id):
                return [event for event in self.events if event["user_id"] == user_id]
            
            def get_critical_events(self):
                return [event for event in self.events if event["severity"] == "critical"]
        
        auditor = SecurityAuditor()
        
        # Test logging d'événements
        login_event = auditor.log_event("login_success", "user123", "192.168.1.100")
        assert login_event["event_type"] == "login_success"
        assert login_event["severity"] == "info"
        
        suspicious_event = auditor.log_event(
            "suspicious_activity", 
            "user456", 
            "203.0.113.1",
            {"reason": "Multiple failed login attempts"}
        )
        assert suspicious_event["severity"] == "critical"
        
        # Test récupération par utilisateur
        user_events = auditor.get_events_by_user("user123")
        assert len(user_events) == 1
        assert user_events[0]["event_type"] == "login_success"
        
        # Test récupération d'événements critiques
        critical_events = auditor.get_critical_events()
        assert len(critical_events) == 1
        assert critical_events[0]["event_type"] == "suspicious_activity"


@pytest.fixture(scope="session")
def event_loop():
    """Fixture pour gérer la boucle d'événements asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Helpers pour les tests de sécurité
class TestSecurityHelpers:
    """Helpers utilitaires pour les tests de sécurité"""
    
    @staticmethod
    def create_mock_request(method="GET", path="/", headers=None, body=None):
        """Crée une requête mock pour les tests"""
        return {
            "method": method,
            "path": path,
            "headers": headers or {},
            "body": body,
            "remote_addr": "127.0.0.1"
        }
    
    @staticmethod
    def create_test_user(username="testuser", role="user", active=True):
        """Crée un utilisateur de test"""
        return {
            "id": f"user_{secrets.token_hex(8)}",
            "username": username,
            "role": role,
            "active": active,
            "created_at": time.time(),
            "last_login": None
        }
    
    @staticmethod
    def assert_secure_response_headers(headers):
        """Vérifie que les headers de sécurité sont présents"""
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]
        
        for header in security_headers:
            assert header in headers, f"Security header missing: {header}"
    
    @staticmethod
    def generate_test_jwt_payload(user_id="test_user", exp_minutes=60):
        """Génère un payload JWT pour les tests"""
        return {
            "user_id": user_id,
            "username": "testuser",
            "role": "user",
            "exp": datetime.utcnow() + timedelta(minutes=exp_minutes),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])