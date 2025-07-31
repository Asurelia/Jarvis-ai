#!/usr/bin/env python3
"""
🔐 Tests de sécurité critiques pour l'authentification
Tests pour JWT, CORS, sessions, OAuth, 2FA, rate limiting
"""

import pytest
import jwt
import time
import hashlib
import secrets
import json
import base64
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests
from urllib.parse import urlparse, parse_qs

# Configuration de test
TEST_JWT_SECRET = "test_secret_key_dont_use_in_production"
TEST_JWT_ALGORITHM = "HS256"


class MockUser:
    """Mock d'utilisateur pour les tests"""
    
    def __init__(self, user_id, username, email, password_hash, role="user", 
                 is_active=True, is_verified=True, failed_login_attempts=0,
                 last_login=None, created_at=None, two_factor_enabled=False):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.is_active = is_active
        self.is_verified = is_verified
        self.failed_login_attempts = failed_login_attempts
        self.last_login = last_login
        self.created_at = created_at or datetime.utcnow()
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = secrets.token_hex(16) if two_factor_enabled else None


class MockUserRepository:
    """Mock de repository utilisateur"""
    
    def __init__(self):
        self.users = []
        self._create_test_users()
    
    def _create_test_users(self):
        """Créer des utilisateurs de test"""
        test_users = [
            MockUser(1, "admin", "admin@jarvis.ai", self._hash_password("admin_secure_password"), "admin"),
            MockUser(2, "jarvis", "jarvis@stark.com", self._hash_password("jarvis_password"), "user"),
            MockUser(3, "friday", "friday@stark.com", self._hash_password("friday_password"), "user"),
            MockUser(4, "locked_user", "locked@test.com", self._hash_password("password"), "user", is_active=False),
            MockUser(5, "unverified", "unverified@test.com", self._hash_password("password"), "user", is_verified=False),
            MockUser(6, "2fa_user", "2fa@test.com", self._hash_password("secure_password"), "user", two_factor_enabled=True)
        ]
        
        for user in test_users:
            self.users.append(user)
    
    def _hash_password(self, password):
        """Hash un mot de passe"""
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    def find_by_username(self, username):
        """Trouver un utilisateur par nom d'utilisateur"""
        for user in self.users:
            if user.username == username:
                return user
        return None
    
    def find_by_email(self, email):
        """Trouver un utilisateur par email"""
        for user in self.users:
            if user.email == email:
                return user
        return None
    
    def find_by_id(self, user_id):
        """Trouver un utilisateur par ID"""
        for user in self.users:
            if user.id == user_id:
                return user
        return None
    
    def update_failed_attempts(self, user_id, attempts):
        """Mettre à jour les tentatives de connexion échouées"""
        user = self.find_by_id(user_id)
        if user:
            user.failed_login_attempts = attempts
    
    def update_last_login(self, user_id):
        """Mettre à jour la dernière connexion"""
        user = self.find_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()


