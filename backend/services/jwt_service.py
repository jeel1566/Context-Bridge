"""
JWT Service for Context Bridge

Provides JWT-based authentication with access and refresh tokens.
Replaces insecure session tokens with industry-standard JWT.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError

logger = logging.getLogger(__name__)


class JWTError(Exception):
    """Raised when JWT operations fail."""
    pass


class TokenExpiredError(JWTError):
    """Raised when a token has expired."""
    pass


class TokenInvalidError(JWTError):
    """Raised when a token is invalid."""
    pass


class JWTService:
    """
    JWT authentication service for Context Bridge.
    
    Features:
    - Access tokens (short-lived, 15 min default)
    - Refresh tokens (long-lived, 7 days default)
    - Token validation with proper error handling
    - Claims extraction for user context
    
    Token Claims:
    - sub: User ID (subject)
    - email: User email
    - exp: Expiration time
    - iat: Issued at time
    - type: Token type (access/refresh)
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_expire_minutes: int = 15,
        refresh_expire_days: int = 7
    ):
        """
        Initialize JWT service.
        
        Args:
            secret_key: Secret key for signing. If not provided,
                       reads from JWT_SECRET_KEY environment variable.
            algorithm: JWT algorithm (default: HS256)
            access_expire_minutes: Access token lifespan in minutes
            refresh_expire_days: Refresh token lifespan in days
        """
        self._secret_key = secret_key or os.environ.get('JWT_SECRET_KEY')
        self._algorithm = algorithm
        self._access_expire_minutes = access_expire_minutes
        self._refresh_expire_days = refresh_expire_days
        
        if not self._secret_key:
            logger.warning("No JWT secret key configured - JWT disabled")
        elif len(self._secret_key) < 32:
            logger.warning("JWT secret key is too short (< 32 chars)")
    
    @property
    def is_configured(self) -> bool:
        """Check if JWT is configured and ready."""
        return bool(self._secret_key and len(self._secret_key) >= 32)
    
    def create_access_token(
        self,
        user_id: str,
        email: Optional[str] = None,
        extra_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an access token.
        
        Args:
            user_id: User identifier (becomes 'sub' claim)
            email: Optional user email
            extra_claims: Additional claims to include
            
        Returns:
            Encoded JWT access token
        """
        return self._create_token(
            user_id=user_id,
            email=email,
            token_type="access",
            expires_delta=timedelta(minutes=self._access_expire_minutes),
            extra_claims=extra_claims
        )
    
    def create_refresh_token(
        self,
        user_id: str,
        email: Optional[str] = None
    ) -> str:
        """
        Create a refresh token.
        
        Args:
            user_id: User identifier
            email: Optional user email
            
        Returns:
            Encoded JWT refresh token
        """
        return self._create_token(
            user_id=user_id,
            email=email,
            token_type="refresh",
            expires_delta=timedelta(days=self._refresh_expire_days)
        )
    
    def create_tokens(
        self,
        user_id: str,
        email: Optional[str] = None,
        extra_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Create both access and refresh tokens.
        
        Args:
            user_id: User identifier
            email: Optional user email
            extra_claims: Additional claims for access token
            
        Returns:
            Dict with 'access_token' and 'refresh_token'
        """
        return {
            "access_token": self.create_access_token(user_id, email, extra_claims),
            "refresh_token": self.create_refresh_token(user_id, email),
            "token_type": "bearer",
            "expires_in": self._access_expire_minutes * 60  # seconds
        }
    
    def _create_token(
        self,
        user_id: str,
        token_type: str,
        expires_delta: timedelta,
        email: Optional[str] = None,
        extra_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Internal method to create a token."""
        if not self.is_configured:
            raise JWTError("JWT not configured - missing or invalid secret key")
        
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        
        claims = {
            "sub": user_id,
            "iat": now,
            "exp": expire,
            "type": token_type,
        }
        
        if email:
            claims["email"] = email
        
        if extra_claims:
            claims.update(extra_claims)
        
        return jwt.encode(claims, self._secret_key, algorithm=self._algorithm)
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode an access token.
        
        Args:
            token: Encoded JWT token
            
        Returns:
            Decoded token claims
            
        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
        """
        claims = self._verify_token(token)
        
        if claims.get("type") != "access":
            raise TokenInvalidError("Not an access token")
        
        return claims
    
    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a refresh token.
        
        Args:
            token: Encoded JWT token
            
        Returns:
            Decoded token claims
            
        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
        """
        claims = self._verify_token(token)
        
        if claims.get("type") != "refresh":
            raise TokenInvalidError("Not a refresh token")
        
        return claims
    
    def _verify_token(self, token: str) -> Dict[str, Any]:
        """Internal method to verify a token."""
        if not self.is_configured:
            raise JWTError("JWT not configured - missing or invalid secret key")
        
        try:
            claims = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
            return claims
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise TokenInvalidError("Invalid token")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Use a refresh token to get a new access token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dict with new 'access_token' (refresh token unchanged)
        """
        claims = self.verify_refresh_token(refresh_token)
        
        return {
            "access_token": self.create_access_token(
                user_id=claims["sub"],
                email=claims.get("email")
            ),
            "token_type": "bearer",
            "expires_in": self._access_expire_minutes * 60
        }
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extract user ID from a token without full validation.
        Useful for logging/debugging. Does not verify signature.
        
        Args:
            token: JWT token
            
        Returns:
            User ID or None if extraction fails
        """
        try:
            # Decode without verification (for debugging only)
            claims = jwt.decode(token, options={"verify_signature": False})
            return claims.get("sub")
        except Exception:
            return None


# Singleton instance
_jwt_service: Optional[JWTService] = None


def get_jwt_service() -> JWTService:
    """Get the singleton JWT service instance."""
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTService()
    return _jwt_service


# Export
__all__ = [
    'JWTService',
    'JWTError',
    'TokenExpiredError',
    'TokenInvalidError',
    'get_jwt_service'
]
