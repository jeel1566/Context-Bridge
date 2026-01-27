"""
Context Bridge Agents Package

Exports the main agents for the Sandbox pattern:
- Orchestrator (root_agent) - Main entry point
- Scope Validator (Gemini 3 Flash) - Input/Output validation
- Context Processor (Gemini 3 Pro) - Main processing
- ContextBridgePipeline (SequentialAgent) - Processing pipeline

Based on Google ADK documentation: https://google.github.io/adk-docs/
"""

# Import the main root_agent first (required by ADK)
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

__all__ = [
    # ADK root agent (must be exported)
    'root_agent',
    
    # Main agents
    'orchestrator',
    'context_bridge_pipeline',
    'scope_validator',
    'context_processor',
    
    # Helper functions
    'validate_input',
    'validate_output',
    'process_context',
    'quick_pii_scan',
    'quick_redact',
]
