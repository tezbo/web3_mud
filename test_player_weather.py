#!/usr/bin/env python3
"""Test script for Phase 1: Player Weather Status"""

import sys
sys.path.append('/Users/terryroberts/Documents/code/web3_mud')

from game.models.player import Player
from game.systems.atmospheric_manager import get_atmospheric_manager

print("=== Phase 1: Player Weather Status Test ===\n")

# Create test player
player = Player("test_weatherman")
print(f"Created player: {player.username}")
print(f"Weather status initialized: {player.weather_status is not None}")

# Get atmospheric manager
atmos = get_atmospheric_manager()

# Simulate being outdoors in rain
print("\n--- Simulating outdoor exposure to rain ---")
from game.world.manager import WorldManager
wm = WorldManager.get_instance()
town_square = wm.get_room("town_square")
player.move_to(town_square)

# Manually set rain for testing
atmos.weather.current_type = "rain"
atmos.weather.current_intensity = "heavy"

print(f"Location: {player.location.name if player.location else 'None'}")
print(f"Outdoor: {getattr(player.location, 'outdoor', False)}")
print(f"Weather: {atmos.weather.current_type} ({atmos.weather.current_intensity})")

# Update weather status multiple times to build up wetness
for i in range(10):
    player.update_weather_status(atmos)

print(f"\nWeather Status after 10 ticks in rain:")
print(f"  Wetness: {player.weather_status.wetness}")
print(f"  Cold: {player.weather_status.cold}")
print(f"  Heat: {player.weather_status.heat}")

# Get weather description
desc_you = player.get_weather_description(pronoun="you")
desc_he = player.get_weather_description(pronoun="he")
desc_she = player.get_weather_description(pronoun="she")
desc_they = player.get_weather_description(pronoun="they")

print(f"\nWeather Descriptions:")
print(f"  You: {desc_you}")
print(f"  He: {desc_he}")
print(f"  She: {desc_she}")
print(f"  They: {desc_they}")

# Test persistence
print(f"\n--- Testing Persistence ---")
state = player.to_state()
print(f"Weather status in state: {'weather_status' in state}")
if 'weather_status' in state:
    print(f"  Wetness in saved state: {state['weather_status'].get('wetness', 0)}")

# Load into new player
player2 = Player("test_weatherman_copy")
player2.load_from_state(state)
print(f"\nLoaded into new player:")
print(f"  Wetness: {player2.weather_status.wetness}")
print(f"  Description: {player2.get_weather_description(pronoun='you')}")

print(f"\n✅ Phase 1 Test Complete!")
