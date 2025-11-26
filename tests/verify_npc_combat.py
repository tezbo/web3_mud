
import sys
import os
import time

# Add current directory to path
sys.path.append(os.getcwd())

from game.models.npc import NPC
from game.models.item import Weapon, Armor
from game.systems.combat import CombatSystem

def run_simulation():
    print("=== NPC Combat Simulation ===\n")
    
    # 1. Setup Environment
    from game.models.room import Room
    arena = Room("arena", "Combat Arena", "A bloody pit.")
    
    # 2. Create Combatants
    orc = NPC("orc_1", "Angry Orc")
    orc.stats = {"hp": 30, "max_hp": 30, "str": 18, "agi": 8, "int": 5}
    orc.attackable = True
    orc.location = arena
    arena.npcs.append(orc.oid)
    
    guard = NPC("guard_1", "Town Guard")
    guard.stats = {"hp": 40, "max_hp": 40, "str": 14, "agi": 12, "int": 10}
    guard.attackable = True
    guard.location = arena
    arena.npcs.append(guard.oid)
    
    # 2. Equip them
    # Orc gets a big axe (high damage, no defense)
    axe = Weapon("great_axe", "Great Axe")
    axe.damage = 8
    axe.weapon_type = "slash"
    orc.inventory.append(axe)
    
    # Guard gets a sword and shield (moderate damage, good defense)
    sword = Weapon("longsword", "Longsword")
    sword.damage = 6
    guard.inventory.append(sword)
    
    chainmail = Armor("chainmail", "Chainmail")
    chainmail.ac = 4
    guard.inventory.append(chainmail)
    
    print(f"{orc.name} (HP: {orc.stats['hp']}) wields {orc.get_weapon().name}.")
    print(f"{guard.name} (HP: {guard.stats['hp']}) wields {guard.get_weapon().name} and wears {chainmail.name} (AC: {guard.get_defense()}).")
    print("\nFIGHT!\n")
    
    # 3. Combat Loop
    combat = CombatSystem.get_instance()
    round_num = 1
    
    while not orc.is_dead and not guard.is_dead:
        print(f"--- Round {round_num} ---")
        
        # Orc attacks Guard
        msgs = combat.resolve_round(orc, guard)
        for msg in msgs:
            print(msg)
            
        if guard.is_dead:
            break
            
        # Guard attacks Orc
        msgs = combat.resolve_round(guard, orc)
        for msg in msgs:
            print(msg)
            
        print(f"Status: {orc.name} [{orc.stats['hp']}/{orc.stats['max_hp']}] vs {guard.name} [{guard.stats['hp']}/{guard.stats['max_hp']}]")
        round_num += 1
        time.sleep(0.5) # Pause for effect
        
    print("\n=== Result ===")
    
    # Find the winner and loser
    if orc.is_dead:
        winner = guard
        loser = orc
    else:
        winner = orc
        loser = guard
        
    print(f"{loser.name} has been defeated!")
    print(f"Winner: {winner.name} with {winner.stats['hp']} HP remaining.")
    
    # Verify corpse
    corpses = [i for i in arena.items if "Corpse" in i.name]
    if corpses:
        corpse = corpses[0]
        print(f"Verified: {corpse.name} is on the ground.")
        print(f"Corpse contains: {[i.name for i in corpse.inventory]}")
        
        # Test Decay
        print("\n=== Testing Decay ===")
        # Speed up decay for test
        corpse.decay_ticks = 2
        
        print(f"Start: {corpse.name}")
        arena.tick() # Tick 1 (decrements to 1)
        arena.tick() # Tick 2 (decrements to 0 -> decay to stage 1)
        print(f"Stage 1: {corpse.name} ({corpse.description})")
        
        # Speed up stage 1
        corpse.decay_ticks = 1
        arena.tick() # Decay to stage 2 (Skeleton)
        print(f"Stage 2: {corpse.name} ({corpse.description})")
        
        # Speed up stage 2
        corpse.decay_ticks = 1
        arena.tick() # Destroy
        
        if corpse not in arena.items:
            print("Verified: Corpse has decayed completely and been removed.")
        else:
            print(f"Error: Corpse still exists: {corpse.name}")
            
    else:
        print("Error: No corpse found!")

if __name__ == "__main__":
    run_simulation()
