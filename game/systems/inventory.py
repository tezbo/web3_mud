"""
Inventory System - Manages item definitions, weights, and inventory logic.

This module centralizes all item-related functionality, replacing the legacy
implementations in game_engine.py.
"""
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter

# Global item definitions registry
# In a future iteration, this could be loaded from JSON files
ITEM_DEFS = {
    "copper_coin": {
        "name": "copper coin",
        "type": "currency",
        "description": "A small, tarnished copper coin.",
        "weight": 0.01,
        "flags": ["stackable"],
    },
    "silver_coin": {
        "name": "silver coin",
        "type": "currency",
        "description": "A shiny silver coin.",
        "weight": 0.01,
        "flags": ["stackable"],
    },
    "gold_coin": {
        "name": "gold coin",
        "type": "currency",
        "description": "A heavy gold coin stamped with the king's visage.",
        "weight": 0.02,
        "flags": ["stackable"],
    },
    "bread": {
        "name": "loaf of bread",
        "type": "food",
        "description": "A crusty loaf of bread.",
        "weight": 0.5,
        "flags": ["consumable"],
    },
    "water_skin": {
        "name": "water skin",
        "type": "drink",
        "description": "A leather skin full of water.",
        "weight": 1.0,
        "flags": ["consumable"],
    },
    "iron_sword": {
        "name": "iron sword",
        "type": "weapon",
        "description": "A sharp blade.",
        "detailed_description": "It has a chip near the hilt.",
        "weight": 5.0,
        "value": 10,
        "flags": [],
    },
    "leather_armor": {
        "name": "leather armor",
        "type": "armor",
        "description": "A suit of hardened leather armor.",
        "weight": 4.0,
        "flags": ["equippable"],
    },
    "healing_potion": {
        "name": "healing potion",
        "type": "potion",
        "description": "A vial of red liquid that smells of strawberries.",
        "weight": 0.2,
        "flags": ["consumable", "magic"],
    },
    "map_fragment": {
        "name": "torn map fragment",
        "type": "quest",
        "description": "A piece of an old map showing a location marked with an X.",
        "weight": 0.1,
        "flags": ["quest"],
    },
    "ancient_relic": {
        "name": "ancient relic",
        "type": "artifact",
        "description": "A strange, glowing object of unknown origin.",
        "weight": 1.5,
        "flags": ["quest", "artifact", "magic"],
    },
    "torch": {
        "name": "torch",
        "type": "light",
        "description": "A wooden torch dipped in pitch.",
        "weight": 0.5,
        "flags": ["consumable"],
    },
    "lantern": {
        "name": "lantern",
        "type": "light",
        "description": "A brass lantern with a glass pane.",
        "weight": 1.0,
        "flags": [],
    },
    "rope": {
        "name": "coil of rope",
        "type": "tool",
        "description": "A 50-foot coil of hemp rope.",
        "weight": 2.0,
        "flags": [],
    },
    "key": {
        "name": "iron key",
        "type": "key",
        "description": "A heavy iron key.",
        "weight": 0.1,
        "flags": [],
    },
    # --- NPC Items ---
    "carved_pipe": {
        "name": "carved wooden pipe",
        "type": "tool",
        "description": "A beautifully carved wooden pipe, smelling faintly of sweet tobacco.",
        "detailed_description": "The carvings depict scenes of ancient forests and dancing spirits.",
        "weight": 0.2,
        "flags": [],
        "is_held": True,
    },
    "tattered_journal": {
        "name": "tattered journal",
        "type": "book",
        "description": "A leather-bound journal with worn pages.",
        "detailed_description": "It's filled with handwritten notes about local legends and history.",
        "weight": 0.5,
        "flags": [],
    },
    "steel_spear": {
        "name": "steel spear",
        "type": "weapon",
        "description": "A sturdy spear with a gleaming steel tip.",
        "weight": 3.0,
        "damage": 6,
        "flags": ["equippable"],
        "is_held": True,
    },
    "guard_badge": {
        "name": "guard badge",
        "type": "misc",
        "description": "A bronze badge bearing the crest of the Hollowvale Watch.",
        "weight": 0.1,
        "flags": [],
    },
    "herbal_satchel": {
        "name": "herbal satchel",
        "type": "container",
        "description": "A worn leather satchel stained with plant juices.",
        "weight": 1.0,
        "capacity": 10.0,
        "flags": ["container"],
    },
    "dried_herbs": {
        "name": "bundle of dried herbs",
        "type": "ingredient",
        "description": "A bundle of aromatic dried herbs.",
        "weight": 0.1,
        "flags": ["consumable"],
    },
}

# Room capacity constants
MAX_ROOM_ITEMS = 50  # Maximum number of items a room can hold
MAX_ROOM_WEIGHT = 100.0  # Maximum total weight (kg) a room can hold


