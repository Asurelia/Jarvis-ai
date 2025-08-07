#!/usr/bin/env python3
"""
[LOCK] JARVIS AI 2025 - Environment Security Validation Script
Validates .env configuration for security compliance and completeness.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
import secrets
import string

class SecurityValidator:
    def __init__(self, env_path: str = ".env"):
        self.env_path = Path(env_path)
        self.env_vars = {}
        self.issues = []
        self.warnings = []
        self.critical_vars = {
            'POSTGRES_PASSWORD', 'REDIS_PASSWORD', 'JWT_SECRET_KEY',
            'SYSTEM_CONTROL_ADMIN_PASSWORD', 'SYSTEM_CONTROL_JARVIS_PASSWORD',
            'GRAFANA_ADMIN_PASSWORD', 'SSL_CERT_PASSWORD'
        }
        self.required_vars = {
            # Database
            'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
            # Security
            'JWT_SECRET_KEY', 'JWT_ALGORITHM', 'JWT_EXPIRATION_HOURS',
            # Redis
            'REDIS_PASSWORD', 'REDIS_MAXMEMORY', 'REDIS_MAXMEMORY_POLICY',
            # Services
            'REDIS_URL', 'MEMORY_DB_URL', 'OLLAMA_URL',
            # Ports
            'BRAIN_API_PORT', 'TTS_SERVICE_PORT', 'STT_SERVICE_PORT',
            'SYSTEM_CONTROL_PORT', 'TERMINAL_SERVICE_PORT', 'MCP_GATEWAY_PORT',
            # Security mode
            'SECURITY_MODE', 'SANDBOX_MODE', 'SAFE_MODE',
        }
    
    def load_env_file(self) -> bool:
        """Load environment variables from .env file."""
        if not self.env_path.exists():
            self.issues.append(f"CRITICAL: .env file not found at {self.env_path}")
            return False
        
        try:
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.env_vars[key.strip()] = value.strip()
            return True
        except Exception as e:
            self.issues.append(f"CRITICAL: Failed to load .env file: {e}")
            return False
    
    def validate_password_strength(self, password: str, min_length: int = 20) -> Tuple[bool, str]:
        """Validate password strength according to security standards."""
        if len(password) < min_length:
            return False, f"Password too short (minimum {min_length} characters)"
        
        checks = {
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'digits': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))
        }
        
        failed_checks = [check for check, passed in checks.items() if not passed]
        if failed_checks:
            return False, f"Password missing: {', '.join(failed_checks)}"
        
        # Check for common weak patterns
        weak_patterns = [
            r'123456', r'password', r'admin123', r'qwerty',
            r'(.)\1{3,}',  # Repeated characters
            r'(.)(.)\1\2',  # Simple patterns
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                return False, "Password contains weak patterns"
        
        return True, "Strong password"
    
    def validate_jwt_secret(self, secret: str) -> Tuple[bool, str]:
        """Validate JWT secret strength."""
        if len(secret) < 64:
            return False, "JWT secret too short (minimum 64 characters for HS256)"
        
        # Check entropy (should be base64-like or high entropy)
        if secret.count('=') > 2:  # Likely base64
            try:
                import base64
                decoded = base64.b64decode(secret + '==')  # Padding
                if len(decoded) < 32:
                    return False, "JWT secret has insufficient entropy"
            except:
                pass  # Not base64, check entropy differently
        
        # Check character diversity
        unique_chars = len(set(secret))
        if unique_chars < 20:
            return False, "JWT secret has insufficient character diversity"
        
        return True, "Strong JWT secret"
    
    def validate_urls(self) -> None:
        """Validate service URLs format and security."""
        url_vars = ['REDIS_URL', 'MEMORY_DB_URL', 'OLLAMA_URL']
        
        for var in url_vars:
            if var not in self.env_vars:
                self.issues.append(f"[X] MISSING: {var} is required")
                continue
            
            url = self.env_vars[var]
            
            # Check for hardcoded passwords in URLs
            if 'localhost' not in url and '127.0.0.1' not in url and 'memory-db' not in url and 'redis' not in url and 'ollama' not in url:
                self.warnings.append(f"[\!]  WARNING: {var} uses external host - ensure secure connection")
            
            # Check Redis URL format
            if var == 'REDIS_URL':
                if not url.startswith('redis://'):
                    self.issues.append(f"[X] INVALID: {var} must start with redis://")
                if ':@' in url:
                    self.issues.append(f"[X] SECURITY: {var} has empty password")
            
            # Check PostgreSQL URL format
            if var == 'MEMORY_DB_URL':
                if not url.startswith('postgresql://'):
                    self.issues.append(f"[X] INVALID: {var} must start with postgresql://")
    
    def validate_ports(self) -> None:
        """Validate port configurations."""
        port_vars = {
            'BRAIN_API_PORT': (5000, 5010),
            'TTS_SERVICE_PORT': (5000, 5010),
            'STT_SERVICE_PORT': (5000, 5010),
            'SYSTEM_CONTROL_PORT': (5000, 5010),
            'TERMINAL_SERVICE_PORT': (5000, 5010),
            'MCP_GATEWAY_PORT': (5000, 5010),
            'FRONTEND_PORT': (3000, 3010),
        }
        
        used_ports = set()
        
        for var, (min_port, max_port) in port_vars.items():
            if var not in self.env_vars:
                self.warnings.append(f"[\!]  MISSING: {var} not configured")
                continue
            
            try:
                port = int(self.env_vars[var])
                if not (min_port <= port <= max_port):
                    self.warnings.append(f"[\!]  WARNING: {var}={port} outside recommended range {min_port}-{max_port}")
                
                if port in used_ports:
                    self.issues.append(f"[X] CONFLICT: Port {port} used by multiple services")
                else:
                    used_ports.add(port)
                    
            except ValueError:
                self.issues.append(f"[X] INVALID: {var} must be a valid port number")
    
    def validate_security_settings(self) -> None:
        """Validate security-related settings."""
        security_checks = {
            'SECURITY_MODE': ['development', 'production'],
            'SANDBOX_MODE': ['true', 'false'],
            'SAFE_MODE': ['true', 'false'],
            'DEBUG_MODE': ['true', 'false'],
            'DISABLE_DEBUG_ENDPOINTS': ['true', 'false'],
            'ENABLE_RATE_LIMITING': ['true', 'false'],
        }
        
        for var, valid_values in security_checks.items():
            if var not in self.env_vars:
                self.warnings.append(f"[\!]  MISSING: {var} not configured")
                continue
            
            value = self.env_vars[var].lower()
            if value not in valid_values:
                self.issues.append(f"[X] INVALID: {var}='{value}' must be one of {valid_values}")
        
        # Check production security
        if self.env_vars.get('SECURITY_MODE') == 'production':
            production_checks = {
                'DEBUG_MODE': 'false',
                'DISABLE_DEBUG_ENDPOINTS': 'true',
                'ENABLE_RATE_LIMITING': 'true',
                'PROD_ENABLE_HTTPS': 'true',
                'PROD_ENABLE_CSRF_PROTECTION': 'true',
            }
            
            for var, expected in production_checks.items():
                actual = self.env_vars.get(var, '').lower()
                if actual != expected:
                    self.issues.append(f"[X] PRODUCTION: {var} should be '{expected}' in production mode")
    
    def check_changeme_values(self) -> None:
        """Check for unchanged CHANGEME values."""
        for key, value in self.env_vars.items():
            if 'CHANGEME' in value.upper():
                self.issues.append(f"[X] CRITICAL: {key} still contains CHANGEME placeholder")
    
    def validate_critical_passwords(self) -> None:
        """Validate all critical passwords."""
        for var in self.critical_vars:
            if var not in self.env_vars:
                self.issues.append(f"[X] CRITICAL: {var} is missing")
                continue
            
            password = self.env_vars[var]
            
            if var == 'JWT_SECRET_KEY':
                valid, msg = self.validate_jwt_secret(password)
                if not valid:
                    self.issues.append(f"[X] JWT: {var} - {msg}")
            else:
                valid, msg = self.validate_password_strength(password)
                if not valid:
                    self.issues.append(f"[X] PASSWORD: {var} - {msg}")
    
    def check_required_variables(self) -> None:
        """Check for all required environment variables."""
        missing = self.required_vars - set(self.env_vars.keys())
        if missing:
            for var in sorted(missing):
                self.issues.append(f"[X] MISSING: {var} is required")
    
    def check_docker_compatibility(self) -> None:
        """Check Docker Compose compatibility."""
        docker_specific = {
            'REDIS_URL': 'redis:6379',
            'MEMORY_DB_URL': 'memory-db:5432',
            'OLLAMA_URL': 'ollama:11434',
        }
        
        for var, expected_host in docker_specific.items():
            if var in self.env_vars:
                url = self.env_vars[var]
                if expected_host not in url:
                    self.warnings.append(f"[\!]  DOCKER: {var} may not work with Docker Compose (expected {expected_host})")
    
    def generate_security_report(self) -> str:
        """Generate comprehensive security report."""
        report = []
        report.append("JARVIS AI 2025 - Environment Security Validation Report")
        report.append("=" * 60)
        report.append(f"Total Variables: {len(self.env_vars)}")
        report.append(f"Critical Variables: {len(self.critical_vars & set(self.env_vars.keys()))}/{len(self.critical_vars)}")
        report.append(f"Required Variables: {len(self.required_vars & set(self.env_vars.keys()))}/{len(self.required_vars)}")
        report.append("")
        
        if self.issues:
            report.append("CRITICAL ISSUES:")
            for issue in self.issues:
                report.append(f"  {issue}")
            report.append("")
        
        if self.warnings:
            report.append("WARNINGS:")
            for warning in self.warnings:
                report.append(f"  {warning}")
            report.append("")
        
        # Security score
        total_checks = len(self.issues) + len(self.warnings)
        if total_checks == 0:
            report.append("SECURITY STATUS: EXCELLENT - No issues found!")
        elif len(self.issues) == 0:
            report.append(f"SECURITY STATUS: GOOD - {len(self.warnings)} warnings to review")
        else:
            report.append(f"SECURITY STATUS: NEEDS ATTENTION - {len(self.issues)} critical issues")
        
        return "\n".join(report)
    
    def run_validation(self) -> bool:
        """Run complete validation suite."""
        print("Starting JARVIS AI environment security validation...")
        
        if not self.load_env_file():
            return False
        
        print(f"Loaded {len(self.env_vars)} environment variables")
        
        # Run all validation checks
        self.check_changeme_values()
        self.check_required_variables()
        self.validate_critical_passwords()
        self.validate_urls()
        self.validate_ports()
        self.validate_security_settings()
        self.check_docker_compatibility()
        
        # Generate and display report
        report = self.generate_security_report()
        print("\n" + report)
        
        return len(self.issues) == 0

def main():
    """Main validation function."""
    validator = SecurityValidator()
    
    if validator.run_validation():
        print("\nEnvironment validation completed successfully!")
        sys.exit(0)
    else:
        print("\nEnvironment validation failed! Please fix critical issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()