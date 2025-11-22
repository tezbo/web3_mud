"""
World loader module for Tiny Web MUD.

Loads world data from JSON files instead of hardcoded Python dicts.
"""

import json
import os
from typing import Dict, Any


def load_world_from_json(base_dir: str = "world") -> Dict[str, Any]:
    """
    Load world data from JSON files.
    
    Reads world_index.json to get the list of rooms, then loads each room file
    from world/rooms/ directory.
    
    Args:
        base_dir: Base directory containing world data (default: "world")
    
    Returns:
        dict: WORLD dict keyed by room_id, with same structure as before
              but now loaded from JSON files
    
    Raises:
        FileNotFoundError: If world_index.json or any room file is missing
        json.JSONDecodeError: If any JSON file is malformed
    """
    world = {}
    
    # Path to world_index.json
    index_path = os.path.join(base_dir, "world_index.json")
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(
            f"World index file not found: {index_path}\n"
            "Please ensure world/world_index.json exists."
        )
    
    # Load world index
    with open(index_path, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    if "rooms" not in index_data:
        raise ValueError("world_index.json must contain a 'rooms' array")
    
    # Load each room file
    rooms_dir = os.path.join(base_dir, "rooms")
    
    for room_entry in index_data["rooms"]:
        if not isinstance(room_entry, dict) or "id" not in room_entry or "file" not in room_entry:
            raise ValueError(f"Invalid room entry in world_index.json: {room_entry}")
        
        room_id = room_entry["id"]
        room_file = room_entry["file"]
        room_path = os.path.join(rooms_dir, room_file)
        
        if not os.path.exists(room_path):
            raise FileNotFoundError(
                f"Room file not found: {room_path}\n"
                f"Referenced in world_index.json for room '{room_id}'"
            )
        
        # Load room JSON
        with open(room_path, 'r', encoding='utf-8') as f:
            room_data = json.load(f)
        
        # Validate required fields
        required_fields = ["id", "name", "description", "exits"]
        for field in required_fields:
            if field not in room_data:
                raise ValueError(
                    f"Room file {room_file} missing required field: {field}"
                )
        
        # Ensure room_id matches
        if room_data["id"] != room_id:
            raise ValueError(
                f"Room ID mismatch: file {room_file} has id '{room_data['id']}' "
                f"but index expects '{room_id}'"
            )
        
        # Ensure optional fields have defaults
        if "items" not in room_data:
            room_data["items"] = []
        if "npcs" not in room_data:
            room_data["npcs"] = []
        if "details" not in room_data:
            room_data["details"] = {}
        
        # Add to world dict
        world[room_id] = room_data
    
    return world

