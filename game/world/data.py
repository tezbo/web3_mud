"""
World Data Module
Loads and provides access to the static world definition.
"""
import sys
import json

try:
    from world_loader import load_world_from_json
    WORLD = load_world_from_json()
except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
    # Fallback: if JSON loading fails, use empty dict and log error
    print(f"ERROR: Failed to load world from JSON: {e}", file=sys.stderr)
    print("The game will not function correctly until world data is available.", file=sys.stderr)
    WORLD = {}
