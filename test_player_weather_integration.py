#!/usr/bin/env python3
"""Integration test for Player Weather Status - simulates actual game"""

import sys
sys.path.append('/Users/terryroberts/Documents/code/web3_mud')

from game_engine import handle_command
from game.systems.atmospheric_manager import get_atmospheric_manager

print("=== Integration Test: Player Weather in Actual Game Loop ===\n")

# Create initial game state
game = {
    "username": "weathertest",
    "location": "town_square",
    "inventory": [],
    "character": {
        "race": "human",
        "gender": "male"
    }
}

# Set weather to heavy rain
atmos = get_atmospheric_manager()
atmos.weather.current_type = "rain"
atmos.weather.current_intensity = "heavy"

print(f"Weather: {atmos.weather.current_type} ({atmos.weather.current_intensity})")
print(f"Starting weather_status in game: {game.get('weather_status', 'None')}\n")

# Simulate 15 commands (should build up wetness)
print("Simulating 15 commands in heavy rain...")
for i in range(15):
    response, game = handle_command(
        command="look",
        game=game,
        username="weathertest"
    )
    if i % 5 == 0:
        wetness = game.get('weather_status', {}).get('wetness', 0)
        print(f"  After {i+1} commands: wetness={wetness}")

print(f"\nFinal weather_status:")
ws = game.get('weather_status', {})
print(f"  Wetness: {ws.get('wetness', 0)}")
print(f"  Cold: {ws.get('cold', 0)}")
print(f"  Heat: {ws.get('heat', 0)}")

# Test description
if ws.get('wetness', 0) > 0:
    from game.models.player import Player
    p = Player("weathertest")
    p.load_from_state(game)
    desc = p.get_weather_description("you")
    print(f"\nWeather description: {desc}")
    print("\n✅ Weather status is accumulating correctly!")
else:
    print("\n❌ Weather status is NOT accumulating!")

# Test going indoors (should decay)
print("\n--- Testing indoor decay ---")
game["location"] = "tavern"  # Indoor room
print("Moved to tavern (indoor)")

for i in range(10):
    response, game = handle_command(
        command="look",
        game=game,
        username="weathertest"
    )
    if i % 3 == 0:
        wetness = game.get('weather_status', {}).get('wetness', 0)
        print(f"  After {i+1} commands indoors: wetness={wetness}")

final_wetness = game.get('weather_status', {}).get('wetness', 0)
if final_wetness < ws.get('wetness', 0):
    print(f"\n✅ Weather status decays indoors!")
else:
    print(f"\n⚠️  Weather status not decaying indoors")

print("\n✅ Integration Test Complete!")
