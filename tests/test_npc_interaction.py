
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from game_engine import handle_command, new_game_state, WORLD, NPCS
from game.world.manager import WorldManager

# Mock broadcast function
broadcast_log = []
def mock_broadcast(room_id, message, exclude_user_id=None):
    broadcast_log.append({
        "room_id": room_id,
        "message": message,
        "exclude": exclude_user_id
    })
    print(f"[BROADCAST to {room_id}]: {message}")

from game_engine import register_broadcast_fn
register_broadcast_fn(mock_broadcast)

def run_test():
    print("=== Starting NPC Interaction Verification ===")
    
    # 1. Setup
    print("\n[1] Initializing Game State...")
    game = new_game_state("NpcTester")
    game["location"] = "town_square"
    
    # Ensure Old Storyteller is in town_square
    # (He is by default in the static data)
    
    # 2. Test TALK
    print("\n[2] Testing TALK command...")
    broadcast_log.clear()
    response, game = handle_command("talk storyteller", game, username="NpcTester", broadcast_fn=mock_broadcast)
    
    print(f"Response: {response}")
    
    # Verify response contains dialogue
    if "Ah, a new face!" in response or "Welcome to our town" in response or "Ah, NpcTester, welcome" in response:
        print("✅ Received NPC dialogue")
    else:
        print("❌ Did not receive expected dialogue")

    # 3. Test ATTACK (Non-attackable NPC)
    print("\n[3] Testing ATTACK command (Non-attackable)...")
    response, game = handle_command("attack storyteller", game, username="NpcTester", broadcast_fn=mock_broadcast)
    
    print(f"Response: {response}")
    
    if "You can't attack" in response or "The Storyteller is too old" in response or "looks at you with deep sadness" in response:
        print("✅ Correctly prevented attack on non-attackable NPC")
    else:
        print("❌ Unexpected attack response")

if __name__ == "__main__":
    try:
        run_test()
        print("\n=== Test Complete ===")
    except Exception as e:
        print(f"\n❌ Test Crashed: {e}")
        import traceback
        traceback.print_exc()
