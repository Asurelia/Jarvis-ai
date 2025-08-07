#!/usr/bin/env python3
"""
JARVIS AI - Configuration Management System
Centralized configuration with environment-specific settings, secrets management, and feature flags
"""

import os
import json
import yaml
import logging
import hashlib
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import boto3
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConfigValue:
    """Represents a configuration value with metadata"""
    value: Any
    encrypted: bool = False
    environment: str = "all"
    feature_flag: bool = False
    description: str = ""
    last_updated: str = ""
    expires_at: Optional[str] = None

@dataclass
class FeatureFlag:
    """Represents a feature flag configuration"""
    name: str
    enabled: bool
    environments: List[str]
    rollout_percentage: int = 0
    conditions: Dict[str, Any] = None
    description: str = ""
    created_at: str = ""
    expires_at: Optional[str] = None

class SecretProvider:
    """Abstract base class for secret providers"""
    
    def get_secret(self, key: str) -> str:
        raise NotImplementedError
    
    def set_secret(self, key: str, value: str) -> bool:
        raise NotImplementedError
    
    def delete_secret(self, key: str) -> bool:
        raise NotImplementedError

class FileSecretProvider(SecretProvider):
    """File-based secret provider with encryption"""
    
    def __init__(self, secrets_dir: str, encryption_key: str):
        self.secrets_dir = Path(secrets_dir)
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        self.cipher = self._initialize_cipher(encryption_key)
    
    def _initialize_cipher(self, key: str) -> Fernet:
        """Initialize encryption cipher"""
        key_bytes = key.encode()
        digest = hashes.Hash(hashes.SHA256())
        digest.update(key_bytes)
        derived_key = base64.urlsafe_b64encode(digest.finalize()[:32])
        return Fernet(derived_key)
    
    def get_secret(self, key: str) -> str:
        secret_file = self.secrets_dir / f"{key}.enc"
        if not secret_file.exists():
            raise KeyError(f"Secret '{key}' not found")
        
        encrypted_data = secret_file.read_bytes()
        return self.cipher.decrypt(encrypted_data).decode()
    
    def set_secret(self, key: str, value: str) -> bool:
        try:
            secret_file = self.secrets_dir / f"{key}.enc"
            encrypted_data = self.cipher.encrypt(value.encode())
            secret_file.write_bytes(encrypted_data)
            return True
        except Exception as e:
            logger.error(f"Failed to set secret '{key}': {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        try:
            secret_file = self.secrets_dir / f"{key}.enc"
            secret_file.unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret '{key}': {e}")
            return False

class AWSSecretsManagerProvider(SecretProvider):
    """AWS Secrets Manager provider"""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    def get_secret(self, key: str) -> str:
        try:
            response = self.client.get_secret_value(SecretId=key)
            return response['SecretString']
        except Exception as e:
            logger.error(f"Failed to get AWS secret '{key}': {e}")
            raise KeyError(f"Secret '{key}' not found")
    
    def set_secret(self, key: str, value: str) -> bool:
        try:
            self.client.create_secret(Name=key, SecretString=value)
            return True
        except self.client.exceptions.ResourceExistsException:
            self.client.update_secret(SecretId=key, SecretString=value)
            return True
        except Exception as e:
            logger.error(f"Failed to set AWS secret '{key}': {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        try:
            self.client.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete AWS secret '{key}': {e}")
            return False

class AzureKeyVaultProvider(SecretProvider):
    """Azure Key Vault provider"""
    
    def __init__(self, vault_url: str):
        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)
    
    def get_secret(self, key: str) -> str:
        try:
            secret = self.client.get_secret(key)
            return secret.value
        except Exception as e:
            logger.error(f"Failed to get Azure secret '{key}': {e}")
            raise KeyError(f"Secret '{key}' not found")
    
    def set_secret(self, key: str, value: str) -> bool:
        try:
            self.client.set_secret(key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set Azure secret '{key}': {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        try:
            self.client.begin_delete_secret(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete Azure secret '{key}': {e}")
            return False

class ConfigurationManager:
    """Centralized configuration management system"""
    
    def __init__(self, 
                 config_dir: str = "./devops/config",
                 environment: str = "development",
                 secret_provider: Optional[SecretProvider] = None):
        self.config_dir = Path(config_dir)
        self.environment = environment
        self.secret_provider = secret_provider
        self.config_cache = {}
        self.feature_flags = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all configuration files"""
        logger.info(f"Loading configurations for environment: {self.environment}")
        
        # Load base configuration
        base_config_file = self.config_dir / "base.yml"
        if base_config_file.exists():
            with open(base_config_file) as f:
                base_config = yaml.safe_load(f)
                self._merge_config(base_config)
        
        # Load environment-specific configuration
        env_config_file = self.config_dir / f"{self.environment}.yml"
        if env_config_file.exists():
            with open(env_config_file) as f:
                env_config = yaml.safe_load(f)
                self._merge_config(env_config)
        
        # Load feature flags
        self._load_feature_flags()
        
        logger.info(f"Loaded {len(self.config_cache)} configuration values")
    
    def _merge_config(self, config: Dict[str, Any], prefix: str = ""):
        """Merge configuration into cache"""
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict) and not self._is_config_value(value):
                self._merge_config(value, full_key)
            else:
                if self._is_config_value(value):
                    config_value = ConfigValue(**value)
                else:
                    config_value = ConfigValue(value=value)
                
                self.config_cache[full_key] = config_value
    
    def _is_config_value(self, value: Any) -> bool:
        """Check if value is a ConfigValue structure"""
        return (isinstance(value, dict) and 
                'value' in value and 
                any(key in value for key in ['encrypted', 'environment', 'feature_flag']))
    
    def _load_feature_flags(self):
        """Load feature flags configuration"""
        flags_file = self.config_dir / "feature-flags.yml"
        if flags_file.exists():
            with open(flags_file) as f:
                flags_data = yaml.safe_load(f)
                for name, flag_data in flags_data.items():
                    self.feature_flags[name] = FeatureFlag(name=name, **flag_data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            config_value = self.config_cache.get(key)
            if not config_value:
                return default
            
            # Check environment filter
            if (config_value.environment != "all" and 
                config_value.environment != self.environment):
                return default
            
            # Check if value is expired
            if config_value.expires_at:
                expires_at = datetime.fromisoformat(config_value.expires_at)
                if datetime.now() > expires_at:
                    logger.warning(f"Configuration '{key}' has expired")
                    return default
            
            # Handle encrypted values
            if config_value.encrypted and self.secret_provider:
                try:
                    return self.secret_provider.get_secret(key)
                except KeyError:
                    logger.warning(f"Encrypted value for '{key}' not found in secret provider")
                    return default
            
            # Handle feature flag values
            if config_value.feature_flag:
                if not self.is_feature_enabled(key):
                    return default
            
            return config_value.value
        
        except Exception as e:
            logger.error(f"Error getting configuration '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, **kwargs) -> bool:
        """Set configuration value"""
        try:
            config_value = ConfigValue(
                value=value,
                last_updated=datetime.now().isoformat(),
                **kwargs
            )
            
            # Handle encrypted values
            if config_value.encrypted and self.secret_provider:
                if not self.secret_provider.set_secret(key, str(value)):
                    return False
                config_value.value = "[ENCRYPTED]"
            
            self.config_cache[key] = config_value
            return True
        
        except Exception as e:
            logger.error(f"Error setting configuration '{key}': {e}")
            return False
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if feature flag is enabled"""
        feature = self.feature_flags.get(feature_name)
        if not feature:
            return False
        
        # Check environment
        if self.environment not in feature.environments and "all" not in feature.environments:
            return False
        
        # Check if expired
        if feature.expires_at:
            expires_at = datetime.fromisoformat(feature.expires_at)
            if datetime.now() > expires_at:
                return False
        
        # Check rollout percentage
        if feature.rollout_percentage < 100:
            # Simple hash-based rollout
            hash_input = f"{feature_name}-{self.environment}".encode()
            hash_value = int(hashlib.md5(hash_input).hexdigest()[:8], 16)
            rollout_bucket = hash_value % 100
            return rollout_bucket < feature.rollout_percentage
        
        return feature.enabled
    
    def get_database_url(self) -> str:
        """Get database URL with proper secret handling"""
        host = self.get("database.host", "localhost")
        port = self.get("database.port", 5432)
        database = self.get("database.name", "jarvis")
        username = self.get("database.username", "jarvis")
        password = self.get("database.password")
        
        if not password:
            raise ValueError("Database password not configured")
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def get_redis_url(self) -> str:
        """Get Redis URL with proper secret handling"""
        host = self.get("redis.host", "localhost")
        port = self.get("redis.port", 6379)
        password = self.get("redis.password")
        database = self.get("redis.database", 0)
        
        if password:
            return f"redis://:{password}@{host}:{port}/{database}"
        return f"redis://{host}:{port}/{database}"
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Get Ollama configuration"""
        return {
            "url": self.get("ollama.url", "http://localhost:11434"),
            "model": self.get("ollama.model", "jarvis-gpt-oss-20b"),
            "timeout": self.get("ollama.timeout", 120),
            "retry_count": self.get("ollama.retry_count", 3),
            "health_check_interval": self.get("ollama.health_check_interval", 30)
        }
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration for deployment"""
        config = {}
        
        for key, config_value in self.config_cache.items():
            # Skip environment-specific values for other environments
            if (config_value.environment != "all" and 
                config_value.environment != self.environment):
                continue
            
            # Skip expired values
            if config_value.expires_at:
                expires_at = datetime.fromisoformat(config_value.expires_at)
                if datetime.now() > expires_at:
                    continue
            
            # Handle encrypted values
            if config_value.encrypted:
                if include_secrets and self.secret_provider:
                    try:
                        config[key] = self.secret_provider.get_secret(key)
                    except KeyError:
                        config[key] = "[SECRET_NOT_FOUND]"
                else:
                    config[key] = "[ENCRYPTED]"
            else:
                config[key] = config_value.value
        
        return config
    
    def generate_env_file(self, output_path: str):
        """Generate .env file for Docker Compose"""
        config = self.export_config(include_secrets=True)
        
        with open(output_path, 'w') as f:
            f.write(f"# JARVIS AI Configuration - {self.environment.upper()}\n")
            f.write(f"# Generated at: {datetime.now().isoformat()}\n\n")
            
            # Group related configurations
            groups = {}
            for key, value in config.items():
                prefix = key.split('.')[0]
                if prefix not in groups:
                    groups[prefix] = {}
                groups[prefix][key] = value
            
            for group_name, group_config in groups.items():
                f.write(f"# {group_name.upper()} Configuration\n")
                for key, value in group_config.items():
                    env_key = key.upper().replace('.', '_')
                    f.write(f"{env_key}={value}\n")
                f.write("\n")
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Required configurations
        required_configs = [
            "database.password",
            "redis.password",
            "jwt.secret_key",
            "api.secret_key"
        ]
        
        for config_key in required_configs:
            if not self.get(config_key):
                issues.append(f"Required configuration '{config_key}' is not set")
        
        # Check for expired configurations
        for key, config_value in self.config_cache.items():
            if config_value.expires_at:
                expires_at = datetime.fromisoformat(config_value.expires_at)
                if datetime.now() > expires_at:
                    issues.append(f"Configuration '{key}' has expired")
        
        # Validate feature flags
        for name, feature in self.feature_flags.items():
            if feature.expires_at:
                expires_at = datetime.fromisoformat(feature.expires_at)
                if datetime.now() > expires_at:
                    issues.append(f"Feature flag '{name}' has expired")
        
        return issues

def main():
    """CLI interface for configuration management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS AI Configuration Manager")
    parser.add_argument("--environment", "-e", default="development", 
                       help="Environment name")
    parser.add_argument("--config-dir", "-c", default="./devops/config",
                       help="Configuration directory")
    parser.add_argument("--action", "-a", required=True,
                       choices=["get", "set", "export", "validate", "generate-env"],
                       help="Action to perform")
    parser.add_argument("--key", "-k", help="Configuration key")
    parser.add_argument("--value", "-v", help="Configuration value")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    # Initialize secret provider based on environment
    secret_provider = None
    if os.getenv("AWS_SECRET_MANAGER"):
        secret_provider = AWSSecretsManagerProvider()
    elif os.getenv("AZURE_KEY_VAULT_URL"):
        secret_provider = AzureKeyVaultProvider(os.getenv("AZURE_KEY_VAULT_URL"))
    else:
        # Use file-based provider
        encryption_key = os.getenv("CONFIG_ENCRYPTION_KEY", "default-key")
        secret_provider = FileSecretProvider("./devops/secrets", encryption_key)
    
    config_manager = ConfigurationManager(
        config_dir=args.config_dir,
        environment=args.environment,
        secret_provider=secret_provider
    )
    
    if args.action == "get":
        if not args.key:
            parser.error("--key is required for get action")
        value = config_manager.get(args.key)
        print(f"{args.key}: {value}")
    
    elif args.action == "set":
        if not args.key or not args.value:
            parser.error("--key and --value are required for set action")
        success = config_manager.set(args.key, args.value)
        print(f"Set {args.key}: {'Success' if success else 'Failed'}")
    
    elif args.action == "export":
        config = config_manager.export_config()
        print(json.dumps(config, indent=2))
    
    elif args.action == "validate":
        issues = config_manager.validate_configuration()
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("Configuration validation passed")
    
    elif args.action == "generate-env":
        output_path = args.output or f".env.{args.environment}"
        config_manager.generate_env_file(output_path)
        print(f"Environment file generated: {output_path}")

if __name__ == "__main__":
    main()