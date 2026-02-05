"""
Test timeout protection for agents

Tests verify that:
1. Agents have reasonable timeout limits
2. Timeout results in fail-closed response (denied, not allowed)
3. Normal fast responses still work
"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from backend.agents.scope_validator import validate_input
from backend.agents.context_processor import process_context


@pytest.mark.asyncio
async def test_validation_times_out_on_slow_llm():
    """Verify validation times out if LLM takes too long"""
    # This test will FAIL until we implement timeout
    # Expected: Should timeout after ~30 seconds
    # Actual (before fix): Would hang forever
    
    with patch('backend.agents.scope_validator.scope_validator') as mock_agent:
        # Mock a slow LLM that takes 60 seconds
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(60)  # Simulate slow API
            return AsyncMock(content='{"allowed": true}')
        
        mock_agent.return_value = slow_response()
        
        # Should timeout in ~30s, not wait 60s
        start = asyncio.get_event_loop().time()
        result = await validate_input("test input")
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should timeout before 35 seconds
        assert elapsed < 35, f"Validation took {elapsed}s - should timeout at 30s"


@pytest.mark.asyncio
async def test_validation_fails_closed_on_timeout():
    """Verify timeout results in DENIAL, not allow"""
    # This test will FAIL until we implement fail-closed timeout
    
    with patch('backend.agents.scope_validator.scope_validator') as mock_agent:
        # Mock hanging LLM
        async def hanging_response(*args, **kwargs):
            await asyncio.sleep(100)
            return AsyncMock(content='{"allowed": true}')
        
        mock_agent.return_value = hanging_response()
        
        result = await validate_input("valid context management request")
        
        # CRITICAL: Must deny on timeout (fail-closed)
        assert result["allowed"] == False, "Timeout must fail-closed (deny)"
        assert "timeout" in result["reason"].lower(), "Reason should mention timeout"


@pytest.mark.asyncio
async def test_fast_validation_still_works():
    """Verify timeout doesn't break normal fast responses"""
    # Normal case should work fine with timeout protection
    result = await validate_input("Save my coding preferences")
    
    # Should get real validation result (not timeout)
    assert "allowed" in result
    assert "timeout" not in result.get("reason", "").lower()


@pytest.mark.asyncio
async def test_context_processing_has_timeout():
    """Verify context processor also has timeout protection"""
    # Same pattern for context_processor
    
    with patch('backend.agents.context_processor.context_processor') as mock_agent:
        async def hanging_response(*args, **kwargs):
            await asyncio.sleep(100)
            return AsyncMock(content='{}')
        
       mock_agent.return_value = hanging_response()
        
        result = await process_context("test context", personality="quick-answer")
        
        # Should timeout and fail gracefully
        assert "error" in result or "timeout" in str(result).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