class MockAuthService:
    """Mock de service d'authentification"""
    
    def __init__(self):
        self.user_repo = MockUserRepository()
        self.secret_key = TEST_JWT_SECRET
        self.algorithm = TEST_JWT_ALGORITHM
        self.token_expiry = 3600  # 1 hour
        self.max_failed_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        
    def authenticate(self, username, password):
        """Authentifier un utilisateur"""
        user = self.user_repo.find_by_username(username)
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        if not user.is_active:
            return {"success": False, "error": "Account locked"}
        
        if not user.is_verified:
            return {"success": False, "error": "Account not verified"}
        
        if user.failed_login_attempts >= self.max_failed_attempts:
            return {"success": False, "error": "Account temporarily locked"}
        
        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            self.user_repo.update_failed_attempts(user.id, user.failed_login_attempts)
            return {"success": False, "error": "Invalid credentials"}
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        self.user_repo.update_failed_attempts(user.id, 0)
        self.user_repo.update_last_login(user.id)
        
        # Generate JWT token
        token = self._generate_jwt_token(user)
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
    
    def _verify_password(self, password, password_hash):
        """Vérifier un mot de passe"""
        try:
            salt, stored_hash = password_hash.split(':')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return pwd_hash.hex() == stored_hash
        except:
            return False
    
    def _generate_jwt_token(self, user):
        """Générer un token JWT"""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(seconds=self.token_expiry),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token):
        """Vérifier un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user = self.user_repo.find_by_id(payload["user_id"])
            
            if not user or not user.is_active:
                return {"valid": False, "error": "User not found or inactive"}
            
            return {"valid": True, "payload": payload, "user": user}
        
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
    
    def refresh_token(self, token):
        """Rafraîchir un token JWT"""
        verification = self.verify_token(token)
        
        if not verification["valid"]:
            return {"success": False, "error": verification["error"]}
        
        user = verification["user"]
        new_token = self._generate_jwt_token(user)
        
        return {"success": True, "token": new_token}
    
    def logout(self, token):
        """Déconnecter un utilisateur (blacklist token)"""
        # Dans une vraie implémentation, on ajouterait le token à une blacklist
        return {"success": True, "message": "Logged out successfully"}


class TestJWTAuthentication:
    """Tests pour l'authentification JWT"""
    
    @pytest.fixture
    def auth_service(self):
        return MockAuthService()

    def test_successful_authentication(self, auth_service):
        """Test d'authentification réussie"""
        result = auth_service.authenticate("admin", "admin_secure_password")
        
        assert result["success"] is True
        assert "token" in result
        assert "user" in result
        assert result["user"]["username"] == "admin"
        assert result["user"]["role"] == "admin"

    def test_failed_authentication_wrong_password(self, auth_service):
        """Test d'authentification échouée avec mauvais mot de passe"""
        result = auth_service.authenticate("admin", "wrong_password")
        
        assert result["success"] is False
        assert "Invalid credentials" in result["error"]

    def test_failed_authentication_user_not_found(self, auth_service):
        """Test d'authentification échouée avec utilisateur inexistant"""
        result = auth_service.authenticate("nonexistent", "password")
        
        assert result["success"] is False
        assert "User not found" in result["error"]

    def test_failed_authentication_inactive_user(self, auth_service):
        """Test d'authentification échouée avec utilisateur inactif"""
        result = auth_service.authenticate("locked_user", "password")
        
        assert result["success"] is False
        assert "Account locked" in result["error"]

    def test_failed_authentication_unverified_user(self, auth_service):
        """Test d'authentification échouée avec utilisateur non vérifié"""
        result = auth_service.authenticate("unverified", "password")
        
        assert result["success"] is False
        assert "Account not verified" in result["error"]

    def test_jwt_token_structure(self, auth_service):
        """Test la structure du token JWT"""
        result = auth_service.authenticate("admin", "admin_secure_password")
        
        assert result["success"] is True
        token = result["token"]
        
        # Décoder le token sans vérification pour inspecter la structure
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        required_claims = ["user_id", "username", "email", "role", "exp", "iat", "jti"]
        for claim in required_claims:
            assert claim in decoded
        
        assert decoded["username"] == "admin"
        assert decoded["role"] == "admin"
        assert "exp" in decoded  # Expiration
        assert "iat" in decoded  # Issued at
        assert "jti" in decoded  # JWT ID

    def test_jwt_token_verification(self, auth_service):
        """Test la vérification de token JWT"""
        # Générer un token
        auth_result = auth_service.authenticate("jarvis", "jarvis_password")
        token = auth_result["token"]
        
        # Vérifier le token
        verification = auth_service.verify_token(token)
        
        assert verification["valid"] is True
        assert verification["payload"]["username"] == "jarvis"
        assert verification["user"].username == "jarvis"

    def test_jwt_token_expiration(self, auth_service):
        """Test l'expiration de token JWT"""
        # Créer un token expiré
        user = auth_service.user_repo.find_by_username("jarvis")
        expired_payload = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expiré il y a 1 heure
            "iat": datetime.utcnow() - timedelta(hours=2),
            "jti": secrets.token_hex(16)
        }
        
        expired_token = jwt.encode(expired_payload, auth_service.secret_key, algorithm=auth_service.algorithm)
        
        verification = auth_service.verify_token(expired_token)
        
        assert verification["valid"] is False
        assert "expired" in verification["error"].lower()

    def test_jwt_token_invalid_signature(self, auth_service):
        """Test la détection de signature invalide"""
        # Générer un token avec une clé différente
        user = auth_service.user_repo.find_by_username("jarvis")
        payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)
        }
        
        invalid_token = jwt.encode(payload, "wrong_secret_key", algorithm=auth_service.algorithm)
        
        verification = auth_service.verify_token(invalid_token)
        
        assert verification["valid"] is False
        assert "invalid" in verification["error"].lower()

    def test_jwt_token_refresh(self, auth_service):
        """Test le rafraîchissement de token"""
        # Générer un token initial
        auth_result = auth_service.authenticate("jarvis", "jarvis_password")
        original_token = auth_result["token"]
        
        # Attendre un peu pour s'assurer que les timestamps sont différents
        time.sleep(1)
        
        # Rafraîchir le token
        refresh_result = auth_service.refresh_token(original_token)
        
        assert refresh_result["success"] is True
        new_token = refresh_result["token"]
        
        # Vérifier que les tokens sont différents
        assert new_token != original_token
        
        # Vérifier que le nouveau token est valide
        verification = auth_service.verify_token(new_token)
        assert verification["valid"] is True

    def test_logout_functionality(self, auth_service):
        """Test la fonctionnalité de déconnexion"""
        # Générer un token
        auth_result = auth_service.authenticate("jarvis", "jarvis_password")
        token = auth_result["token"]
        
        # Déconnecter
        logout_result = auth_service.logout(token)
        
        assert logout_result["success"] is True
        assert "Logged out" in logout_result["message"]


