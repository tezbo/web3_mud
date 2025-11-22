"""
Game engine for Tiny Web MUD.

This module contains pure game logic - world definition, state transitions,
and command handling. It has no dependencies on Flask or web frameworks.
"""

import re
import os
import json
import time
from datetime import datetime, timedelta

# Safe import of AI client (optional)
try:
    from ai_client import generate_npc_reply
except ImportError:
    generate_npc_reply = None

# Import NPC system
from npc import NPCS, match_npc_in_room, get_npc_reaction, generate_npc_line

# --- NPC definitions moved to npc.py ---
# NPCs are now loaded via the NPC class system from npc.py

# --- Admin configuration ---

# Admin users (can be extended via environment variable or database)
ADMIN_USERS = set(os.environ.get("ADMIN_USERS", "admin,tezbo").split(","))

# --- Character Creation & Onboarding Constants ---

AVAILABLE_RACES = {
    "human": {
        "name": "Human",
        "description": "Versatile and adaptable, humans are the most common folk in Hollowvale. You have no special abilities, but your flexibility allows you to excel in any path you choose.",
    },
    "elf": {
        "name": "Elf",
        "description": "Graceful and long-lived, elves have keen senses and a natural affinity for the arcane. You move with an otherworldly elegance.",
    },
    "dwarf": {
        "name": "Dwarf",
        "description": "Sturdy and resilient, dwarves are masters of craft and stone. You have a natural toughness and an eye for detail.",
    },
    "halfling": {
        "name": "Halfling",
        "description": "Small but determined, halflings are known for their luck and resourcefulness. You have a knack for finding opportunities where others see none.",
    },
    "fae-touched": {
        "name": "Fairy",
        "description": "Touched by the magic of the fae realm, you have an otherworldly presence. Reality seems to bend slightly around you.",
    },
    "outlander": {
        "name": "Lyzard",
        "description": "From lands unknown, you are a mystery to most. Your origins are strange, and you carry the weight of distant places.",
    },
}

AVAILABLE_GENDERS = {
    "male": {"name": "Male", "pronoun": "he", "pronoun_cap": "He", "possessive": "his"},
    "female": {"name": "Female", "pronoun": "she", "pronoun_cap": "She", "possessive": "her"},
    "nonbinary": {"name": "Nonbinary", "pronoun": "they", "pronoun_cap": "They", "possessive": "their"},
    "other": {"name": "Other", "pronoun": "they", "pronoun_cap": "They", "possessive": "their"},
}

AVAILABLE_BACKSTORIES = {
    "scarred_past": {
        "name": "Scarred Past",
        "description": "You carry the weight of loss and hardship. Your past has left marks, but also made you stronger.",
    },
    "forgotten_lineage": {
        "name": "Forgotten Lineage",
        "description": "You know little of your true heritage, but sense there is more to your story than meets the eye.",
    },
    "broken_oath": {
        "name": "Broken Oath",
        "description": "You once made a promise you could not keep. The weight of that failure drives you forward.",
    },
    "hopeful_spark": {
        "name": "Hopeful Spark",
        "description": "Despite the darkness in the world, you carry a light within. You believe in better days ahead.",
    },
    "quiet_mystery": {
        "name": "Quiet Mystery",
        "description": "You prefer to keep your past to yourself. There are things you know that others do not.",
    },
    "custom": {
        "name": "Custom",
        "description": "Your story is your own to tell.",
    },
}

STAT_NAMES = {
    "str": "Strength",
    "agi": "Agility",
    "wis": "Wisdom",
    "wil": "Willpower",
    "luck": "Luck",
}

TOTAL_STAT_POINTS = 10

# --- Onboarding Narrative Text ---

ONBOARDING_USERNAME_PROMPT = """In the darkness, you drift...

A voice, ancient and warm, reaches through the void:

"Awaken, lost soul. Your journey begins in the realm between worlds."

Slowly, awareness returns. You feel... something. A presence. A purpose.

"Before you step into Hollowvale, you must remember who you are."

The voice asks: "What name will you bear in this realm?"

Enter your username (this will be your character name):"""

ONBOARDING_PASSWORD_PROMPT = """"Good. Now, choose a password to protect your identity."

Enter your password (minimum 4 characters):"""

ONBOARDING_RACE_PROMPT = """The voice speaks again:

"First, tell me: what form do you remember? What blood flows in your veins?"

Choose your race:
- human
- elf
- dwarf
- halfling
- fae-touched
- outlander

Type the name of your race:"""

ONBOARDING_GENDER_PROMPT = """"Good. Now, how do you know yourself? What is your nature?"

Choose your gender:
- male
- female
- nonbinary
- other

Type your choice:"""

ONBOARDING_STATS_PROMPT = """"Your essence takes shape. Now, where do your strengths lie?"

You have 10 points to distribute across five attributes:
- str (Strength): Physical power and might
- agi (Agility): Speed, dexterity, and reflexes
- wis (Wisdom): Knowledge, insight, and understanding
- wil (Willpower): Mental fortitude and determination
- luck (Luck): Fortune and chance

Enter your stat allocation like this: str 3, agi 2, wis 2, wil 2, luck 1
(All five stats must total exactly 10 points)

Your allocation:"""

ONBOARDING_BACKSTORY_PROMPT = """"Every soul carries a story. What is yours?"

Choose your backstory:
- scarred_past: You carry the weight of loss and hardship
- forgotten_lineage: You know little of your true heritage
- broken_oath: You once made a promise you could not keep
- hopeful_spark: You believe in better days ahead
- quiet_mystery: You prefer to keep your past to yourself
- custom: Your story is your own to tell

Type your choice (or 'custom' to write your own):"""

ONBOARDING_COMPLETE = """The voice grows distant:

"Your form is complete. Your story begins. Welcome to Hollowvale, {username}."

Light floods your vision. The darkness fades away...

You find yourself standing in the Town Square of Hollowvale, a frontier town where adventure awaits."""


def handle_onboarding_command(command, onboarding_state, username=None, db_conn=None):
    """
    Handle commands during the onboarding process.
    
    Args:
        command: User's command input
        onboarding_state: Dict with onboarding_step and character data
        username: Player's username (optional, may be None during account creation)
        db_conn: Optional database connection for creating user account
    
    Returns:
        tuple: (response_text, updated_onboarding_state, is_complete, created_user_id)
    """
    step = onboarding_state.get("step", 0)
    character = onboarding_state.get("character", {})
    command_lower = command.strip().lower()
    created_user_id = None
    
    if step == 0:  # Username creation
        username_input = command.strip()
        if not username_input:
            return "Please enter a username.", onboarding_state, False, None
        if len(username_input) < 2:
            return "Username must be at least 2 characters long.", onboarding_state, False, None
        if len(username_input) > 20:
            return "Username must be 20 characters or less.", onboarding_state, False, None
        
        # Check if username already exists
        if db_conn:
            existing = db_conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username_input,)
            ).fetchone()
            if existing:
                return f"Username '{username_input}' is already taken. Please choose another.", onboarding_state, False, None
        
        onboarding_state["username"] = username_input
        onboarding_state["step"] = 0.5  # Next: password
        return ONBOARDING_PASSWORD_PROMPT, onboarding_state, False, None
    
    elif step == 0.5:  # Password creation
        password_input = command
        if not password_input:
            return "Please enter a password.", onboarding_state, False, None
        if len(password_input) < 4:
            return "Password must be at least 4 characters long.", onboarding_state, False, None
        
        onboarding_state["password"] = password_input
        onboarding_state["step"] = 1  # Next: race
        return ONBOARDING_RACE_PROMPT, onboarding_state, False, None
    
    elif step == 1:  # Race selection
        if command_lower in AVAILABLE_RACES:
            character["race"] = command_lower
            onboarding_state["character"] = character
            onboarding_state["step"] = 2
            return ONBOARDING_GENDER_PROMPT, onboarding_state, False, None
        else:
            return "Please choose a valid race: human, elf, dwarf, halfling, fae-touched, or outlander", onboarding_state, False, None
    
    elif step == 2:  # Gender selection
        if command_lower in AVAILABLE_GENDERS:
            character["gender"] = command_lower
            onboarding_state["character"] = character
            onboarding_state["step"] = 3
            return ONBOARDING_STATS_PROMPT, onboarding_state, False, None
        else:
            return "Please choose a valid gender: male, female, nonbinary, or other", onboarding_state, False, None
    
    elif step == 3:  # Stat allocation
        # Parse stat allocation: "str 3, agi 2, wis 2, wil 2, luck 1"
        stats = {"str": 0, "agi": 0, "wis": 0, "wil": 0, "luck": 0}
        try:
            # Split by comma and parse each stat
            parts = [p.strip() for p in command_lower.split(",")]
            for part in parts:
                if not part:
                    continue
                # Match pattern like "str 3" or "str:3" or "str=3"
                match = re.match(r'(\w+)\s*[:=]?\s*(\d+)', part)
                if match:
                    stat_name = match.group(1).lower()
                    stat_value = int(match.group(2))
                    if stat_name in stats:
                        stats[stat_name] = stat_value
                    else:
                        return f"Unknown stat: {stat_name}. Valid stats are: str, agi, wis, wil, luck", onboarding_state, False, None
            
            # Validate total
            total = sum(stats.values())
            if total != TOTAL_STAT_POINTS:
                return f"Your stats must total exactly {TOTAL_STAT_POINTS} points. You allocated {total} points. Please try again.", onboarding_state, False, None
            
            # Check for negative values
            if any(v < 0 for v in stats.values()):
                return "Stat values cannot be negative. Please try again.", onboarding_state, False, None
            
            character["stats"] = stats
            onboarding_state["character"] = character
            onboarding_state["step"] = 4
            return ONBOARDING_BACKSTORY_PROMPT, onboarding_state, False, None
        except Exception as e:
            return f"Invalid stat format. Please use: str 3, agi 2, wis 2, wil 2, luck 1", onboarding_state, False, None
    
    elif step == 4:  # Backstory selection
        if command_lower == "custom":
            onboarding_state["step"] = 5  # Custom backstory input
            return "Tell me your story in your own words (keep it brief, 1-2 sentences):", onboarding_state, False, None
        elif command_lower in AVAILABLE_BACKSTORIES:
            character["backstory"] = command_lower
            character["backstory_text"] = AVAILABLE_BACKSTORIES[command_lower]["description"]
            onboarding_state["character"] = character
            onboarding_state["step"] = 6  # Complete
            
            # Create user account now that character is complete
            if db_conn and onboarding_state.get("username") and onboarding_state.get("password"):
                from werkzeug.security import generate_password_hash
                username_final = onboarding_state["username"]
                password_hash = generate_password_hash(onboarding_state["password"])
                try:
                    cursor = db_conn.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username_final, password_hash)
                    )
                    db_conn.commit()
                    created_user_id = cursor.lastrowid
                except Exception as e:
                    return f"Error creating account: {str(e)}", onboarding_state, False, None
            
            final_username = onboarding_state.get("username", username or "adventurer")
            return ONBOARDING_COMPLETE.format(username=final_username), onboarding_state, True, created_user_id
        else:
            return "Please choose a valid backstory or type 'custom' to write your own.", onboarding_state, False, None
    
    elif step == 5:  # Custom backstory input
        if command_lower and len(command_lower) > 5:
            character["backstory"] = "custom"
            character["backstory_text"] = command.strip()  # Keep original case
            onboarding_state["character"] = character
            onboarding_state["step"] = 6  # Complete
            
            # Create user account now that character is complete
            if db_conn and onboarding_state.get("username") and onboarding_state.get("password"):
                from werkzeug.security import generate_password_hash
                username_final = onboarding_state["username"]
                password_hash = generate_password_hash(onboarding_state["password"])
                try:
                    cursor = db_conn.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username_final, password_hash)
                    )
                    db_conn.commit()
                    created_user_id = cursor.lastrowid
                except Exception as e:
                    return f"Error creating account: {str(e)}", onboarding_state, False, None
            
            final_username = onboarding_state.get("username", username or "adventurer")
            return ONBOARDING_COMPLETE.format(username=final_username), onboarding_state, True, created_user_id
        else:
            return "Please provide a brief backstory (at least a few words).", onboarding_state, False, None
    
    return "Invalid command during onboarding.", onboarding_state, False, None, None


def is_admin_user(username=None, game=None):
    """
    Check if a user is an admin.
    
    Args:
        username: Optional username string
        game: Optional game state dict (may contain is_admin flag)
    
    Returns:
        bool: True if user is admin
    """
    # Check game state first (if admin flag is set there)
    if game and game.get("is_admin"):
        return True
    
    # Check username against admin list
    if username and username.lower() in {u.lower() for u in ADMIN_USERS}:
        return True
    
    return False


# --- Direction maps for room enter/leave messages ---

DIRECTION_MAP = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
}

OPPOSITE_DIRECTION = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}

# --- Emote definitions (static templates) ---

EMOTES = {
    "nod": {
        "self": "You nod.",
        "self_target": "You nod at {target}.",
        "room": "{actor} nods.",
        "room_target": "{actor} nods at {target}.",
        "target": "{actor} nods at you.",
    },
    "smile": {
        "self": "You smile.",
        "self_target": "You smile at {target}.",
        "room": "{actor} smiles.",
        "room_target": "{actor} smiles at {target}.",
        "target": "{actor} smiles at you.",
    },
    "wave": {
        "self": "You wave.",
        "self_target": "You wave at {target}.",
        "room": "{actor} waves.",
        "room_target": "{actor} waves at {target}.",
        "target": "{actor} waves at you.",
    },
    "shrug": {
        "self": "You shrug.",
        "self_target": "You shrug at {target}.",
        "room": "{actor} shrugs.",
        "room_target": "{actor} shrugs at {target}.",
        "target": "{actor} shrugs at you.",
    },
    "stare": {
        "self": "You stare into the distance.",
        "self_target": "You stare at {target}.",
        "room": "{actor} stares.",
        "room_target": "{actor} stares at {target}.",
        "target": "{actor} stares at you.",
    },
    "laugh": {
        "self": "You laugh.",
        "self_target": "You laugh with {target}.",
        "room": "{actor} laughs.",
        "room_target": "{actor} laughs with {target}.",
        "target": "{actor} laughs with you.",
    },
    "grin": {
        "self": "You grin.",
        "self_target": "You grin at {target}.",
        "room": "{actor} grins.",
        "room_target": "{actor} grins at {target}.",
        "target": "{actor} grins at you.",
    },
    "frown": {
        "self": "You frown.",
        "self_target": "You frown at {target}.",
        "room": "{actor} frowns.",
        "room_target": "{actor} frowns at {target}.",
        "target": "{actor} frowns at you.",
    },
    "sigh": {
        "self": "You sigh.",
        "self_target": "You sigh at {target}.",
        "room": "{actor} sighs.",
        "room_target": "{actor} sighs at {target}.",
        "target": "{actor} sighs at you.",
    },
    "yawn": {
        "self": "You yawn.",
        "self_target": "You yawn at {target}.",
        "room": "{actor} yawns.",
        "room_target": "{actor} yawns at {target}.",
        "target": "{actor} yawns at you.",
    },
    "clap": {
        "self": "You clap.",
        "self_target": "You clap for {target}.",
        "room": "{actor} claps.",
        "room_target": "{actor} claps for {target}.",
        "target": "{actor} claps for you.",
    },
    "bow": {
        "self": "You bow.",
        "self_target": "You bow to {target}.",
        "room": "{actor} bows.",
        "room_target": "{actor} bows to {target}.",
        "target": "{actor} bows to you.",
    },
    "salute": {
        "self": "You salute.",
        "self_target": "You salute {target}.",
        "room": "{actor} salutes.",
        "room_target": "{actor} salutes {target}.",
        "target": "{actor} salutes you.",
    },
}

# --- Item definitions (interactables system) ---

