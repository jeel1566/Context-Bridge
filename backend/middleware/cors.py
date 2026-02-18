"""
CORS Middleware
Handle Cross-Origin Resource Sharing (CORS) headers and preflight requests.
"""

import azure.functions as func

# Allowed origins
ALLOWED_ORIGINS = [
    "https://chat.openai.com",
    "https://chatgpt.com",
    "https://claude.ai",
    "https://gemini.google.com",
    "chrome-extension://dcjnolonjjjpcabfbndhmapgdaahhade" # Development ID
]

def get_cors_headers(origin: str) -> dict:
    """Get CORS headers for a specific origin."""
    
    # Allow all origins for now to simplify debugging context-bridge issues
    # In production, this should be stricter
    return {
        "Access-Control-Allow-Origin": origin if origin else "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, x-session-id",
        "Access-Control-Max-Age": "86400",
        "Access-Control-Allow-Credentials": "true"
    }

def apply_cors_headers(response: func.HttpResponse, req: func.HttpRequest) -> func.HttpResponse:
    """Apply CORS headers to an existing response."""
    origin = req.headers.get("Origin")
    
    headers = get_cors_headers(origin)
    
    for key, value in headers.items():
        response.headers[key] = value
        
    return response

def handle_cors_preflight(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight (OPTIONS) request."""
    origin = req.headers.get("Origin")
    
    return func.HttpResponse(
        body=None,
        status_code=204,
        headers=get_cors_headers(origin)
    )