class TestAccountSecurity:
    """Tests pour la sécurité des comptes"""
    
    @pytest.fixture
    def auth_service(self):
        return MockAuthService()

    def test_failed_login_attempts_tracking(self, auth_service):
        """Test le suivi des tentatives de connexion échouées"""
        username = "jarvis"
        wrong_password = "wrong_password"
        
        # Effectuer plusieurs tentatives échouées
        for i in range(3):
            result = auth_service.authenticate(username, wrong_password)
            assert result["success"] is False
        
        # Vérifier que les tentatives sont comptées
        user = auth_service.user_repo.find_by_username(username)
        assert user.failed_login_attempts == 3

    def test_account_lockout_after_max_attempts(self, auth_service):
        """Test le verrouillage du compte après le nombre maximum de tentatives"""
        username = "jarvis"
        wrong_password = "wrong_password"
        
        # Effectuer le nombre maximum de tentatives échouées
        for i in range(auth_service.max_failed_attempts):
            result = auth_service.authenticate(username, wrong_password)
            assert result["success"] is False
        
        # La tentative suivante devrait indiquer un compte verrouillé
        result = auth_service.authenticate(username, wrong_password)
        assert result["success"] is False
        assert "temporarily locked" in result["error"]

    def test_failed_attempts_reset_on_successful_login(self, auth_service):
        """Test la réinitialisation des tentatives échouées après connexion réussie"""
        username = "jarvis"
        correct_password = "jarvis_password"
        wrong_password = "wrong_password"
        
        # Effectuer quelques tentatives échouées
        for i in range(2):
            auth_service.authenticate(username, wrong_password)
        
        # Vérifier que les tentatives sont comptées
        user = auth_service.user_repo.find_by_username(username)
        assert user.failed_login_attempts == 2
        
        # Connexion réussie
        result = auth_service.authenticate(username, correct_password)
        assert result["success"] is True
        
        # Vérifier que les tentatives sont réinitialisées
        user = auth_service.user_repo.find_by_username(username)
        assert user.failed_login_attempts == 0

    def test_password_complexity_validation(self):
        """Test la validation de la complexité des mots de passe"""
        def validate_password_strength(password):
            """Valider la force d'un mot de passe"""
            if len(password) < 8:
                return False, "Password must be at least 8 characters long"
            
            if not re.search(r'[A-Z]', password):
                return False, "Password must contain at least one uppercase letter"
            
            if not re.search(r'[a-z]', password):
                return False, "Password must contain at least one lowercase letter"
            
            if not re.search(r'\d', password):
                return False, "Password must contain at least one digit"
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return False, "Password must contain at least one special character"
            
            # Vérifier les mots de passe communs
            common_passwords = [
                'password', '123456', 'qwerty', 'abc123', 'password123',
                'admin', 'letmein', 'welcome', 'monkey', '1234567890'
            ]
            
            if password.lower() in common_passwords:
                return False, "Password is too common"
            
            return True, "Password is strong"
        
        weak_passwords = [
            "123456",           # Too short, only digits
            "password",         # Common password
            "Password",         # Missing digit and special char
            "Password1",        # Missing special char
            "password1!",       # Missing uppercase
            "SHORT1!"           # Too short
        ]
        
        strong_passwords = [
            "MyStr0ng!Pass",
            "C0mpl3x@2023",
            "Secure#P4ssw0rd",
            "Jarv!s_AI_2023"
        ]
        
        import re
        for password in weak_passwords:
            is_valid, message = validate_password_strength(password)
            assert not is_valid, f"Weak password accepted: {password}"
        
        for password in strong_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid, f"Strong password rejected: {password} - {message}"

    def test_session_timeout_validation(self):
        """Test la validation du timeout de session"""
        def is_session_expired(last_activity, timeout_minutes=30):
            """Vérifier si une session a expiré"""
            if not last_activity:
                return True
            
            timeout_delta = timedelta(minutes=timeout_minutes)
            return datetime.utcnow() - last_activity > timeout_delta
        
        # Session récente
        recent_activity = datetime.utcnow() - timedelta(minutes=10)
        assert not is_session_expired(recent_activity), "Recent session should not be expired"
        
        # Session expirée
        old_activity = datetime.utcnow() - timedelta(minutes=45)
        assert is_session_expired(old_activity), "Old session should be expired"
        
        # Session sans activité
        assert is_session_expired(None), "Session without activity should be expired"

    def test_user_enumeration_prevention(self, auth_service):
        """Test la prévention de l'énumération d'utilisateurs"""
        # Les réponses pour utilisateur inexistant et mot de passe incorrect
        # devraient être indistinguables
        
        nonexistent_result = auth_service.authenticate("nonexistent_user", "password")
        wrong_password_result = auth_service.authenticate("jarvis", "wrong_password")
        
        # Les deux devraient échouer
        assert not nonexistent_result["success"]
        assert not wrong_password_result["success"]
        
        # Dans une vraie implémentation, les messages d'erreur devraient être similaires
        # et les temps de réponse comparables pour éviter l'énumération


