"""Test script to check import errors."""
import traceback
import sys

try:
    from src.copilot_endpoint import copilot_app
    print("Import successful!")
except Exception as e:
    print("=" * 50)
    print("IMPORT ERROR:")
    print("=" * 50)
    traceback.print_exc()
    print("=" * 50)
    sys.exit(1)
