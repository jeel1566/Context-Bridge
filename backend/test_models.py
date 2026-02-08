"""Test different OpenRouter model names"""
import os
import requests


def main() -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Skipping: OPENROUTER_API_KEY not found in environment")
        return

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://contextbridge.app",
        "Content-Type": "application/json",
    }

    # Try different model name formats
    model_names = [
        "openai/gpt-oss-120b:free",
        "openai/gpt-oss-120b",
        "gpt-oss-120b:free",
        "gpt-oss-120b",
        "openai/gpt-4o-mini",  # Known working model
        "openai/gpt-4o-mini:free",
    ]

    for model in model_names:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10,
        }

        print(f"\nTrying model: {model}")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                print("OK SUCCESS! This model works.")
                data = response.json()
                print(f"Model used: {data.get('model', 'unknown')}")
                break
            else:
                print(f"ERROR HTTP {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
