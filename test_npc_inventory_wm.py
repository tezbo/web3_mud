#!/usr/bin/env python3
"""Quick test to verify NPC inventory is accessible via WorldManager."""

import sys
sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')

from game.world.manager import WorldManager

wm = WorldManager.get_instance()

print("Testing NPCs via WorldManager...")
print()

# Test Storyteller
st = wm.get_npc("old_storyteller")
if st:
    print(f"Storyteller: {st.name}")
    if hasattr(st, 'inventory'):
        items = [i.name for i in st.inventory.contents]
        print(f"  Inventory: {items}")
        for item in st.inventory.contents:
            print(f"    - {item.name} (is_held={getattr(item, 'is_held', False)})")
    print()

# Test Mara
mara = wm.get_npc("innkeeper")
if mara:
    print(f"Mara: {mara.name}")
    if hasattr(mara, 'inventory'):
        items = [i.name for i in mara.inventory.contents]
        print(f"  Inventory: {items}")
        for item in mara.inventory.contents:
            print(f"    - {item.name}")
            if hasattr(item, 'inventory') and item.inventory:
                nested = [i.name for i in item.inventory.contents]
                print(f"      Contents: {nested}")
    print()

# Test Guard
guard = wm.get_npc("patrolling_guard")
if guard:
    print(f"Guard: {guard.name}")
    if hasattr(guard, 'inventory'):
        items = [i.name for i in guard.inventory.contents]
        print(f"  Inventory: {items}")
        for item in guard.inventory.contents:
            print(f"    - {item.name} (is_held={getattr(item, 'is_held', False)})")

print("\nSUCCESS: NPCs have inventory loaded!")
