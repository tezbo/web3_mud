import sys
import os
import json

# Add current directory to path
sys.path.append(os.getcwd())

from game_engine import WORLD
from game.world.data import WORLD as DATA_WORLD

def debug_weather_logic():
    print("--- Debugging Weather Logic ---")
    
    room_id = "watchtower_path"
    
    # 1. Check WORLD in game_engine
    print(f"\nChecking game_engine.WORLD for '{room_id}':")
    if room_id in WORLD:
        room_data = WORLD[room_id]
        outdoor_val = room_data.get("outdoor")
        print(f"  Found in WORLD: Yes")
        print(f"  Raw 'outdoor' value: {outdoor_val} (Type: {type(outdoor_val)})")
        
        # Replicate background_events.py logic
        is_outdoor = str(outdoor_val).lower() in ['true', '1', 'yes'] if isinstance(outdoor_val, str) else bool(outdoor_val)
        print(f"  Calculated is_outdoor: {is_outdoor}")
    else:
        print(f"  Found in WORLD: No")
        
    # 2. Check WORLD in game.world.data
    print(f"\nChecking game.world.data.WORLD for '{room_id}':")
    if room_id in DATA_WORLD:
        room_data = DATA_WORLD[room_id]
        outdoor_val = room_data.get("outdoor")
        print(f"  Found in DATA_WORLD: Yes")
        print(f"  Raw 'outdoor' value: {outdoor_val} (Type: {type(outdoor_val)})")
    else:
        print(f"  Found in DATA_WORLD: No")

    # 3. Check JSON file directly
    json_path = "world/rooms/watchtower_path.json"
    print(f"\nChecking JSON file '{json_path}':")
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
            print(f"  'outdoor' in JSON: {data.get('outdoor')}")
    else:
        print("  JSON file not found")

if __name__ == "__main__":
    debug_weather_logic()
