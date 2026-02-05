"""Simple validation test"""
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agents.scope_validator import validate_input

async def main():
    result = await validate_input("Test message about coding preferences")
    print(f"Result: {result}")
    print(f"Allowed: {result.get('allowed')}")
    
try:
    asyncio.run(main())
    print("✓ Test passed!")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
