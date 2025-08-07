import pytest
import os
import hashlib
import secrets
from unittest.mock import patch

# This is a bit of a hack to import from a parent directory.
# In a real-world scenario, this project should be structured as a proper package.
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../services/system-control')))

from main import PasswordManager

class TestPasswordManager:
    """
    Unit tests for the PasswordManager class in the system-control service.
    These tests verify the core security functions of password hashing and verification.
    """

    def test_hash_password_creates_valid_hash_and_salt(self):
        """
        Tests that hash_password returns a valid hash and salt in hex format.
        """
        password = "my_super_secret_password"
        pwd_hash, salt_hex = PasswordManager.hash_password(password)

        assert isinstance(pwd_hash, str)
        assert isinstance(salt_hex, str)
        assert len(pwd_hash) == 64  # SHA256 hash is 32 bytes -> 64 hex chars
        assert len(salt_hex) == 64  # Salt is 32 bytes -> 64 hex chars

        # Ensure they are valid hex strings
        bytes.fromhex(pwd_hash)
        bytes.fromhex(salt_hex)

    def test_verify_password_with_correct_password(self):
        """
        Tests that verify_password returns True for the correct password.
        """
        password = "a_very_secure_password_123!"
        pwd_hash, salt_hex = PasswordManager.hash_password(password)

        assert PasswordManager.verify_password(password, pwd_hash, salt_hex) is True

    def test_verify_password_with_incorrect_password(self):
        """
        Tests that verify_password returns False for an incorrect password.
        """
        password = "a_very_secure_password_123!"
        incorrect_password = "not_the_right_password"
        pwd_hash, salt_hex = PasswordManager.hash_password(password)

        assert PasswordManager.verify_password(incorrect_password, pwd_hash, salt_hex) is False

    def test_verify_password_with_different_salts(self):
        """
        Tests that two identical passwords hashed with different salts produce different hashes
        but both verify correctly.
        """
        password = "password123"

        # Hash the password twice, which should use different salts
        hash1, salt1 = PasswordManager.hash_password(password)
        hash2, salt2 = PasswordManager.hash_password(password)

        # Hashes and salts should be different
        assert hash1 != hash2
        assert salt1 != salt2

        # Both should verify correctly with their respective hash and salt
        assert PasswordManager.verify_password(password, hash1, salt1) is True
        assert PasswordManager.verify_password(password, hash2, salt2) is True

    def test_verify_password_handles_invalid_hex(self):
        """
        Tests that verify_password handles malformed hex strings gracefully and returns False.
        """
        password = "some_password"
        pwd_hash, salt_hex = PasswordManager.hash_password(password)

        # Invalid hash and salt
        assert PasswordManager.verify_password(password, "invalid-hex", salt_hex) is False
        assert PasswordManager.verify_password(password, pwd_hash, "invalid-hex") is False

    @patch.dict(os.environ, {
        "SYSTEM_CONTROL_ADMIN_USER": "test_admin",
        "SYSTEM_CONTROL_ADMIN_PASSWORD_HASH": "d8a2e7a32247b19b784a0d54e48b3f2c9e4c1b2a9e8d7f6e5c4b3a2918e7d6c5",
        "SYSTEM_CONTROL_ADMIN_PASSWORD_SALT": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    })
    def test_get_secure_credentials_from_env(self):
        """
        Tests that get_secure_credentials correctly loads credentials from environment variables.
        """
        credentials = PasswordManager.get_secure_credentials()

        assert "test_admin" in credentials
        admin_creds = credentials["test_admin"]
        assert admin_creds["hash"] == "d8a2e7a32247b19b784a0d54e48b3f2c9e4c1b2a9e8d7f6e5c4b3a2918e7d6c5"
        assert admin_creds["salt"] == "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"

    def test_get_secure_credentials_empty_when_env_vars_missing(self):
        """
        Tests that get_secure_credentials returns an empty dict if no env vars are set.
        """
        # Ensure the environment variables are not set for this test
        with patch.dict(os.environ, {}, clear=True):
            credentials = PasswordManager.get_secure_credentials()
            assert credentials == {}

if __name__ == "__main__":
    pytest.main()
