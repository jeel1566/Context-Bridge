"""
OpenRouter API Service

Provides OpenAI-compatible chat completion interface for OpenRouter API.
Implements production-ready error handling, retry logic, and streaming support.

Based on OpenRouter API documentation: https://openrouter.ai/docs
"""

import httpx
import asyncio
import json
import logging
from typing import List, Dict, Optional, AsyncGenerator, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """Chat message structure"""
    role: MessageRole
    content: str


@dataclass
class ChatCompletionResponse:
    """Response from chat completion"""
    content: str
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class OpenRouterError(Exception):
    """Base exception for OpenRouter errors"""
    pass


class OpenRouterAuthError(OpenRouterError):
    """Authentication error"""
    pass


class OpenRouterRateLimitError(OpenRouterError):
    """Rate limit exceeded"""
    pass


class OpenRouterService:
    """
    OpenRouter API Service
    
    Provides async interface to OpenRouter API with:
    - Retry logic with exponential backoff
    - Streaming support
    - Error handling
    - Request/response logging
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openai/gpt-oss-120b:free",
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        Initialize OpenRouter service.
        
        Args:
            api_key: OpenRouter API key
            base_url: OpenRouter API base URL
            model: Model identifier to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Create async HTTP client
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://contextbridge.app",  # Required by OpenRouter
                    "X-Title": "Context Bridge",  # Optional, for OpenRouter dashboard
                    "Content-Type": "application/json",
                }
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry function with exponential backoff.
        
        Args:
            func: Async function to retry
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            OpenRouterError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                last_exception = e
                
                # Don't retry on authentication errors
                if e.response.status_code == 401:
                    raise OpenRouterAuthError("Invalid API key") from e
                
                # Handle rate limiting
                if e.response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        delay = 2 ** attempt
                        logger.warning(f"Rate limited, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                    raise OpenRouterRateLimitError("Rate limit exceeded") from e
                
                # Retry on server errors (5xx)
                if 500 <= e.response.status_code < 600:
                    if attempt < self.max_retries - 1:
                        delay = 2 ** attempt
                        logger.warning(f"Server error {e.response.status_code}, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                
                # Don't retry on client errors (4xx except 429)
                raise OpenRouterError(f"API error: {e.response.status_code}") from e
                
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(f"Request failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                raise OpenRouterError(f"Request failed after {self.max_retries} attempts") from e
        
        raise OpenRouterError("All retry attempts failed") from last_exception
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletionResponse | AsyncGenerator[str, None]:
        """
        Create a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional API parameters
            
        Returns:
            ChatCompletionResponse if not streaming, AsyncGenerator if streaming
            
        Raises:
            OpenRouterError: If API request fails
        """
        
        async def _make_request():
            client = await self._get_client()
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
                **kwargs
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            logger.debug(f"OpenRouter request: model={self.model}, messages={len(messages)}, stream={stream}")
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            return response
        
        if stream:
            return self._stream_completion(_make_request)
        else:
            response = await self._retry_with_backoff(_make_request)
            return self._parse_completion_response(response)
    
    def _parse_completion_response(self, response: httpx.Response) -> ChatCompletionResponse:
        """Parse completion API response"""
        data = response.json()
        
        if "error" in data:
            raise OpenRouterError(f"API error: {data['error']}")
        
        choice = data["choices"][0]
        content = choice["message"]["content"]
        
        return ChatCompletionResponse(
            content=content,
            model=data.get("model", self.model),
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage")
        )
    
    async def _stream_completion(self, request_func) -> AsyncGenerator[str, None]:
        """
        Stream completion response.
        
        Args:
            request_func: Function that makes the HTTP request
            
        Yields:
            Content chunks as they arrive
        """
        response = await self._retry_with_backoff(request_func)
        
        async for line in response.aiter_lines():
            if not line or line.strip() == "":
                continue
            
            if line.startswith("data: "):
                data_str = line[6:]  # Remove "data: " prefix
                
                if data_str == "[DONE]":
                    break
                
                try:
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse streaming chunk: {data_str}")
                    continue
    
    async def simple_completion(self, prompt: str, **kwargs) -> str:
        """
        Simple completion helper for single prompt.
        
        Args:
            prompt: User prompt
            **kwargs: Additional chat completion parameters
            
        Returns:
            Response text
        """
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat_completion(messages, stream=False, **kwargs)
        return response.content


# Singleton instance
_openrouter_service: Optional[OpenRouterService] = None


async def get_openrouter_service() -> OpenRouterService:
    """
    Get singleton OpenRouter service instance.
    
    Returns:
        Configured OpenRouterService instance
    """
    global _openrouter_service
    
    if _openrouter_service is None:
        from backend.config import get_settings
        settings = get_settings()
        
        if not settings.openrouter_configured:
            raise OpenRouterError("OpenRouter not configured. Set OPENROUTER_API_KEY environment variable.")
        
        _openrouter_service = OpenRouterService(
            api_key=settings.openrouter_api_key.get_secret_value(),
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            timeout=60.0,
            max_retries=3,
        )
    
    return _openrouter_service


__all__ = [
    'OpenRouterService',
    'ChatMessage',
    'ChatCompletionResponse',
    'OpenRouterError',
    'OpenRouterAuthError',
    'OpenRouterRateLimitError',
    'get_openrouter_service',
]
