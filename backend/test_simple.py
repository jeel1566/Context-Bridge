"""Simple test - just verify agents can be created and used"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
logging.basicConfig(level=logging.INFO)

from backend.agents.scope_validator import validate_input

async def test():
    print("Testing scope validation...")
    
    # Test 1: Valid input
    result = await validate_input("I want to save my coding preferences")
    print(f"\nResult: {result}")
    print(f"Allowed: {result.get('allowed')}")
    print(f"Category: {result.get('category')}")
    
    if result.get('allowed'):
        print("\n✓ TEST PASSED - Valid input was allowed")
    else:
        print(f"\n✗ TEST FAILED - Valid input was blocked: {result.get('reason')}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(test())
