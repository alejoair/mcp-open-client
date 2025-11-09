"""
Encryption utilities for secure data storage
"""
import os
import logging
from typing import Optional
from cryptography.fernet import Fernet
from pathlib import Path

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Handles encryption and decryption of sensitive data"""

    def __init__(self, config_dir: Path):
        self.key_file = config_dir / ".encryption_key"
        self._cipher_suite: Optional[Fernet] = None
        self._init_encryption()

    def _init_encryption(self):
        """Initialize encryption key"""
        try:
            if self.key_file.exists():
                # Load existing key
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions (600)
                os.chmod(self.key_file, 0o600)

            self._cipher_suite = Fernet(key)
            logger.info("Encryption initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self._cipher_suite = None

    def encrypt_value(self, value: str) -> Optional[str]:
        """Encrypt a string value"""
        if not self._cipher_suite or not value:
            return None

        try:
            encrypted_bytes = self._cipher_suite.encrypt(value.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt value: {e}")
            return None

    def decrypt_value(self, encrypted_value: str) -> Optional[str]:
        """Decrypt a string value"""
        if not self._cipher_suite or not encrypted_value:
            return None

        try:
            decrypted_bytes = self._cipher_suite.decrypt(encrypted_value.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            return None

    @property
    def is_initialized(self) -> bool:
        """Check if encryption is properly initialized"""
        return self._cipher_suite is not None