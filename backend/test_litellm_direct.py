"""Test direct LiteLLM call to OpenRouter (bypass ADK)"""
import os

# Set environment
os.environ['OPENROUTER_API_KEY'] = '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'

print("Testing LiteLLM → OpenRouter direct call...\n")

try:
    import litellm
    
    # Test 1: Direct OpenRouter call
    print("[Test 1] Direct LiteLLM completion call")
    response = litellm.completion(
        model="openrouter/openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Say 'LiteLLM works!' if you can read this"}],
        api_key=os.environ['OPENROUTER_API_KEY']
    )
    
    print(f"✓ Response: {response.choices[0].message.content}")
    print(f"✓ Model: {response.model}")
    
    # Test 2: Try without 'openai/' prefix
    print("\n[Test 2] Testing model name without 'openai/' prefix")
    try:
        response2 = litellm.completion(
            model="openrouter/gpt-oss-120b",
            messages=[{"role": "user", "content": "Test 2"}],
            api_key=os.environ['OPENROUTER_API_KEY']
        )
        print(f"✓ Works without prefix: {response2.choices[0].message.content}")
    except Exception as e:
        print(f"✗ Fails without prefix: {e}")
    
    print("\n✅ LiteLLM → OpenRouter working!")
    print(f"Correct model format: openrouter/openai/gpt-oss-120b")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