ITEM_DEFS = {
    "copper_coin": {
        "name": "copper coin",
        "type": "currency",
        "description": "A simple copper coin, worn and slightly tarnished.",
        "weight": 0.01,
        "flags": ["stackable"],
    },
    "wooden_tankard": {
        "name": "wooden tankard",
        "type": "container",
        "description": "A simple wooden tankard, well-used but sturdy.",
        "weight": 0.2,
        "flags": [],
    },
    "iron_hammer": {
        "name": "iron hammer",
        "type": "tool",
        "description": "A heavy iron hammer, well-balanced and ready for work.",
        "weight": 2.0,
        "flags": [],
    },
    "lump_of_ore": {
        "name": "lump of ore",
        "type": "material",
        "description": "A rough lump of unrefined ore, heavy and promising.",
        "weight": 1.5,
        "flags": [],
    },
    "fresh_bread": {
        "name": "fresh bread",
        "type": "food",
        "description": "A loaf of fresh bread, still warm and smelling of the oven.",
        "weight": 0.5,
        "flags": [],
    },
    "simple_amulet": {
        "name": "simple amulet",
        "type": "trinket",
        "description": "A small amulet of simple design, worn smooth by time.",
        "weight": 0.1,
        "flags": [],
    },
    "smooth_rune_stone": {
        "name": "smooth rune stone",
        "type": "artifact",
        "description": "A smooth stone marked with ancient runes, humming with subtle energy.",
        "weight": 0.3,
        "flags": [],
        "droppable": False,  # Example of a non-droppable item (bound artifact)
    },
    "bundle_of_herbs": {
        "name": "bundle of herbs",
        "type": "material",
        "description": "A small bundle of dried herbs, fragrant and useful.",
        "weight": 0.1,
        "flags": [],
    },
    "strange_leaf": {
        "name": "strange leaf",
        "type": "material",
        "description": "An unusual leaf that seems to shimmer slightly in the light.",
        "weight": 0.05,
        "flags": [],
    },
    "loose_stone": {
        "name": "loose stone",
        "type": "misc",
        "description": "A loose stone that has fallen from the path.",
        "weight": 0.3,
        "flags": [],
    },
    "cracked_spyglass": {
        "name": "cracked spyglass",
        "type": "tool",
        "description": "A spyglass with a cracked lens, but still somewhat functional.",
        "weight": 0.4,
        "flags": [],
    },
    "weathered_signpost": {
        "name": "weathered signpost",
        "type": "misc",
        "description": "An old signpost, its markings faded but still readable.",
        "weight": 5.0,
        "flags": [],
    },
    "bowl_of_stew": {
        "name": "bowl of stew",
        "type": "food",
        "description": "A hearty bowl of stew that smells of herbs and slow-cooked meat.",
        "weight": 0.3,
        "flags": [],
    },
    "tankard_of_ale": {
        "name": "tankard of ale",
        "type": "food",
        "description": "A frothy tankard of ale, cool and refreshing.",
        "weight": 0.3,
        "flags": [],
    },
    "loaf_of_bread": {
        "name": "loaf of bread",
        "type": "food",
        "description": "A substantial loaf of bread, perfect for sharing or keeping.",
        "weight": 0.5,
        "flags": [],
    },
    "piece_of_bread": {
        "name": "piece of bread",
        "type": "food",
        "description": "A small piece of bread, still fresh and soft.",
        "weight": 0.1,
        "flags": [],
    },
}


def get_item_def(item_id: str) -> dict:
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


def calculate_inventory_weight(inventory: list) -> float:
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


def calculate_room_items_weight(room_items: list) -> float:
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


# Room capacity constants
MAX_ROOM_ITEMS = 50  # Maximum number of items a room can hold
MAX_ROOM_WEIGHT = 100.0  # Maximum total weight (kg) a room can hold


def group_inventory_items(inventory: list) -> list:
    """
    Group inventory items by type and return formatted strings.
    
    Args:
        inventory: List of item IDs
    
    Returns:
        list: List of formatted strings like "4 loaves of bread", "1 iron hammer"
    """
    from collections import Counter
    
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


def match_item_name_in_collection(input_text: str, items: list[str]) -> str | None:
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


# --- Merchant items definition (what NPCs sell) ---
# Merchant items - now uses economy system for pricing
# item_given is what the player receives
MERCHANT_ITEMS = {
    "innkeeper": {
        "stew": {"item_given": "bowl_of_stew", "display_name": "bowl of stew", "initial_stock": 10},
        "bowl_of_stew": {"item_given": "bowl_of_stew", "display_name": "bowl of stew", "initial_stock": 10},
        "ale": {"item_given": "tankard_of_ale", "display_name": "tankard of ale", "initial_stock": 20},
        "tankard_of_ale": {"item_given": "tankard_of_ale", "display_name": "tankard of ale", "initial_stock": 20},
        "bread": {"item_given": "loaf_of_bread", "display_name": "loaf of bread", "initial_stock": 15},
        "loaf_of_bread": {"item_given": "loaf_of_bread", "display_name": "loaf of bread", "initial_stock": 15},
        "piece_of_bread": {"item_given": "piece_of_bread", "display_name": "piece of bread", "initial_stock": 20},
    }
}

# --- Simple game world definition (static, never mutated at runtime) ---
# 
# Room definitions can include an optional "movement_message" field for custom
# messages when entering the room. Examples:
#   "movement_message": "You step through the archway and enter {location}."
#   "movement_message": lambda direction, location: f"You climb {direction}ward and reach {location}."
# If not specified, defaults to: "You go {direction}, and find yourself in the {location}."

WORLD = {
    "town_square": {
        "name": "Hollowvale Town Square",
        "description": (
            "You stand in the heart of Hollowvale, a cozy frontier square where "
            "cracked cobblestones circle an old fountain. The water still flows, "
            "though the basin is weathered with age. A notice board stands to one side, "
            "its parchment fluttering in the breeze. To the north, a rocky path leads "
            "up toward the watchtower that overlooks the valley. The square feels "
            "familiar and safe, yet there's a sense that this place has seen many stories."
        ),
        "exits": {"north": "watchtower_path", "south": "tavern", "east": "market_lane", "west": "forest_edge"},
        "items": ["copper_coin"],
        "npcs": ["old_storyteller"],
    },
    "tavern": {
        "name": "The Rusty Tankard Tavern",
        "description": (
            "The Rusty Tankard welcomes you with warmth and noise. The air is thick with "
            "the smell of stew and wood smoke. Rough-hewn tables fill the space, and "
            "adventurers and locals share stories over tankards of ale. A fire crackles "
            "in the hearth, casting dancing shadows on the walls. This is the kind of "
            "place where news travels and friendships are forged."
        ),
        "exits": {"north": "town_square", "south": "smithy"},
        "items": ["wooden_tankard"],
        "npcs": ["innkeeper"],
    },
    "smithy": {
        "name": "Old Stoneforge Smithy",
        "description": (
            "The smithy is a low building of stone and timber, its walls hung with tools "
            "and half-finished work. The forge glows with banked embers, and the air "
            "carries the scent of coal and hot metal. Anvils stand ready, and the walls "
            "are lined with hammers, tongs, and other implements of the trade. This is "
            "where the village's metalwork is born, practical and honest."
        ),
        "exits": {"north": "tavern"},
        "items": ["iron_hammer", "lump_of_ore"],
        "npcs": ["blacksmith"],
    },
    "market_lane": {
        "name": "Market Lane",
        "description": (
            "A narrow lane runs between buildings, where market stalls would normally "
            "crowd the space. Today it's quiet, but you can see where vendors set up "
            "their wares—bread, herbs, trinkets, and simple goods. The lane feels "
            "lived-in, with worn stones underfoot and the lingering scents of spices "
            "and fresh bread. On market days, this place would be bustling, but now "
            "it holds a peaceful, almost contemplative air."
        ),
        "exits": {"west": "town_square", "east": "old_road", "south": "shrine_of_the_forgotten"},
        "items": ["fresh_bread", "simple_amulet"],
        "npcs": ["herbalist"],
    },
    "shrine_of_the_forgotten": {
        "name": "Shrine of the Forgotten Path",
        "description": (
            "A small stone shrine stands here, its carvings worn smooth by time and weather. "
            "The patterns etched into the stone are ancient, their meaning lost to most, "
            "but they seem to hum with a subtle energy. There's something mysterious about "
            "this place—a sense of deep history and forgotten knowledge. The air feels "
            "different here, as if the boundary between the mundane and something more "
            "is thinner. This is a place of quiet power, waiting to be understood."
        ),
        "exits": {"north": "market_lane"},
        "items": ["smooth_rune_stone"],
        "npcs": ["quiet_acolyte"],
        # Example of custom movement message:
        # "movement_message": "You step through the ancient archway and find yourself at the {location}.",
    },
    "forest_edge": {
        "name": "Edge of the Whispering Wood",
        "description": (
            "The last cottages of Hollowvale give way to the forest here. The trees begin "
            "to crowd closer, and the familiar sounds of village life—birdsong, voices, "
            "the clang of the smithy—begin to fade. There's a slight unease in the air, "
            "as if the wood itself is watching. The path into the trees looks inviting "
            "yet somehow foreboding. This is where the known world meets the unknown, "
            "where stories of the deeper forest begin."
        ),
        "exits": {"east": "town_square", "north": "whispering_trees"},
        "items": ["bundle_of_herbs"],
        "npcs": ["nervous_farmer"],
    },
    "whispering_trees": {
        "name": "The Whispering Trees",
        "description": (
            "You've entered a dense grove where the trees seem to lean in, their branches "
            "creating a canopy that filters the light. The air is still, and there's a "
            "sense that you're not entirely alone. The trees themselves seem to hold "
            "conversations in rustling leaves, though you can't quite make out the words. "
            "This place feels alive in a way that goes beyond the ordinary, as if the "
            "forest has its own voice, its own awareness. A good place to listen, if you "
            "know how."
        ),
        "exits": {"south": "forest_edge", "east": "ancient_door"},
        "items": ["strange_leaf"],
        "npcs": ["forest_spirit"],
    },
    "ancient_door": {
        "name": "The Buried Door",
        "description": (
            "Half-buried in the earth and overgrown with moss, a stone door stands here, "
            "its surface covered in runes that seem to shift when you look away. The door "
            "is clearly ancient, older than the village, older than memory. It doesn't "
            "open—not yet, perhaps not ever by ordinary means. But its presence here is "
            "significant, a marker of something important that lies beyond current "
            "understanding. The runes whisper of forgotten ages and paths not yet taken."
        ),
        "exits": {"west": "whispering_trees"},
        "items": [],
        "npcs": [],
    },
    "watchtower_path": {
        "name": "Watchtower Path",
        "description": (
            "A rocky path winds up the hill from the town square. Scrub and hardy grasses "
            "cling to the slopes, and the wind has a sharper bite here. The path is well-worn, "
            "suggesting regular use, though you see no one on it now. Above, the watchtower "
            "stands sentinel, its stone weathered but still strong. This path connects the "
            "heart of the village to its highest point, where the wider world can be seen."
        ),
        "exits": {"south": "town_square", "north": "watchtower"},
        "items": ["loose_stone"],
        "npcs": ["patrolling_guard"],
    },
    "watchtower": {
        "name": "Old Watchtower",
        "description": (
            "You stand at the top of the watchtower, where the wind whips freely and the "
            "valley spreads out below. The stone is crumbling in places, but the structure "
            "still serves its purpose. From here, you can see Hollowvale spread out like a "
            "map—the square, the lanes, the forest edge, and beyond that, the unknown lands "
            "that stretch to the horizon. There's something slightly eerie about this place, "
            "as if the tower has seen things it cannot forget. Yet it also offers a sense "
            "of perspective, a reminder that this village is part of a much larger world."
        ),
        "exits": {"south": "watchtower_path"},
        "items": ["cracked_spyglass"],
        "npcs": ["watch_guard"],
    },
    "old_road": {
        "name": "Old Eastward Road",
        "description": (
            "An old, rutted road runs eastward out of Hollowvale, its surface worn by "
            "countless travelers and the passage of time. This road leads toward lands "
            "you've only heard of in stories—kingdoms, cities, and adventures that lie "
            "beyond the horizon. For now, it feels like the edge of your known world, "
            "a threshold between the familiar and the vast unknown. The road promises "
            "journeys yet to come, stories yet to be written."
        ),
        "exits": {"west": "market_lane"},
        "items": ["weathered_signpost"],
        "npcs": ["wandering_trader"],
    },
}

# --- Global shared room state (shared across all players) ---

ROOM_STATE = {
    room_id: {
        "items": list(room_def.get("items", []))
    }
    for room_id, room_def in WORLD.items()
}

# --- World Clock (tracks in-game time) ---
# In-game time: 1 in-game hour = 1 real-world hour (configurable)
# 1 in-game day = 2 real-world hours (daybreak at hour 0, nightfall at hour 1, repeat)
WORLD_CLOCK = {
    "start_time": datetime.now().isoformat(),  # When the world clock started
    "in_game_hours": 0,  # Total in-game hours elapsed
    "last_restock": {},  # {npc_id: last_restock_in_game_hour}
    "current_period": "day",  # "day" or "night"
    "last_period_change_hour": 0,  # Last in-game hour when period changed
}

# Configuration: 1 in-game hour = X real-world hours
# Default: 1 in-game hour = 1 real-world hour
IN_GAME_HOUR_DURATION = float(os.environ.get("IN_GAME_HOUR_DURATION", "1.0"))

# Configuration: 1 in-game day = X real-world hours
# Default: 1 in-game day = 2 real-world hours
IN_GAME_DAY_DURATION = float(os.environ.get("IN_GAME_DAY_DURATION", "2.0"))


def get_current_in_game_hour():
    """
    Calculate current in-game hour based on real-world time.
    
    Returns:
        float: Current in-game hour (can be fractional)
    """
    if not WORLD_CLOCK.get("start_time"):
        WORLD_CLOCK["start_time"] = datetime.now().isoformat()
        WORLD_CLOCK["in_game_hours"] = 0
        WORLD_CLOCK["current_period"] = "day"
        WORLD_CLOCK["last_period_change_hour"] = 0
        return 0.0
    
    start_time = datetime.fromisoformat(WORLD_CLOCK["start_time"])
    elapsed_real_hours = (datetime.now() - start_time).total_seconds() / 3600.0
    elapsed_in_game_hours = elapsed_real_hours / IN_GAME_HOUR_DURATION
    WORLD_CLOCK["in_game_hours"] = elapsed_in_game_hours
    return elapsed_in_game_hours


def get_current_in_game_day():
    """
    Calculate current in-game day number (0-based).
    
    Returns:
        int: Current in-game day number
    """
    current_hour = get_current_in_game_hour()
    # 1 in-game day = 2 in-game hours (since 1 in-game day = 2 real-world hours)
    in_game_hours_per_day = IN_GAME_DAY_DURATION / IN_GAME_HOUR_DURATION
    return int(current_hour / in_game_hours_per_day)


def get_current_period():
    """
    Get current time period (day or night).
    Day: hours 0-1 of each day (first half)
    Night: hours 1-2 of each day (second half)
    
    Returns:
        str: "day" or "night"
    """
    current_hour = get_current_in_game_hour()
    in_game_hours_per_day = IN_GAME_DAY_DURATION / IN_GAME_HOUR_DURATION
    hour_in_day = current_hour % in_game_hours_per_day
    
    # Day is first half, night is second half
    if hour_in_day < (in_game_hours_per_day / 2):
        return "day"
    else:
        return "night"


