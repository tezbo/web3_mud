
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from game_engine import handle_command, new_game_state, WORLD
from game.world.manager import WorldManager

def run_test():
    print("=== Starting Refactor Verification Test ===")
    
    # 1. Setup
    print("\n[1] Initializing Game State...")
    game = new_game_state("Tester")
    # Force location to town_square
    game["location"] = "town_square"
    
    # Ensure WorldManager is initialized
    wm = WorldManager.get_instance()
    print(f"WorldManager initialized: {wm}")

    # 2. Test LOOK (describe_location refactor)
    print("\n[2] Testing LOOK command...")
    response, game = handle_command("look", game, username="Tester")
    print(f"Response length: {len(response)}")
    if "Town Square" in response or "town_square" in response: # Check for title or ID
        print("✅ LOOK command successful (Room title found)")
    else:
        print("❌ LOOK command failed")
        print(response)

    # 3. Test MOVE (Player.move refactor)
    print("\n[3] Testing MOVE command (go north)...")
    # Find a valid exit from town_square
    room = wm.get_room("town_square")
    if not room.exits:
        print("⚠️ No exits from town_square, skipping move test")
    else:
        direction = list(room.exits.keys())[0]
        print(f"Attempting to move {direction}...")
        response, game = handle_command(f"go {direction}", game, username="Tester")
        
        new_loc = game["location"]
        if new_loc != "town_square":
            print(f"✅ MOVE command successful. New location: {new_loc}")
        else:
            print("❌ MOVE command failed. Location did not change.")
            print(response)

    # 4. Test TAKE (Player.take_item refactor)
    print("\n[4] Testing TAKE command...")
    # Add a dummy item to the current room for testing
    current_room_id = game["location"]
    current_room = wm.get_room(current_room_id)
    
    test_item = "copper_coin"
    current_room.items.append(test_item)
    print(f"Added {test_item} to {current_room_id}")
    
    response, game = handle_command(f"take {test_item}", game, username="Tester")
    
    if test_item in game["inventory"]:
        print(f"✅ TAKE command successful. Item in inventory.")
    else:
        print("❌ TAKE command failed.")
        print(response)

    # 5. Test DROP (Player.drop_item refactor)
    print("\n[5] Testing DROP command...")
    response, game = handle_command(f"drop {test_item}", game, username="Tester")
    
    if test_item not in game["inventory"] and test_item in current_room.items:
        print(f"✅ DROP command successful. Item removed from inventory and back in room.")
    else:
        print("❌ DROP command failed.")
        print(response)

if __name__ == "__main__":
    try:
        run_test()
        print("\n=== Test Complete ===")
    except Exception as e:
        print(f"\n❌ Test Crashed: {e}")
        import traceback
        traceback.print_exc()
