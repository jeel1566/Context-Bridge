"""
Encryption Service for Context Bridge

Provides AES-256-GCM authenticated encryption for sensitive data.
Falls back to no encryption if pycryptodome is not installed.
"""

import os
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Crypto - make it optional
try:
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    from Crypto.Protocol.KDF import HKDF
    from Crypto.Hash import SHA256
    CRYPTO_AVAILABLE = True
except ImportError:
    logger.warning("pycryptodome not installed - encryption disabled")
    CRYPTO_AVAILABLE = False
    AES = None
    get_random_bytes = None
    HKDF = None
    SHA256 = None


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class EncryptionService:
    """
    AES-256-GCM encryption service for Context Bridge.
    Falls back to plaintext if pycryptodome is not available.
    """
    
    IV_LENGTH = 12
    TAG_LENGTH = 16
    KEY_LENGTH = 32
    
    def __init__(self, master_key: Optional[str] = None):
        if not CRYPTO_AVAILABLE:
            logger.warning("Crypto not available - encryption disabled")
            self._key = None
            return
            
        key_hex = master_key or os.environ.get('ENCRYPTION_KEY')
        
        if not key_hex:
            logger.warning("No encryption key configured - encryption disabled")
            self._key = None
            return
        
        try:
            key_bytes = bytes.fromhex(key_hex)
            if len(key_bytes) != self.KEY_LENGTH:
                raise ValueError(f"Key must be {self.KEY_LENGTH} bytes")
            
            self._key = HKDF(
                master=key_bytes,
                key_len=self.KEY_LENGTH,
                salt=b'ContextBridge_v1',
                hashmod=SHA256,
                context=b'encryption'
            )
            logger.info("Encryption service initialized successfully")
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid encryption key format: {e}")
            raise EncryptionError(f"Invalid encryption key: {e}")
    
    @property
    def is_configured(self) -> bool:
        return self._key is not None and CRYPTO_AVAILABLE
    
    def encrypt(self, plaintext: str) -> str:
        if not self.is_configured:
            return plaintext
        
        if not plaintext:
            return ""
        
        try:
            iv = get_random_bytes(self.IV_LENGTH)
            cipher = AES.new(self._key, AES.MODE_GCM, nonce=iv)
            ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
            combined = iv + ciphertext + tag
            return base64.b64encode(combined).decode('ascii')
        except Exception as e:
            logger.error(f"Encryption failed: {type(e).__name__}")
            raise EncryptionError("Encryption failed") from e
    
    def decrypt(self, ciphertext: str) -> str:
        if not self.is_configured:
            return ciphertext
        
        if not ciphertext:
            return ""
        
        try:
            combined = base64.b64decode(ciphertext.encode('ascii'))
            if len(combined) < self.IV_LENGTH + self.TAG_LENGTH:
                raise EncryptionError("Ciphertext too short")
            
            iv = combined[:self.IV_LENGTH]
            tag = combined[-self.TAG_LENGTH:]
            encrypted_data = combined[self.IV_LENGTH:-self.TAG_LENGTH]
            
            cipher = AES.new(self._key, AES.MODE_GCM, nonce=iv)
            plaintext = cipher.decrypt_and_verify(encrypted_data, tag)
            return plaintext.decode('utf-8')
        except EncryptionError:
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {type(e).__name__}")
            raise EncryptionError("Decryption failed") from e
    
    @staticmethod
    def generate_key() -> str:
        if CRYPTO_AVAILABLE:
            return get_random_bytes(32).hex()
        return os.urandom(32).hex()


_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


__all__ = ['EncryptionService', 'EncryptionError', 'get_encryption_service', 'CRYPTO_AVAILABLE']
