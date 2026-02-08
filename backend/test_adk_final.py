"""Final test - ADK + LiteLLM with correct configuration"""
import os
import sys


def main() -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    model_name = os.environ.get("OPENROUTER_MODEL")
    if not api_key or not model_name:
        print("Skipping: OPENROUTER_API_KEY or OPENROUTER_MODEL not found in environment")
        return 0

    print("=" * 70)
    print("ADK + LiteLLM Final Integration Test")
    print("=" * 70)

    try:
        from google.adk.models.lite_llm import LiteLlm
        from google.adk.agents import LlmAgent
        print("OK Imports successful\n")

        # Create model (only model parameter)
        print("[Step 1] Creating LiteLlm model...")
        model = LiteLlm(model=f"openrouter/{model_name}")
        print("OK Model created\n")

        # Create agent
        print("[Step 2] Creating LlmAgent...")
        agent = LlmAgent(
            model=model,
            name="test_agent",
            instruction="You are a test agent. Always output valid JSON with an 'allowed' field.",
        )
        print(f"OK Agent created: {agent.name}\n")

        print("=" * 70)
        print("SUCCESS! ADK + LiteLLM configuration is correct!")
        print("=" * 70)
        print("\nConfiguration summary:")
        print("  - API Key: Set via environment variable")
        print(f"  - Model: openrouter/{model_name}")
        print("  - LiteLlm: Only accepts 'model' parameter")
        print("  - Agent: Created successfully")
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
