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
    """
    Build a dictionary of CORS response headers appropriate for the given request origin.
    
    Parameters:
        origin (str): The request's Origin header value; if empty or falsy, headers will allow any origin.
    
    Returns:
        dict: Mapping of CORS header names to values, including `Access-Control-Allow-Origin`,
        allowed methods, allowed headers, max age, and credentials allowance.
    """
    
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
    """
    Attach CORS headers to the given HttpResponse based on the request's Origin header.
    
    Reads the "Origin" header from `req` and uses it to build standard CORS response headers, then sets those headers on `response`.
    
    Parameters:
        response (func.HttpResponse): The response to modify with CORS headers.
        req (func.HttpRequest): The incoming request; its "Origin" header determines the value of Access-Control-Allow-Origin.
    
    Returns:
        func.HttpResponse: The same `response` instance with CORS headers applied.
    """
    origin = req.headers.get("Origin")
    
    headers = get_cors_headers(origin)
    
    for key, value in headers.items():
        response.headers[key] = value
        
    return response

def handle_cors_preflight(req: func.HttpRequest) -> func.HttpResponse:
    """
    Responds to CORS preflight (OPTIONS) requests with the appropriate CORS headers.
    
    Parameters:
        req (func.HttpRequest): Incoming Azure Functions HTTP request; the request's `Origin` header is read to build response CORS headers.
    
    Returns:
        func.HttpResponse: An HTTP response with status code 204 (No Content) and CORS headers derived from the request's `Origin` (or `"*"` if the origin is missing).
    """
    origin = req.headers.get("Origin")
    
    return func.HttpResponse(
        body=None,
        status_code=204,
        headers=get_cors_headers(origin)
    )