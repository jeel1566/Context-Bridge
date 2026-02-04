"""
Session Service Singleton Manager for ADK Agents

Provides a shared InMemorySessionService instance to prevent memory leaks
from creating new sessions on every agent call.

Usage:
    from backend.agents.session_manager import get_session_service
    
    session = get_session_service()  # Returns singleton instance
    response = await runner.run(agent=my_agent, session_service=session)
"""
from google.adk.sessions import InMemorySessionService
import logging

logger = logging.getLogger(__name__)

# Module-level singleton
_session_service: InMemorySessionService | None = None


def get_session_service() -> InMemorySessionService:
    """
    Get or create the shared session service singleton.
    
    This function is thread-safe for async usage and ensures only one
    InMemorySessionService instance is created and reused across all
    agent calls, preventing memory leaks.
    
    Returns:
        InMemorySessionService: The singleton session service instance
    """
    global _session_service
    
    if _session_service is None:
        logger.info("Creating singleton InMemorySessionService")
        _session_service = InMemorySessionService()
    
    return _session_service


def reset_session_service() -> None:
    """
    Reset the session service singleton.
    
    Useful for testing or when you need to clear all session state.
    In production, this should rarely (if ever) be called.
    """
    global _session_service
    
    if _session_service is not None:
        logger.warning("Resetting session service singleton")
        _session_service = None
