"""
Context Bridge Agents Package

Exports the main agents for the Sandbox pattern.
ADK agents are optional - basic memory operations work without them.
"""

# Try to import ADK agents, but make it optional
try:
    from .agent import (
        root_agent,
        orchestrator,
        context_bridge_pipeline,
    )
    
    from .scope_validator import (
        scope_validator,
        validate_input,
        validate_output
    )
    
    from .context_processor import (
        context_processor,
        process_context,
        quick_pii_scan,
        quick_redact
    )
    
    ADK_AVAILABLE = True
    
    __all__ = [
        'root_agent',
        'orchestrator',
        'context_bridge_pipeline',
        'scope_validator',
        'context_processor',
        'validate_input',
        'validate_output',
        'process_context',
        'quick_pii_scan',
        'quick_redact',
        'ADK_AVAILABLE',
    ]
    
except ImportError as e:
    # ADK not installed - that's OK, basic memory operations still work
    import logging
    logging.warning(f"Google ADK not available: {e}. AI agent features disabled.")
    
    ADK_AVAILABLE = False
    root_agent = None
    orchestrator = None
    context_bridge_pipeline = None
    scope_validator = None
    context_processor = None
    
    def validate_input(*args, **kwargs):
        return {"valid": True, "message": "ADK not available"}
    
    def validate_output(*args, **kwargs):
        return {"valid": True, "message": "ADK not available"}
    
    def process_context(*args, **kwargs):
        return {"processed": False, "message": "ADK not available"}
    
    def quick_pii_scan(*args, **kwargs):
        return {"contains_pii": False, "message": "ADK not available"}
    
    def quick_redact(*args, **kwargs):
        return args[0] if args else ""
    
    __all__ = [
        'ADK_AVAILABLE',
        'validate_input',
        'validate_output',
        'process_context',
        'quick_pii_scan',
        'quick_redact',
    ]
