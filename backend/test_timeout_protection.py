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
@pytest.mark.asyncio
async def test_validation_times_out_on_slow_llm():
    """Verify validation times out if LLM takes too long"""
    # This test will FAIL until we implement timeout
    # Expected: Should timeout after ~30 seconds
    # Actual (before fix): Would hang forever
    
    with patch('backend.agents.scope_validator.Runner') as MockRunner:
        # Mock a slow LLM that takes 60 seconds
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(60)  # Simulate slow API
            yield "ignore" # Yield dummy value for async generator
        
        MockRunner.return_value.run_async.side_effect = slow_response
        
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
    
    with patch('backend.agents.scope_validator.Runner') as MockRunner:
        # Mock hanging LLM
        async def hanging_response(*args, **kwargs):
            await asyncio.sleep(100)
            yield "ignore"
        
        MockRunner.return_value.run_async.side_effect = hanging_response
        
        result = await validate_input("valid context management request")
        
        # CRITICAL: Must deny on timeout (fail-closed)
        assert result["allowed"] == False, "Timeout must fail-closed (deny)"
        assert "timeout" in result["reason"].lower(), "Reason should mention timeout"


@pytest.mark.asyncio
async def test_fast_validation_still_works():
    """Verify timeout doesn't break normal fast responses"""
    # Normal case should work fine with timeout protection
    # We need to mock Runner for success case too if we don't want to call real API
    
    with patch('backend.agents.scope_validator.Runner') as MockRunner:
        # return a valid response event stream
        async def success_response(*args, **kwargs):
            # We need to mock the Event structure... this is complex.
            # But wait, validate_input calls run_async and iterates events.
            # We can mock yield of an Event object with content parts.
            from unittest.mock import MagicMock
            event = MagicMock()
            event.author = "model"
            part = MagicMock()
            part.text = '{"allowed": true, "reason": "valid"}'
            event.content.parts = [part]
            yield event
            
        MockRunner.return_value.run_async.side_effect = success_response

        result = await validate_input("Save my coding preferences")
        
        # Should get real validation result
        assert "allowed" in result
        assert result["allowed"] is True
        assert "timeout" not in result.get("reason", "").lower()


@pytest.mark.asyncio
async def test_context_processing_has_timeout():
    """Verify context processor also has timeout protection"""
    # Same pattern for context_processor
    
    with patch('backend.agents.context_processor.Runner') as MockRunner:
        async def hanging_response(*args, **kwargs):
            await asyncio.sleep(100)
            yield "ignore"
        
        MockRunner.return_value.run_async.side_effect = hanging_response
        
        result = await process_context("test context", personality="quick-answer")
        
        # Should timeout and fail gracefully
        assert "error" in result or "timeout" in str(result).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
