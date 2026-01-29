"""
Services package for Context Bridge

Provides core infrastructure services:
- encryption: AES-256-GCM encryption for stored data
- cosmos: Azure Cosmos DB storage with in-memory fallback
- jwt_service: JWT authentication tokens
"""

from .encryption import EncryptionService, EncryptionError, get_encryption_service
from .jwt_service import JWTService, JWTError, TokenExpiredError, TokenInvalidError, get_jwt_service
from .cosmos import CosmosService, get_cosmos_service

__all__ = [
    # Encryption
    'EncryptionService',
    'EncryptionError',
    'get_encryption_service',
    
    # JWT
    'JWTService',
    'JWTError',
    'TokenExpiredError',
    'TokenInvalidError',
    'get_jwt_service',
    
    # Cosmos DB
    'CosmosService',
    'get_cosmos_service',
]
