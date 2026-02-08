"""Test direct LiteLLM call to OpenRouter (bypass ADK)"""
import os
import sys
import abc


def test_litellm_direct_call():
    print("Testing LiteLLM -> OpenRouter direct call...\n")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    model_name = os.environ.get("OPENROUTER_MODEL")
    if not api_key or not model_name:
        print("Skipping test: OPENROUTER_API_KEY or OPENROUTER_MODEL not found in environment")
        return

    try:
        import litellm

        # Test 1: Direct OpenRouter call
        print("[Test 1] Direct LiteLLM completion call")
        response = litellm.completion(
            model=f"openrouter/{model_name}",
            messages=[{"role": "user", "content": "Say 'LiteLLM works!' if you can read this"}],
            api_key=api_key,
        )

        print(f"OK Response: {response.choices[0].message.content}")
        print(f"OK Model: {response.model}")

        # Test 2: Try without provider prefix if applicable
        if "/" in model_name:
            print("\n[Test 2] Testing model name without provider prefix")
            short_model = model_name.split("/", 1)[1]
            try:
                response2 = litellm.completion(
                    model=f"openrouter/{short_model}",
                    messages=[{"role": "user", "content": "Test 2"}],
                    api_key=api_key,
                )
                print(f"OK Works without provider prefix: {response2.choices[0].message.content}")
            except Exception as e:
                print(f"ERROR Fails without provider prefix: {e}")

        print("\nOK LiteLLM -> OpenRouter working!")
        print(f"Correct model format: openrouter/{model_name}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        raise e


if __name__ == "__main__":
    try:
        test_litellm_direct_call()
    except Exception:
        sys.exit(1)
