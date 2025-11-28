
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from game_engine import WORLD
from game.world.manager import WorldManager
from game.models.player import Player

def debug_tavern():
    print("--- DEBUG TAVERN ---")
    
    # 1. Check raw WORLD data
    tavern_data = WORLD.get("tavern", {})
    print(f"WORLD['tavern'] raw outdoor value: {tavern_data.get('outdoor')} (Type: {type(tavern_data.get('outdoor'))})")
    
    # 2. Check WorldManager Room object
    wm = WorldManager.get_instance()
    room = wm.get_room("tavern")
    
    if not room:
        print("ERROR: Tavern room not found in WorldManager")
        return
        
    print(f"Room object class: {room.__class__.__name__}")
    print(f"Room object outdoor flag: {room.outdoor} (Type: {type(room.outdoor)})")
    
    # 3. Check look() output
    player = Player("debug_admin")
    description = room.look(player)
    
    print("\n--- ROOM DESCRIPTION ---")
    print(description)
    print("------------------------")
    
    if "Clear skies allow" in description or "moon to shine" in description:
        print("FAIL: Weather message found in description!")
    else:
        print("PASS: No weather message in description.")

if __name__ == "__main__":
    debug_tavern()
