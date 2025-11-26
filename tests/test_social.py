
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from game_engine import handle_command, new_game_state, WORLD, EMOTES
from game.world.manager import WorldManager

# Mock broadcast function to capture messages
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
    print("=== Starting Social Commands Verification ===")
    
    # 1. Setup
    print("\n[1] Initializing Game State...")
    game = new_game_state("SocialTester")
    game["location"] = "town_square"
    
    # Inject our mock broadcast into the game engine's scope if needed, 
    # but handle_command accepts it as an arg.
    
    # 2. Test SAY
    print("\n[2] Testing SAY command...")
    broadcast_log.clear()
    response, game = handle_command("say Hello World", game, username="SocialTester", broadcast_fn=mock_broadcast)
    
    print(f"Response: {response}")
    
    # Verify player response
    if "You say: \"Hello World\"" in response:
        print("✅ Player received confirmation")
    else:
        print("❌ Player did not receive confirmation")
        
    # Verify broadcast
    if len(broadcast_log) > 0:
        msg = broadcast_log[0]["message"]
        if "SocialTester says: \"Hello World\"" in msg and "[CYAN]" in msg:
            print("✅ Room received broadcast (with color)")
        else:
            print(f"❌ Unexpected broadcast message: {msg}")
    else:
        print("❌ No broadcast sent")

    # 3. Test EMOTE (nod)
    print("\n[3] Testing EMOTE (nod)...")
    broadcast_log.clear()
    response, game = handle_command("nod", game, username="SocialTester", broadcast_fn=mock_broadcast)
    
    print(f"Response: {response}")
    
    # Verify player response (from EMOTES dict)
    expected_self = EMOTES["nod"]["self"]
    if response == expected_self:
        print("✅ Player received correct emote description")
    else:
        print(f"❌ Unexpected response: {response}")
        
    # Verify broadcast
    if len(broadcast_log) > 0:
        msg = broadcast_log[0]["message"]
        expected_room = EMOTES["nod"]["room"].format(actor="SocialTester", actor_possessive="SocialTester's")
        if msg == expected_room:
            print("✅ Room received correct emote broadcast")
        else:
            print(f"❌ Unexpected broadcast: {msg}")
            print(f"Expected: {expected_room}")
    else:
        print("❌ No broadcast sent")

if __name__ == "__main__":
    try:
        run_test()
        print("\n=== Test Complete ===")
    except Exception as e:
        print(f"\n❌ Test Crashed: {e}")
        import traceback
        traceback.print_exc()