def check_period_transition():
    """
    Check if day/night period has changed and return notification message if so.
    
    Returns:
        str | None: Notification message if period changed, None otherwise
    """
    current_period = get_current_period()
    last_period = WORLD_CLOCK.get("current_period", "day")
    current_hour = get_current_in_game_hour()
    last_change_hour = WORLD_CLOCK.get("last_period_change_hour", 0)
    in_game_hours_per_day = IN_GAME_DAY_DURATION / IN_GAME_HOUR_DURATION
    
    # Check if period has changed
    if current_period != last_period:
        WORLD_CLOCK["current_period"] = current_period
        WORLD_CLOCK["last_period_change_hour"] = current_hour
        
        if current_period == "day":
            return "Another day has dawned."
        else:
            return "The cover of night sweeps over the land."
    
    return None


def should_restock_merchant(npc_id):
    """
    Check if a merchant should restock (24 in-game hours since last restock).
    
    Args:
        npc_id: Merchant NPC ID
    
    Returns:
        bool: True if should restock
    """
    current_hour = get_current_in_game_hour()
    last_restock = WORLD_CLOCK.get("last_restock", {}).get(npc_id, 0)
    
    # Restock every 24 in-game hours
    return (current_hour - last_restock) >= 24.0


def mark_merchant_restocked(npc_id):
    """Mark a merchant as restocked at the current in-game hour."""
    current_hour = get_current_in_game_hour()
    if "last_restock" not in WORLD_CLOCK:
        WORLD_CLOCK["last_restock"] = {}
    WORLD_CLOCK["last_restock"][npc_id] = current_hour


# --- Global NPC state (tracks NPC locations and dynamic state) ---

NPC_STATE = {}


def init_npc_state():
    """Initialize NPC_STATE from WORLD static definitions."""
    global NPC_STATE
    
    # Only initialize if NPC_STATE is empty (don't overwrite loaded state)
    if NPC_STATE:
        return
    
    from npc import NPCS
    
    # Track which room each NPC first appears in (for home_room)
    npc_first_room = {}
    
    for room_id, room_def in WORLD.items():
        npc_ids = room_def.get("npcs", [])
        for npc_id in npc_ids:
            if npc_id not in npc_first_room:
                npc_first_room[npc_id] = room_id
            
            if npc_id not in NPC_STATE:
                # Determine home_room: prefer NPCS[npc_id].home, else first room
                npc = NPCS.get(npc_id)
                home_room = None
                if npc and hasattr(npc, 'home') and npc.home:
                    home_room = npc.home
                else:
                    home_room = npc_first_room.get(npc_id, room_id)
                
                # Get stats from NPCS if available
                max_hp = 10  # default
                if npc and hasattr(npc, 'stats') and npc.stats:
                    max_hp = npc.stats.get("max_hp", 10)
                
                npc_state = {
                    "room": room_id,
                    "home_room": home_room,
                    "hp": max_hp,
                    "alive": True,
                    "status": "idle"
                }
                
                # Initialize merchant inventory if this NPC is a merchant
                if npc_id in MERCHANT_ITEMS:
                    npc_state["merchant_inventory"] = {}
                    for item_key, item_info in MERCHANT_ITEMS[npc_id].items():
                        item_given = item_info.get("item_given")
                        if item_given:
                            # Use the item_given as the key for stock tracking
                            initial_stock = item_info.get("initial_stock", 10)
                            npc_state["merchant_inventory"][item_given] = initial_stock
                
                NPC_STATE[npc_id] = npc_state


def get_npcs_in_room(room_id):
    """Returns a list of npc_id strings whose NPC_STATE['room'] == room_id."""
    return [
        npc_id for npc_id, state in NPC_STATE.items()
        if state.get("room") == room_id
    ]


def get_npc_home_room(npc_id: str) -> str | None:
    """
    Get the home room for an NPC.
    
    Args:
        npc_id: The NPC identifier
    
    Returns:
        str | None: Home room ID, or None if not found
    """
    from npc import NPCS
    
    # Check NPC_STATE first
    if npc_id in NPC_STATE:
        home_room = NPC_STATE[npc_id].get("home_room")
        if home_room:
            return home_room
    
    # Fall back to NPCS metadata
    npc = NPCS.get(npc_id)
    if npc and hasattr(npc, 'home') and npc.home:
        return npc.home
    
    return None


def reset_npc_to_home(npc_id: str):
    """
    Reset an NPC to their home room.
    
    Args:
        npc_id: The NPC identifier
    """
    home_room = get_npc_home_room(npc_id)
    if home_room:
        if npc_id not in NPC_STATE:
            # Create basic entry if missing
            from npc import NPCS
            npc = NPCS.get(npc_id)
            max_hp = 10
            if npc and hasattr(npc, 'stats') and npc.stats:
                max_hp = npc.stats.get("max_hp", 10)
            NPC_STATE[npc_id] = {
                "room": home_room,
                "home_room": home_room,
                "hp": max_hp,
                "alive": True,
                "status": "idle"
            }
        else:
            # Update room, preserve other state
            NPC_STATE[npc_id]["room"] = home_room


def resolve_item_target(game, target_text):
    """
    Resolve an item target from user input.
    
    Args:
        game: Game state dict
        target_text: User input (e.g., "coin", "copper coin")
    
    Returns:
        tuple: (item_id, source, container) or (None, None, None) if not found
        - item_id: canonical item ID (e.g., "copper_coin")
        - source: "room", "inventory", or "npc_inventory"
        - container: optional container ID (None for now)
    """
    loc_id = game.get("location", "town_square")
    
    # Check current room items
    room_state = ROOM_STATE.get(loc_id, {"items": []})
    room_items = room_state.get("items", [])
    matched_item = match_item_name_in_collection(target_text, room_items)
    if matched_item:
        return matched_item, "room", None
    
    # Check player inventory
    inventory = game.get("inventory", [])
    matched_item = match_item_name_in_collection(target_text, inventory)
    if matched_item:
        return matched_item, "inventory", None
    
    return None, None, None


def resolve_npc_target(game, target_text):
    """
    Resolve an NPC target from user input.
    
    Args:
        game: Game state dict
        target_text: User input (e.g., "mara", "innkeeper", "guard")
    
    Returns:
        tuple: (npc_id, npc) or (None, None) if not found
    """
    loc_id = game.get("location", "town_square")
    npc_ids = get_npcs_in_room(loc_id)
    
    # Use existing match_npc_in_room helper
    npc_id, npc = match_npc_in_room(npc_ids, target_text)
    if npc_id and npc:
        return npc_id, npc
    
    # Fallback: try global NPC lookup (for admin stat command)
    # This allows looking up NPCs not in current room
    target_lower = target_text.lower().strip()
    for candidate_id, candidate_npc in NPCS.items():
        if (target_lower == candidate_id.lower() or
            target_lower == candidate_npc.name.lower() or
            (hasattr(candidate_npc, 'shortname') and target_lower == candidate_npc.shortname.lower())):
            return candidate_id, candidate_npc
    
    return None, None


def _format_item_look(item_id, source):
    """
    Format a player-facing description of an item.
    
    Args:
        item_id: Item identifier
        source: "room", "inventory", etc.
    
    Returns:
        str: Player-facing description
    """
    item_def = get_item_def(item_id)
    name = item_def.get("name", item_id.replace("_", " "))
    description = item_def.get("description", "")
    item_type = item_def.get("type", "misc")
    flags = item_def.get("flags", [])
    
    lines = [f"You look at the {name}."]
    
    if description:
        lines.append(description)
    elif not description:
        lines.append(f"You see {name}.")
    
    # Add type/flag hints in a natural way
    if "container" in flags or item_type == "container":
        lines.append("It looks like it can hold other items.")
    elif item_type == "currency":
        lines.append("This looks like a form of currency.")
    elif item_type == "food":
        lines.append("It looks edible.")
    elif item_type == "tool":
        lines.append("It appears to be a useful tool.")
    elif item_type == "artifact":
        lines.append("You sense it might have special properties.")
    
    if source == "inventory":
        lines.append("(You are carrying this.)")
    elif source == "room":
        lines.append("(It's here in the room.)")
    
    return "\n".join(lines)


def _format_npc_look(npc_id, npc, game):
    """
    Format a player-facing description of an NPC.
    
    Args:
        npc_id: NPC identifier
        npc: NPC object
        game: Game state dict
    
    Returns:
        str: Player-facing description
    """
    lines = []
    
    # Base description
    if hasattr(npc, 'description') and npc.description:
        lines.append(npc.description)
    else:
        lines.append(f"You look at {npc.name}.")
    
    # Personality/title
    personality_parts = []
    if hasattr(npc, 'title') and npc.title and npc.title != npc.name:
        personality_parts.append(npc.title)
    if hasattr(npc, 'personality') and npc.personality:
        personality_parts.append(npc.personality)
    
    if personality_parts:
        lines.append(f"{npc.name} is {', '.join(personality_parts)}.")
    
    # Status hints from NPC_STATE
    if npc_id in NPC_STATE:
        state = NPC_STATE[npc_id]
        hp = state.get("hp", 10)
        max_hp = 10
        if hasattr(npc, 'stats') and npc.stats:
            max_hp = npc.stats.get("max_hp", 10)
        
        # Natural status descriptions
        if hp < max_hp * 0.5:
            lines.append(f"{npc.name} looks injured or unwell.")
        elif hp < max_hp * 0.8:
            lines.append(f"{npc.name} looks a bit tired.")
        
        status = state.get("status", "idle")
        if status != "idle":
            lines.append(f"{npc.name} appears to be {status}.")
    
    # Traits hints (subtle, in-universe)
    if hasattr(npc, 'traits') and npc.traits:
        traits = npc.traits
        if traits.get("kindness", 0) >= 0.7:
            lines.append(f"{npc.name} has a warm, kind demeanor.")
        elif traits.get("kindness", 0) <= 0.3:
            lines.append(f"{npc.name} seems somewhat distant.")
        
        if traits.get("authority", 0) >= 0.7:
            lines.append(f"{npc.name} carries an air of authority.")
    
    return "\n".join(lines)


def _format_player_look(game, username, db_conn=None):
    """
    Format a player-facing description of the player themselves (first person).
    
    Args:
        game: Game state dict
        username: Player username
        db_conn: Optional database connection for loading description
    
    Returns:
        str: Player-facing self-description
    """
    lines = ["You look at yourself."]
    
    # Character info (race, gender, stats, backstory)
    character = game.get("character", {})
    if character:
        race = character.get("race", "")
        gender = character.get("gender", "")
        stats = character.get("stats", {})
        backstory_text = character.get("backstory_text", "")
        
        if race:
            race_name = AVAILABLE_RACES.get(race, {}).get("name", race.capitalize())
            gender_name = AVAILABLE_GENDERS.get(gender, {}).get("name", gender.capitalize()) if gender else ""
            if gender_name:
                lines.append(f"You are a {gender_name.lower()} {race_name.lower()} adventurer in Hollowvale.")
            else:
                lines.append(f"You are a {race_name.lower()} adventurer in Hollowvale.")
        else:
            lines.append("You are an adventurer in Hollowvale.")
        
        # Stats
        if stats and any(v > 0 for v in stats.values()):
            stat_lines = []
            for stat_key, stat_value in stats.items():
                stat_name = STAT_NAMES.get(stat_key, stat_key.capitalize())
                stat_lines.append(f"{stat_name}: {stat_value}")
            lines.append("Stats: " + ", ".join(stat_lines))
        
        # Backstory
        if backstory_text:
            lines.append(f"Backstory: {backstory_text}")
    else:
        lines.append("You are an adventurer in Hollowvale.")
    
    # User description (first person)
    description = game.get("user_description")
    if not description and db_conn:
        # Try to load from database if not in game state
        try:
            if db_conn:
                user_row = db_conn.execute(
                    "SELECT description FROM users WHERE username = ?",
                    (username,)
                ).fetchone()
                if user_row and user_row["description"]:
                    description = user_row["description"]
                    game["user_description"] = description
        except Exception:
            pass
    
    if description:
        # First person: "You are..."
        lines.append(f"You are {description}.")
    
    # Status effects (if tracked)
    status_effects = game.get("status_effects", [])
    if status_effects:
        lines.append(f"Status: {', '.join(status_effects)}")
    
    # Inventory (grouped)
    inventory = game.get("inventory", [])
    if inventory:
        grouped_items = group_inventory_items(inventory)
        if len(grouped_items) == 1:
            lines.append(f"You are carrying {grouped_items[0]}.")
        elif len(grouped_items) == 2:
            lines.append(f"You are carrying {grouped_items[0]} and {grouped_items[1]}.")
        else:
            lines.append("You are carrying: " + ", ".join(grouped_items[:-1]) + f", and {grouped_items[-1]}.")
    else:
        lines.append("You are not carrying anything.")
    
    # Reputation summary (if any notable relationships)
    reputation = game.get("reputation", {})
    if reputation:
        notable = []
        for npc_id, rep_score in reputation.items():
            npc = NPCS.get(npc_id)
            if npc and rep_score >= 25:
                notable.append(f"{npc.name}")
        if notable:
            lines.append(f"You feel you are on good terms with {', '.join(notable)}.")
    
    return "\n".join(lines)


def _format_other_player_look(target_username, target_game, db_conn=None):
    """
    Format a player-facing description of another player (third person).
    
    Args:
        target_username: Username of the player being looked at
        target_game: Game state dict of the target player
        db_conn: Optional database connection for loading description
    
    Returns:
        str: Player-facing description of other player
    """
    lines = [f"You look at {target_username}."]
    
    # Character info (race, gender, stats, backstory)
    character = target_game.get("character", {})
    if character:
        race = character.get("race", "")
        gender = character.get("gender", "")
        
        # Get pronoun from gender
        gender_info = AVAILABLE_GENDERS.get(gender, {})
        pronoun = gender_info.get("pronoun", "they")
        pronoun_cap = gender_info.get("pronoun_cap", "They")
        
        if race:
            race_name = AVAILABLE_RACES.get(race, {}).get("name", race.capitalize())
            gender_name = gender_info.get("name", gender.capitalize()) if gender else ""
            if gender_name:
                lines.append(f"{target_username} is a {gender_name.lower()} {race_name.lower()} adventurer in Hollowvale.")
            else:
                lines.append(f"{target_username} is a {race_name.lower()} adventurer in Hollowvale.")
        else:
            lines.append(f"{target_username} is an adventurer in Hollowvale.")
    else:
        # Default pronoun if no character info
        pronoun_cap = "He"
        lines.append(f"{target_username} is an adventurer in Hollowvale.")
    
    # User description (third person)
    description = target_game.get("user_description")
    if not description and db_conn:
        # Try to load from database if not in game state
        try:
            user_row = db_conn.execute(
                "SELECT description FROM users WHERE username = ?",
                (target_username,)
            ).fetchone()
            if user_row and user_row["description"]:
                description = user_row["description"]
                target_game["user_description"] = description
        except Exception:
            pass
    
    if description:
        # Get pronoun from character if available
        if character:
            gender = character.get("gender", "")
            gender_info = AVAILABLE_GENDERS.get(gender, {})
            pronoun_cap = gender_info.get("pronoun_cap", "They")
        # Third person: "He/She/They is..."
        lines.append(f"{pronoun_cap} is {description}.")
    
    # Inventory (grouped, third person)
    inventory = target_game.get("inventory", [])
    if inventory:
        grouped_items = group_inventory_items(inventory)
        if len(grouped_items) == 1:
            lines.append(f"{pronoun_cap} is carrying {grouped_items[0]}.")
        elif len(grouped_items) == 2:
            lines.append(f"{pronoun_cap} is carrying {grouped_items[0]} and {grouped_items[1]}.")
        else:
            lines.append(f"{pronoun_cap} is carrying: " + ", ".join(grouped_items[:-1]) + f", and {grouped_items[-1]}.")
    else:
        lines.append(f"{pronoun_cap} is not carrying anything.")
    
    return "\n".join(lines)


