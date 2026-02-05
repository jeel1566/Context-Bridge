# OpenRouter API Test
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from backend.services.openrouter_service import OpenRouterService, OpenRouterError


async def test_openrouter_auth():
    """Test OpenRouter API authentication and basic completion"""
    
    api_key = "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"
    model = "openai/gpt-oss-120b:free"
    
    print(f"Testing OpenRouter API...")
    print(f"Model: {model}")
    print(f"API Key: {api_key[:20]}...")
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
        
        print(f"✓ Response: {response}")
        
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
        
        print(f"✓ Response: {completion.content[:200]}...")
        print(f"✓ Model: {completion.model}")
        print(f"✓ Finish reason: {completion.finish_reason}")
        if completion.usage:
            print(f"✓ Tokens used: {completion.usage}")
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! OpenRouter is working correctly.")
        print("=" * 50)
        
    except OpenRouterError as e:
        print(f"\n✗ OpenRouter Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_openrouter_auth())
    exit(0 if success else 1)
