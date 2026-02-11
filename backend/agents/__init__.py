"""
Context Bridge Agents Package

Simple import for ADK discovery.
Imports are wrapped in try/except to handle missing optional dependencies
(e.g., google-adk[extensions] not installed).
"""

try:
    from .agent import (
        root_agent,
        context_bridge_pipeline,
        scope_validator,
        context_processor,
        validate_input,
        validate_output,
        process_context,
    )
    __all__ = [
        'root_agent',
        'context_bridge_pipeline',
        'scope_validator',
        'context_processor',
        'validate_input',
        'validate_output',
        'process_context',
    ]
except ImportError:
    # ADK extensions (LiteLLM) not installed - individual modules can
    # still be imported directly when their dependencies are available
    pass
