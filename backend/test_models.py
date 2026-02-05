"""Test different OpenRouter model names"""
import requests

api_key = "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"
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
        "max_tokens": 10
    }
    
    print(f"\nTrying model: {model}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            print(f"  ✓ SUCCESS! This model works.")
            data = response.json()
            print(f"  Model used: {data.get('model', 'unknown')}")
            break
        else:
            print(f"  ✗ HTTP {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
