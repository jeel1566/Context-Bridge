# OpenRouter API Test
import sys
import os
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from backend.services.openrouter_service import OpenRouterService, OpenRouterError

api_key = os.environ.get("OPENROUTER_API_KEY")
model = os.environ.get("OPENROUTER_MODEL")
if not api_key or not model:
    if __name__ == "__main__":
        print("Skipping: OPENROUTER_API_KEY or OPENROUTER_MODEL not set")
        sys.exit(0)
    pytest.skip("OPENROUTER_API_KEY or OPENROUTER_MODEL not set", allow_module_level=True)


async def test_openrouter_auth():
    """Test OpenRouter API authentication and basic completion"""

    print("Testing OpenRouter API...")
    print(f"Model: {model}")
    print(f"API Key: {api_key[:8]}...")
    print("-" * 50)

    service = OpenRouterService(
        api_key=api_key,
        model=model,
        timeout=30.0,
        max_retries=3
    )

    try:
        # Test simple completion
        print("\n1. Testing simple completion...")
        response = await service.simple_completion(
            "Say 'OpenRouter connection successful!' if you can read this message.",
            temperature=0.7,
            max_tokens=50
        )

        print(f"OK Response: {response}")

        # Test chat completion with validation
        print("\n2. Testing scope validation...")
        messages = [
            {
                "role": "user",
                "content": "Validate this INPUT for Context Bridge:\n\nI want to save my coding preferences for AI context management."
            }
        ]

        completion = await service.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )

        print(f"OK Response: {completion.content[:200]}...")
        print(f"OK Model: {completion.model}")
        print(f"OK Finish reason: {completion.finish_reason}")
        if completion.usage:
            print(f"OK Tokens used: {completion.usage}")

        print("\n" + "=" * 50)
        print("OK All tests passed! OpenRouter is working correctly.")
        print("=" * 50)

    except OpenRouterError as e:
        print(f"\nOpenRouter Error: {e}")
        assert False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        assert False
    finally:
        await service.close()


if __name__ == "__main__":
    try:
        asyncio.run(test_openrouter_auth())
    except Exception:
        sys.exit(1)
