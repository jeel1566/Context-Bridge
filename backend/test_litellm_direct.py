"""Test direct LiteLLM call to OpenRouter (bypass ADK)"""
import os
import sys
import abc

def test_litellm_direct_call():
    print("Testing LiteLLM → OpenRouter direct call...\n")
    
    if not os.environ.get('OPENROUTER_API_KEY'):
        print("Skipping test: OPENROUTER_API_KEY not found in environment")
        return

    try:
        import litellm
        
        # Test 1: Direct OpenRouter call
        print("[Test 1] Direct LiteLLM completion call")
        response = litellm.completion(
            model="openrouter/openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Say 'LiteLLM works!' if you can read this"}],
            api_key=os.environ.get('OPENROUTER_API_KEY')
        )
        
        print(f"✓ Response: {response.choices[0].message.content}")
        print(f"✓ Model: {response.model}")
        
        # Test 2: Try without 'openai/' prefix
        print("\n[Test 2] Testing model name without 'openai/' prefix")
        try:
            response2 = litellm.completion(
                model="openrouter/gpt-oss-120b",
                messages=[{"role": "user", "content": "Test 2"}],
                api_key=os.environ.get('OPENROUTER_API_KEY')
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
        raise e

if __name__ == "__main__":
    try:
        test_litellm_direct_call()
    except Exception:
        sys.exit(1)
