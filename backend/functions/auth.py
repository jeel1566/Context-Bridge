"""
Auth Function - Google OAuth 2.0 Authentication with JWT

Endpoints:
- POST /api/auth/google - Verify Google ID token and issue JWT
- POST /api/auth/refresh - Refresh access token
- GET /api/auth/user - Get current user info
"""

import azure.functions as func
import json
import logging
import os
from typing import Optional
from datetime import datetime

from services import get_cosmos_service, get_jwt_service
from middleware import (
    require_json_body,
    require_fields,
    handle_exception,
    require_auth,
    ValidationError,
    AuthenticationError,
)

logger = logging.getLogger(__name__)

try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
except ImportError:
    id_token = None
    google_requests = None


async def auth_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Handle authentication requests."""
    
    path = req.url.split('/api/auth/')[-1].split('?')[0]
    method = req.method
    
    try:
        if path == 'google' and method == 'POST':
            return await verify_google_token(req)
        elif path == 'refresh' and method == 'POST':
            return await refresh_token(req)
        elif path == 'user' and method == 'GET':
            return await get_current_user(req)
        else:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Invalid auth endpoint"}),
                mimetype="application/json",
                status_code=404
            )
    except Exception as e:
        return handle_exception(e)


async def verify_google_token(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/auth/google - Verify Google ID token and issue JWT."""
    
    body = require_json_body(req)
    
    token = body.get('idToken')
    if not token:
        raise ValidationError("Missing idToken field")
    
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    
    if not client_id:
        logger.error("GOOGLE_CLIENT_ID not configured")
        raise AuthenticationError("Authentication not configured")
    
    try:
        # Verify the token with Google
        if id_token and google_requests:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                client_id
            )
        else:
            # Mock for local development without google-auth
            logger.warning("Google auth not available - using mock for development")
            idinfo = {
                "sub": "mock-user-id",
                "email": "dev@example.com",
                "name": "Dev User",
                "picture": ""
            }
        
        user_id = idinfo['sub']
        email = idinfo.get('email', '')
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')
        
        # Get or create user in storage
        cosmos = get_cosmos_service()
        existing_user = await cosmos.users.read(user_id)
        
        now = datetime.utcnow().isoformat() + 'Z'
        
        if existing_user:
            # Update existing user
            user = existing_user
            user['lastLogin'] = now
            user['name'] = name  # Update in case it changed
            user['picture'] = picture
            await cosmos.users.update(user_id, user)
        else:
            # Create new user
            user = {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "createdAt": now,
                "lastLogin": now
            }
            await cosmos.users.create(user)
        
        # Generate JWT tokens
        jwt_service = get_jwt_service()
        
        if jwt_service.is_configured:
            tokens = jwt_service.create_tokens(
                user_id=user_id,
                email=email,
                extra_claims={"name": name}
            )
        else:
            # Fallback for development without JWT configured
            import secrets
            logger.warning("JWT not configured - using insecure token")
            tokens = {
                "access_token": secrets.token_urlsafe(32),
                "refresh_token": secrets.token_urlsafe(32),
                "token_type": "bearer",
                "expires_in": 900
            }
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "data": {
                    "user": {
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "picture": picture
                    },
                    **tokens
                }
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError as e:
        logger.error(f"Invalid token: {e}")
        raise AuthenticationError("Invalid Google token")


async def refresh_token(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/auth/refresh - Refresh access token using refresh token."""
    
    body = require_json_body(req)
    
    refresh_token = body.get('refreshToken') or body.get('refresh_token')
    if not refresh_token:
        raise ValidationError("Missing refreshToken field")
    
    jwt_service = get_jwt_service()
    
    if not jwt_service.is_configured:
        raise AuthenticationError("Token refresh not available")
    
    try:
        tokens = jwt_service.refresh_access_token(refresh_token)
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "data": tokens
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        raise AuthenticationError("Invalid or expired refresh token")


async def get_current_user(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/auth/user - Get current authenticated user."""
    
    user = require_auth(req)
    user_id = user['id']
    
    # Get full user data from storage
    cosmos = get_cosmos_service()
    stored_user = await cosmos.users.read(user_id)
    
    if not stored_user:
        # User exists in token but not in database (edge case)
        stored_user = {
            "id": user_id,
            "email": user.get('email'),
        }
    
    # Remove sensitive fields
    stored_user.pop('_rid', None)
    stored_user.pop('_self', None)
    stored_user.pop('_etag', None)
    stored_user.pop('_attachments', None)
    stored_user.pop('_ts', None)
    
    return func.HttpResponse(
        json.dumps({
            "status": "success",
            "data": stored_user
        }),
        mimetype="application/json",
        status_code=200
    )
