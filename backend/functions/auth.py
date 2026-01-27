"""
Auth Function - Google OAuth 2.0 Authentication

Endpoints:
- POST /api/auth/google - Verify Google ID token
- GET /api/auth/user - Get current user info
"""

import azure.functions as func
import json
import logging
import os
from typing import Optional

try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
except ImportError:
    # Fallback for local dev without google-auth
    id_token = None
    google_requests = None


# In-memory user store (replace with Cosmos DB)
USER_STORE = {}


async def auth_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Handle authentication requests."""
    
    path = req.url.split('/api/auth/')[-1]
    method = req.method
    
    try:
        if path == 'google' and method == 'POST':
            return await verify_google_token(req)
        elif path == 'user' and method == 'GET':
            return get_current_user(req)
        else:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Invalid auth endpoint"}),
                mimetype="application/json",
                status_code=404
            )
    except Exception as e:
        logging.error(f"Auth error: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )


async def verify_google_token(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/auth/google - Verify Google ID token and create/login user."""
    
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Invalid JSON"}),
            mimetype="application/json",
            status_code=400
        )
    
    token = body.get('idToken')
    
    if not token:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Missing idToken"}),
            mimetype="application/json",
            status_code=400
        )
    
    # Get Google Client ID from environment
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    
    if not client_id:
        logging.error("GOOGLE_CLIENT_ID not configured")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Auth not configured"}),
            mimetype="application/json",
            status_code=500
        )
    
    try:
        # Verify the token with Google
        if id_token and google_requests:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                client_id
            )
        else:
            # Mock for local development
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
        
        # Create or update user
        user = USER_STORE.get(user_id, {})
        user.update({
            "id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "lastLogin": req.headers.get('X-Timestamp', '')
        })
        USER_STORE[user_id] = user
        
        # Generate session token (simplified - use JWT in production)
        import secrets
        session_token = secrets.token_urlsafe(32)
        
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
                    "token": session_token
                }
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError as e:
        logging.error(f"Invalid token: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Invalid token"}),
            mimetype="application/json",
            status_code=401
        )


def get_current_user(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/auth/user - Get current authenticated user."""
    
    user_id = req.headers.get('X-User-Id')
    
    if not user_id:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Not authenticated"}),
            mimetype="application/json",
            status_code=401
        )
    
    user = USER_STORE.get(user_id)
    
    if not user:
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "User not found"}),
            mimetype="application/json",
            status_code=404
        )
    
    return func.HttpResponse(
        json.dumps({
            "status": "success",
            "data": user
        }),
        mimetype="application/json",
        status_code=200
    )
