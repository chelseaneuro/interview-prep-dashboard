#!/usr/bin/env python3
"""Simple script to test Anthropic API connection"""

import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("ERROR: No API key found in .env")
    exit(1)

print(f"Testing API key: {api_key[:20]}...")
print()

client = anthropic.Anthropic(api_key=api_key)

# Try different models to see which ones work
models_to_try = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307"
]

for model in models_to_try:
    try:
        print(f"Testing {model}...", end=" ")
        message = client.messages.create(
            model=model,
            max_tokens=100,
            messages=[{"role": "user", "content": "Hello"}]
        )
        print(f"✓ SUCCESS - {message.content[0].text[:50]}")
        print(f"\n✓ This model works: {model}")
        break
    except anthropic.NotFoundError:
        print(f"✗ Not found")
    except anthropic.AuthenticationError as e:
        print(f"✗ Auth error: {e}")
        print("\n⚠ Your API key appears to be invalid.")
        break
    except Exception as e:
        print(f"✗ Error: {e}")

print("\nDone!")
