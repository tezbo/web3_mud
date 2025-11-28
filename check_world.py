
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

# Mock logging
logging.basicConfig(level=logging.INFO)

def check_world_consistency():
    print("--- Checking WORLD Consistency ---")
    
    # 1. Check game_engine.WORLD
    try:
        from game_engine import WORLD
        print(f"game_engine.WORLD type: {type(WORLD)}")
        if "tavern" in WORLD:
            tavern_def = WORLD["tavern"]
            print(f"game_engine.WORLD['tavern']: {tavern_def}")
            print(f"game_engine.WORLD['tavern'].get('outdoor'): {tavern_def.get('outdoor')}")
        else:
            print("tavern NOT in game_engine.WORLD")
    except ImportError:
        print("Could not import game_engine")
    except Exception as e:
        print(f"Error checking game_engine.WORLD: {e}")

    # 2. Check WorldManager
    try:
        from game.world.manager import WorldManager
        wm = WorldManager.get_instance()
        tavern_room = wm.get_room("tavern")
        if tavern_room:
            print(f"WorldManager room 'tavern' outdoor: {tavern_room.outdoor}")
        else:
            print("tavern NOT found in WorldManager")
    except Exception as e:
        print(f"Error checking WorldManager: {e}")

if __name__ == "__main__":
    check_world_consistency()
