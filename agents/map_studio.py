#!/usr/bin/env python3
"""
Mapmaker Agent: Create Aethermoor World Map
"""
import os
import sys
from dotenv import load_dotenv

# Add project root to import path if needed
# sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')

load_dotenv()

from agents.mapmaker import MapmakerAgent

def main():
    # Initialize Mapmaker with full context
    mapmaker = MapmakerAgent()
    
    # Task: Create the world map
    task = """Create a detailed world map for Aethermoor showing:
1. The three realms (Sunward Kingdoms, Twilight Dominion, Shadowfen)
2. Major geographical features (the Scar, seas, mountains, forests)
3. 15 major locations to be developed (5 per realm)
4. Travel routes and connections between realms
5. Distance/travel time estimates

Format as ASCII art map with detailed region descriptions below.
Make it evocative and match the lore:
- Sunward is the western continent (stone cities, forests, coasts)
- Twilight is the eastern archipelago (islands, jade towers, eternal twilight)
- Shadowfen is the central scar zone (swamps, mist, the reality tear)

Include a legend and notes about travel methods (walking, waystones)."""
    
    print("🗺️  MAPMAKER AGENT WORKING...")
    print("=" * 60)
    print()
    
    result = mapmaker.generate(task, model="gpt-4o", temperature=0.7)
    
    print(result)
    print()
    print("=" * 60)
    print("✓ World map created!")
    
    # Save the output
    output_path = mapmaker.save_output(result, "aethermoor_world_map.md", "completed")
    print(f"📁 Saved to: {output_path}")

if __name__ == "__main__":
    main()
