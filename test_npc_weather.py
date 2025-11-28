#!/usr/bin/env python3
"""Test script for Phase 2: NPC Weather Status & Reactions"""

import sys
sys.path.append('/Users/terryroberts/Documents/code/web3_mud')

from npc import NPCS, load_npcs
from game.systems.atmospheric_manager import get_atmospheric_manager
from game.world.manager import WorldManager
from game.state import NPC_STATE

print("=== Phase 2: NPC Weather Status & Reactions Test ===\n")

# Load NPCs
load_npcs()
print(f"Loaded {len(NPCS)} NPCs")

# Get atmospheric manager
atmos = get_atmospheric_manager()

# Get world manager
wm = WorldManager.get_instance()

# Test with Old Storyteller
npc_id = "old_storyteller"
if npc_id not in NPCS:
    print(f"ERROR: {npc_id} not found in NPCS")
    sys.exit(1)

npc = NPCS[npc_id]
print(f"\n--- Testing NPC: {npc.name} ---")
print(f"Pronoun: {npc.pronoun}")
print(f"Has weather_status: {hasattr(npc, 'weather_status')}")
print(f"Has weather_reactions: {hasattr(npc, 'weather_reactions')}")
print(f"Number of weather reactions: {len(npc.weather_reactions)}")

# Set NPC location to town square (outdoor)
town_square = wm.get_room("town_square")
if town_square:
    npc.location = town_square
    print(f"\nSet location to: {town_square.name}")
    print(f"Room is outdoor: {town_square.outdoor}")
else:
    print("ERROR: Could not load town_square room")
    sys.exit(1)

# Test 1: Weather status updates
print("\n--- Test 1: Weather Status Updates ---")
atmos.weather.current_type = "rain"
atmos.weather.current_intensity = "heavy"

# Initialize NPC in NPC_STATE if needed
if npc_id not in NPC_STATE:
    NPC_STATE[npc_id] = {"room": "town_square"}

print(f"Weather: {atmos.weather.current_type} ({atmos.weather.current_intensity})")

# Update weather status multiple times with advancing ticks
# We need to manually advance time to get different ticks
from game_engine import get_current_game_tick
initial_tick = get_current_game_tick()
print(f"Initial tick: {initial_tick}")

for i in range(10):
    # Manually advance the tick by calling atmos.update() which advances time
    atmos.update()
    npc.update_weather_status(atmos)
    print(f"  Tick {i+1}: wetness={npc.weather_status.wetness}, tick={npc.weather_status.last_update_tick}")

print(f"\nWeather Status after 10 ticks in heavy rain:")
print(f"  Wetness: {npc.weather_status.wetness}")
print(f"  Cold: {npc.weather_status.cold}")
print(f"  Heat: {npc.weather_status.heat}")
print(f"  Has status: {npc.weather_status.has_status()}")

# Test 2: Weather descriptions
print("\n--- Test 2: Weather Descriptions ---")
desc = npc.get_weather_description()
print(f"Weather description: '{desc}'")

# Test 3: Weather reactions
print("\n--- Test 3: Weather Reactions ---")
weather_state = atmos.weather.get_state()
season = atmos.seasons.get_season(atmos.time.get_day_of_year())
reaction = npc.get_weather_reaction(weather_state, season)
print(f"Weather state: {weather_state}")
print(f"Season: {season}")
print(f"Weather reaction: {reaction if reaction else '(None - NPC may not have reaction for this weather type)'}")

# Test 4: Test with different weather
print("\n--- Test 4: Test with Heatwave ---")
atmos.weather.current_type = "heatwave"
atmos.weather.current_intensity = "heavy"

# Reset weather status for clean test
npc.weather_status.wetness = 0
npc.weather_status.cold = 0
npc.weather_status.heat = 0

for i in range(8):
    npc.update_weather_status(atmos)

print(f"\nWeather Status after 8 ticks in heavy heatwave:")
print(f"  Wetness: {npc.weather_status.wetness}")
print(f"  Cold: {npc.weather_status.cold}")
print(f"  Heat: {npc.weather_status.heat}")

desc = npc.get_weather_description()
print(f"Weather description: '{desc}'")

weather_state = atmos.weather.get_state()
reaction = npc.get_weather_reaction(weather_state, season)
print(f"Weather reaction: {reaction if reaction else '(None)'}")

# Test 5: Test with Mara (different pronoun)
print("\n--- Test 5: Test with Mara (she pronoun) ---")
mara_id = "innkeeper"
if mara_id in NPCS:
    mara = NPCS[mara_id]
    print(f"NPC: {mara.name}, Pronoun: {mara.pronoun}")
    
    # Set location
    mara.location = town_square
    
    # Reset and apply rain
    mara.weather_status.wetness = 0
    atmos.weather.current_type = "rain"
    atmos.weather.current_intensity = "heavy"
    
    for i in range(6):
        mara.update_weather_status(atmos)
    
    desc = mara.get_weather_description()
    print(f"Weather description: '{desc}'")
    print(f"  (Should use 'she' pronoun)")
    
    weather_state = atmos.weather.get_state()
    reaction = mara.get_weather_reaction(weather_state, season)
    print(f"Weather reaction: {reaction if reaction else '(None)'}")
else:
    print(f"ERROR: {mara_id} not found")

# Test 6: Indoor decay
print("\n--- Test 6: Indoor Decay (Moving Inside) ---")
tavern = wm.get_room("tavern")
if tavern:
    npc.location = tavern
    print(f"Moved NPC to: {tavern.name}")
    print(f"Room is outdoor: {tavern.outdoor}")
    
    # Update a few times to see decay
    for i in range(5):
        npc.update_weather_status(atmos)
    
    print(f"\nWeather Status after 5 ticks indoors:")
    print(f"  Wetness: {npc.weather_status.wetness} (should be decreasing)")
    print(f"  Cold: {npc.weather_status.cold}")
    print(f"  Heat: {npc.weather_status.heat}")
else:
    print("ERROR: Could not load tavern room")

print(f"\n✅ Phase 2 Test Complete!")

