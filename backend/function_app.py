"""
Context Bridge - Azure Functions Backend
Main application entry point
"""

import azure.functions as func
import logging
import json

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
# Diagnostic (TEMPORARY - remove after debugging)
# ============================================
@app.route(route="debug/imports", methods=["GET"])
def debug_imports(req: func.HttpRequest) -> func.HttpResponse:
    """Diagnostic endpoint to check which imports work/fail on Azure."""
    import traceback
    results = {}
    
    # Test each import that the 503 endpoints need
    test_imports = [
        ("azure.functions", "import azure.functions"),
        ("azure.cosmos", "from azure.cosmos import CosmosClient"),
        ("jwt (PyJWT)", "import jwt"),
        ("pycryptodome", "from Crypto.Cipher import AES"),
        ("google.auth", "from google.auth.transport import requests"),
        ("google.oauth2", "from google.oauth2 import id_token"),
        ("services", "from services import get_cosmos_service, get_encryption_service"),
        ("services.jwt_service", "from services.jwt_service import get_jwt_service"),
        ("middleware", "from middleware import require_auth, handle_exception"),
        ("middleware.supabase_auth", "from middleware.supabase_auth import validate_supabase_jwt"),
        ("middleware.cors", "from middleware.cors import apply_cors_headers"),
        ("middleware.errors", "from middleware.errors import ValidationError"),
        ("functions.memories", "from functions.memories import memories_handler"),
        ("functions.auth", "from functions.auth import auth_handler"),
        ("functions.share", "from functions.share import share_handler"),
        ("functions.sync", "from functions.sync import sync_handler"),
        ("functions.sanitize", "from functions.sanitize import sanitize_handler"),
        ("agents", "from agents import validate_input, validate_output, process_context"),
    ]
    
    for name, import_stmt in test_imports:
        try:
            exec(import_stmt)
            results[name] = {"status": "ok"}
        except Exception as e:
            results[name] = {
                "status": "FAILED",
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()[-500:]
            }
    
    return func.HttpResponse(
        json.dumps({"diagnostic": results}, indent=2),
        mimetype="application/json",
        status_code=200
    )

# ============================================
# Sandbox Processing
# ============================================
@app.route(route="sanitize", methods=["POST"])
def sanitize(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/sanitize - Main Sandbox processing endpoint"""
    try:
        from functions.sanitize import sanitize_handler
        return sanitize_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import sanitize_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

@app.route(route="curate", methods=["POST"])
def curate(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/curate - Format context for target LLM"""
    try:
        from functions.curate import curate_handler
        return curate_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import curate_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

# ============================================
# Memory Bank CRUD
# ============================================
@app.route(route="memories", methods=["GET", "POST"])
async def memories(req: func.HttpRequest) -> func.HttpResponse:
    """GET/POST /api/memories"""
    try:
        from functions.memories import memories_handler
        return await memories_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import memories_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

@app.route(route="memories/{id}", methods=["GET", "PUT", "DELETE"])
async def memory_by_id(req: func.HttpRequest) -> func.HttpResponse:
    """GET/PUT/DELETE /api/memories/:id"""
    try:
        from functions.memories import memories_handler
        return await memories_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import memories_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

# ============================================
# Collaboration
# ============================================
@app.route(route="share", methods=["POST"])
def share(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/share - Generate share link"""
    try:
        from functions.share import share_handler
        return share_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import share_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

@app.route(route="shared/{share_code}", methods=["GET"])
def shared(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/shared/:shareCode - Access shared bank"""
    try:
        from functions.share import share_handler
        return share_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import share_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

# ============================================
# Authentication
# ============================================
@app.route(route="auth/google", methods=["POST"])
def auth_google(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/auth/google - Verify Google ID token"""
    try:
        from functions.auth import auth_handler
        return auth_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import auth_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

@app.route(route="auth/user", methods=["GET"])
def auth_user(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/auth/user - Get current user info"""
    try:
        from functions.auth import auth_handler
        return auth_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import auth_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

@app.route(route="auth/refresh", methods=["POST"])
def auth_refresh(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/auth/refresh - Refresh access token"""
    try:
        from functions.auth import auth_handler
        return auth_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import auth_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

# ============================================
# Sync
# ============================================
@app.route(route="sync", methods=["POST"])
def sync(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/sync - Sync memories across devices"""
    try:
        from functions.sync import sync_handler
        return sync_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import sync_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )

@app.route(route="sync/status", methods=["GET"])
def sync_status(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/sync/status - Get sync status"""
    try:
        from functions.sync import sync_handler
        return sync_handler(req)
    except ImportError as e:
        logging.error(f"Failed to import sync_handler: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Service unavailable due to missing dependencies"}),
            status_code=503
        )
