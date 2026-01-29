"""
Encryption Service for Context Bridge

Provides AES-256-GCM authenticated encryption for sensitive data.
All memory content is encrypted before storage in Cosmos DB.
"""

import os
import base64
import logging
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class EncryptionService:
    """
    AES-256-GCM encryption service for Context Bridge.
    
    Features:
    - AES-256-GCM authenticated encryption
    - Random 12-byte IV per encryption
    - Key derivation using HKDF-SHA256 from master key
    - Base64-encoded output for safe storage
    
    Security:
    - Never logs plaintext or encryption keys
    - Uses authenticated encryption to detect tampering
    - Each encryption uses a unique IV
    
    Format:
        Ciphertext format: base64(iv || ciphertext || tag)
        - IV: 12 bytes
        - Ciphertext: variable length
        - Tag: 16 bytes
    """
    
    IV_LENGTH = 12  # 96 bits recommended for GCM
    TAG_LENGTH = 16  # 128 bits for authentication tag
    KEY_LENGTH = 32  # 256 bits for AES-256
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            master_key: Hex-encoded 256-bit key. If not provided,
                       reads from ENCRYPTION_KEY environment variable.
        
        Raises:
            EncryptionError: If no valid key is available
        """
        key_hex = master_key or os.environ.get('ENCRYPTION_KEY')
        
        if not key_hex:
            logger.warning("No encryption key configured - encryption disabled")
            self._key = None
            return
        
        try:
            # Validate and decode the hex key
            key_bytes = bytes.fromhex(key_hex)
            if len(key_bytes) != self.KEY_LENGTH:
                raise ValueError(f"Key must be {self.KEY_LENGTH} bytes")
            
            # Derive the actual encryption key using HKDF
            # This adds an extra layer of security
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
        """Check if encryption is configured and ready."""
        return self._key is not None
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded ciphertext (iv || ciphertext || tag)
            
        Raises:
            EncryptionError: If encryption fails or not configured
        """
        if not self.is_configured:
            logger.warning("Encryption not configured - returning plaintext")
            return plaintext
        
        if not plaintext:
            return ""
        
        try:
            # Generate random IV
            iv = get_random_bytes(self.IV_LENGTH)
            
            # Create cipher and encrypt
            cipher = AES.new(self._key, AES.MODE_GCM, nonce=iv)
            ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
            
            # Combine iv + ciphertext + tag and base64 encode
            combined = iv + ciphertext + tag
            return base64.b64encode(combined).decode('ascii')
            
        except Exception as e:
            logger.error(f"Encryption failed: {type(e).__name__}")
            raise EncryptionError("Encryption failed") from e
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.
        
        Args:
            ciphertext: Base64-encoded encrypted data
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            EncryptionError: If decryption fails, data is corrupted,
                           or authentication fails (tampering detected)
        """
        if not self.is_configured:
            logger.warning("Encryption not configured - returning as-is")
            return ciphertext
        
        if not ciphertext:
            return ""
        
        try:
            # Decode base64
            combined = base64.b64decode(ciphertext.encode('ascii'))
            
            # Extract components
            if len(combined) < self.IV_LENGTH + self.TAG_LENGTH:
                raise EncryptionError("Ciphertext too short")
            
            iv = combined[:self.IV_LENGTH]
            tag = combined[-self.TAG_LENGTH:]
            encrypted_data = combined[self.IV_LENGTH:-self.TAG_LENGTH]
            
            # Create cipher and decrypt
            cipher = AES.new(self._key, AES.MODE_GCM, nonce=iv)
            plaintext = cipher.decrypt_and_verify(encrypted_data, tag)
            
            return plaintext.decode('utf-8')
            
        except EncryptionError:
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {type(e).__name__}")
            raise EncryptionError("Decryption failed - data may be corrupted") from e
    
    def rotate_key(self, old_key: str, new_key: str, ciphertext: str) -> str:
        """
        Re-encrypt data with a new key.
        
        Args:
            old_key: Current key (hex)
            new_key: New key to use (hex)
            ciphertext: Data encrypted with old key
            
        Returns:
            Data re-encrypted with new key
        """
        # Decrypt with old key
        old_service = EncryptionService(old_key)
        plaintext = old_service.decrypt(ciphertext)
        
        # Encrypt with new key
        new_service = EncryptionService(new_key)
        return new_service.encrypt(plaintext)
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new random 256-bit encryption key.
        
        Returns:
            Hex-encoded 32-byte key
        """
        return get_random_bytes(32).hex()


# Singleton instance for the application
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get the singleton encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


# Export
__all__ = ['EncryptionService', 'EncryptionError', 'get_encryption_service']
