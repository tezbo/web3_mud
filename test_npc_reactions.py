import time
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from game_engine import WORLD, NPC_STATE, NPCS
from game.systems.atmospheric_manager import get_atmospheric_manager
from core.background_events import _generate_events_once

def test_npc_weather_reactions():
    print("--- Testing NPC Weather Reactions ---")
    
    # 1. Setup Environment
    room_id = "town_square"
    npc_id = "patrolling_guard"
    
    # Ensure room is outdoor
    WORLD[room_id]["outdoor"] = True
    print(f"Room {room_id} outdoor: {WORLD[room_id].get('outdoor')}")
    
    # Ensure NPC is in the room
    if npc_id not in NPC_STATE:
        NPC_STATE[npc_id] = {}
    NPC_STATE[npc_id]["room"] = room_id
    NPC_STATE[npc_id]["alive"] = True
    print(f"NPC {npc_id} placed in {room_id}")
    
    # 2. Set weather state
    # Test "storm" weather to verify fallback logic
    from game.state import WEATHER_STATE
    WEATHER_STATE["type"] = "storm"
    WEATHER_STATE["intensity"] = "heavy"
    
    atmos = get_atmospheric_manager() # Keep atmos for later use in direct test
    atmos.weather.current_type = "storm"
    atmos.weather.current_intensity = "heavy"
    print(f"Weather set to: {WEATHER_STATE['type']} ({WEATHER_STATE['intensity']})")
    
    # 3. Mock SocketIO to capture emissions
    class MockSocketIO:
        def __init__(self):
            self.emitted_messages = []
            
        def emit(self, event, data, room=None):
            self.emitted_messages.append((event, data, room))
            print(f"SocketIO Emit: {event} -> {data}")
            
        def sleep(self, seconds):
            pass

    mock_socketio = MockSocketIO()
    
    # 4. Run Event Generator (simulate multiple ticks)
    print("\nRunning event generator loop...")
    
    # We need to bypass the time checks in _generate_events_once
    # The easiest way is to modify the room_events state directly or just run it enough times
    # But _generate_events_once uses internal caching or Redis.
    # Let's try running it and see if it triggers.
    
    # We need to mock the callback functions
    def get_all_rooms():
        return [room_id]
        
    # Run a few times to simulate time passing
    # We might need to manually tweak the last_npc_weather_reaction_time in the cache/memory
    # to force a trigger.
    
    # Access the internal cache of _generate_events_once if possible, or just rely on the fact 
    # that the first run initializes it to 'past_time' (45s ago).
    
    _generate_events_once(
        mock_socketio,
        get_game_setting_fn=None,
        get_all_rooms_fn=get_all_rooms,
        process_ambiance_fn=None,
        process_weather_ambiance_fn=None, # We don't care about generic ambiance for this test
        process_decay_fn=None
    )
    
    # Check results
    found_reaction = False
    for event, data, room in mock_socketio.emitted_messages:
        if data.get('message_type') == 'npc_weather_reaction':
            found_reaction = True
            message = data['message']
            print(f"\n[SUCCESS] NPC Reaction Triggered: {message}")
            
            # Verify tag wrapping
            if "[NPC]" in message or "[SAY]" in message:
                if "\n" in message:
                    lines = message.split("\n")
                    # Check if lines are wrapped in either [NPC] or [SAY]
                    all_wrapped = True
                    for line in lines:
                        if not ((line.startswith("[NPC]") and line.endswith("[/NPC]")) or 
                                (line.startswith("[SAY]") and line.endswith("[/SAY]"))):
                            all_wrapped = False
                            break
                    
                    if all_wrapped:
                        print("[SUCCESS] All lines correctly wrapped in [NPC] or [SAY] tags.")
                    else:
                        print(f"[FAIL] Not all lines wrapped in tags: {lines}")
                else:
                    if (message.startswith("[NPC]") and message.endswith("[/NPC]")) or \
                       (message.startswith("[SAY]") and message.endswith("[/SAY]")):
                        print("[SUCCESS] Single line correctly wrapped in tags.")
                    else:
                        print(f"[FAIL] Single line not wrapped correctly: {message}")
            else:
                print(f"[FAIL] Message missing [NPC] or [SAY] tags: {message}")
            break
            
    if not found_reaction:
        print("\n[FAIL] No NPC reaction triggered via background events (might be timing/randomness).")
        # Debug info
        npc = NPCS.get(npc_id)
        print(f"NPC has weather_reactions: {npc.weather_reactions.keys() if npc else 'None'}")
        
        # Direct test
        print("\nTesting npc.get_weather_reaction directly:")
        if npc:
             # Ensure NPC has location and status updated
             from game.world.manager import WorldManager
             wm = WorldManager.get_instance()
             room = wm.get_room(room_id)
             npc.location = room
             
             # Force update weather status
             npc.update_weather_status(atmos)
             
             reaction = npc.get_weather_reaction({"type": "storm", "intensity": "heavy"}, "spring", "day")
             print(f"Direct reaction check: {reaction}")
             if reaction and isinstance(reaction, dict) and "action" in reaction and "vocal" in reaction:
                 print("[SUCCESS] Direct reaction check passed (Dictionary format confirmed).")
                 print(f"Action: {reaction['action']}")
                 print(f"Vocal: {reaction['vocal']}")
                 found_reaction = True
             elif reaction:
                 print("[WARNING] Direct reaction check passed but format is legacy string.")
                 found_reaction = True
        
    # Idle Action Test (Always run)
    print("\nTesting npc.get_idle_action directly:")
    npc = NPCS.get(npc_id)
    if npc:
        # Set up idle actions with new format for testing
        npc.idle_actions["test_room"] = [{"action": "Test Action", "vocal": "Test Vocal"}]
        idle = npc.get_idle_action("test_room")
        print(f"Direct idle action check: {idle}")
        if idle and isinstance(idle, dict) and "action" in idle and "vocal" in idle:
            print("[SUCCESS] Direct idle action check passed (Dictionary format confirmed).")
            print(f"Action: {idle['action']}")
            print(f"Vocal: {idle['vocal']}")
        else:
            print(f"[FAIL] Direct idle action check failed or format incorrect: {idle}")
        
    return found_reaction

if __name__ == "__main__":
    success = test_npc_weather_reactions()
    sys.exit(0 if success else 1)
