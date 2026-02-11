"""
Context Bridge Agents Package

Simple import for ADK discovery.
Imports are wrapped in try/except to handle missing optional dependencies
(e.g., google-adk[extensions] not installed).
"""

try:
    from . import agent
except ImportError:
    # ADK extensions (LiteLLM) not installed - individual modules can
    # still be imported directly when their dependencies are available
    pass
