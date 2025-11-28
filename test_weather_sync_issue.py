#!/usr/bin/env python3
"""Simple test to check weather sync"""

import sys
sys.path.append('/Users/terryroberts/Documents/code/web3_mud')

from game.systems.atmospheric_manager import get_atmospheric_manager
from game.state import WEATHER_STATE

print("=== Weather State Sync Check ===\n")

atmos = get_atmospheric_manager()

print(f"WEATHER_STATE dict: {WEATHER_STATE}")
print(f"\nAtmosphericManager weather state: {atmos.weather.get_state()}")

# Check combined description
desc = atmos.get_combined_description(is_outdoor=True)
print(f"\nCombined description (outdoor): {desc}")

# Try manually updating WEATHER_STATE  
print("\n--- Updating WEATHER_STATE directly ---")
WEATHER_STATE['type'] = 'rain'
WEATHER_STATE['intensity'] = 'heavy'

print(f"WEATHER_STATE after update: {WEATHER_STATE}")
print(f"AtmosphericManager weather (should NOT change): {atmos.weather.get_state()}")

print("\n❌ Problem: Changing WEATHER_STATE doesn't affect AtmosphericManager!")
print("This is why setweather doesn't work - it updates WEATHER_STATE but AtmosphericManager has its own copy.")