def get_item_def(item_id: str) -> Dict[str, Any]:
    """
    Get item definition, with graceful fallback for unknown items.
    
    Args:
        item_id: The item identifier (e.g., "copper_coin")
    
    Returns:
        dict: Item definition with at least name, type, description, flags, droppable, weight
    """
    if item_id in ITEM_DEFS:
        item_def = ITEM_DEFS[item_id].copy()
        # Ensure droppable defaults to True if not specified
        if "droppable" not in item_def:
            item_def["droppable"] = True
        # Ensure weight is set (default 0.1 kg for unknown items)
        if "weight" not in item_def:
            item_def["weight"] = 0.1
        return item_def
    
    # Fallback for unknown items
    return {
        "name": item_id.replace("_", " "),
        "type": "misc",
        "description": "",
        "weight": 0.1,  # Default weight in kg
        "flags": [],
        "droppable": True,  # Default to droppable
    }


def calculate_inventory_weight(inventory: List[str]) -> float:
    """
    Calculate total weight of items in inventory (in kg).
    
    Args:
        inventory: List of item IDs
    
    Returns:
        float: Total weight in kg
    """
    total_weight = 0.0
    for item_id in inventory:
        item_def = get_item_def(item_id)
        weight = item_def.get("weight", 0.1)
        total_weight += weight
    return total_weight


def calculate_room_items_weight(room_items: List[str]) -> float:
    """
    Calculate total weight of items in a room (in kg).
    
    Args:
        room_items: List of item IDs in the room
    
    Returns:
        float: Total weight in kg
    """
    total_weight = 0.0
    for item_id in room_items:
        item_def = get_item_def(item_id)
        weight = item_def.get("weight", 0.1)
        total_weight += weight
    return total_weight


def is_quest_item(item_id: str) -> bool:
    """
    Check if an item is a quest item (non-droppable, non-sellable, non-buryable).
    
    Args:
        item_id: Item identifier
    
    Returns:
        bool: True if item is a quest item
    """
    item_def = get_item_def(item_id)
    flags = item_def.get("flags", [])
    return "quest" in flags


def is_item_buryable(item_id: str) -> Tuple[bool, str]:
    """
    Check if an item can be buried (permanently removed).
    
    Args:
        item_id: Item identifier
    
    Returns:
        tuple: (can_bury, reason_message)
        - can_bury: True if item can be buried, False otherwise
        - reason_message: Explanation if cannot be buried (empty string if can bury)
    """
    item_def = get_item_def(item_id)
    
    # Currency cannot be buried
    item_type = item_def.get("type", "misc")
    if item_type == "currency":
        return False, "You cannot bury money."
    
    # Special/quest items cannot be buried (non-droppable items are usually special)
    if not item_def.get("droppable", True):
        return False, "That item is too special to bury."
    
    # Check for quest flags
    flags = item_def.get("flags", [])
    if "quest" in flags or "unique" in flags or "artifact" in flags:
        return False, "That item is too special to bury."
    
    # Artifact type items cannot be buried
    if item_type == "artifact":
        return False, "That item is too special to bury."
    
    return True, ""


def pluralize_word(word: str) -> str:
    """
    Pluralize a single word using English rules.
    
    Args:
        word: Single word to pluralize
    
    Returns:
        str: Pluralized word
    """
    if not word:
        return word
    
    lower_word = word.lower()
    
    # Special cases dictionary for irregular plurals
    irregular_plurals = {
        'loaf': 'loaves',
        'leaf': 'leaves',
        'knife': 'knives',
        'wife': 'wives',
        'life': 'lives',
        'half': 'halves',
        'wolf': 'wolves',
        'thief': 'thieves',
        'shelf': 'shelves',
        'elf': 'elves',
        'calf': 'calves',
        'self': 'selves',
        'piece': 'pieces',
        'child': 'children',
        'person': 'people',
        'man': 'men',
        'woman': 'women',
        'mouse': 'mice',
        'goose': 'geese',
        'tooth': 'teeth',
        'foot': 'feet',
        'ox': 'oxen',
        'fish': 'fish',  # Can be singular or plural
        'deer': 'deer',  # Can be singular or plural
        'sheep': 'sheep',  # Can be singular or plural
    }
    
    # Check irregular plurals first
    if lower_word in irregular_plurals:
        # Preserve capitalization
        if word[0].isupper():
            return irregular_plurals[lower_word].capitalize()
        return irregular_plurals[lower_word]
    
    # Already plural? (ends with common plural endings)
    if lower_word.endswith(('loaves', 'leaves', 'knives', 'wives', 'pieces', 'children', 'men', 'women', 'mice', 'geese', 'teeth', 'feet')):
        return word
    
    # Words ending in 'y' -> 'ies' (but not if preceded by vowel)
    if lower_word.endswith('y') and len(lower_word) > 1:
        second_last = lower_word[-2]
        if second_last not in 'aeiou':
            # Change 'y' to 'ies'
            if word[0].isupper():
                return word[:-1].capitalize() + 'ies'
            return word[:-1] + 'ies'
    
    # Words ending in 's', 'sh', 'ch', 'x', 'z' -> 'es'
    if lower_word.endswith(('s', 'sh', 'ch', 'x', 'z')):
        # But not if it already ends in 'es'
        if not lower_word.endswith('es'):
            return word + 'es'
        return word
    
    # Words ending in 'f' -> 'ves' (but not all 'f' words)
    if lower_word.endswith('f') and len(lower_word) > 1:
        # Common 'f' -> 'ves' words
        if lower_word in ('loaf', 'leaf', 'knife', 'wife', 'life', 'half', 'wolf', 'thief', 'shelf', 'elf', 'calf', 'self'):
            return word[:-1] + 'ves'
    
    # Words ending in 'fe' -> 'ves'
    if lower_word.endswith('fe'):
        return word[:-2] + 'ves'
    
    # Default: add 's'
    return word + 's'


