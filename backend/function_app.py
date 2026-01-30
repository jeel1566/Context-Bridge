"""
Context Bridge - Azure Functions Backend
Main application entry point
"""

import azure.functions as func
import logging
import json

# Import function handlers
from functions.sanitize import sanitize_handler
from functions.curate import curate_handler
from functions.memories import memories_handler
from functions.share import share_handler
from functions.auth import auth_handler

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ============================================
# Health Check
# ============================================
@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "context-bridge"}),
        mimetype="application/json",
        status_code=200
    )

# ============================================
# Sandbox Processing
# ============================================
@app.route(route="sanitize", methods=["POST"])
def sanitize(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/sanitize - Main Sandbox processing endpoint"""
    return sanitize_handler(req)

@app.route(route="curate", methods=["POST"])
def curate(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/curate - Format context for target LLM"""
    return curate_handler(req)

# ============================================
# Memory Bank CRUD
# ============================================
@app.route(route="memories", methods=["GET", "POST"])
async def memories(req: func.HttpRequest) -> func.HttpResponse:
    """GET/POST /api/memories"""
    return await memories_handler(req)

@app.route(route="memories/{id}", methods=["GET", "PUT", "DELETE"])
async def memory_by_id(req: func.HttpRequest) -> func.HttpResponse:
    """GET/PUT/DELETE /api/memories/:id"""
    return await memories_handler(req)

# ============================================
# Collaboration
# ============================================
@app.route(route="share", methods=["POST"])
def share(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/share - Generate share link"""
    return share_handler(req)

@app.route(route="shared/{share_code}", methods=["GET"])
def shared(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/shared/:shareCode - Access shared bank"""
    return share_handler(req)

# ============================================
# Authentication
# ============================================
@app.route(route="auth/google", methods=["POST"])
def auth_google(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/auth/google - Verify Google ID token"""
    return auth_handler(req)

@app.route(route="auth/user", methods=["GET"])
def auth_user(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/auth/user - Get current user info"""
    return auth_handler(req)

@app.route(route="auth/refresh", methods=["POST"])
def auth_refresh(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/auth/refresh - Refresh access token"""
    return auth_handler(req)

# ============================================
# Sync
# ============================================
from functions.sync import sync_handler

@app.route(route="sync", methods=["POST"])
def sync(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/sync - Sync memories across devices"""
    return sync_handler(req)

@app.route(route="sync/status", methods=["GET"])
def sync_status(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/sync/status - Get sync status"""
    return sync_handler(req)