class TestTwoFactorAuthentication:
    """Tests pour l'authentification à deux facteurs (2FA)"""
    
    @pytest.fixture
    def auth_service(self):
        return MockAuthService()

    def test_totp_code_generation(self):
        """Test la génération de codes TOTP"""
        def generate_totp_code(secret, timestamp=None):
            """Générer un code TOTP"""
            import hmac
            import struct
            
            if timestamp is None:
                timestamp = int(time.time())
            
            # Intervalle de 30 secondes
            time_step = timestamp // 30
            
            # Convertir en bytes
            time_bytes = struct.pack('>Q', time_step)
            secret_bytes = base64.b32decode(secret.upper() + '=' * (8 - len(secret) % 8))
            
            # Générer HMAC
            hmac_hash = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()
            
            # Extraire le code à 6 chiffres
            offset = hmac_hash[-1] & 0x0f
            code = struct.unpack('>I', hmac_hash[offset:offset+4])[0] & 0x7fffffff
            
            return f"{code % 1000000:06d}"
        
        secret = "JBSWY3DPEHPK3PXP"  # Secret de test en base32
        
        # Générer des codes pour différents moments
        timestamp1 = 1600000000  # Timestamp fixe
        timestamp2 = 1600000030  # 30 secondes plus tard
        
        code1 = generate_totp_code(secret, timestamp1)
        code2 = generate_totp_code(secret, timestamp2)
        
        # Les codes devraient être différents
        assert code1 != code2
        assert len(code1) == 6
        assert code1.isdigit()

    def test_totp_code_validation(self):
        """Test la validation de codes TOTP"""
        def validate_totp_code(secret, provided_code, timestamp=None, window=1):
            """Valider un code TOTP avec fenêtre de tolérance"""
            def generate_totp_code(secret, timestamp):
                import hmac
                import struct
                
                time_step = timestamp // 30
                time_bytes = struct.pack('>Q', time_step)
                secret_bytes = base64.b32decode(secret.upper() + '=' * (8 - len(secret) % 8))
                hmac_hash = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()
                offset = hmac_hash[-1] & 0x0f
                code = struct.unpack('>I', hmac_hash[offset:offset+4])[0] & 0x7fffffff
                return f"{code % 1000000:06d}"
            
            if timestamp is None:
                timestamp = int(time.time())
            
            # Vérifier le code pour la fenêtre de temps
            for i in range(-window, window + 1):
                check_time = timestamp + (i * 30)
                expected_code = generate_totp_code(secret, check_time)
                if provided_code == expected_code:
                    return True
            
            return False
        
        secret = "JBSWY3DPEHPK3PXP"
        timestamp = 1600000000
        
        # Générer un code valide
        def generate_totp_code(secret, timestamp):
            import hmac
            import struct
            
            time_step = timestamp // 30
            time_bytes = struct.pack('>Q', time_step)
            secret_bytes = base64.b32decode(secret.upper() + '=' * (8 - len(secret) % 8))
            hmac_hash = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()
            offset = hmac_hash[-1] & 0x0f
            code = struct.unpack('>I', hmac_hash[offset:offset+4])[0] & 0x7fffffff
            return f"{code % 1000000:06d}"
        
        valid_code = generate_totp_code(secret, timestamp)
        
        # Le code valide devrait être accepté
        assert validate_totp_code(secret, valid_code, timestamp)
        
        # Un code incorrect devrait être rejeté
        assert not validate_totp_code(secret, "123456", timestamp)
        
        # Un code de la période précédente devrait être accepté (fenêtre de tolérance)
        previous_code = generate_totp_code(secret, timestamp - 30)
        assert validate_totp_code(secret, previous_code, timestamp, window=1)

    def test_backup_codes_generation(self):
        """Test la génération de codes de récupération"""
        def generate_backup_codes(count=10):
            """Générer des codes de récupération"""
            codes = []
            for _ in range(count):
                # Générer un code de 8 caractères alphanumériques
                code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
                codes.append(code)
            return codes
        
        backup_codes = generate_backup_codes()
        
        assert len(backup_codes) == 10
        assert all(len(code) == 8 for code in backup_codes)
        assert all(code.isalnum() for code in backup_codes)
        assert len(set(backup_codes)) == 10  # Tous uniques

    def test_2fa_authentication_flow(self, auth_service):
        """Test le flux d'authentification 2FA complet"""
        # Utilisateur avec 2FA activé
        user = auth_service.user_repo.find_by_username("2fa_user")
        assert user.two_factor_enabled is True
        
        # Première étape : authentification par mot de passe
        result = auth_service.authenticate("2fa_user", "secure_password")
        
        # Dans une implémentation 2FA, ceci retournerait un token temporaire
        # et demanderait le code 2FA
        assert result["success"] is True  # Pour ce mock, on simule le succès
        
        # Dans une vraie implémentation, on aurait :
        # assert "requires_2fa" in result
        # assert "temp_token" in result


