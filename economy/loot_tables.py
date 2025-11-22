"""
Loot tables for rooms and NPCs in Tiny Web MUD.

Defines what players can find when searching/scavenging/looting.
"""

import random
from typing import List, Tuple, Optional

# Loot table entry: (item_key, chance, min_amount, max_amount)
# chance is 0.0 to 1.0 (probability of finding)
LootEntry = Tuple[str, float, int, int]


# Room-based loot tables
ROOM_LOOT_TABLES = {
    "town_square": [
        ("gold", 0.15, 1, 5),  # 15% chance, 1-5 gold
        ("copper_coin", 0.10, 1, 3),  # Legacy item
    ],
    "tavern": [
        ("gold", 0.10, 1, 3),
        ("wooden_tankard", 0.05, 1, 1),
    ],
    "smithy": [
        ("gold", 0.12, 1, 4),
        ("lump_of_ore", 0.08, 1, 2),
    ],
    "herbalist_shop": [
        ("gold", 0.10, 1, 3),
    ],
    "shrine": [
        ("gold", 0.08, 1, 2),
    ],
    "forest_edge": [
        ("gold", 0.20, 1, 6),  # Higher chance in forest
    ],
    "watchtower_path": [
        ("gold", 0.12, 1, 4),
        ("loose_stone", 0.15, 1, 2),
    ],
    "watchtower": [
        ("gold", 0.10, 1, 3),
        ("cracked_spyglass", 0.05, 1, 1),
    ],
    "old_road": [
        ("gold", 0.15, 1, 5),
        ("weathered_signpost", 0.03, 1, 1),
    ],
}


# NPC-based loot tables (when looting from NPCs)
NPC_LOOT_TABLES = {
    # Most NPCs don't drop loot, but some might
    "wandering_trader": [
        ("gold", 0.30, 5, 15),  # Trader has more gold
    ],
}


def get_room_loot_table(room_id: str) -> List[LootEntry]:
    """Get loot table for a room."""
    return ROOM_LOOT_TABLES.get(room_id, [])


def get_npc_loot_table(npc_id: str) -> List[LootEntry]:
    """Get loot table for an NPC."""
    return NPC_LOOT_TABLES.get(npc_id, [])


def roll_loot(loot_table: List[LootEntry], reputation_bonus: float = 0.0) -> List[Tuple[str, int]]:
    """
    Roll for loot from a loot table.
    
    Args:
        loot_table: List of loot entries
        reputation_bonus: Bonus to chance (0.0 to 1.0) based on reputation
    
    Returns:
        List of (item_key, amount) tuples for items found
    """
    found = []
    
    for item_key, base_chance, min_amount, max_amount in loot_table:
        # Apply reputation bonus (caps at 1.0)
        chance = min(1.0, base_chance + reputation_bonus)
        
        if random.random() < chance:
            amount = random.randint(min_amount, max_amount)
            found.append((item_key, amount))
    
    return found


def search_room(room_id: str, reputation: int = 0) -> List[Tuple[str, int]]:
    """
    Search a room for loot.
    
    Args:
        room_id: Room identifier
        reputation: Player reputation (affects chance, uses highest rep in area)
    
    Returns:
        List of (item_key, amount) tuples
    """
    loot_table = get_room_loot_table(room_id)
    
    # Reputation bonus: +0.05 per 10 reputation points, max +0.20
    rep_bonus = min(0.20, (reputation / 10) * 0.05)
    
    return roll_loot(loot_table, rep_bonus)


def loot_npc(npc_id: str, reputation: int = 0) -> List[Tuple[str, int]]:
    """
    Loot an NPC (if they have a loot table).
    
    Args:
        npc_id: NPC identifier
        reputation: Player reputation with this NPC
    
    Returns:
        List of (item_key, amount) tuples
    """
    loot_table = get_npc_loot_table(npc_id)
    
    if not loot_table:
        return []
    
    # Higher reputation with NPC = better loot chance
    rep_bonus = min(0.30, (reputation / 10) * 0.05)
    
    return roll_loot(loot_table, rep_bonus)

