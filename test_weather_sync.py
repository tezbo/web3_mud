#!/usr/bin/env python3
"""Test script to verify weather sync."""

import sys
sys.path.append('/Users/terryroberts/Documents/code/web3_mud')

from game.systems.atmospheric_manager import get_atmospheric_manager
from game.state import WEATHER_STATE

print("=== Weather Sync Test ===\n")

# Get current state
print(f"WEATHER_STATE (global dict): {WEATHER_STATE}\n")

# Get atmospheric manager
atmos = get_atmospheric_manager()
weather_obj = atmos.weather.get_state()
print(f"AtmosphericManager weather: {weather_obj}\n")

# Test weather line for outdoor room
weather_line = atmos.get_combined_description(is_outdoor=True)
print(f"Weather line (outdoor room):")
print(f"  {weather_line}\n")

# Update weather manually to see if it syncs
print("Forcing weather update...")
atmos.weather.current_type = "storm"
atmos.weather.current_intensity = "heavy"
atmos.weather.current_temperature = "cold"

# Manually sync
from game.state import WEATHER_STATE as WS
WS.update(atmos.weather.to_dict())

print(f"\nAfter manual update:")
print(f"WEATHER_STATE: {WS}")
print(f"Weather line: {atmos.get_combined_description(is_outdoor=True)}")