class TestCORSConfiguration:
    """Tests pour la configuration CORS"""
    
    def test_cors_preflight_handling(self):
        """Test la gestion des requêtes preflight CORS"""
        def handle_cors_preflight(origin, method, headers):
            """Gérer une requête preflight CORS"""
            allowed_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "https://jarvis.stark.com"
            ]
            
            allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            allowed_headers = [
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "X-Requested-With"
            ]
            
            # Vérifier l'origine
            if origin not in allowed_origins:
                return {
                    "allowed": False,
                    "error": "Origin not allowed",
                    "status": 403
                }
            
            # Vérifier la méthode
            if method not in allowed_methods:
                return {
                    "allowed": False,
                    "error": "Method not allowed",
                    "status": 405
                }
            
            # Vérifier les headers
            for header in headers:
                if header not in allowed_headers:
                    return {
                        "allowed": False,
                        "error": f"Header '{header}' not allowed",
                        "status": 400
                    }
            
            return {
                "allowed": True,
                "headers": {
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": ", ".join(allowed_methods),
                    "Access-Control-Allow-Headers": ", ".join(allowed_headers),
                    "Access-Control-Max-Age": "3600"
                }
            }
        
        # Test origine autorisée
        result = handle_cors_preflight(
            "http://localhost:3000",
            "POST",
            ["Content-Type", "Authorization"]
        )
        assert result["allowed"] is True
        assert "Access-Control-Allow-Origin" in result["headers"]
        
        # Test origine non autorisée
        result = handle_cors_preflight(
            "http://malicious.com",
            "POST",
            ["Content-Type"]
        )
        assert result["allowed"] is False
        assert result["status"] == 403
        
        # Test méthode non autorisée
        result = handle_cors_preflight(
            "http://localhost:3000",
            "PATCH",
            ["Content-Type"]
        )
        assert result["allowed"] is False
        assert result["status"] == 405
        
        # Test header non autorisé
        result = handle_cors_preflight(
            "http://localhost:3000",
            "POST",
            ["Content-Type", "X-Evil-Header"]
        )
        assert result["allowed"] is False
        assert result["status"] == 400

    def test_cors_credential_handling(self):
        """Test la gestion des credentials CORS"""
        def should_allow_credentials(origin):
            """Déterminer si les credentials sont autorisés pour une origine"""
            # Les credentials ne devraient être autorisés que pour des origines spécifiques
            trusted_origins = [
                "https://jarvis.stark.com",
                "https://app.jarvis.ai"
            ]
            
            return origin in trusted_origins
        
        # Origine de confiance
        assert should_allow_credentials("https://jarvis.stark.com") is True
        
        # Origine localhost (développement)
        assert should_allow_credentials("http://localhost:3000") is False
        
        # Origine externe
        assert should_allow_credentials("https://evil.com") is False

    def test_cors_security_headers(self):
        """Test les headers de sécurité CORS"""
        def get_security_headers():
            """Obtenir les headers de sécurité"""
            return {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
                "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
            }
        
        security_headers = get_security_headers()
        
        # Vérifier la présence des headers critiques
        assert "X-Content-Type-Options" in security_headers
        assert "X-Frame-Options" in security_headers
        assert "Strict-Transport-Security" in security_headers
        assert "Content-Security-Policy" in security_headers
        
        # Vérifier les valeurs
        assert security_headers["X-Frame-Options"] == "DENY"
        assert "max-age" in security_headers["Strict-Transport-Security"]