def _format_item_stat(item_id, source):
    """
    Format an admin-facing detailed stat view of an item.
    
    Args:
        item_id: Item identifier
        source: "room", "inventory", etc.
    
    Returns:
        str: Admin stat view
    """
    item_def = get_item_def(item_id)
    
    lines = ["Item:"]
    lines.append(f"Name: {item_def.get('name', item_id.replace('_', ' '))}")
    lines.append(f"ID: {item_id}")
    lines.append(f"Type: {item_def.get('type', 'misc')}")
    
    description = item_def.get("description", "")
    if description:
        lines.append(f"Description: {description}")
    
    flags = item_def.get("flags", [])
    if flags:
        lines.append(f"Flags: {', '.join(flags)}")
    
    weight = item_def.get("weight")
    if weight is not None:
        lines.append(f"Weight: {weight}")
    
    # Container properties
    if item_def.get("is_container"):
        lines.append(f"Container: Yes")
        capacity = item_def.get("capacity")
        if capacity is not None:
            lines.append(f"Capacity: {capacity}")
        contents = item_def.get("contents", [])
        if contents:
            lines.append(f"Contents: {', '.join(contents)}")
        if item_def.get("locked"):
            lines.append(f"Locked: Yes")
        key_required = item_def.get("key_required")
        if key_required:
            lines.append(f"Key Required: {key_required}")
    
    # Location
    if source == "room":
        lines.append(f"Location: room (current room)")
    elif source == "inventory":
        lines.append(f"Location: player inventory")
    
    return "\n".join(lines)


def _format_npc_stat(npc_id, npc):
    """
    Format an admin-facing detailed stat view of an NPC.
    
    Args:
        npc_id: NPC identifier
        npc: NPC object
    
    Returns:
        str: Admin stat view
    """
    lines = ["NPC:"]
    lines.append(f"Name: {npc.name}")
    lines.append(f"ID: {npc_id}")
    
    if hasattr(npc, 'title') and npc.title:
        lines.append(f"Title: {npc.title}")
    
    # Location
    if npc_id in NPC_STATE:
        state = NPC_STATE[npc_id]
        room = state.get("room", "unknown")
        home_room = state.get("home_room", "unknown")
        lines.append(f"Location: {room}")
        lines.append(f"Home / Spawn: {home_room}")
    else:
        lines.append(f"Location: unknown")
    
    # Description and personality
    if hasattr(npc, 'description') and npc.description:
        lines.append(f"Description: {npc.description}")
    if hasattr(npc, 'personality') and npc.personality:
        lines.append(f"Personality: {npc.personality}")
    
    # Stats
    if hasattr(npc, 'stats') and npc.stats:
        lines.append("Stats:")
        for key, value in npc.stats.items():
            lines.append(f"  {key}: {value}")
    
    # Traits
    if hasattr(npc, 'traits') and npc.traits:
        lines.append("Traits:")
        for key, value in npc.traits.items():
            lines.append(f"  {key}: {value}")
    
    # NPC_STATE fields
    if npc_id in NPC_STATE:
        state = NPC_STATE[npc_id]
        hp = state.get("hp")
        if hp is not None:
            lines.append(f"HP: {hp}")
        alive = state.get("alive")
        if alive is not None:
            lines.append(f"Alive: {alive}")
        status = state.get("status")
        if status:
            lines.append(f"Status: {status}")
    
    return "\n".join(lines)


def _format_player_stat(game, username):
    """
    Format an admin-facing detailed stat view of a player.
    
    Args:
        game: Game state dict
        username: Player username
    
    Returns:
        str: Admin stat view
    """
    lines = ["Player:"]
    lines.append(f"Name: {username}")
    
    # Character object
    character = game.get("character", {})
    if character:
        lines.append("Character:")
        lines.append(f"  Race: {character.get('race', 'none')}")
        lines.append(f"  Gender: {character.get('gender', 'none')}")
        stats = character.get("stats", {})
        if stats:
            lines.append("  Stats:")
            for stat_key, stat_value in stats.items():
                stat_name = STAT_NAMES.get(stat_key, stat_key.capitalize())
                lines.append(f"    {stat_name}: {stat_value}")
        lines.append(f"  Backstory: {character.get('backstory', 'none')}")
        if character.get("backstory_text"):
            lines.append(f"  Backstory Text: {character.get('backstory_text')}")
        if character.get("description"):
            lines.append(f"  Description: {character.get('description')}")
    else:
        lines.append("Character: (not created)")
    
    # Location
    loc_id = game.get("location", "town_square")
    room_name = WORLD.get(loc_id, {}).get("name", loc_id)
    lines.append(f"Location: {loc_id} ({room_name})")
    
    # Inventory
    inventory = game.get("inventory", [])
    if inventory:
        lines.append("Inventory:")
        for item_id in inventory:
            item_name = render_item_name(item_id)
            lines.append(f"  {item_id} ({item_name})")
    else:
        lines.append("Inventory: (empty)")
    
    # Currency
    from economy.currency import get_currency, format_currency
    currency = get_currency(game)
    currency_str = format_currency(currency)
    lines.append(f"Currency: {currency_str}")
    
    # Reputation
    reputation = game.get("reputation", {})
    if reputation:
        lines.append("Reputation:")
        for npc_id, rep_score in reputation.items():
            npc = NPCS.get(npc_id)
            npc_name = npc.name if npc else npc_id
            lines.append(f"  {npc_id} ({npc_name}): {rep_score}")
    else:
        lines.append("Reputation: (none)")
    
    # Status effects
    status_effects = game.get("status_effects", [])
    if status_effects:
        lines.append(f"Status Effects: {', '.join(status_effects)}")
    
    # Flags and other properties
    is_admin = game.get("is_admin", False)
    if is_admin:
        lines.append("Flags: is_admin")
    
    # Other notable fields
    notify = game.get("notify", {})
    if notify:
        lines.append(f"Notify Settings: {notify}")
    
    npc_memory = game.get("npc_memory", {})
    if npc_memory:
        lines.append(f"NPC Memory: {len(npc_memory)} NPCs")
    
    return "\n".join(lines)


def move_npc(npc_id, new_room_id):
    """Move an NPC to a new room."""
    if npc_id in NPC_STATE:
        NPC_STATE[npc_id]["room"] = new_room_id


# Initialize NPC state on module import
init_npc_state()


def new_game_state(username="adventurer", character=None):
    """
    Create a fresh game state for one player.

    IMPORTANT:
    - Room items are now shared globally via ROOM_STATE.
    - WORLD stays read-only, which makes it safe for many users.

    Args:
        username: The username of the player (default: "adventurer")
        character: Optional character object from onboarding

    Returns:
        dict: A new game state dictionary
    """
    # Initialize economy (currency system)
    from economy.economy_manager import initialize_player_currency
    
    # Create character object if not provided (for backward compatibility)
    if character is None:
        character = {
            "race": "",
            "gender": "",
            "stats": {"str": 0, "agi": 0, "wis": 0, "wil": 0, "luck": 0},
            "backstory": "",
            "backstory_text": "",
            "description": "",
        }
    
    game_state = {
        "location": "town_square",
        "inventory": [],
        "max_carry_weight": 20.0,  # Default max carry weight in kg
        "character": character,  # Character object
        "log": [
            "Welcome to the Tiny MUD, " + username + "!",
            "Type 'look' to see where you are, 'go north/east/south/west' to move, "
            "'take <item>' to pick something up, 'talk <npc>' to talk, "
            "'say <message>' to speak to everyone in the room, "
            "'nod', 'smile', 'wave' and other emotes to express yourself, "
            "and 'inventory' to see what you're carrying.",
        ],
        "npc_memory": {},  # Track conversation history with NPCs: {npc_id: [list of interactions]}
        "reputation": {},  # Track reputation with NPCs: {npc_id: score}
        "notify": {
            "login": False,  # player can enable with 'notify login'
            "time": False,  # player can enable with 'notify time'
        },
    }
    initialize_player_currency(game_state)
    return game_state


# Reaction counter for deterministic NPC reactions
_reaction_counters = {}


# get_npc_reaction moved to npc.py

