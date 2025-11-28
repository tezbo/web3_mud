
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

# Mock logging
logging.basicConfig(level=logging.INFO)

# Initialize systems
from game.world.manager import WorldManager
from game.models.player import Player
from game.systems.atmospheric_manager import get_atmospheric_manager

def test_tavern_weather():
    print("--- Testing Tavern Weather Logic ---")
    
    # Get WorldManager
    wm = WorldManager.get_instance()
    
    # Get Tavern
    room_id = "tavern"
    room = wm.get_room(room_id)
    
    if not room:
        print(f"ERROR: Room {room_id} not found")
        return
        
    print(f"Room: {room.name} ({room.oid})")
    print(f"Outdoor: {room.outdoor}")
    print(f"Type: {type(room)}")
    
    # Check weather status
    atmos = get_atmospheric_manager()
    weather_state = atmos.weather.get_state()
    print(f"Current Weather: {weather_state}")
    
    # Force overcast weather to trigger the specific message
    print("Forcing overcast weather...")
    atmos.weather.from_dict({"type": "overcast", "intensity": "light"})
    
    # Check look() output
    viewer = Player("tester")
    description = room.look(viewer)
    
    print("\n--- Room Description ---")
    print(description)
    print("------------------------")
    
    # Check for the specific message
    target_msg = "muted, somber atmosphere"
    if target_msg in description:
        print(f"\n[FAIL] Weather message found in description!")
    else:
        print(f"\n[PASS] Weather message NOT found in description.")
        
    # Check _get_weather_time_line explicitly
    weather_line = room._get_weather_time_line()
    print(f"\n_get_weather_time_line(): '{weather_line}'")
    
    # Check _get_base_description_text explicitly
    base_desc = room._get_base_description_text()
    print(f"\n_get_base_description_text(): '{base_desc}'")
    
    if target_msg in base_desc:
        print(f"[FAIL] Weather message found in base description!")

if __name__ == "__main__":
    test_tavern_weather()