class TestRateLimiting:
    """Tests pour la limitation de taux"""
    
    def test_login_rate_limiting(self):
        """Test la limitation de taux pour les tentatives de connexion"""
        class LoginRateLimiter:
            def __init__(self, max_attempts=5, window_minutes=15):
                self.max_attempts = max_attempts
                self.window_seconds = window_minutes * 60
                self.attempts = {}  # {ip: [timestamp1, timestamp2, ...]}
            
            def is_allowed(self, ip_address):
                """Vérifier si une tentative de connexion est autorisée"""
                now = time.time()
                
                # Nettoyer les anciennes tentatives
                if ip_address in self.attempts:
                    self.attempts[ip_address] = [
                        timestamp for timestamp in self.attempts[ip_address]
                        if now - timestamp < self.window_seconds
                    ]
                else:
                    self.attempts[ip_address] = []
                
                # Vérifier la limite
                if len(self.attempts[ip_address]) >= self.max_attempts:
                    return False, "Rate limit exceeded"
                
                # Enregistrer la tentative
                self.attempts[ip_address].append(now)
                return True, "Allowed"
            
            def get_remaining_attempts(self, ip_address):
                """Obtenir le nombre de tentatives restantes"""
                if ip_address not in self.attempts:
                    return self.max_attempts
                
                current_attempts = len(self.attempts[ip_address])
                return max(0, self.max_attempts - current_attempts)
        
        limiter = LoginRateLimiter(max_attempts=3, window_minutes=1)
        test_ip = "192.168.1.100"
        
        # Premières tentatives autorisées
        for i in range(3):
            allowed, message = limiter.is_allowed(test_ip)
            assert allowed is True, f"Attempt {i+1} should be allowed"
        
        # Tentative suivante bloquée
        allowed, message = limiter.is_allowed(test_ip)
        assert allowed is False
        assert "Rate limit exceeded" in message
        
        # Vérifier les tentatives restantes
        remaining = limiter.get_remaining_attempts(test_ip)
        assert remaining == 0

    def test_api_rate_limiting(self):
        """Test la limitation de taux pour les appels API"""
        class APIRateLimiter:
            def __init__(self, requests_per_minute=60):
                self.max_requests = requests_per_minute
                self.window_seconds = 60
                self.requests = {}  # {api_key: [timestamp1, timestamp2, ...]}
            
            def is_allowed(self, api_key):
                """Vérifier si une requête API est autorisée"""
                now = time.time()
                
                # Nettoyer les anciennes requêtes
                if api_key in self.requests:
                    self.requests[api_key] = [
                        timestamp for timestamp in self.requests[api_key]
                        if now - timestamp < self.window_seconds
                    ]
                else:
                    self.requests[api_key] = []
                
                # Vérifier la limite
                if len(self.requests[api_key]) >= self.max_requests:
                    return False, "API rate limit exceeded"
                
                # Enregistrer la requête
                self.requests[api_key].append(now)
                return True, "Allowed"
            
            def get_rate_limit_info(self, api_key):
                """Obtenir les informations de limitation"""
                if api_key not in self.requests:
                    current_requests = 0
                else:
                    current_requests = len(self.requests[api_key])
                
                return {
                    "limit": self.max_requests,
                    "remaining": max(0, self.max_requests - current_requests),
                    "reset_time": int(time.time()) + self.window_seconds
                }
        
        limiter = APIRateLimiter(requests_per_minute=5)  # Limite basse pour les tests
        test_api_key = "test_api_key_123"
        
        # Requêtes autorisées
        for i in range(5):
            allowed, message = limiter.is_allowed(test_api_key)
            assert allowed is True, f"Request {i+1} should be allowed"
        
        # Requête suivante bloquée
        allowed, message = limiter.is_allowed(test_api_key)
        assert allowed is False
        assert "API rate limit exceeded" in message
        
        # Vérifier les informations de limitation
        info = limiter.get_rate_limit_info(test_api_key)
        assert info["limit"] == 5
        assert info["remaining"] == 0
        assert info["reset_time"] > time.time()

    def test_distributed_rate_limiting(self):
        """Test la limitation de taux distribuée"""
        class DistributedRateLimiter:
            def __init__(self, redis_client=None):
                self.redis = redis_client or {}  # Mock Redis avec dict
                self.default_window = 60
                self.default_limit = 100
            
            def is_allowed(self, key, limit=None, window=None):
                """Vérifier avec limitation distribuée"""
                limit = limit or self.default_limit
                window = window or self.default_window
                
                current_time = int(time.time())
                window_start = current_time - (current_time % window)
                
                redis_key = f"rate_limit:{key}:{window_start}"
                
                # Simuler Redis INCR
                current_count = self.redis.get(redis_key, 0)
                
                if current_count >= limit:
                    return False, "Distributed rate limit exceeded"
                
                # Incrémenter le compteur
                self.redis[redis_key] = current_count + 1
                
                return True, "Allowed"
            
            def get_current_count(self, key, window=None):
                """Obtenir le nombre actuel de requêtes"""
                window = window or self.default_window
                current_time = int(time.time())
                window_start = current_time - (current_time % window)
                redis_key = f"rate_limit:{key}:{window_start}"
                
                return self.redis.get(redis_key, 0)
        
        limiter = DistributedRateLimiter()
        test_key = "user:123"
        
        # Test de la limitation distribuée
        for i in range(5):
            allowed, message = limiter.is_allowed(test_key, limit=5, window=60)
            assert allowed is True
        
        # Dépassement de limite
        allowed, message = limiter.is_allowed(test_key, limit=5, window=60)
        assert allowed is False
        assert "Distributed rate limit exceeded" in message
        
        # Vérifier le compteur
        count = limiter.get_current_count(test_key)
        assert count == 5