def add_session_welcome(game, username):
    """
    Add a session separator and welcome message to the game log.
    Called when a user logs in to mark the start of a new session.

    Args:
        game: The game state dictionary (will be mutated)
        username: The username of the player
    """
    game.setdefault("log", [])
    
    # Add two blank lines for spacing
    game["log"].append("")
    game["log"].append("")
    
    # Add separator line
    game["log"].append("-------------------------------------------")
    
    # Add one blank line
    game["log"].append("")
    
    # Get current in-game time - extract just the time string from format_time_message
    # format_time_message returns a full message, we need to extract the time
    current_hour = get_current_in_game_hour()
    in_game_hours_per_day = IN_GAME_DAY_DURATION / IN_GAME_HOUR_DURATION
    hour_in_day = current_hour % in_game_hours_per_day
    
    # Convert to 12-hour format with exact minutes
    if hour_in_day < 1.0:
        total_minutes_in_period = hour_in_day * 12 * 60
        total_minutes_from_6am = 6 * 60 + total_minutes_in_period
    else:
        total_minutes_in_period = (hour_in_day - 1.0) * 12 * 60
        total_minutes_from_6am = 18 * 60 + total_minutes_in_period
    
    if total_minutes_from_6am >= 24 * 60:
        total_minutes_from_6am -= 24 * 60
    
    real_hour = int(total_minutes_from_6am // 60)
    minutes = int(total_minutes_from_6am % 60)
    period = "AM" if real_hour < 12 else "PM"
    display_hour = real_hour if real_hour <= 12 else real_hour - 12
    if display_hour == 0:
        display_hour = 12
    time_str = f"{display_hour}:{minutes:02d}{period}"
    
    # Get location information
    loc_id = game.get("location", "town_square")
    room_def = WORLD.get(loc_id, {})
    room_name = room_def.get("name", loc_id.replace("_", " ").title())
    
    # Add welcome back message with time
    game["log"].append(f"You blink and wake up. Welcome back to Hollowvale, {username}! It's currently {time_str}.")
    
    # Add room name in dark green (using HTML like movement messages)
    game["log"].append(f'<span style="color: #006400;">You\'re standing in the {room_name}</span>')
    
    # Add room description
    room_description = describe_location(game)
    # Split description into lines if it's multi-line
    if isinstance(room_description, str):
        desc_lines = room_description.split("\n")
        for line in desc_lines:
            if line.strip():
                game["log"].append(line)


# generate_npc_line moved to npc.py

def handle_emote(verb, args, game, username=None):
    """
    Handle social/emote verbs like 'nod' or 'smile'.
    
    Args:
        verb: The command word, e.g. 'nod'
        args: List of remaining tokens, e.g. ['guard']
        game: The game state dictionary
        username: Optional username of the player
    
    Returns:
        tuple: (response_string, updated_game_state)
    """
    # Look up verb in EMOTES
    if verb not in EMOTES:
        return "You flail about uncertainly.", game
    
    # Determine actor name
    actor_name = username or "Someone"
    
    # No target (e.g. command is just "nod")
    if not args:
        response = EMOTES[verb]["self"]
        return response, game
    
    # With target (e.g. "nod guard" or "nod watch guard")
    target_text = " ".join(args).lower()
    loc_id = game.get("location", "town_square")
    
    if loc_id not in WORLD:
        return "You feel disoriented for a moment.", game
    
    room_def = WORLD[loc_id]
    npc_ids = get_npcs_in_room(loc_id)
    
    # Use centralized NPC matching
    matched_npc_id, matched_npc = match_npc_in_room(npc_ids, target_text)
    
    if not matched_npc:
        return "You do not see anyone like that here.", game
    
    # Get target name
    target_name = matched_npc.name or matched_npc.title or "someone"
    
    # Generate player view using self_target template
    player_view = EMOTES[verb]["self_target"].format(target=target_name)
    
    # Get NPC reaction if available
    reaction = get_npc_reaction(matched_npc_id, verb)
    
    if reaction:
        response = player_view + "\n" + reaction
    else:
        response = player_view
    
    return response, game


def get_movement_message(target_room_id, direction):
    """
    Get the movement message when entering a room.
    
    Args:
        target_room_id: The room ID being entered
        direction: The direction traveled (e.g., "north", "east")
    
    Returns:
        str: HTML-formatted movement message in dark green
    """
    if target_room_id not in WORLD:
        # Fallback if room doesn't exist
        location_name = "an unknown place"
    else:
        room_def = WORLD[target_room_id]
        location_name = room_def.get("name", target_room_id)
        
        # Check if room has custom movement message
        movement_message = room_def.get("movement_message")
        if movement_message:
            # Support both string templates and callable functions
            if callable(movement_message):
                return f'<span style="color: #006400;">{movement_message(direction, location_name)}</span>'
            else:
                # Format string template with {direction} and {location} placeholders
                formatted = movement_message.format(direction=direction, location=location_name)
                return f'<span style="color: #006400;">{formatted}</span>'
    
    # Default message
    default_message = f"You go {direction}, and find yourself in the {location_name}."
    return f'<span style="color: #006400;">{default_message}</span>'


def format_time_message(game):
    """
    Format a creative time message based on the player's location and current in-game time.
    
    Args:
        game: The game state dictionary
    
    Returns:
        str: A creative time announcement message
    """
    loc_id = game.get("location", "town_square")
    
    # Get location name
    if loc_id not in WORLD:
        location_name = "Hollowvale"
    else:
        room_def = WORLD[loc_id]
        room_name = room_def.get("name", "Hollowvale")
        
        # Extract township/location name creatively
        # Try to extract meaningful location names
        if "Hollowvale" in room_name:
            location_name = "Hollowvale"
        elif "Town Square" in room_name:
            location_name = "Hollowvale Town Square"
        elif "Tavern" in room_name:
            location_name = "The Rusty Tankard"
        elif "Smithy" in room_name:
            location_name = "Old Stoneforge"
        elif "Market" in room_name:
            location_name = "Market Lane"
        elif "Shrine" in room_name:
            location_name = "the Shrine of the Forgotten Path"
        elif "Watchtower" in room_name:
            location_name = "the Old Watchtower"
        elif "Forest" in room_name or "Wood" in room_name or "Trees" in room_name:
            location_name = "the Whispering Wood"
        elif "Road" in room_name:
            location_name = "the Old Eastward Road"
        else:
            location_name = room_name
    
    # Get current in-game time (returns fractional hours with full precision)
    current_hour = get_current_in_game_hour()
    in_game_hours_per_day = IN_GAME_DAY_DURATION / IN_GAME_HOUR_DURATION
    
    # Calculate hour within the day (0-2 hours per day, with full precision)
    hour_in_day = current_hour % in_game_hours_per_day
    
    # Convert to 12-hour format with exact minutes
    # Each in-game day = 2 in-game hours, mapped to 24 real-world hours
    # 0-1 in-game hours = day (6:00 AM - 6:00 PM), 1-2 = night (6:00 PM - 6:00 AM)
    if hour_in_day < 1.0:
        # Day period: map 0-1 in-game hours to 6:00 AM - 6:00 PM (12 hours)
        # hour_in_day ranges from 0.0 to 1.0, representing 0 to 12 hours
        total_minutes_in_period = hour_in_day * 12 * 60  # Total minutes elapsed in day period
        total_minutes_from_6am = 6 * 60 + total_minutes_in_period  # Minutes since midnight
    else:
        # Night period: map 1-2 in-game hours to 6:00 PM - 6:00 AM (12 hours)
        # hour_in_day ranges from 1.0 to 2.0, representing 12 to 24 hours
        total_minutes_in_period = (hour_in_day - 1.0) * 12 * 60  # Total minutes elapsed in night period
        total_minutes_from_6am = 18 * 60 + total_minutes_in_period  # Minutes since midnight
    
    # Handle wrap-around for night period (after midnight)
    if total_minutes_from_6am >= 24 * 60:
        total_minutes_from_6am -= 24 * 60
    
    # Convert to hours and minutes
    real_hour = int(total_minutes_from_6am // 60)
    minutes = int(total_minutes_from_6am % 60)
    
    # Determine AM/PM and format hour for 12-hour display
    period = "AM" if real_hour < 12 else "PM"
    display_hour = real_hour if real_hour <= 12 else real_hour - 12
    if display_hour == 0:
        display_hour = 12
    
    # Format time string with exact minutes (e.g., "6:05AM", "12:30PM")
    time_str = f"{display_hour}:{minutes:02d}{period}"
    
    # Get period description
    current_period = get_current_period()
    period_desc = "day" if current_period == "day" else "night"
    
    # Create creative messages with variations
    messages = [
        f"At the third stroke, the clock in {location_name} will strike {time_str}.",
        f"The bells of {location_name} chime, marking the hour of {time_str}.",
        f"You hear the distant tolling of a bell: it is {time_str} in {location_name}.",
        f"A voice calls out from somewhere nearby: 'The time in {location_name} is {time_str}.'",
        f"Glancing at the sky, you estimate it to be {time_str} in {location_name}.",
        f"The shadows and light tell you it is {time_str} in {location_name}.",
    ]
    
    # Add period-specific messages
    if current_period == "day":
        messages.extend([
            f"Under the bright {period_desc}light, the time in {location_name} is {time_str}.",
            f"The sun's position confirms it is {time_str} in {location_name}.",
        ])
    else:
        messages.extend([
            f"Beneath the {period_desc} sky, the time in {location_name} is {time_str}.",
            f"The moon and stars mark the hour as {time_str} in {location_name}.",
        ])
    
    # Use deterministic selection based on hour to avoid randomness
    message_index = int(current_hour) % len(messages)
    return messages[message_index]


def describe_location(game):
    """
    Generate a description of the player's current location.

    Args:
        game: The game state dictionary

    Returns:
        str: A formatted description of the current location with HTML markup
    """
    loc_id = game.get("location", "town_square")

    # Fallback if something weird happens
    if loc_id not in WORLD:
        loc_id = "town_square"
        game["location"] = loc_id

    room_def = WORLD[loc_id]
    room_state = ROOM_STATE.get(loc_id, {"items": []})

    desc = room_def["description"]
    exits = ", ".join(room_def["exits"].keys()) or "none"
    items = room_state.get("items", [])
    
    # Get NPCs from NPC_STATE and any player characters in this location
    npc_ids = get_npcs_in_room(loc_id)
    # TODO: Add player characters from other users in same location
    # For now, we'll get this from game state when multiplayer is implemented
    player_characters = game.get("other_players", {}).get(loc_id, [])

    # Build items text using ITEM_DEFS for human-friendly names
    if items:
        item_names = [render_item_name(item_id) for item_id in items]
        items_text = "You can see: " + ", ".join(item_names) + "."
    else:
        items_text = "You don't see anything notable lying around."

    # Build NPCs and player characters text
    present_entities = []
    
    # Add NPCs
    for npc_id in npc_ids:
        if npc_id in NPCS:
            present_entities.append(NPCS[npc_id].name)
    
    # Add player characters (when implemented)
    for pc_name in player_characters:
        present_entities.append(pc_name)
    
    npcs_text = ""
    if present_entities:
        notice_prefix = "<span style='color: #00ffff; font-weight: bold;'>You notice:</span>"
        if len(present_entities) == 1:
            npcs_text = f"{notice_prefix} {present_entities[0]} is here."
        elif len(present_entities) == 2:
            npcs_text = f"{notice_prefix} {present_entities[0]} and {present_entities[1]} are here."
        else:
            # Format: "name1, name2 and name3 are here"
            all_but_last = ", ".join(present_entities[:-1])
            npcs_text = f"{notice_prefix} {all_but_last} and {present_entities[-1]} are here."

    # Combine all parts
    parts = [
        room_def['name'],
        desc,
        f"<span style='color: #ffff00; font-weight: bold;'>Exits:</span> {exits}.",
        items_text,
    ]
    
    if npcs_text:
        parts.append(npcs_text)
    
    return "\n".join(parts)


def adjust_reputation(game, npc_id, amount, reason=""):
    """
    Adjust reputation with an NPC. Can be positive or negative.
    
    This is the main function for reputation changes from:
    - Quests (positive for completion, negative for failure)
    - Actions (positive for helping, negative for harming)
    - Politeness (small positive, capped)
    - Other game events
    
    Args:
        game: The game state dictionary
        npc_id: The NPC ID to adjust reputation with
        amount: The amount to adjust (positive or negative integer)
        reason: Optional reason for the adjustment (for logging/debugging)
    
    Returns:
        tuple: (new_reputation, message) where message describes the change
    """
    if not npc_id:
        return 0, None
    
    # Initialize reputation if needed
    if "reputation" not in game:
        game["reputation"] = {}
    
    current_reputation = game["reputation"].get(npc_id, 0)
    new_reputation = current_reputation + amount
    
    # Cap reputation at reasonable bounds (can be adjusted)
    # Very high positive (exceptional friends/allies)
    max_reputation = 200
    # Very low negative (enemies)
    min_reputation = -100
    
    new_reputation = max(min_reputation, min(max_reputation, new_reputation))
    game["reputation"][npc_id] = new_reputation
    
    # Generate descriptive message
    message = None
    if amount > 0:
        if amount >= 20:
            message = f"Your reputation with {NPCS.get(npc_id, {}).get('name', 'them')} has greatly improved!"
        elif amount >= 10:
            message = f"Your reputation with {NPCS.get(npc_id, {}).get('name', 'them')} has significantly improved."
        elif amount >= 5:
            message = f"Your reputation with {NPCS.get(npc_id, {}).get('name', 'them')} has improved."
        else:
            message = None  # Small changes don't need messages to avoid spam
    elif amount < 0:
        if amount <= -20:
            message = f"Your reputation with {NPCS.get(npc_id, {}).get('name', 'them')} has greatly deteriorated!"
        elif amount <= -10:
            message = f"Your reputation with {NPCS.get(npc_id, {}).get('name', 'them')} has significantly worsened."
        elif amount <= -5:
            message = f"Your reputation with {NPCS.get(npc_id, {}).get('name', 'them')} has worsened."
        else:
            message = None  # Small changes don't need messages
    
    return new_reputation, message


def _update_reputation_for_politeness(game, npc_id, text):
    """
    Update reputation with an NPC for using polite language.
    Includes limits to prevent exploitation.
    
    Returns: (reputation_gained, message) where message is None if no gain
    """
    if not npc_id:
        return 0, None
    
    # Initialize reputation tracking if needed
    if "reputation" not in game:
        game["reputation"] = {}
    if "politeness_tracking" not in game:
        game["politeness_tracking"] = {}
    
    # Get current reputation
    current_reputation = game["reputation"].get(npc_id, 0)
    
    # Initialize politeness tracking for this NPC
    if npc_id not in game["politeness_tracking"]:
        game["politeness_tracking"][npc_id] = {
            "last_polite_interaction": 0,
            "polite_interaction_count": 0,
            "total_politeness_reputation": 0,
        }
    
    tracking = game["politeness_tracking"][npc_id]
    
    # Check for polite words
    text_lower = text.lower()
    polite_words = ["please", "thanks", "thank you", "thank", "appreciate", "grateful"]
    has_polite = any(word in text_lower for word in polite_words)
    
    if not has_polite:
        return 0, None
    
    # Anti-exploitation limits:
    # 1. Max reputation from politeness alone: 5 points
    max_politeness_reputation = 5
    if tracking["total_politeness_reputation"] >= max_politeness_reputation:
        return 0, None  # Already maxed out politeness reputation
    
    # 2. Cooldown: Can only gain reputation from politeness once per 3 interactions
    interaction_count = tracking.get("polite_interaction_count", 0)
    if interaction_count > 0 and interaction_count % 3 != 0:
        tracking["polite_interaction_count"] += 1
        return 0, None  # Still in cooldown
    
    # 3. Diminishing returns: Smaller gains as reputation increases
    # Note: With new thresholds, politeness can still contribute at higher levels
    # but the cap ensures it's not the primary way to build reputation
    if current_reputation >= 20:
        reputation_gain = 0  # High reputation - no more gains from just politeness
    elif current_reputation >= 10:
        reputation_gain = 0.5  # Moderate reputation - very small gains
    elif current_reputation >= 5:
        reputation_gain = 0.5  # Low-moderate reputation - small gains
    else:
        reputation_gain = 1  # Low reputation - normal gains
    
    # Round down to prevent fractional reputation (we'll use integer tracking)
    if reputation_gain < 1:
        # For fractional gains, use a probability system
        import random
        if random.random() < reputation_gain:
            reputation_gain = 1
        else:
            reputation_gain = 0
    
    if reputation_gain == 0:
        tracking["polite_interaction_count"] += 1
        return 0, None
    
    # Apply the gain using the main reputation adjustment function
    new_reputation, _ = adjust_reputation(game, npc_id, reputation_gain, reason="politeness")
    tracking["total_politeness_reputation"] += reputation_gain
    tracking["polite_interaction_count"] += 1
    
    return reputation_gain, None  # Return gain but no message (to avoid spam)


from utils.prompt_loader import load_prompt


def _get_purchase_intent_system_prompt(items_text):
    """Load and format the purchase intent system prompt."""
    fallback = f"""You are analyzing a player's message to determine if they want to purchase something from a merchant.

Available items for sale:
{items_text}

Your task:
1. Determine if the player wants to BUY something (purchase intent)
2. If yes, identify which item (use the exact 'key' from the list above)
3. Determine the quantity (default is 1 if not specified)

IMPORTANT:
- Only return purchase intent if the player is clearly trying to BUY something
- Do NOT treat complaints, questions, or conversational statements as purchase intent
- Examples of purchase intent: "I'll take a stew", "Can I get some bread?", "A tankard of ale please"
- Examples of NOT purchase intent: "Why did you give me a whole loaf?", "I only wanted a piece", "That costs too much"

Return your response as JSON only, in this exact format:
{{"has_intent": true/false, "item_key": "item_key_or_null", "quantity": number}}

If has_intent is false, set item_key to null and quantity to 0."""
    
    return load_prompt("purchase_intent_system.txt", fallback_text=fallback, items_text=items_text)


def _get_purchase_intent_user_message(text):
    """Load and format the purchase intent user message."""
    fallback = f"Player message: \"{text}\"\n\nAnalyze this message and return JSON with purchase intent."
    return load_prompt("purchase_intent_user.txt", fallback_text=fallback, text=text)


def _parse_purchase_intent_ai(text, merchant_items, npc, room_def, game, username, user_id=None, db_conn=None, npc_id=None):
    """
    Use AI to parse purchase intent from natural language.
    Much more robust than pattern matching - understands context.
    
    Returns: (item_key, quantity) or (None, 0) if no purchase detected.
    """
    if not generate_npc_reply:
        return None, 0  # AI not available, fall back to pattern matching
    
    # Build list of available items for the AI
    # Prices are calculated dynamically using the economy system
    from economy.economy_manager import get_item_price
    from economy.currency import format_currency, copper_to_currency
    
    # Get npc_id - prefer passed parameter, then try to extract from npc object
    npc_id_for_pricing = npc_id
    if not npc_id_for_pricing:
        if npc and hasattr(npc, 'id'):
            npc_id_for_pricing = npc.id
        elif npc and isinstance(npc, dict):
            # Try to find npc_id by matching npc name
            from npc import NPCS
            for nid, n in NPCS.items():
                if hasattr(n, 'name') and n.name == npc.get('name'):
                    npc_id_for_pricing = nid
                    break
    
    items_list = []
    for item_key, item_info in merchant_items.items():
        display_name = item_info.get("display_name", item_key.replace("_", " "))
        # Get price dynamically from economy system (returns copper coins)
        try:
            if npc_id_for_pricing:
                price_copper = get_item_price(item_key, npc_id_for_pricing, game)
                price_currency = copper_to_currency(price_copper)
                price_str = format_currency(price_currency)
            else:
                # Fallback: use a generic price estimate
                price_str = "varies"
        except Exception:
            # Fallback if price calculation fails
            price_str = "varies"
        items_list.append(f"- {display_name} (key: {item_key}, price: {price_str})")
    
    items_text = "\n".join(items_list)
    
    # Create a special AI prompt to determine purchase intent
    try:
        from ai_client import OpenAI, OPENAI_AVAILABLE
        if not OPENAI_AVAILABLE:
            return None, 0
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Load prompts from files
        system_prompt = _get_purchase_intent_system_prompt(items_text)
        user_message = _get_purchase_intent_user_message(text)

        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=100,
            temperature=0.3,  # Lower temperature for more deterministic parsing
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response (in case AI adds extra text)
        json_match = re.search(r'\{[^}]+\}', ai_response)
        if json_match:
            result = json.loads(json_match.group(0))
            
            if result.get("has_intent") and result.get("item_key"):
                item_key = result["item_key"]
                quantity = result.get("quantity", 1)
                
                # Validate item_key exists in merchant_items
                if item_key in merchant_items:
                    return item_key, max(1, int(quantity))  # Ensure quantity is at least 1
        
        return None, 0
        
    except Exception as e:
        # If AI parsing fails, fall back to pattern matching
        print(f"AI purchase intent parsing failed: {e}")
        return None, 0


def _parse_purchase_intent(text, merchant_items, npc=None, room_def=None, game=None, username=None, user_id=None, db_conn=None, npc_id=None):
    """
    Parse natural language to detect purchase intent.
    Uses AI if available, falls back to pattern matching.
    
    Returns: (item_key, quantity) or (None, 0) if no purchase detected.
    """
    # Try AI first if available and we have the necessary context
    if npc and room_def and game and generate_npc_reply:
        ai_result = _parse_purchase_intent_ai(text, merchant_items, npc, room_def, game, username or "adventurer", user_id, db_conn, npc_id)
        if ai_result[0] is not None:
            return ai_result
    
    # Fallback to pattern matching (simpler, less robust)
    text_lower = text.lower()
    
    # Common purchase phrases
    purchase_phrases = [
        "i'll take", "i'll have", "i want", "i need", "give me", "get me",
        "can i get", "can i have", "i'd like", "i would like",
        "sure, i'll take", "yes, i'll take", "ok, i'll take",
        "please", "i'll buy", "buy me", "i'll purchase"
    ]
    
    # Quick check for obvious non-purchase patterns
    conversational_patterns = [
        "why did", "why does", "why would", "why should",
        "i only wanted", "i wanted", "i thought",
        "you gave me", "you gave", "you sold me",
        "i don't want", "i didn't want", "i don't need",
        "that cost", "that costs", "costs the same",
    ]
    
    if any(pattern in text_lower for pattern in conversational_patterns):
        return None, 0
    
    # Check for explicit purchase phrases
    has_intent = any(phrase in text_lower for phrase in purchase_phrases)
    
    if not has_intent:
        return None, 0
    
    # Try to extract quantity
    import re
    quantity = 1
    quantity_match = re.search(r'\b(\d+)\b', text_lower)
    if quantity_match:
        try:
            quantity = int(quantity_match.group(1))
        except ValueError:
            quantity = 1
    
    # Try to match items (simple word matching)
    for item_key, item_info in merchant_items.items():
        display_name = item_info.get("display_name", item_key.replace("_", " "))
        item_words = set(display_name.lower().split())
        key_words = set(item_key.replace("_", " ").split())
        text_words = set(text_lower.split())
        
        if item_words.intersection(text_words) or key_words.intersection(text_words):
            return item_key, quantity
    
    return None, 0


def _restock_merchant_if_needed(npc_id):
    """
    Restock a merchant's inventory if 24 in-game hours have passed.
    
    Args:
        npc_id: Merchant NPC ID
    """
    if npc_id not in MERCHANT_ITEMS or npc_id not in NPC_STATE:
        return
    
    if should_restock_merchant(npc_id):
        # Restock all items to initial stock levels
        merchant_state = NPC_STATE[npc_id]
        if "merchant_inventory" not in merchant_state:
            merchant_state["merchant_inventory"] = {}
        
        for item_key, item_info in MERCHANT_ITEMS[npc_id].items():
            item_given = item_info.get("item_given")
            if item_given:
                initial_stock = item_info.get("initial_stock", 10)
                merchant_state["merchant_inventory"][item_given] = initial_stock
        
        mark_merchant_restocked(npc_id)


def _get_merchant_stock(npc_id, item_given):
    """
    Get current stock level for a merchant item.
    
    Args:
        npc_id: Merchant NPC ID
        item_given: The item_given identifier
    
    Returns:
        int: Current stock (0 if out of stock or not found)
    """
    if npc_id not in NPC_STATE:
        return 0
    
    merchant_state = NPC_STATE[npc_id]
    inventory = merchant_state.get("merchant_inventory", {})
    return inventory.get(item_given, 0)


def _decrement_merchant_stock(npc_id, item_given, quantity):
    """
    Decrement merchant stock after a purchase.
    
    Args:
        npc_id: Merchant NPC ID
        item_given: The item_given identifier
        quantity: Amount to decrement
    """
    if npc_id not in NPC_STATE:
        return
    
    merchant_state = NPC_STATE[npc_id]
    if "merchant_inventory" not in merchant_state:
        merchant_state["merchant_inventory"] = {}
    
    current_stock = merchant_state["merchant_inventory"].get(item_given, 0)
    new_stock = max(0, current_stock - quantity)
    merchant_state["merchant_inventory"][item_given] = new_stock


def _process_purchase(game, matched_npc, matched_npc_id, item_key, quantity, username, user_id, db_conn):
    """
    Process a purchase transaction using the economy system.
    Returns (success, response_message, actual_price_per_item).
    """
    if matched_npc_id not in MERCHANT_ITEMS:
        return False, "There's nobody here to serve you!", 0
    
    npc_items = MERCHANT_ITEMS[matched_npc_id]
    if item_key not in npc_items:
        return False, None, 0  # Let caller handle unknown items
    
    item_info = npc_items[item_key]
    item_given = item_info["item_given"]
    
    # Use economy system for pricing and payment
    from economy import process_purchase_with_gold, get_item_price
    from npc import NPCS
    
    npc = NPCS.get(matched_npc_id)
    npc_name = npc.name if npc else "merchant"
    
    # Process purchase with gold
    success, message, price_per_item = process_purchase_with_gold(
        game, item_key, quantity, matched_npc_id, npc_name
    )
    
    if not success:
        return False, message, 0
    
    # Add items to inventory
    inventory = game.get("inventory", [])
    for _ in range(quantity):
        inventory.append(item_given)
    game["inventory"] = inventory
    
    return True, message, price_per_item


def handle_command(
    command,
    game,
    username=None,
    user_id=None,
    db_conn=None,
    broadcast_fn=None,
    who_fn=None,
):
    """
    Process a game command and update the game state.

    Args:
        command: The command string from the player
        game: The current game state dictionary (will be mutated)
        username: Optional username for restart command (default: "adventurer")
        user_id: Optional user ID for AI token budget tracking
        db_conn: Optional database connection for AI token budget tracking
        broadcast_fn: Optional callback(room_id: str, text: str) for broadcasting to room
        who_fn: Optional callback() -> list[dict] for getting active players

    Returns:
        tuple: (response_string, updated_game_state)
    """
    text = command.strip()
    if not text:
        return "You say nothing.", game

    tokens = text.lower().split()
    verb = tokens[0]
    args = tokens[1:]

    # Emote / social commands (check before other commands)
    if verb in EMOTES:
        response, game = handle_emote(verb, args, game, username=username or "adventurer")

    # Core commands
    elif verb in ["look", "l", "examine"]:
        if len(tokens) == 1 or (len(tokens) == 2 and tokens[1] in ["here", "room", "around"]):
            # No target or "here" - show room description
            response = describe_location(game)
        elif len(tokens) >= 2:
            target_text = " ".join(tokens[1:]).lower()
            original_target = " ".join(tokens[1:])  # Preserve original case for username matching
            
            # Handle "me" or username
            if target_text in ["me", "self"] or target_text == (username or "").lower():
                # Look at self
                response = _format_player_look(game, username or "adventurer", db_conn)
            else:
                # Check if target is another player in the same room
                other_player_found = False
                if who_fn:
                    try:
                        active_players = who_fn()
                        loc_id = game.get("location", "town_square")
                        
                        for player_info in active_players:
                            player_username = player_info.get("username", "")
                            # Match by username (case-insensitive)
                            if player_username.lower() == target_text and player_info.get("location") == loc_id:
                                # Found another player in the same room
                                from app import ACTIVE_GAMES
                                if player_username in ACTIVE_GAMES:
                                    target_game = ACTIVE_GAMES[player_username]
                                    response = _format_other_player_look(player_username, target_game, db_conn)
                                    other_player_found = True
                                    break
                    except Exception:
                        pass  # If who_fn fails, continue to item/NPC resolution
                
                if not other_player_found:
                    # Try to resolve as item or NPC
                    item_id, source, container = resolve_item_target(game, target_text)
                    if item_id:
                        response = _format_item_look(item_id, source)
                    else:
                        npc_id, npc = resolve_npc_target(game, target_text)
                        if npc_id and npc:
                            response = _format_npc_look(npc_id, npc, game)
                        else:
                            response = f"You don't see anything like '{original_target}' here."
        else:
            response = describe_location(game)

    elif tokens[0] in ["go", "move", "walk"] and len(tokens) >= 2:
        direction = tokens[-1]
        loc_id = game.get("location", "town_square")

        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
            game["location"] = "town_square"
            response += "\n" + describe_location(game)
        else:
            room_def = WORLD[loc_id]
            # Convert abbreviation to full direction if needed
            full_direction = DIRECTION_MAP.get(direction.lower(), direction.lower())
            exits = room_def.get("exits", {})
            exit_def = exits.get(full_direction)
            
            # Support both string (backward compatible) and dict exits
            if exit_def is None:
                target = None
            elif isinstance(exit_def, str):
                target = exit_def
            elif isinstance(exit_def, dict):
                target = exit_def.get("target")
                # For now, ignore locked/key_required flags (will be implemented later)
            else:
                target = None
            
            if target:
                old_loc = loc_id
                game["location"] = target
                
                # Broadcast leave message to old room
                if broadcast_fn is not None:
                    actor_name = username or "Someone"
                    leave_msg = f"{actor_name} leaves {full_direction}."
                    broadcast_fn(old_loc, leave_msg)
                
                # Broadcast arrive message to new room
                if broadcast_fn is not None:
                    actor_name = username or "Someone"
                    opposite = OPPOSITE_DIRECTION.get(full_direction, "somewhere")
                    arrive_msg = f"{actor_name} arrives from the {opposite}."
                    broadcast_fn(target, arrive_msg)
                
                # Get movement message and room description
                movement_msg = get_movement_message(target, full_direction)
                location_desc = describe_location(game)
                response = f"{movement_msg}\n{location_desc}"
            else:
                response = "You can't go that way."
    
    elif tokens[0] in ["n", "north", "s", "south", "e", "east", "w", "west"]:
        # Allow direct direction commands (e.g., "n" or "north")
        direction = tokens[0]
        loc_id = game.get("location", "town_square")

        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
            game["location"] = "town_square"
            response += "\n" + describe_location(game)
        else:
            room_def = WORLD[loc_id]
            # Convert abbreviation to full direction if needed
            full_direction = DIRECTION_MAP.get(direction.lower(), direction.lower())
            exits = room_def.get("exits", {})
            exit_def = exits.get(full_direction)
            
            # Support both string (backward compatible) and dict exits
            if exit_def is None:
                target = None
            elif isinstance(exit_def, str):
                target = exit_def
            elif isinstance(exit_def, dict):
                target = exit_def.get("target")
                # For now, ignore locked/key_required flags (will be implemented later)
            else:
                target = None
            
            if target:
                old_loc = loc_id
                game["location"] = target
                
                # Broadcast leave message to old room
                if broadcast_fn is not None:
                    actor_name = username or "Someone"
                    leave_msg = f"{actor_name} leaves {full_direction}."
                    broadcast_fn(old_loc, leave_msg)
                
                # Broadcast arrive message to new room
                if broadcast_fn is not None:
                    actor_name = username or "Someone"
                    opposite = OPPOSITE_DIRECTION.get(full_direction, "somewhere")
                    arrive_msg = f"{actor_name} arrives from the {opposite}."
                    broadcast_fn(target, arrive_msg)
                
                # Get movement message and room description
                movement_msg = get_movement_message(target, full_direction)
                location_desc = describe_location(game)
                response = f"{movement_msg}\n{location_desc}"
            else:
                response = "You can't go that way."

    elif tokens[0] in ["inventory", "inv", "i"]:
        inventory = game.get("inventory", [])
        response_parts = []
        
        # Show items
        if inventory:
            grouped_items = group_inventory_items(inventory)
            if len(grouped_items) == 1:
                response_parts.append(f"You are carrying {grouped_items[0]}.")
            elif len(grouped_items) == 2:
                response_parts.append(f"You are carrying {grouped_items[0]} and {grouped_items[1]}.")
            else:
                response_parts.append("You are carrying: " + ", ".join(grouped_items[:-1]) + f", and {grouped_items[-1]}.")
        else:
            response_parts.append("You are not carrying anything.")
        
        # Show currency in wallet
        from economy.currency import get_currency, format_currency
        currency = get_currency(game)
        currency_str = format_currency(currency)
        
        # Only show wallet if player has currency
        if currency_str != "no currency":
            response_parts.append(f"Wallet: You have {currency_str}.")
        
        response = "\n".join(response_parts)
    
    elif tokens[0] in ["gold", "money", "currency"]:
        # Show player's currency amount
        from economy.currency import get_currency, format_currency
        currency = get_currency(game)
        currency_str = format_currency(currency)
        response = f"You have {currency_str}."
    
    elif tokens[0] == "earn" and len(tokens) >= 2:
        # Debug/admin command to add currency (legacy: accepts gold amount, converts to new system)
        # TODO: Add admin check in production
        try:
            amount = int(tokens[1])
            if amount <= 0:
                response = "Amount must be positive."
            else:
                from economy.currency import add_gold, format_gold
                new_total = add_gold(game, amount)
                response = f"You earn {format_gold(amount)}. You now have {format_gold(new_total)}."
        except ValueError:
            response = "Usage: earn <amount>"
    
    elif tokens[0] == "pay" and len(tokens) >= 3:
        # Future-proofing: pay command (not fully implemented yet)
        try:
            amount = int(tokens[1])
            npc_target = " ".join(tokens[2:]).lower()
            
            loc_id = game.get("location", "town_square")
            if loc_id not in WORLD:
                response = "You feel disoriented for a moment."
            else:
                room_def = WORLD[loc_id]
                npc_ids = room_def.get("npcs", [])
                
                # Find matching NPC
                matched_npc_id, matched_npc = match_npc_in_room(npc_ids, npc_target)
                
                if not matched_npc:
                    response = "There's no one like that here to pay."
                else:
                    # For now, just acknowledge the command
                    response = f"You attempt to pay {matched_npc.name} {amount} gold, but they don't accept payments yet."
        except ValueError:
            response = "Usage: pay <amount> <npc>"
    
    elif tokens[0] in ["search", "scavenge", "loot"]:
        # Search current room for loot
        loc_id = game.get("location", "town_square")
        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
        else:
            from economy import handle_search_command
            response = handle_search_command(game, loc_id)

    elif tokens[0] == "take" and len(tokens) >= 2:
        item_input = " ".join(tokens[1:]).lower()
        loc_id = game.get("location", "town_square")
        inventory = game.get("inventory", [])
        max_weight = game.get("max_carry_weight", 20.0)
        current_weight = calculate_inventory_weight(inventory)

        if loc_id not in WORLD:
            response = "You reach for something that isn't really there."
        elif item_input in ["all", "everything"]:
            # Take all items from room (respecting weight limits)
            room_state = ROOM_STATE.setdefault(loc_id, {"items": []})
            room_items = room_state["items"]
            
            if not room_items:
                response = "There's nothing here to pick up."
            else:
                taken_items = []
                skipped_items = []
                
                for item_id in list(room_items):  # Copy list to avoid modification during iteration
                    item_def = get_item_def(item_id)
                    item_weight = item_def.get("weight", 0.1)
                    
                    if current_weight + item_weight > max_weight:
                        skipped_items.append(item_id)
                    else:
                        room_items.remove(item_id)
                        inventory.append(item_id)
                        current_weight += item_weight
                        taken_items.append(item_id)
                
                game["inventory"] = inventory
                
                if taken_items:
                    if len(taken_items) == 1:
                        display_name = render_item_name(taken_items[0])
                        response = f"You pick up the {display_name}."
                    else:
                        item_names = [render_item_name(item) for item in taken_items]
                        response = f"You pick up: {', '.join(item_names)}."
                    
                    if skipped_items:
                        response += f"\nYou can't carry any more - you'll fall over!"
                else:
                    response = "You can't pick up much more, you'll fall over!"
        else:
            # Take a specific item
            room_state = ROOM_STATE.setdefault(loc_id, {"items": []})
            room_items = room_state["items"]

            # Use match_item_name_in_collection for intelligent matching
            matched_item = match_item_name_in_collection(item_input, room_items)
            
            if matched_item:
                item_def = get_item_def(matched_item)
                item_weight = item_def.get("weight", 0.1)
                
                if current_weight + item_weight > max_weight:
                    response = "You can't pick up much more, you'll fall over!"
                else:
                    room_items.remove(matched_item)
                    inventory.append(matched_item)
                    game["inventory"] = inventory
                    display_name = render_item_name(matched_item)
                    response = f"You pick up the {display_name}."
            else:
                response = f"You don't see a '{item_input}' here."

    elif tokens[0] == "drop" and len(tokens) >= 2:
        item_input = " ".join(tokens[1:]).lower()
        loc_id = game.get("location", "town_square")
        inventory = game.get("inventory", [])

        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
        elif not inventory:
            response = "You're not carrying anything."
        else:
            room_state = ROOM_STATE.setdefault(loc_id, {"items": []})
            room_items = room_state["items"]
            
            # Check room capacity
            if len(room_items) >= MAX_ROOM_ITEMS:
                response = "There just isn't enough space to make such a mess here!"
            else:
                room_weight = calculate_room_items_weight(room_items)
                
                if item_input in ["all", "everything"]:
                    # Drop all droppable items (checking room capacity)
                    dropped_items = []
                    non_droppable_items = []
                    
                    # Work backwards through inventory to avoid index issues when removing
                    items_to_drop = []
                    for item_id in inventory:
                        item_def = get_item_def(item_id)
                        if item_def.get("droppable", True):
                            items_to_drop.append(item_id)
                        else:
                            non_droppable_items.append(item_id)
                    
                    # Check if dropping all items would exceed room capacity
                    total_items_after = len(room_items) + len(items_to_drop)
                    if total_items_after > MAX_ROOM_ITEMS:
                        response = "There just isn't enough space to make such a mess here!"
                    else:
                        # Check weight capacity (though weight is less restrictive than item count)
                        for item_id in items_to_drop:
                            item_def = get_item_def(item_id)
                            item_weight = item_def.get("weight", 0.1)
                            if room_weight + item_weight > MAX_ROOM_WEIGHT:
                                response = "There just isn't enough space to make such a mess here!"
                                break
                        else:
                            # All items can fit, drop them
                            for item_id in items_to_drop:
                                if item_id in inventory:
                                    inventory.remove(item_id)
                                    room_items.append(item_id)
                                    dropped_items.append(item_id)
                            
                            game["inventory"] = inventory
                            
                            # Build response
                            if dropped_items:
                                item_names = [render_item_name(item_id) for item_id in dropped_items]
                                if len(dropped_items) == 1:
                                    response = f"You drop the {item_names[0]}."
                                else:
                                    response = f"You drop: {', '.join(item_names)}."
                                
                                if non_droppable_items:
                                    non_droppable_names = [render_item_name(item_id) for item_id in non_droppable_items]
                                    response += f"\n(You cannot drop: {', '.join(non_droppable_names)}.)"
                            else:
                                if non_droppable_items:
                                    non_droppable_names = [render_item_name(item_id) for item_id in non_droppable_items]
                                    response = f"You cannot drop any of your items. ({', '.join(non_droppable_names)} cannot be dropped.)"
                                else:
                                    response = "You have nothing to drop."
                else:
                    # Drop a specific item
                    matched_item = match_item_name_in_collection(item_input, inventory)
                    
                    if not matched_item:
                        response = f"You're not carrying a '{item_input}'."
                    else:
                        item_def = get_item_def(matched_item)
                        
                        if not item_def.get("droppable", True):
                            response = "You cannot drop that item."
                        elif len(room_items) >= MAX_ROOM_ITEMS:
                            response = "There just isn't enough space to make such a mess here!"
                        else:
                            item_weight = item_def.get("weight", 0.1)
                            if room_weight + item_weight > MAX_ROOM_WEIGHT:
                                response = "There just isn't enough space to make such a mess here!"
                            else:
                                inventory.remove(matched_item)
                                game["inventory"] = inventory
                                room_items.append(matched_item)
                                display_name = render_item_name(matched_item)
                                response = f"You drop the {display_name}."

    elif tokens[0] == "give" and len(tokens) >= 2:
        # Give command: "give <item> to <npc>" or "give <npc> <item>"
        loc_id = game.get("location", "town_square")
        inventory = game.get("inventory", [])
        
        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
        else:
            room_def = WORLD[loc_id]
            npc_ids = room_def.get("npcs", [])
            
            # Parse the command - handle both "give item to npc" and "give npc item"
            args_str = " ".join(tokens[1:]).lower()
            
            # Initialize variables
            matched_npc_id = None
            matched_npc = None
            npc_target = None
            item_name = None
            
            # Try to find "to" separator
            if " to " in args_str:
                parts = args_str.split(" to ", 1)
                item_name = parts[0].strip()
                npc_target = parts[1].strip()
            else:
                # Try to match NPC first, then item
                # Look for known NPC names/IDs in the args
                
                # Try to match NPC using centralized matching
                matched_npc_id, matched_npc = match_npc_in_room(npc_ids, args_str)
                if matched_npc:
                    npc_name_lower = matched_npc.name.lower()
                    npc_id_lower = matched_npc_id.lower()
                    # Remove NPC name from args to get item
                    item_name = args_str.replace(npc_name_lower, "").replace(npc_id_lower, "").strip()
                    npc_target = npc_name_lower
                
                # If no NPC found, assume first word is item and rest is NPC
                if not npc_target:
                    words = args_str.split()
                    if len(words) >= 2:
                        item_name = words[0]
                        npc_target = " ".join(words[1:])
                    else:
                        response = "Syntax: give <item> to <npc> or give <npc> <item>"
                        npc_target = None  # Prevent further processing
            
            if npc_target:
                # Find matching NPC using centralized matching
                if not matched_npc:
                    matched_npc_id, matched_npc = match_npc_in_room(npc_ids, npc_target)
                
                if not matched_npc:
                    response = "There's no one like that here to give things to."
                elif not item_name:
                    npc_name = matched_npc.name if hasattr(matched_npc, 'name') else matched_npc.get('name', 'someone')
                    response = f"What do you want to give to {npc_name}?"
                else:
                    # Check if player has the item (try exact match and variations)
                    item_found = None
                    for inv_item in inventory:
                        if inv_item.lower() == item_name.lower() or inv_item.lower().replace("_", " ") == item_name.lower():
                            item_found = inv_item
                            break
                    
                    if not item_found:
                        response = f"You don't have a '{item_name}' to give."
                    else:
                        # Remove item from inventory
                        inventory.remove(item_found)
                        game["inventory"] = inventory
                        
                        # Update reputation for politeness (check original command text)
                        # Reconstruct the command to check for polite words
                        original_command_lower = command.lower()
                        _update_reputation_for_politeness(game, matched_npc_id, original_command_lower)
                        
                        # Generate AI response if NPC uses AI
                        npc_response = ""
                        npc_dict = matched_npc.to_dict() if hasattr(matched_npc, 'to_dict') else matched_npc
                        if (matched_npc.use_ai if hasattr(matched_npc, 'use_ai') else matched_npc.get("use_ai", False)) and generate_npc_reply is not None:
                            game["_current_npc_id"] = matched_npc_id
                            ai_response, error_message = generate_npc_reply(
                                npc_dict, room_def, game, username or "adventurer",
                                f"give {item_found}",
                                recent_log=game.get("log", [])[-10:],
                                user_id=user_id, db_conn=db_conn
                            )
                            if ai_response and ai_response.strip():
                                npc_response = "\n" + ai_response
                                if error_message:
                                    npc_response += f"\n[Note: {error_message}]"
                            
                            # Update memory
                            if matched_npc_id not in game.get("npc_memory", {}):
                                game.setdefault("npc_memory", {})[matched_npc_id] = []
                            game["npc_memory"][matched_npc_id].append({
                                "type": "gave",
                                "item": item_found,
                                "response": ai_response or "Thank you.",
                            })
                            if len(game["npc_memory"][matched_npc_id]) > 20:
                                game["npc_memory"][matched_npc_id] = game["npc_memory"][matched_npc_id][-20:]
                        else:
                            # Default response
                            npc_name = matched_npc.name if hasattr(matched_npc, 'name') else matched_npc.get('name', 'someone')
                            npc_response = f"\n{npc_name} accepts the {item_found.replace('_', ' ')} with a nod."
                        
                        npc_name = matched_npc.name if hasattr(matched_npc, 'name') else matched_npc.get('name', 'someone')
                        response = f"You give the {item_found.replace('_', ' ')} to {npc_name}." + npc_response

    elif tokens[0] == "buy" and len(tokens) >= 2:
        # Buy command: "buy <item>" or "buy <item> from <npc>"
        loc_id = game.get("location", "town_square")
        inventory = game.get("inventory", [])
        
        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
        else:
            room_def = WORLD[loc_id]
            npc_ids = room_def.get("npcs", [])
            
            # Parse item name and quantity (remove "from <npc>" if present)
            args_str = " ".join(tokens[1:]).lower()
            if " from " in args_str:
                parts = args_str.split(" from ", 1)
                item_name = parts[0].strip()
                npc_target = parts[1].strip()
            else:
                item_name = args_str
                npc_target = None
            
            # Try to extract quantity (e.g., "buy 3 bread" -> quantity=3, item="bread")
            quantity = 1
            import re
            quantity_match = re.match(r'^(\d+)\s+(.+)', item_name)
            if quantity_match:
                try:
                    quantity = int(quantity_match.group(1))
                    item_name = quantity_match.group(2).strip()
                except (ValueError, IndexError):
                    pass
            
            # Find matching merchant NPC (if specified, or use first merchant NPC in room)
            matched_npc = None
            matched_npc_id = None
            
            # First, find all merchant NPCs in the room
            merchant_npcs = []
            for npc_id in npc_ids:
                if npc_id in NPCS and npc_id in MERCHANT_ITEMS:
                    merchant_npcs.append((npc_id, NPCS[npc_id]))
            
            if npc_target:
                # Look for specific merchant NPC using centralized matching
                matched_npc_id, matched_npc = match_npc_in_room(
                    [npc_id for npc_id, _ in merchant_npcs], npc_target
                )
            else:
                # Use first merchant NPC in room
                if merchant_npcs:
                    matched_npc_id, matched_npc = merchant_npcs[0]
            
            if not matched_npc:
                response = "There's nobody here to serve you!"
            else:
                # Check if this NPC is actually a merchant
                npc_items = MERCHANT_ITEMS.get(matched_npc_id, {})
                
                if not npc_items:
                    response = "There's nobody here to serve you!"
                else:
                    # Try to match item - check multiple strategies
                    item_key = None
                    item_name_lower = item_name.lower()
                    
                    # Strategy 1: Direct key match (e.g., "bread" -> "bread")
                    direct_key = item_name_lower.replace(" ", "_")
                    if direct_key in npc_items:
                        item_key = direct_key
                    
                    # Strategy 2: Match against display names - prefer more specific matches first
                    # Sort by key length (longer = more specific) to prefer "piece_of_bread" over "bread"
                    sorted_items = sorted(npc_items.items(), key=lambda x: len(x[0]), reverse=True)
                    
                    if not item_key:
                        for key, item_info in sorted_items:
                            display_name = item_info.get("display_name", key.replace("_", " "))
                            display_name_lower = display_name.lower()
                            key_lower = key.replace("_", " ").lower()
                            
                            # Check if display_name is fully contained in item_name (best match)
                            # e.g., "piece of bread" in "piece of bread" or "loaf of bread" in "loaf of bread"
                            if display_name_lower in item_name_lower or item_name_lower in display_name_lower:
                                item_key = key
                                break
                            
                            # Check if key is contained in item_name
                            if key_lower in item_name_lower:
                                item_key = key
                                break
                            
                            # Check word-by-word: if key words appear in item_name
                            key_words = set(key_lower.split())
                            display_words = set(display_name_lower.split())
                            item_words = set(item_name_lower.split())
                            
                            # Prefer matches where more words match (more specific)
                            key_match_count = len(key_words.intersection(item_words))
                            display_match_count = len(display_words.intersection(item_words))
                            
                            if key_match_count > 0 or display_match_count > 0:
                                # If we have a partial match, store it but keep looking for better
                                if not item_key or (key_match_count > len(set(item_key.replace("_", " ").split()).intersection(item_words))):
                                    item_key = key
                    
                    # Strategy 3: Partial word match - try each word in item_name (fallback)
                    if not item_key:
                        item_words = item_name_lower.split()
                        # Check from end first (e.g., "bread" in "loaf of bread")
                        for word in reversed(item_words):
                            for key, item_info in sorted_items:
                                key_lower = key.replace("_", " ").lower()
                                display_name_lower = item_info.get("display_name", key.replace("_", " ")).lower()
                                if word in key_lower or word in display_name_lower:
                                    item_key = key
                                    break
                            if item_key:
                                break
                    
                    if not item_key:
                        # No AI for transactional commands - just simple response
                        npc_name = matched_npc.name if hasattr(matched_npc, 'name') else matched_npc.get('name', 'merchant')
                        response = f"{npc_name} doesn't sell '{item_name}'."
                    else:
                        # Process purchase with quantity and reputation discounts
                        success, purchase_response, actual_price = _process_purchase(
                            game, matched_npc, matched_npc_id, item_key, quantity, 
                            username or "adventurer", user_id, db_conn
                        )
                        
                        if not success:
                            response = purchase_response
                        else:
                            # Update reputation for politeness (check original command for polite words)
                            original_command = " ".join(tokens)
                            _update_reputation_for_politeness(game, matched_npc_id, original_command)
                            
                            response = purchase_response
                            
                            # No AI for transactional commands - simple deterministic response
                            # Get item_info from npc_items using item_key
                            item_info = npc_items.get(item_key, {})
                            item_display = item_info.get("display_name", item_key.replace("_", " "))
                            npc_name = matched_npc.name if hasattr(matched_npc, 'name') else matched_npc.get('name', 'merchant')
                            npc_response = f"\n{npc_name} hands you the {item_display}."
                            
                            # Update memory (without AI response)
                            if matched_npc_id not in game.get("npc_memory", {}):
                                game.setdefault("npc_memory", {})[matched_npc_id] = []
                            game["npc_memory"][matched_npc_id].append({
                                "type": "bought",
                                "item": item_name,
                                "quantity": quantity,
                                "price": actual_price,
                                "response": "Transaction completed.",
                            })
                            if len(game["npc_memory"][matched_npc_id]) > 20:
                                game["npc_memory"][matched_npc_id] = game["npc_memory"][matched_npc_id][-20:]
                            
                            response += npc_response

    elif tokens[0] == "list":
        # List command: show what's for sale in commercial establishments
        loc_id = game.get("location", "town_square")
        
        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
        else:
            room_def = WORLD[loc_id]
            npc_ids = room_def.get("npcs", [])
            
            # Find merchant NPCs in the room
            merchant_npcs = []
            for npc_id in npc_ids:
                if npc_id in NPCS and npc_id in MERCHANT_ITEMS:
                    merchant_npcs.append((npc_id, NPCS[npc_id]))
            
            if not merchant_npcs:
                response = "There's nothing for sale here."
            else:
                # Build list of items for sale using economy system
                from economy.economy_manager import get_item_price
                from economy.currency import format_currency, copper_to_currency
                items_list = []
                merchant_npc_id = None
                merchant_npc = None
                
                for npc_id, npc in merchant_npcs:
                    merchant_npc_id = npc_id
                    merchant_npc = npc
                    items = MERCHANT_ITEMS[npc_id]
                    
                    # Check and restock if needed
                    _restock_merchant_if_needed(npc_id)
                    
                    # Deduplicate by item_given to avoid showing the same item multiple times
                    # (e.g., "stew" and "bowl_of_stew" both give "bowl_of_stew")
                    seen_items = {}  # item_given -> (display_name, price_copper, item_key)
                    
                    for item_key, item_info in items.items():
                        item_given = item_info.get("item_given")
                        if not item_given:
                            continue
                        
                        # Only add if we haven't seen this item_given before, or if this is a more specific key
                        # (prefer longer keys like "bowl_of_stew" over "stew")
                        if item_given not in seen_items:
                            # Get price using economy system (returns copper coins)
                            price_copper = get_item_price(item_key, npc_id, game)
                            display_name = item_info.get("display_name", item_key.replace("_", " "))
                            seen_items[item_given] = (display_name, price_copper, item_key)
                        else:
                            # If we've seen it, prefer the more specific key (longer key name)
                            existing_key = seen_items[item_given][2]
                            if len(item_key) > len(existing_key):
                                price_copper = get_item_price(item_key, npc_id, game)
                                display_name = item_info.get("display_name", item_key.replace("_", " "))
                                seen_items[item_given] = (display_name, price_copper, item_key)
                    
                    # Build the list from unique items, showing availability
                    for display_name, price_copper, item_key in seen_items.values():
                        item_info = items[item_key]
                        item_given = item_info.get("item_given")
                        stock = _get_merchant_stock(npc_id, item_given)
                        
                        # Convert price to currency format
                        price_currency = copper_to_currency(price_copper)
                        price_str = format_currency(price_currency)
                        
                        if stock > 0:
                            items_list.append(f"  {display_name} - {price_str}")
                        else:
                            items_list.append(f"  {display_name} - {price_str} (sold out)")
                    
                    # Only show first merchant's items for now
                    break
                
                response = "Items for sale:\n" + "\n".join(items_list)
                
                # No AI for transactional commands - simple deterministic response
                if merchant_npc:
                    response += f"\n\n{merchant_npc.name} says: 'Feel free to have a look around.'"

    elif tokens[0] == "say" and len(tokens) >= 2:
        # Say something to everyone in the room
        message = " ".join(tokens[1:])
        loc_id = game.get("location", "town_square")
        actor_name = username or "Someone"
        
        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
        else:
            room_def = WORLD[loc_id]
            npc_ids = room_def.get("npcs", [])
            
            # Check for purchase intent in natural language
            purchase_processed = False
            for npc_id in npc_ids:
                if npc_id in NPCS and npc_id in MERCHANT_ITEMS:
                    npc = NPCS[npc_id]
                    merchant_items = MERCHANT_ITEMS[npc_id]
                    item_key, quantity = _parse_purchase_intent(
                        message, merchant_items, npc=npc, room_def=room_def,
                        game=game, username=username or "adventurer",
                        user_id=user_id, db_conn=db_conn, npc_id=npc_id
                    )
                    
                    if item_key:
                        # Found purchase intent - process it
                        success, purchase_response, actual_price = _process_purchase(
                            game, npc, npc_id, item_key, quantity,
                            username or "adventurer", user_id, db_conn
                        )
                        
                        if success:
                            # Update reputation for politeness in purchase
                            _update_reputation_for_politeness(game, npc_id, message)
                            
                            response = f"You say: \"{message}\"\n{purchase_response}"
                            
                            # Generate AI response
                            npc_dict = npc.to_dict() if hasattr(npc, 'to_dict') else npc
                            if (npc.use_ai if hasattr(npc, 'use_ai') else npc.get("use_ai", False)) and generate_npc_reply is not None:
                                game["_current_npc_id"] = npc_id
                                ai_response, error_message = generate_npc_reply(
                                    npc_dict, room_def, game, username or "adventurer",
                                    message,
                                    recent_log=game.get("log", [])[-10:],
                                    user_id=user_id, db_conn=db_conn
                                )
                                if ai_response and ai_response.strip():
                                    response += "\n" + ai_response
                                    if error_message:
                                        response += f"\n[Note: {error_message}]"
                                
                                # Update memory
                                if npc_id not in game.get("npc_memory", {}):
                                    game.setdefault("npc_memory", {})[npc_id] = []
                                game["npc_memory"][npc_id].append({
                                    "type": "bought",
                                    "item": item_key,
                                    "quantity": quantity,
                                    "price": actual_price,
                                    "response": ai_response or "Enjoy!",
                                })
                                if len(game["npc_memory"][npc_id]) > 20:
                                    game["npc_memory"][npc_id] = game["npc_memory"][npc_id][-20:]
                            
                            purchase_processed = True
                            break
                        elif purchase_response:
                            # Purchase failed (not enough money, etc.)
                            response = f"You say: \"{message}\"\n{purchase_response}"
                            purchase_processed = True
                            break
            
            if not purchase_processed:
                # Normal say command - no purchase detected
                player_message = f"{actor_name} says: \"{message}\""
                response = f"You say: \"{message}\""
                
                # Check for AI NPC reactions
                ai_reactions = []
                for npc_id in npc_ids:
                    if npc_id in NPCS:
                        npc = NPCS[npc_id]
                        
                        # Update reputation for politeness
                        rep_gain, _ = _update_reputation_for_politeness(game, npc_id, message)
                        
                        npc_dict = npc.to_dict() if hasattr(npc, 'to_dict') else npc
                        if (npc.use_ai if hasattr(npc, 'use_ai') else npc.get("use_ai", False)) and generate_npc_reply is not None:
                            # Store NPC ID in game for AI client to access
                            game["_current_npc_id"] = npc_id
                            
                            # Call AI to generate reaction (now returns tuple: response, error_message)
                            ai_response, error_message = generate_npc_reply(
                                npc_dict, room_def, game, username or "adventurer", 
                                message, recent_log=game.get("log", [])[-10:],
                                user_id=user_id, db_conn=db_conn
                            )
                            
                            if ai_response and ai_response.strip():
                                ai_reactions.append(ai_response)
                                
                                # Add error message if present
                                if error_message:
                                    ai_reactions.append(f"[Note: {error_message}]")
                                
                                # Update memory
                                if npc_id not in game.get("npc_memory", {}):
                                    game.setdefault("npc_memory", {})[npc_id] = []
                                game["npc_memory"][npc_id].append({
                                    "type": "said",
                                    "message": message,
                                    "response": ai_response,
                                })
                                # Keep memory from growing too large
                                if len(game["npc_memory"][npc_id]) > 20:
                                    game["npc_memory"][npc_id] = game["npc_memory"][npc_id][-20:]
                
                # Add AI reactions to response
                if ai_reactions:
                    response += "\n" + "\n".join(ai_reactions)
                
                # Broadcast say message to other players in the room
                if broadcast_fn is not None:
                    broadcast_fn(loc_id, player_message)

    elif tokens[0] in ["talk", "speak", "chat"]:
        if len(tokens) < 2:
            # No NPC specified - provide syntax help
            loc_id = game.get("location", "town_square")
            if loc_id in WORLD:
                room_def = WORLD[loc_id]
                npc_ids = room_def.get("npcs", [])
                if npc_ids:
                    # List available NPCs
                    npc_names = [NPCS[nid].name if hasattr(NPCS[nid], 'name') else NPCS[nid].get("name", "NPC") for nid in npc_ids if nid in NPCS]
                    if npc_names:
                        npc_list = ", ".join(npc_names)
                        response = f"Talk to whom? You can talk to: {npc_list}.\nSyntax: talk <npc name or id>"
                    else:
                        response = "Syntax: talk <npc name or id>\n(No NPCs are present here.)"
                else:
                    response = "Syntax: talk <npc name or id>\n(No NPCs are present here.)"
            else:
                response = "Syntax: talk <npc name or id>"
        else:
            # Talk to an NPC
            # Handle "talk to <npc>" syntax by skipping "to" if present
            target_tokens = tokens[1:]
            if target_tokens and target_tokens[0] == "to":
                target_tokens = target_tokens[1:]
            
            if not target_tokens:
                # No NPC specified after "to" - provide syntax help
                loc_id = game.get("location", "town_square")
                if loc_id in WORLD:
                    room_def = WORLD[loc_id]
                    npc_ids = room_def.get("npcs", [])
                    if npc_ids:
                        npc_names = [NPCS[nid].name if hasattr(NPCS[nid], 'name') else NPCS[nid].get("name", "NPC") for nid in npc_ids if nid in NPCS]
                        if npc_names:
                            npc_list = ", ".join(npc_names)
                            response = f"Talk to whom? You can talk to: {npc_list}.\nSyntax: talk <npc name or id>"
                        else:
                            response = "Syntax: talk <npc name or id>\n(No NPCs are present here.)"
                    else:
                        response = "Syntax: talk <npc name or id>\n(No NPCs are present here.)"
                else:
                    response = "Syntax: talk <npc name or id>"
            else:
                npc_target = " ".join(target_tokens).lower()
                loc_id = game.get("location", "town_square")
                
                if loc_id not in WORLD:
                    response = "You feel disoriented for a moment."
                else:
                    room_def = WORLD[loc_id]
                    npc_ids = room_def.get("npcs", [])
                    
                    # Use centralized NPC matching
                    matched_npc_id, matched_npc = match_npc_in_room(npc_ids, npc_target)
                    
                    if matched_npc:
                        # Generate dialogue for the NPC
                        response = generate_npc_line(matched_npc_id, game, username, user_id=user_id, db_conn=db_conn)
                    else:
                        response = "There's no one like that to talk to here."

    elif tokens[0] == "stat":
        # Admin-only stat command
        if not is_admin_user(username, game):
            response = "You don't have permission to do that."
        elif len(tokens) >= 2:
            target_text = " ".join(tokens[1:]).lower()
            
            # Handle "me" or username
            if target_text in ["me", "self"] or target_text == (username or "").lower():
                response = _format_player_stat(game, username or "adventurer")
            else:
                # Try to resolve as item or NPC
                item_id, source, container = resolve_item_target(game, target_text)
                if item_id:
                    response = _format_item_stat(item_id, source)
                else:
                    npc_id, npc = resolve_npc_target(game, target_text)
                    if npc_id and npc:
                        response = _format_npc_stat(npc_id, npc)
                    else:
                        response = f"You see nothing like '{target_text}' to examine."
        else:
            response = "Usage: stat <target> or stat me"

    elif tokens[0] == "describe" and len(tokens) >= 2:
        # Describe command: edit user's own description
        description_text = " ".join(tokens[1:])
        
        # Check length (max 500 characters)
        if len(description_text) > 500:
            response = "Your description is too long! It must be 500 characters or less (including spaces and punctuation)."
        else:
            # Store description in game state (will be saved to database via app.py)
            game["user_description"] = description_text
            response = f"Your description has been updated: {description_text}"
    
    elif tokens[0] in ["help", "?"]:
        emote_list = ", ".join(sorted(EMOTES.keys())[:5])  # Show first 5 emotes
        response = (
            "Commands: look, go <direction>, take <item>, take all, drop <item>, drop all, inventory, talk <npc>, say <message>, give <item> to <npc>, list, buy <item>, describe <text>, restart, quit.\n"
            "Emotes: nod, smile, wave, shrug, stare, laugh, grin, frown, sigh, yawn, clap, bow, salute, and more.\n"
            "You can use emotes alone (e.g., 'nod') or target NPCs (e.g., 'nod guard').\n"
            "Use 'say <message>' to speak to everyone in the room. AI-enhanced NPCs will react!\n"
            "Use 'drop <item>' to drop an item, or 'drop all' to drop all droppable items.\n"
            "Use 'give <item> to <npc>' to give items to NPCs. Use 'list' to see what's for sale. Use 'buy <item>' to purchase from merchants.\n"
            "Directions: north, south, east, west."
        )

    elif tokens[0] == "who":
        if who_fn:
            players = who_fn()
        else:
            players = []
        
        if not players:
            response = "You don't sense anyone else connected."
        else:
            lines = ["Players online:"]
            for p in players:
                uname = p.get("username", "Someone")
                loc_id = p.get("location", "town_square")
                room_name = WORLD.get(loc_id, {}).get("name", loc_id)
                lines.append(f"  {uname} - {room_name}")
            response = "\n".join(lines)

    elif tokens[0] == "time":
        # Display current in-game time in a creative format
        response = format_time_message(game)

    elif tokens[0] == "notify":
        notify_cfg = game.setdefault("notify", {})
        notify_cfg.setdefault("login", False)
        notify_cfg.setdefault("time", False)
        
        if len(tokens) == 1:
            status_login = "on" if notify_cfg.get("login") else "off"
            status_time = "on" if notify_cfg.get("time") else "off"
            response = (
                "Notification settings:\n"
                f"  login - {status_login}\n"
                f"  time - {status_time}\n"
                "Use 'notify <setting>', 'notify <setting> on', or 'notify <setting> off' to change."
            )
        else:
            what = tokens[1]
            explicit = tokens[2] if len(tokens) >= 3 else None
            
            if what in ["login", "logins"]:
                if explicit in ["on", "off"]:
                    notify_cfg["login"] = (explicit == "on")
                else:
                    notify_cfg["login"] = not notify_cfg.get("login", False)
                
                status = "on" if notify_cfg["login"] else "off"
                response = f"Login/logout notifications are now {status}."
            elif what in ["time", "day", "night"]:
                if explicit in ["on", "off"]:
                    notify_cfg["time"] = (explicit == "on")
                else:
                    notify_cfg["time"] = not notify_cfg.get("time", False)
                
                status = "on" if notify_cfg["time"] else "off"
                response = f"Day/night notifications are now {status}."
            else:
                response = (
                    "Unknown notify setting. Supported: 'notify', 'notify login', "
                    "'notify login on/off', 'notify time', 'notify time on/off'."
                )

    elif text.lower() in ["restart", "reset"]:
        # Create a new game state with the provided username
        game = new_game_state(username or "adventurer")
        response = "Game reset. " + describe_location(game)
        # Clear any pending quit when restarting
        game.pop("pending_quit", None)

    elif text.lower() in ["quit", "logout", "exit"]:
        # Set pending quit flag and ask for confirmation
        game["pending_quit"] = True
        response = "Are you sure you want to logout? (Type 'yes' to confirm, 'no' to cancel)"

    elif text.lower() in ["yes", "y"] and game.get("pending_quit"):
        # User confirmed logout - return special response that Flask will interpret
        game.pop("pending_quit", None)
        response = "__LOGOUT__"

    elif text.lower() in ["no", "n"] and game.get("pending_quit"):
        # User cancelled logout
        game.pop("pending_quit", None)
        response = "You decide to carry on adventuring. The world awaits!"

    else:
        # Any other command clears pending quit
        game.pop("pending_quit", None)
        response = "You mutter some nonsense. (Try 'help' for ideas.)"

    # Log the interaction (skip logging for logout confirmation)
    if response != "__LOGOUT__":
        game.setdefault("log", [])
        game["log"].append(f"> {command}")
        game["log"].append(response)
        # Keep log from growing forever
        game["log"] = game["log"][-50:]

    return response, game


def get_global_state_snapshot():
    """
    Returns a JSON-serialisable dict containing global state (ROOM_STATE, NPC_STATE).
    
    Returns:
        dict: {"room_state": ROOM_STATE, "npc_state": NPC_STATE}
    """
    return {
        "room_state": ROOM_STATE,
        "npc_state": NPC_STATE,
    }


def load_global_state_snapshot(snapshot):
    """
    Updates ROOM_STATE, NPC_STATE, and WORLD_CLOCK from a snapshot dict.
    Backfills missing fields for backward compatibility.
    
    Args:
        snapshot: dict with optional "room_state", "npc_state", and "world_clock" keys
    """
    global ROOM_STATE, NPC_STATE, WORLD_CLOCK
    from npc import NPCS
    
    if not isinstance(snapshot, dict):
        return  # Malformed snapshot, ignore
    
    if "room_state" in snapshot and isinstance(snapshot["room_state"], dict):
        ROOM_STATE = snapshot["room_state"]
    
    if "world_clock" in snapshot and isinstance(snapshot["world_clock"], dict):
        WORLD_CLOCK = snapshot["world_clock"]
        # Ensure required fields exist
        if "start_time" not in WORLD_CLOCK:
            WORLD_CLOCK["start_time"] = datetime.now().isoformat()
        if "last_restock" not in WORLD_CLOCK:
            WORLD_CLOCK["last_restock"] = {}
        if "current_period" not in WORLD_CLOCK:
            WORLD_CLOCK["current_period"] = "day"
        if "last_period_change_hour" not in WORLD_CLOCK:
            WORLD_CLOCK["last_period_change_hour"] = 0
    
    if "npc_state" in snapshot and isinstance(snapshot["npc_state"], dict):
        NPC_STATE = snapshot["npc_state"]
        
        # Backfill missing fields for backward compatibility
        for npc_id, state in NPC_STATE.items():
            # Ensure home_room exists
            if "home_room" not in state:
                npc = NPCS.get(npc_id)
                if npc and hasattr(npc, 'home') and npc.home:
                    state["home_room"] = npc.home
                else:
                    state["home_room"] = state.get("room", "town_square")
            
            # Ensure hp exists
            if "hp" not in state:
                npc = NPCS.get(npc_id)
                max_hp = 10
                if npc and hasattr(npc, 'stats') and npc.stats:
                    max_hp = npc.stats.get("max_hp", 10)
                state["hp"] = max_hp
            
            # Ensure alive exists
            if "alive" not in state:
                state["alive"] = True
            
            # Initialize merchant inventory if missing for merchants
            if npc_id in MERCHANT_ITEMS and "merchant_inventory" not in state:
                state["merchant_inventory"] = {}
                for item_key, item_info in MERCHANT_ITEMS[npc_id].items():
                    item_given = item_info.get("item_given")
                    if item_given:
                        initial_stock = item_info.get("initial_stock", 10)
                        state["merchant_inventory"][item_given] = initial_stock


def highlight_exits_in_log(log_entries):
    """
    Process log entries to highlight 'Exits:' in yellow.

    This is a presentation helper that ensures all "Exits:" text is highlighted,
    even in older log entries that might not have HTML markup.

    Args:
        log_entries: List of log entry strings

    Returns:
        list: List of log entries with HTML markup for "Exits:"
    """
    processed = []
    for entry in log_entries:
        # If entry doesn't already contain HTML span for Exits, add it
        if "Exits:" in entry and "<span" not in entry:
            entry = re.sub(
                r'Exits:',
                r'<span style="color: #ffff00; font-weight: bold;">Exits:</span>',
                entry
            )
        processed.append(entry)
    return processed