def pluralize_item_name(item_name: str, count: int) -> str:
    """
    Pluralize an item name intelligently.
    
    Handles compound nouns (e.g., "loaf of bread" -> "loaves of bread"),
    special cases (e.g., "loaf" -> "loaves"), and regular pluralization.
    
    Args:
        item_name: Singular item name
        count: Quantity (unused but kept for API consistency)
    
    Returns:
        str: Pluralized item name
    """
    # Remove article if present
    if item_name.lower().startswith(('a ', 'an ')):
        item_name = item_name.split(' ', 1)[1] if ' ' in item_name else item_name
    
    # Handle compound nouns with "of" (e.g., "loaf of bread", "bowl of stew")
    if ' of ' in item_name.lower():
        parts = item_name.split(' of ', 1)
        if len(parts) == 2:
            first_word = parts[0].strip()
            rest = parts[1].strip()
            # Pluralize the first word
            plural_first = pluralize_word(first_word)
            return f"{plural_first} of {rest}"
    
    # Handle simple nouns - pluralize the whole thing
    return pluralize_word(item_name)


def render_item_name(item_id: str) -> str:
    """
    Render a human-friendly item name from an item_id.
    
    Args:
        item_id: The item identifier
    
    Returns:
        str: Human-friendly name (e.g., "copper coin" instead of "copper_coin")
    """
    item_def = get_item_def(item_id)
    return item_def.get("name", item_id.replace("_", " "))


def group_inventory_items(inventory: List[str]) -> List[str]:
    """
    Group inventory items by type and return formatted strings.
    
    Args:
        inventory: List of item IDs
    
    Returns:
        list: List of formatted strings like "4 loaves of bread", "1 iron hammer"
    """
    if not inventory:
        return []
    
    # Count items
    item_counts = Counter(inventory)
    
    grouped = []
    for item_id, count in sorted(item_counts.items()):
        item_name = render_item_name(item_id)
        
        # Handle pluralization
        if count == 1:
            # Use singular form with article
            if item_name.lower().startswith(('a', 'e', 'i', 'o', 'u')):
                grouped.append(f"an {item_name}")
            else:
                grouped.append(f"a {item_name}")
        else:
            # Use plural form
            # Try to pluralize intelligently
            plural_name = pluralize_item_name(item_name, count)
            grouped.append(f"{count} {plural_name}")
    
    return grouped


def match_item_name_in_collection(input_text: str, items: List[str]) -> Optional[str]:
    """
    Match user input against a collection of item_ids.
    
    Args:
        input_text: User input (e.g., "coin", "piece of bread")
        items: List of item_ids to search
    
    Returns:
        str | None: Best matching item_id, or None if no match
    """
    if not items:
        return None
    
    input_lower = input_text.lower().strip()
    input_normalized = " ".join(input_lower.split())
    
    # Track matches with scores (longer matches preferred)
    matches = []
    
    for item_id in items:
        item_lower = item_id.lower()
        item_spaced = item_id.replace("_", " ").lower()
        item_def = get_item_def(item_id)
        item_name_lower = item_def.get("name", item_spaced).lower()
        
        # Exact matches get highest priority
        if input_normalized == item_lower or input_normalized == item_spaced or input_normalized == item_name_lower:
            return item_id  # Immediate return for exact match
        
        # Check if input is contained in item name/id
        if input_normalized in item_lower or input_normalized in item_spaced or input_normalized in item_name_lower:
            match_length = len(input_normalized)
            matches.append((item_id, match_length, len(item_id)))
        
        # Check word-level matches
        item_words = item_spaced.split()
        input_words = input_normalized.split()
        
        for word in input_words:
            if word in item_words:
                match_length = len(word)
                matches.append((item_id, match_length, len(item_id)))
    
    if not matches:
        return None
    
    # Sort by match length (longer is better), then by item length (shorter is better for specificity)
    matches.sort(key=lambda x: (-x[1], x[2]))
    return matches[0][0]