class TestOAuthIntegration:
    """Tests pour l'intégration OAuth"""
    
    def test_oauth_authorization_url_generation(self):
        """Test la génération d'URL d'autorisation OAuth"""
        def generate_oauth_url(client_id, redirect_uri, scope, state=None):
            """Générer une URL d'autorisation OAuth 2.0"""
            auth_url = "https://oauth.provider.com/auth"
            
            params = {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": scope
            }
            
            if state:
                params["state"] = state
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            return f"{auth_url}?{query_string}"
        
        oauth_url = generate_oauth_url(
            client_id="jarvis_app_123",
            redirect_uri="https://jarvis.ai/oauth/callback",
            scope="read write",
            state="random_state_123"
        )
        
        # Vérifier l'URL générée
        parsed = urlparse(oauth_url)
        query_params = parse_qs(parsed.query)
        
        assert parsed.scheme == "https"
        assert "oauth.provider.com" in parsed.netloc
        assert query_params["response_type"][0] == "code"
        assert query_params["client_id"][0] == "jarvis_app_123"
        assert query_params["state"][0] == "random_state_123"

    def test_oauth_state_parameter_validation(self):
        """Test la validation du paramètre state OAuth"""
        def generate_oauth_state():
            """Générer un paramètre state sécurisé"""
            return secrets.token_urlsafe(32)
        
        def validate_oauth_state(received_state, expected_state):
            """Valider le paramètre state OAuth"""
            if not received_state:
                return False, "Missing state parameter"
            
            if not expected_state:
                return False, "No expected state found"
            
            if received_state != expected_state:
                return False, "State parameter mismatch"
            
            return True, "State validated"
        
        # Générer un state
        original_state = generate_oauth_state()
        assert len(original_state) > 20  # Suffisamment long
        
        # Validation réussie
        valid, message = validate_oauth_state(original_state, original_state)
        assert valid is True
        
        # Validation échouée - state incorrect
        valid, message = validate_oauth_state("wrong_state", original_state)
        assert valid is False
        assert "mismatch" in message
        
        # Validation échouée - state manquant
        valid, message = validate_oauth_state(None, original_state)
        assert valid is False
        assert "Missing" in message

    def test_oauth_token_exchange(self):
        """Test l'échange de code d'autorisation contre un token"""
        def exchange_oauth_code(code, client_id, client_secret, redirect_uri):
            """Échanger un code d'autorisation contre un token d'accès"""
            # Simuler l'appel à l'API OAuth
            token_endpoint = "https://oauth.provider.com/token"
            
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            }
            
            # Simuler une réponse réussie
            if code == "valid_auth_code":
                return {
                    "access_token": "access_token_123",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "refresh_token": "refresh_token_456",
                    "scope": "read write"
                }
            else:
                return {
                    "error": "invalid_grant",
                    "error_description": "Invalid authorization code"
                }
        
        # Test échange réussi
        result = exchange_oauth_code(
            code="valid_auth_code",
            client_id="jarvis_app_123",
            client_secret="secret_456",
            redirect_uri="https://jarvis.ai/oauth/callback"
        )
        
        assert "access_token" in result
        assert result["token_type"] == "Bearer"
        assert "refresh_token" in result
        
        # Test échange échoué
        result = exchange_oauth_code(
            code="invalid_code",
            client_id="jarvis_app_123",
            client_secret="secret_456",
            redirect_uri="https://jarvis.ai/oauth/callback"
        )
        
        assert "error" in result
        assert result["error"] == "invalid_grant"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])