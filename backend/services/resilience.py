"""
Resilience Service for Production AI Applications

Provides retry logic with exponential backoff and jitter for handling
transient failures in LLM API calls.

Features:
- Exponential backoff (1s, 2s, 4s...)
- Jitter to prevent thundering herd
- Configurable max retries
- Selective retry (retries transient errors, not validation errors)
"""
import asyncio
import random
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""
    pass


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff and jitter.
    
    Args:
        func: Async function to retry
        *args: Positional arguments for func
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 10.0)
        exponential_base: Base for exponential calculation (default: 2.0)
        jitter: Whether to add random jitter (default: True)
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from func
        
    Raises:
        RetryExhaustedError: If all retries are exhausted
        Exception: The last exception if retries exhausted
        
    Example:
        result = await retry_with_backoff(
            my_async_function,
            arg1, arg2,
            max_retries=3,
            base_delay=1.0
        )
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries} for {func.__name__}")
            result = await func(*args, **kwargs)
            
            if attempt > 0:
                logger.info(f"Success on attempt {attempt + 1} for {func.__name__}")
            
            return result
            
        except Exception as e:
            last_exception = e
            
            # Don't retry on validation errors or client errors
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['validation', 'invalid', 'bad request', '400']):
                logger.warning(f"Non-retriable error in {func.__name__}: {e}")
                raise
            
            # If this was the last attempt, raise
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} retry attempts exhausted for {func.__name__}")
                raise RetryExhaustedError(
                    f"Failed after {max_retries} attempts"
                ) from last_exception
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter (0-10% of delay)
            if jitter:
                jitter_amount = random.uniform(0, delay * 0.1)
                delay += jitter_amount
            
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            await asyncio.sleep(delay)
    
    # Should never reach here, but just in case
    raise RetryExhaustedError(f"Failed after {max_retries} attempts") from last_exception


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    Decorator to add retry logic to async functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter
        
    Example:
        @with_retry(max_retries=3, base_delay=1.0)
        async def call_llm_api():
            # ... API call ...
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                **kwargs
            )
        return wrapper
    return decorator


# Convenience function for LLM calls
async def retry_llm_call(
    func: Callable[..., T],
    *args,
    **kwargs
) -> T:
    """
    Retry an LLM API call with sensible defaults.
    
    Defaults optimized for LLM APIs:
    - 3 retries
    - 1s, 2s, 4s delays (with jitter)
    - Max 10s delay
    
    Args:
        func: Async function making the LLM call
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Result from func
    """
    return await retry_with_backoff(
        func,
        *args,
        max_retries=3,
        base_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True,
        **kwargs
    )
