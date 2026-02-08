"""Test different ways to configure LiteLlm"""
import os


def main() -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    model_name = os.environ.get("OPENROUTER_MODEL")
    if not api_key or not model_name:
        print("Skipping: OPENROUTER_API_KEY or OPENROUTER_MODEL not found in environment")
        return

    print("Testing LiteLlm configuration methods...\n")

    try:
        from google.adk.models.lite_llm import LiteLlm

        # Method 1: Just model name (rely on env var)
        print("[Test 1] Using only model name (env var for API key)")
        try:
            model1 = LiteLlm(model=f"openrouter/{model_name}")
            print(f"OK Method 1 works: {model1}")
        except Exception as e:
            print(f"ERROR Method 1 failed: {e}")

        # Method 2: Check if there are other parameters
        print("\n[Test 2] Checking LiteLlm signature")
        import inspect
        sig = inspect.signature(LiteLlm)
        print(f"LiteLlm parameters: {sig}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
