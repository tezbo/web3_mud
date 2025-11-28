
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from npc import NPCS
from game.models.entity import Entity
from game.models.item import Item
from game.systems.inventory_system import InventorySystem

def verify_npc_items():
    print("--- Verifying NPC Items ---")
    
    # 1. Storyteller
    storyteller = NPCS.get("old_storyteller")
    print(f"\nChecking Storyteller ({storyteller.name})...")
    items = [i.name for i in storyteller.inventory.contents]
    print(f"Inventory: {items}")
    
    assert "carved wooden pipe" in items, "Storyteller missing pipe"
    assert "tattered journal" in items, "Storyteller missing journal"
    
    pipe = next(i for i in storyteller.inventory.contents if i.name == "carved wooden pipe")
    assert pipe.is_held, "Pipe should be held"
    
    # 2. Patrol Guard
    guard = NPCS.get("patrolling_guard")
    print(f"\nChecking Patrol Guard ({guard.name})...")
    items = [i.name for i in guard.inventory.contents]
    print(f"Inventory: {items}")
    
    assert "steel spear" in items, "Guard missing spear"
    assert "guard badge" in items, "Guard missing badge"
    
    spear = next(i for i in guard.inventory.contents if i.name == "steel spear")
    assert spear.is_held, "Spear should be held"
    
    # 3. Mara
    mara = NPCS.get("innkeeper")
    print(f"\nChecking Mara ({mara.name})...")
    items = [i.name for i in mara.inventory.contents]
    print(f"Inventory: {items}")
    
    assert "herbal satchel" in items, "Mara missing satchel"
    
    satchel = next(i for i in mara.inventory.contents if i.name == "herbal satchel")
    assert satchel.inventory, "Satchel should have inventory"
    satchel_items = [i.name for i in satchel.inventory.contents]
    print(f"Satchel Contents: {satchel_items}")
    assert "bundle of dried herbs" in satchel_items, "Satchel missing herbs"

def verify_encumbrance():
    print("\n--- Verifying Encumbrance ---")
    
    # Create a dummy entity
    e = Entity("tester", "Tester")
    e.location = "some_room" # Mock location
    
    # Check default max weight
    print(f"Max Weight: {e.inventory.max_weight}")
    
    # Add items that together exceed max weight
    items = []
    for i in range(15):
        rock = Item(f"rock_{i}", f"rock {i}", f"Rock number {i}")
        rock.weight = 10.0
        items.append(rock)
        e.inventory.add(rock)
    
    print(f"Current Weight: {e.inventory.current_weight}")
    print(f"Total items: {len(e.inventory.contents)}")
    
   # Try to move
    can_move = e.move("north")
    print(f"Can move when over-encumbered? {can_move}")
    
    assert not can_move, "Entity should NOT be able to move when overburdened"
    
    # Remove most rocks
    for rock in items[::2]:  # Remove every other rock
        e.inventory.remove(rock)
        
    print(f"Weight after drop: {e.inventory.current_weight}")
    
    can_move = e.move("north")
    print(f"Can move when under limit? {can_move}")
    
    assert can_move, "Entity SHOULD be able to move when not overburdened"

if __name__ == "__main__":
    try:
        verify_npc_items()
        verify_encumbrance()
        print("\nSUCCESS: All checks passed!")
    except AssertionError as e:
        print(f"\nFAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
