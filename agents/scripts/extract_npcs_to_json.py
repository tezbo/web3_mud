#!/usr/bin/env python3
"""
Extract hardcoded NPCs from npc.py to individual JSON files.
This is a one-time migration script to enable agent-driven NPC updates.
"""
import os
import sys
import json
from pathlib import Path

# Add project root to import path
sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')

from npc import _NPCS_DICT

OUTPUT_DIR = Path('world/npcs')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_npcs():
    print(f"Extracting {len(_NPCS_DICT)} NPCs to {OUTPUT_DIR}...")
    
    for npc_id, data in _NPCS_DICT.items():
        # Ensure ID is in the data
        if 'id' not in data:
            data['id'] = npc_id
            
        # Define output path
        output_file = OUTPUT_DIR / f"{npc_id}.json"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"✓ Created {output_file}")

    print("\nExtraction complete.")

if __name__ == "__main__":
    extract_npcs()
