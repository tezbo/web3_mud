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

def register_room_in_realm(oid, name, description, exits, realm="shadowfen", outdoor=False):
    """
    Register a new room in the world data structure.
    
    Args:
        oid (str): Unique object ID for the room (e.g., 'dark_cave')
        name (str): Display name of the room
        description (str): Full description
        exits (dict): Dictionary of direction -> target_oid
        realm (str): Realm name to add the room to
        outdoor (bool): Whether the room is outdoors
    """
    if realm not in WORLD:
        WORLD[realm] = {}
    
    WORLD[realm][oid] = {
        "name": name,
        "description": description,
        "exits": exits,
        "outdoor": outdoor
    }
    # Note: This updates the in-memory WORLD dictionary. 
    # To persist, we would need to save back to the JSON file.

