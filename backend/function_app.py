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
# Sandbox Processing
# ============================================
@app.route(route="sanitize", methods=["POST"])
def sanitize(req: func.HttpRequest) -> func.HttpResponse:
    """
    Process sandbox input from the HTTP request and return a JSON HttpResponse.
    
    Parameters:
        req (func.HttpRequest): Incoming HTTP request containing the data to sanitize.
    
    Returns:
        func.HttpResponse: JSON response with the processing result on success. If required dependencies are missing, returns a 503 Service Unavailable response with `{"status": "error", "message": "Service unavailable due to missing dependencies"}`.
    """
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
    """
    Prepare and return curated context formatted for a target LLM.
    
    Parameters:
        req (func.HttpRequest): Incoming HTTP request containing data to be curated.
    
    Returns:
        func.HttpResponse: JSON response with curated context on success. If required dependencies are missing, returns a JSON error message with HTTP status 503.
    """
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
    """
    Handle HTTP GET and POST requests for the /memories endpoint.
    
    Parameters:
        req (func.HttpRequest): The incoming HTTP request for the /memories route.
    
    Returns:
        func.HttpResponse: The HTTP response produced by the memory handler. If required dependencies are missing, returns a 503 response with JSON: `{"status": "error", "message": "Service unavailable due to missing dependencies"}`.
    """
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
    """
    Handle GET, PUT, and DELETE requests for a memory identified by ID and return the resulting HTTP response.
    
    Returns:
        func.HttpResponse: The response produced by the memory service for the requested operation. If required dependencies are unavailable, returns a JSON error response with HTTP status code 503.
    """
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
    """
    Create a share link for the provided HTTP request.
    
    Processes the incoming request to generate and return a shareable link. If required dependencies are missing, returns an HTTP 503 response with a JSON error message.
    
    Parameters:
        req (func.HttpRequest): The incoming HTTP request containing share data.
    
    Returns:
        func.HttpResponse: A JSON HTTP response containing the share information on success, or `{"status": "error", "message": "<reason>"}` with status code 503 when dependencies are unavailable.
    """
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
    """
    Handle HTTP requests to retrieve a shared memory bank identified by a share code.
    
    @returns func.HttpResponse containing the shared bank data on success, or a JSON error response with HTTP 503 when required dependencies are unavailable.
    """
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
    """
    Handle a Google ID token verification request for the /api/auth/google endpoint.
    
    Parameters:
        req (func.HttpRequest): Incoming HTTP request expected to contain a Google ID token (typically in the request body or Authorization header).
    
    Returns:
        func.HttpResponse: HTTP response containing a JSON object with the verification result. If required dependencies are missing, returns a 503 response with an error message.
    """
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
    """
    Get current authenticated user's information.
    
    Returns:
        func.HttpResponse: HTTP response containing user information in JSON on success; if required handler dependencies are missing, a 503 response with a JSON error message.
    """
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
    """
    Refreshes an authentication access token using the provided HTTP request.
    
    Parameters:
        req (func.HttpRequest): The incoming HTTP request for the refresh operation.
    
    Returns:
        func.HttpResponse: The HTTP response from the auth handler, or a 503 Service Unavailable
        response containing a JSON error message if required dependencies cannot be imported.
    """
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
    """
    Synchronizes memories across devices.
    
    Delegates the request to the sync handler and returns its HTTP response. If the sync handler cannot be imported, returns a 503 HttpResponse with a JSON error message.
    
    Parameters:
        req (azure.functions.HttpRequest): The incoming HTTP request.
    
    Returns:
        azure.functions.HttpResponse: The handler's response, or a 503 response with `{"status":"error","message":"Service unavailable due to missing dependencies"}` when dependencies are unavailable.
    """
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