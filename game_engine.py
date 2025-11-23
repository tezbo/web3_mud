"""
Game engine for Tiny Web MUD.

This module contains pure game logic - world definition, state transitions,
and command handling. It has no dependencies on Flask or web frameworks.
"""

import re
import os
import json
import time
import sys
import random
from datetime import datetime, timedelta

# Safe import of AI client (optional)
try:
    from ai_client import generate_npc_reply
except ImportError:
    generate_npc_reply = None

# Import NPC system
from npc import NPCS, match_npc_in_room, get_npc_reaction, generate_npc_line

# Import onboarding system
from onboarding import (
    ONBOARDING_USERNAME_PROMPT,
    ONBOARDING_PASSWORD_PROMPT,
    ONBOARDING_RACE_PROMPT,
    ONBOARDING_GENDER_PROMPT,
    ONBOARDING_STATS_PROMPT,
    ONBOARDING_BACKSTORY_PROMPT,
    ONBOARDING_COMPLETE,
    process_onboarding_message,
    handle_onboarding_command,
    AVAILABLE_RACES,
    AVAILABLE_GENDERS,
    AVAILABLE_BACKSTORIES,
    TOTAL_STAT_POINTS,
)

# Import command registry
from command_registry import register_command, get_handler

# --- NPC definitions moved to npc.py ---
# NPCs are now loaded via the NPC class system from npc.py

# --- Admin configuration ---

# Admin users (can be extended via environment variable or database)
ADMIN_USERS = set(os.environ.get("ADMIN_USERS", "admin,tezbo").split(","))

# --- Character Creation & Onboarding Constants ---

# --- Character creation constants ---
# These are also used outside onboarding (e.g., in character formatting)
STAT_NAMES = {
    "str": "Strength",
    "agi": "Agility",
    "wis": "Wisdom",
    "wil": "Willpower",
    "luck": "Luck",
}

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
# Based on Discworld MUD "soul" system pattern
# Each emote has: self (no target), self_target (with target), room (broadcast no target), 
# room_target (broadcast with target), target (message for target)

EMOTES = {
    # === Basic Social Gestures ===
    "nod": {
        "self": "You nod.",
        "self_target": "You nod at {target}.",
        "room": "{actor} nods.",
        "room_target": "{actor} nods at {target}.",
        "target": "{actor} nods at you.",
    },
    "shake": {
        "self": "You shake your head.",
        "self_target": "You shake your head at {target}.",
        "room": "{actor} shakes {actor_possessive} head.",
        "room_target": "{actor} shakes {actor_possessive} head at {target}.",
        "target": "{actor} shakes {actor_possessive} head at you.",
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
    "bow": {
        "self": "You bow.",
        "self_target": "You bow to {target}.",
        "room": "{actor} bows.",
        "room_target": "{actor} bows to {target}.",
        "target": "{actor} bows to you.",
    },
    "curtsey": {
        "self": "You curtsey gracefully.",
        "self_target": "You curtsey gracefully to {target}.",
        "room": "{actor} curtseys gracefully.",
        "room_target": "{actor} curtseys gracefully to {target}.",
        "target": "{actor} curtseys gracefully to you.",
    },
    "salute": {
        "self": "You salute.",
        "self_target": "You salute {target}.",
        "room": "{actor} salutes.",
        "room_target": "{actor} salutes {target}.",
        "target": "{actor} salutes you.",
    },
    "applaud": {
        "self": "You applaud.",
        "self_target": "You applaud {target}.",
        "room": "{actor} applauds.",
        "room_target": "{actor} applauds {target}.",
        "target": "{actor} applauds you.",
    },
    "clap": {
        "self": "You clap your hands.",
        "self_target": "You clap for {target}.",
        "room": "{actor} claps {actor_possessive} hands.",
        "room_target": "{actor} claps for {target}.",
        "target": "{actor} claps for you.",
    },
    
    # === Facial Expressions ===
    "smile": {
        "self": "You smile.",
        "self_target": "You smile at {target}.",
        "room": "{actor} smiles.",
        "room_target": "{actor} smiles at {target}.",
        "target": "{actor} smiles at you.",
    },
    "grin": {
        "self": "You grin widely.",
        "self_target": "You grin at {target}.",
        "room": "{actor} grins widely.",
        "room_target": "{actor} grins at {target}.",
        "target": "{actor} grins at you.",
    },
    "smirk": {
        "self": "You smirk.",
        "self_target": "You smirk at {target}.",
        "room": "{actor} smirks.",
        "room_target": "{actor} smirks at {target}.",
        "target": "{actor} smirks at you.",
    },
    "frown": {
        "self": "You frown.",
        "self_target": "You frown at {target}.",
        "room": "{actor} frowns.",
        "room_target": "{actor} frowns at {target}.",
        "target": "{actor} frowns at you.",
    },
    "scowl": {
        "self": "You scowl.",
        "self_target": "You scowl at {target}.",
        "room": "{actor} scowls.",
        "room_target": "{actor} scowls at {target}.",
        "target": "{actor} scowls at you.",
    },
    "glare": {
        "self": "You glare.",
        "self_target": "You glare at {target}.",
        "room": "{actor} glares.",
        "room_target": "{actor} glares at {target}.",
        "target": "{actor} glares at you.",
    },
    "stare": {
        "self": "You stare into the distance.",
        "self_target": "You stare at {target}.",
        "room": "{actor} stares.",
        "room_target": "{actor} stares at {target}.",
        "target": "{actor} stares at you.",
    },
    "gaze": {
        "self": "You gaze thoughtfully.",
        "self_target": "You gaze at {target}.",
        "room": "{actor} gazes thoughtfully.",
        "room_target": "{actor} gazes at {target}.",
        "target": "{actor} gazes at you.",
    },
    "blink": {
        "self": "You blink.",
        "self_target": "You blink at {target}.",
        "room": "{actor} blinks.",
        "room_target": "{actor} blinks at {target}.",
        "target": "{actor} blinks at you.",
    },
    "wink": {
        "self": "You wink.",
        "self_target": "You wink at {target}.",
        "room": "{actor} winks.",
        "room_target": "{actor} winks at {target}.",
        "target": "{actor} winks at you.",
    },
    "roll": {
        "self": "You roll your eyes.",
        "self_target": "You roll your eyes at {target}.",
        "room": "{actor} rolls {actor_possessive} eyes.",
        "room_target": "{actor} rolls {actor_possessive} eyes at {target}.",
        "target": "{actor} rolls {actor_possessive} eyes at you.",
    },
    "pout": {
        "self": "You pout.",
        "self_target": "You pout at {target}.",
        "room": "{actor} pouts.",
        "room_target": "{actor} pouts at {target}.",
        "target": "{actor} pouts at you.",
    },
    "sneer": {
        "self": "You sneer.",
        "self_target": "You sneer at {target}.",
        "room": "{actor} sneers.",
        "room_target": "{actor} sneers at {target}.",
        "target": "{actor} sneers at you.",
    },
    "blush": {
        "self": "You blush.",
        "self_target": "You blush at {target}.",
        "room": "{actor} blushes.",
        "room_target": "{actor} blushes at {target}.",
        "target": "{actor} blushes at you.",
    },
    
    # === Vocal Expressions ===
    "laugh": {
        "self": "You laugh.",
        "self_target": "You laugh with {target}.",
        "room": "{actor} laughs.",
        "room_target": "{actor} laughs with {target}.",
        "target": "{actor} laughs with you.",
    },
    "chuckle": {
        "self": "You chuckle.",
        "self_target": "You chuckle at {target}.",
        "room": "{actor} chuckles.",
        "room_target": "{actor} chuckles at {target}.",
        "target": "{actor} chuckles at you.",
    },
    "giggle": {
        "self": "You giggle.",
        "self_target": "You giggle at {target}.",
        "room": "{actor} giggles.",
        "room_target": "{actor} giggles at {target}.",
        "target": "{actor} giggles at you.",
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
    "groan": {
        "self": "You groan.",
        "self_target": "You groan at {target}.",
        "room": "{actor} groans.",
        "room_target": "{actor} groans at {target}.",
        "target": "{actor} groans at you.",
    },
    "moan": {
        "self": "You moan.",
        "self_target": "You moan at {target}.",
        "room": "{actor} moans.",
        "room_target": "{actor} moans at {target}.",
        "target": "{actor} moans at you.",
    },
    "whine": {
        "self": "You whine.",
        "self_target": "You whine to {target}.",
        "room": "{actor} whines.",
        "room_target": "{actor} whines to {target}.",
        "target": "{actor} whines to you.",
    },
    "shout": {
        "self": "You shout!",
        "self_target": "You shout at {target}!",
        "room": "{actor} shouts!",
        "room_target": "{actor} shouts at {target}!",
        "target": "{actor} shouts at you!",
    },
    "yell": {
        "self": "You yell!",
        "self_target": "You yell at {target}!",
        "room": "{actor} yells!",
        "room_target": "{actor} yells at {target}!",
        "target": "{actor} yells at you!",
    },
    "whisper": {
        "self": "You whisper.",
        "self_target": "You whisper to {target}.",
        "room": "{actor} whispers.",
        "room_target": "{actor} whispers to {target}.",
        "target": "{actor} whispers to you.",
    },
    "mutter": {
        "self": "You mutter to yourself.",
        "self_target": "You mutter to {target}.",
        "room": "{actor} mutters to {actor_possessive}self.",
        "room_target": "{actor} mutters to {target}.",
        "target": "{actor} mutters to you.",
    },
    "grumble": {
        "self": "You grumble.",
        "self_target": "You grumble at {target}.",
        "room": "{actor} grumbles.",
        "room_target": "{actor} grumbles at {target}.",
        "target": "{actor} grumbles at you.",
    },
    "hum": {
        "self": "You hum a tune.",
        "self_target": "You hum at {target}.",
        "room": "{actor} hums a tune.",
        "room_target": "{actor} hums at {target}.",
        "target": "{actor} hums at you.",
    },
    "whistle": {
        "self": "You whistle.",
        "self_target": "You whistle at {target}.",
        "room": "{actor} whistles.",
        "room_target": "{actor} whistles at {target}.",
        "target": "{actor} whistles at you.",
    },
    "sing": {
        "self": "You sing.",
        "self_target": "You sing to {target}.",
        "room": "{actor} sings.",
        "room_target": "{actor} sings to {target}.",
        "target": "{actor} sings to you.",
    },
    "cough": {
        "self": "You cough.",
        "self_target": "You cough at {target}.",
        "room": "{actor} coughs.",
        "room_target": "{actor} coughs at {target}.",
        "target": "{actor} coughs at you.",
    },
    "sniff": {
        "self": "You sniff.",
        "self_target": "You sniff at {target}.",
        "room": "{actor} sniffs.",
        "room_target": "{actor} sniffs at {target}.",
        "target": "{actor} sniffs at you.",
    },
    "sniffle": {
        "self": "You sniffle.",
        "self_target": "You sniffle at {target}.",
        "room": "{actor} sniffles.",
        "room_target": "{actor} sniffles at {target}.",
        "target": "{actor} sniffles at you.",
    },
    "gasp": {
        "self": "You gasp!",
        "self_target": "You gasp at {target}!",
        "room": "{actor} gasps!",
        "room_target": "{actor} gasps at {target}!",
        "target": "{actor} gasps at you!",
    },
    "scream": {
        "self": "You scream!",
        "self_target": "You scream at {target}!",
        "room": "{actor} screams!",
        "room_target": "{actor} screams at {target}!",
        "target": "{actor} screams at you!",
    },
    "cry": {
        "self": "You cry.",
        "self_target": "You cry to {target}.",
        "room": "{actor} cries.",
        "room_target": "{actor} cries to {target}.",
        "target": "{actor} cries to you.",
    },
    "sob": {
        "self": "You sob.",
        "self_target": "You sob to {target}.",
        "room": "{actor} sobs.",
        "room_target": "{actor} sobs to {target}.",
        "target": "{actor} sobs to you.",
    },
    "hiccup": {
        "self": "You hiccup.",
        "self_target": "You hiccup at {target}.",
        "room": "{actor} hiccups.",
        "room_target": "{actor} hiccups at {target}.",
        "target": "{actor} hiccups at you.",
    },
    "burp": {
        "self": "You burp.",
        "self_target": "You burp at {target}.",
        "room": "{actor} burps.",
        "room_target": "{actor} burps at {target}.",
        "target": "{actor} burps at you.",
    },
    "snore": {
        "self": "You snore.",
        "self_target": "You snore at {target}.",
        "room": "{actor} snores.",
        "room_target": "{actor} snores at {target}.",
        "target": "{actor} snores at you.",
    },
    "snarl": {
        "self": "You snarl.",
        "self_target": "You snarl at {target}.",
        "room": "{actor} snarls.",
        "room_target": "{actor} snarls at {target}.",
        "target": "{actor} snarls at you.",
    },
    "growl": {
        "self": "You growl.",
        "self_target": "You growl at {target}.",
        "room": "{actor} growls.",
        "room_target": "{actor} growls at {target}.",
        "target": "{actor} growls at you.",
    },
    "hiss": {
        "self": "You hiss.",
        "self_target": "You hiss at {target}.",
        "room": "{actor} hisses.",
        "room_target": "{actor} hisses at {target}.",
        "target": "{actor} hisses at you.",
    },
    "cheer": {
        "self": "You cheer!",
        "self_target": "You cheer for {target}!",
        "room": "{actor} cheers!",
        "room_target": "{actor} cheers for {target}!",
        "target": "{actor} cheers for you!",
    },
    
    # === Physical Actions ===
    "sit": {
        "self": "You sit down.",
        "self_target": "You sit down near {target}.",
        "room": "{actor} sits down.",
        "room_target": "{actor} sits down near {target}.",
        "target": "{actor} sits down near you.",
    },
    "stand": {
        "self": "You stand up.",
        "self_target": "You stand up near {target}.",
        "room": "{actor} stands up.",
        "room_target": "{actor} stands up near {target}.",
        "target": "{actor} stands up near you.",
    },
    "kneel": {
        "self": "You kneel down.",
        "self_target": "You kneel before {target}.",
        "room": "{actor} kneels down.",
        "room_target": "{actor} kneels before {target}.",
        "target": "{actor} kneels before you.",
    },
    "lie": {
        "self": "You lie down.",
        "self_target": "You lie down near {target}.",
        "room": "{actor} lies down.",
        "room_target": "{actor} lies down near {target}.",
        "target": "{actor} lies down near you.",
    },
    "rest": {
        "self": "You rest.",
        "self_target": "You rest near {target}.",
        "room": "{actor} rests.",
        "room_target": "{actor} rests near {target}.",
        "target": "{actor} rests near you.",
    },
    "sleep": {
        "self": "You fall asleep.",
        "self_target": "You fall asleep near {target}.",
        "room": "{actor} falls asleep.",
        "room_target": "{actor} falls asleep near {target}.",
        "target": "{actor} falls asleep near you.",
    },
    "wake": {
        "self": "You wake up.",
        "self_target": "You wake up near {target}.",
        "room": "{actor} wakes up.",
        "room_target": "{actor} wakes up near {target}.",
        "target": "{actor} wakes up near you.",
    },
    "jump": {
        "self": "You jump.",
        "self_target": "You jump at {target}.",
        "room": "{actor} jumps.",
        "room_target": "{actor} jumps at {target}.",
        "target": "{actor} jumps at you.",
    },
    "hop": {
        "self": "You hop.",
        "self_target": "You hop toward {target}.",
        "room": "{actor} hops.",
        "room_target": "{actor} hops toward {target}.",
        "target": "{actor} hops toward you.",
    },
    "skip": {
        "self": "You skip.",
        "self_target": "You skip toward {target}.",
        "room": "{actor} skips.",
        "room_target": "{actor} skips toward {target}.",
        "target": "{actor} skips toward you.",
    },
    "dance": {
        "self": "You dance.",
        "self_target": "You dance with {target}.",
        "room": "{actor} dances.",
        "room_target": "{actor} dances with {target}.",
        "target": "{actor} dances with you.",
    },
    "stretch": {
        "self": "You stretch.",
        "self_target": "You stretch near {target}.",
        "room": "{actor} stretches.",
        "room_target": "{actor} stretches near {target}.",
        "target": "{actor} stretches near you.",
    },
    "pace": {
        "self": "You pace back and forth.",
        "self_target": "You pace around {target}.",
        "room": "{actor} paces back and forth.",
        "room_target": "{actor} paces around {target}.",
        "target": "{actor} paces around you.",
    },
    "fidget": {
        "self": "You fidget.",
        "self_target": "You fidget near {target}.",
        "room": "{actor} fidgets.",
        "room_target": "{actor} fidgets near {target}.",
        "target": "{actor} fidgets near you.",
    },
    "twirl": {
        "self": "You twirl.",
        "self_target": "You twirl around {target}.",
        "room": "{actor} twirls.",
        "room_target": "{actor} twirls around {target}.",
        "target": "{actor} twirls around you.",
    },
    "spin": {
        "self": "You spin around.",
        "self_target": "You spin around {target}.",
        "room": "{actor} spins around.",
        "room_target": "{actor} spins around {target}.",
        "target": "{actor} spins around you.",
    },
    "lean": {
        "self": "You lean against something.",
        "self_target": "You lean against {target}.",
        "room": "{actor} leans against something.",
        "room_target": "{actor} leans against {target}.",
        "target": "{actor} leans against you.",
    },
    "stomp": {
        "self": "You stomp your foot.",
        "self_target": "You stomp your foot at {target}.",
        "room": "{actor} stomps {actor_possessive} foot.",
        "room_target": "{actor} stomps {actor_possessive} foot at {target}.",
        "target": "{actor} stomps {actor_possessive} foot at you.",
    },
    "tap": {
        "self": "You tap your foot.",
        "self_target": "You tap your foot at {target}.",
        "room": "{actor} taps {actor_possessive} foot.",
        "room_target": "{actor} taps {actor_possessive} foot at {target}.",
        "target": "{actor} taps {actor_possessive} foot at you.",
    },
    "shiver": {
        "self": "You shiver.",
        "self_target": "You shiver near {target}.",
        "room": "{actor} shivers.",
        "room_target": "{actor} shivers near {target}.",
        "target": "{actor} shivers near you.",
    },
    "tremble": {
        "self": "You tremble.",
        "self_target": "You tremble near {target}.",
        "room": "{actor} trembles.",
        "room_target": "{actor} trembles near {target}.",
        "target": "{actor} trembles near you.",
    },
    "shudder": {
        "self": "You shudder.",
        "self_target": "You shudder near {target}.",
        "room": "{actor} shudders.",
        "room_target": "{actor} shudders near {target}.",
        "target": "{actor} shudders near you.",
    },
    "collapse": {
        "self": "You collapse.",
        "self_target": "You collapse near {target}.",
        "room": "{actor} collapses.",
        "room_target": "{actor} collapses near {target}.",
        "target": "{actor} collapses near you.",
    },
    "squat": {
        "self": "You squat down.",
        "self_target": "You squat down near {target}.",
        "room": "{actor} squats down.",
        "room_target": "{actor} squats down near {target}.",
        "target": "{actor} squats down near you.",
    },
    
    # === Gestures & Touching ===
    "point": {
        "self": "You point.",
        "self_target": "You point at {target}.",
        "room": "{actor} points.",
        "room_target": "{actor} points at {target}.",
        "target": "{actor} points at you.",
    },
    "poke": {
        "self": "You poke the air.",
        "self_target": "You poke {target}.",
        "room": "{actor} pokes the air.",
        "room_target": "{actor} pokes {target}.",
        "target": "{actor} pokes you.",
    },
    "pat": {
        "self": "You pat yourself.",
        "self_target": "You pat {target}.",
        "room": "{actor} pats {actor_possessive}self.",
        "room_target": "{actor} pats {target}.",
        "target": "{actor} pats you.",
    },
    "rub": {
        "self": "You rub your hands together.",
        "self_target": "You rub {target}.",
        "room": "{actor} rubs {actor_possessive} hands together.",
        "room_target": "{actor} rubs {target}.",
        "target": "{actor} rubs you.",
    },
    "scratch": {
        "self": "You scratch your head.",
        "self_target": "You scratch {target}.",
        "room": "{actor} scratches {actor_possessive} head.",
        "room_target": "{actor} scratches {target}.",
        "target": "{actor} scratches you.",
    },
    "massage": {
        "self": "You massage your temples.",
        "self_target": "You massage {target}.",
        "room": "{actor} massages {actor_possessive} temples.",
        "room_target": "{actor} massages {target}.",
        "target": "{actor} massages you.",
    },
    "tickle": {
        "self": "You tickle yourself.",
        "self_target": "You tickle {target}.",
        "room": "{actor} tickles {actor_possessive}self.",
        "room_target": "{actor} tickles {target}.",
        "target": "{actor} tickles you.",
    },
    "tug": {
        "self": "You tug at your clothes.",
        "self_target": "You tug at {target}.",
        "room": "{actor} tugs at {actor_possessive} clothes.",
        "room_target": "{actor} tugs at {target}.",
        "target": "{actor} tugs at you.",
    },
    "stroke": {
        "self": "You stroke your chin thoughtfully.",
        "self_target": "You stroke {target}.",
        "room": "{actor} strokes {actor_possessive} chin thoughtfully.",
        "room_target": "{actor} strokes {target}.",
        "target": "{actor} strokes you.",
    },
    "fold": {
        "self": "You fold your arms.",
        "self_target": "You fold your arms and look at {target}.",
        "room": "{actor} folds {actor_possessive} arms.",
        "room_target": "{actor} folds {actor_possessive} arms and looks at {target}.",
        "target": "{actor} folds {actor_possessive} arms and looks at you.",
    },
    "cross": {
        "self": "You cross your arms.",
        "self_target": "You cross your arms and look at {target}.",
        "room": "{actor} crosses {actor_possessive} arms.",
        "room_target": "{actor} crosses {actor_possessive} arms and looks at {target}.",
        "target": "{actor} crosses {actor_possessive} arms and looks at you.",
    },
    "place": {
        "self": "You place your hands on your hips.",
        "self_target": "You place your hands on your hips and look at {target}.",
        "room": "{actor} places {actor_possessive} hands on {actor_possessive} hips.",
        "room_target": "{actor} places {actor_possessive} hands on {actor_possessive} hips and looks at {target}.",
        "target": "{actor} places {actor_possessive} hands on {actor_possessive} hips and looks at you.",
    },
    "facepalm": {
        "self": "You facepalm.",
        "self_target": "You facepalm at {target}.",
        "room": "{actor} facepalms.",
        "room_target": "{actor} facepalms at {target}.",
        "target": "{actor} facepalms at you.",
    },
    "headscratch": {
        "self": "You scratch your head.",
        "self_target": "You scratch your head at {target}.",
        "room": "{actor} scratches {actor_possessive} head.",
        "room_target": "{actor} scratches {actor_possessive} head at {target}.",
        "target": "{actor} scratches {actor_possessive} head at you.",
    },
    "chin": {
        "self": "You stroke your chin thoughtfully.",
        "self_target": "You stroke your chin while looking at {target}.",
        "room": "{actor} strokes {actor_possessive} chin thoughtfully.",
        "room_target": "{actor} strokes {actor_possessive} chin while looking at {target}.",
        "target": "{actor} strokes {actor_possessive} chin while looking at you.",
    },
    
    # === Affectionate Actions ===
    "hug": {
        "self": "You hug yourself.",
        "self_target": "You hug {target}.",
        "room": "{actor} hugs {actor_possessive}self.",
        "room_target": "{actor} hugs {target}.",
        "target": "{actor} hugs you.",
    },
    "embrace": {
        "self": "You embrace yourself.",
        "self_target": "You embrace {target}.",
        "room": "{actor} embraces {actor_possessive}self.",
        "room_target": "{actor} embraces {target}.",
        "target": "{actor} embraces you.",
    },
    "kiss": {
        "self": "You blow a kiss.",
        "self_target": "You kiss {target}.",
        "room": "{actor} blows a kiss.",
        "room_target": "{actor} kisses {target}.",
        "target": "{actor} kisses you.",
    },
    "nuzzle": {
        "self": "You nuzzle yourself.",
        "self_target": "You nuzzle {target}.",
        "room": "{actor} nuzzles {actor_possessive}self.",
        "room_target": "{actor} nuzzles {target}.",
        "target": "{actor} nuzzles you.",
    },
    "cuddle": {
        "self": "You cuddle yourself.",
        "self_target": "You cuddle {target}.",
        "room": "{actor} cuddles {actor_possessive}self.",
        "room_target": "{actor} cuddles {target}.",
        "target": "{actor} cuddles you.",
    },
    "snuggle": {
        "self": "You snuggle yourself.",
        "self_target": "You snuggle {target}.",
        "room": "{actor} snuggles {actor_possessive}self.",
        "room_target": "{actor} snuggles {target}.",
        "target": "{actor} snuggles you.",
    },
    "peck": {
        "self": "You peck the air.",
        "self_target": "You peck {target}.",
        "room": "{actor} pecks the air.",
        "room_target": "{actor} pecks {target}.",
        "target": "{actor} pecks you.",
    },
    "hold": {
        "self": "You hold your own hand.",
        "self_target": "You hold {target}'s hand.",
        "room": "{actor} holds {actor_possessive} own hand.",
        "room_target": "{actor} holds {target}'s hand.",
        "target": "{actor} holds your hand.",
    },
    
    # === Aggressive Actions ===
    "punch": {
        "self": "You punch the air.",
        "self_target": "You punch {target}!",
        "room": "{actor} punches the air.",
        "room_target": "{actor} punches {target}!",
        "target": "{actor} punches you!",
    },
    "slap": {
        "self": "You slap your own hand.",
        "self_target": "You slap {target}!",
        "room": "{actor} slaps {actor_possessive} own hand.",
        "room_target": "{actor} slaps {target}!",
        "target": "{actor} slaps you!",
    },
    "kick": {
        "self": "You kick the air.",
        "self_target": "You kick {target}!",
        "room": "{actor} kicks the air.",
        "room_target": "{actor} kicks {target}!",
        "target": "{actor} kicks you!",
    },
    "hit": {
        "self": "You hit yourself.",
        "self_target": "You hit {target}!",
        "room": "{actor} hits {actor_possessive}self.",
        "room_target": "{actor} hits {target}!",
        "target": "{actor} hits you!",
    },
    "smack": {
        "self": "You smack your own hand.",
        "self_target": "You smack {target}!",
        "room": "{actor} smacks {actor_possessive} own hand.",
        "room_target": "{actor} smacks {target}!",
        "target": "{actor} smacks you!",
    },
    "bite": {
        "self": "You bite the air.",
        "self_target": "You bite {target}!",
        "room": "{actor} bites the air.",
        "room_target": "{actor} bites {target}!",
        "target": "{actor} bites you!",
    },
    "spit": {
        "self": "You spit.",
        "self_target": "You spit at {target}!",
        "room": "{actor} spits.",
        "room_target": "{actor} spits at {target}!",
        "target": "{actor} spits at you!",
    },
    "push": {
        "self": "You push the air.",
        "self_target": "You push {target}!",
        "room": "{actor} pushes the air.",
        "room_target": "{actor} pushes {target}!",
        "target": "{actor} pushes you!",
    },
    "shove": {
        "self": "You shove the air.",
        "self_target": "You shove {target}!",
        "room": "{actor} shoves the air.",
        "room_target": "{actor} shoves {target}!",
        "target": "{actor} shoves you!",
    },
    "threaten": {
        "self": "You make a threatening gesture.",
        "self_target": "You threaten {target}!",
        "room": "{actor} makes a threatening gesture.",
        "room_target": "{actor} threatens {target}!",
        "target": "{actor} threatens you!",
    },
    
    # === Thoughtful/Contemplative Actions ===
    "think": {
        "self": "You think deeply.",
        "self_target": "You think about {target}.",
        "room": "{actor} thinks deeply.",
        "room_target": "{actor} thinks about {target}.",
        "target": "{actor} thinks about you.",
    },
    "ponder": {
        "self": "You ponder.",
        "self_target": "You ponder {target}.",
        "room": "{actor} ponders.",
        "room_target": "{actor} ponders {target}.",
        "target": "{actor} ponders you.",
    },
    "consider": {
        "self": "You consider the situation.",
        "self_target": "You consider {target}.",
        "room": "{actor} considers the situation.",
        "room_target": "{actor} considers {target}.",
        "target": "{actor} considers you.",
    },
    "meditate": {
        "self": "You meditate.",
        "self_target": "You meditate near {target}.",
        "room": "{actor} meditates.",
        "room_target": "{actor} meditates near {target}.",
        "target": "{actor} meditates near you.",
    },
    "concentrate": {
        "self": "You concentrate.",
        "self_target": "You concentrate on {target}.",
        "room": "{actor} concentrates.",
        "room_target": "{actor} concentrates on {target}.",
        "target": "{actor} concentrates on you.",
    },
    "examine": {
        "self": "You examine yourself.",
        "self_target": "You examine {target}.",
        "room": "{actor} examines {actor_possessive}self.",
        "room_target": "{actor} examines {target}.",
        "target": "{actor} examines you.",
    },
    "study": {
        "self": "You study your hands.",
        "self_target": "You study {target}.",
        "room": "{actor} studies {actor_possessive} hands.",
        "room_target": "{actor} studies {target}.",
        "target": "{actor} studies you.",
    },
    "contemplate": {
        "self": "You contemplate.",
        "self_target": "You contemplate {target}.",
        "room": "{actor} contemplates.",
        "room_target": "{actor} contemplates {target}.",
        "target": "{actor} contemplates you.",
    },
    
    # === Other Useful Actions ===
    "look": {
        "self": "You look around.",
        "self_target": "You look at {target}.",
        "room": "{actor} looks around.",
        "room_target": "{actor} looks at {target}.",
        "target": "{actor} looks at you.",
    },
    "watch": {
        "self": "You watch carefully.",
        "self_target": "You watch {target}.",
        "room": "{actor} watches carefully.",
        "room_target": "{actor} watches {target}.",
        "target": "{actor} watches you.",
    },
    "listen": {
        "self": "You listen carefully.",
        "self_target": "You listen to {target}.",
        "room": "{actor} listens carefully.",
        "room_target": "{actor} listens to {target}.",
        "target": "{actor} listens to you.",
    },
    "smell": {
        "self": "You smell the air.",
        "self_target": "You smell {target}.",
        "room": "{actor} smells the air.",
        "room_target": "{actor} smells {target}.",
        "target": "{actor} smells you.",
    },
    "taste": {
        "self": "You taste the air.",
        "self_target": "You taste {target}.",
        "room": "{actor} tastes the air.",
        "room_target": "{actor} tastes {target}.",
        "target": "{actor} tastes you.",
    },
    "feel": {
        "self": "You feel around.",
        "self_target": "You feel {target}.",
        "room": "{actor} feels around.",
        "room_target": "{actor} feels {target}.",
        "target": "{actor} feels you.",
    },
    "wait": {
        "self": "You wait patiently.",
        "self_target": "You wait for {target}.",
        "room": "{actor} waits patiently.",
        "room_target": "{actor} waits for {target}.",
        "target": "{actor} waits for you.",
    },
    "hope": {
        "self": "You hope for the best.",
        "self_target": "You hope for {target}.",
        "room": "{actor} hopes for the best.",
        "room_target": "{actor} hopes for {target}.",
        "target": "{actor} hopes for you.",
    },
    "pray": {
        "self": "You pray.",
        "self_target": "You pray for {target}.",
        "room": "{actor} prays.",
        "room_target": "{actor} prays for {target}.",
        "target": "{actor} prays for you.",
    },
    "bless": {
        "self": "You bless yourself.",
        "self_target": "You bless {target}.",
        "room": "{actor} blesses {actor_possessive}self.",
        "room_target": "{actor} blesses {target}.",
        "target": "{actor} blesses you.",
    },
    "curse": {
        "self": "You curse.",
        "self_target": "You curse {target}.",
        "room": "{actor} curses.",
        "room_target": "{actor} curses {target}.",
        "target": "{actor} curses you.",
    },
    "thank": {
        "self": "You express gratitude.",
        "self_target": "You thank {target}.",
        "room": "{actor} expresses gratitude.",
        "room_target": "{actor} thanks {target}.",
        "target": "{actor} thanks you.",
    },
    "apologize": {
        "self": "You apologize.",
        "self_target": "You apologize to {target}.",
        "room": "{actor} apologizes.",
        "room_target": "{actor} apologizes to {target}.",
        "target": "{actor} apologizes to you.",
    },
    "forgive": {
        "self": "You forgive yourself.",
        "self_target": "You forgive {target}.",
        "room": "{actor} forgives {actor_possessive}self.",
        "room_target": "{actor} forgives {target}.",
        "target": "{actor} forgives you.",
    },
    "agree": {
        "self": "You nod in agreement.",
        "self_target": "You agree with {target}.",
        "room": "{actor} nods in agreement.",
        "room_target": "{actor} agrees with {target}.",
        "target": "{actor} agrees with you.",
    },
    "disagree": {
        "self": "You shake your head in disagreement.",
        "self_target": "You disagree with {target}.",
        "room": "{actor} shakes {actor_possessive} head in disagreement.",
        "room_target": "{actor} disagrees with {target}.",
        "target": "{actor} disagrees with you.",
    },
    "approve": {
        "self": "You nod approvingly.",
        "self_target": "You approve of {target}.",
        "room": "{actor} nods approvingly.",
        "room_target": "{actor} approves of {target}.",
        "target": "{actor} approves of you.",
    },
    "disapprove": {
        "self": "You shake your head disapprovingly.",
        "self_target": "You disapprove of {target}.",
        "room": "{actor} shakes {actor_possessive} head disapprovingly.",
        "room_target": "{actor} disapproves of {target}.",
        "target": "{actor} disapproves of you.",
    },
    "welcome": {
        "self": "You welcome the company.",
        "self_target": "You welcome {target}.",
        "room": "{actor} welcomes the company.",
        "room_target": "{actor} welcomes {target}.",
        "target": "{actor} welcomes you.",
    },
    "greet": {
        "self": "You greet everyone.",
        "self_target": "You greet {target}.",
        "room": "{actor} greets everyone.",
        "room_target": "{actor} greets {target}.",
        "target": "{actor} greets you.",
    },
    "goodbye": {
        "self": "You say goodbye.",
        "self_target": "You say goodbye to {target}.",
        "room": "{actor} says goodbye.",
        "room_target": "{actor} says goodbye to {target}.",
        "target": "{actor} says goodbye to you.",
    },
    "farewell": {
        "self": "You bid farewell.",
        "self_target": "You bid farewell to {target}.",
        "room": "{actor} bids farewell.",
        "room_target": "{actor} bids farewell to {target}.",
        "target": "{actor} bids farewell to you.",
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
    "lost_package": {
        "name": "lost package",
        "type": "misc",
        "description": "A small wrapped package, slightly dusty. It looks like it was misplaced.",
        "weight": 0.3,
        "flags": [],
    },
    "mara_lucky_charm": {
        "name": "Mara's lucky charm",
        "type": "trinket",
        "description": "A small, handcrafted charm given to you by Mara as a token of gratitude. It seems to carry a bit of luck with it.",
        "weight": 0.05,
        "flags": ["quest"],
        "droppable": False,
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


def is_item_buryable(item_id: str) -> tuple:
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


def cleanup_buried_items():
    """
    Remove buried items that are older than 1 in-game day (1440 minutes).
    Items are permanently deleted after this period.
    """
    global BURIED_ITEMS
    current_minutes = get_current_game_minutes()
    
    # 1 in-game day = 1440 minutes
    MINUTES_PER_DAY = HOURS_PER_DAY * MINUTES_PER_HOUR
    deletion_threshold_minutes = current_minutes - MINUTES_PER_DAY
    
    rooms_to_clean = []
    for room_id, buried_list in BURIED_ITEMS.items():
        if not buried_list:
            continue
        
        # Filter out items that are too old (permanently deleted)
        remaining_items = []
        for buried_item in buried_list:
            buried_at_minutes = buried_item.get("buried_at_minutes", 0)
            if buried_at_minutes > deletion_threshold_minutes:
                remaining_items.append(buried_item)
        
        if remaining_items:
            BURIED_ITEMS[room_id] = remaining_items
        else:
            rooms_to_clean.append(room_id)
    
    # Remove rooms with no buried items
    for room_id in rooms_to_clean:
        del BURIED_ITEMS[room_id]


def get_buried_items_in_room(room_id: str) -> list:
    """
    Get list of buried items in a room that can still be recovered.
    
    Args:
        room_id: Room identifier
    
    Returns:
        list: List of buried item dicts with item_id and burial info
    """
    cleanup_buried_items()  # Clean up old items first
    return BURIED_ITEMS.get(room_id, [])


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
#
# WORLD is now loaded from JSON files via world_loader.py

# Import world loader
try:
    from world_loader import load_world_from_json
    WORLD = load_world_from_json()
except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
    # Fallback: if JSON loading fails, use empty dict and log error
    # This will cause issues, but at least the module will import
    print(f"ERROR: Failed to load world from JSON: {e}", file=sys.stderr)
    print("The game will not function correctly until world data is available.", file=sys.stderr)
    WORLD = {}

# Legacy hardcoded WORLD dict removed - now loaded from JSON
# If you need to see the old structure, check git history

# --- Global shared room state (shared across all players) ---

ROOM_STATE = {
    room_id: {
        "items": list(room_def.get("items", []))
    }
    for room_id, room_def in WORLD.items()
}

# --- Buried Items Tracking (for recovery system) ---
# Format: {room_id: [{"item_id": str, "buried_at_tick": int, "buried_at_minutes": int}, ...]}
# Items are permanently deleted after 1 in-game day (1440 minutes)
BURIED_ITEMS = {}

# --- Quest Global State (tracks active quest ownership across all players) ---
# Format: {
#   quest_id: {
#     "active_players": [username1, username2, ...],  # Who currently has this quest active
#     "completions": {username: count, ...},  # How many times each player has completed it
#     "first_taken_at": tick  # When first player took it (for rotation/reset)
#   }
# }
QUEST_GLOBAL_STATE = {}

# --- NPC Periodic Actions State (tracks when NPCs last performed actions per room) ---
# Format: {
#   room_id: {
#     "last_action_tick": int,  # Last tick when an NPC action was shown in this room
#     "last_weather_change_tick": int,  # Last tick when weather changed (for reactions)
#     "last_weather_state": dict  # Last weather state (to detect changes)
#   }
# }
NPC_ACTIONS_STATE = {}


def process_npc_periodic_actions(game, broadcast_fn=None, who_fn=None):
    """
    Process NPC periodic actions based on elapsed time.
    Shows accumulated NPC actions and weather reactions since last update.
    
    Args:
        game: Player's game state dict
        broadcast_fn: Optional callback(room_id: str, text: str) for broadcasting to room
        who_fn: Optional callback() -> list[dict] for getting active players
    """
    global NPC_ACTIONS_STATE, GAME_TIME, WEATHER_STATE
    import random
    
    current_tick = get_current_game_tick()
    current_room = game.get("location", "town_square")
    
    # Initialize room state if needed
    if current_room not in NPC_ACTIONS_STATE:
        NPC_ACTIONS_STATE[current_room] = {
            "last_action_tick": current_tick,
            "last_weather_change_tick": current_tick,
            "last_weather_state": WEATHER_STATE.copy()
        }
    
    room_state = NPC_ACTIONS_STATE[current_room]
    last_action_tick = room_state.get("last_action_tick", current_tick)
    
    # Calculate elapsed time (ticks since last action)
    elapsed_ticks = current_tick - last_action_tick
    
    # NPC actions should happen roughly every 3-8 in-game minutes (36-96 ticks at 12x speed)
    # More frequent if there are more NPCs in the room
    # This makes NPCs more active, even when player is idle
    npc_ids = get_npcs_in_room(current_room)
    num_npcs = len(npc_ids)
    
    if num_npcs > 0:
        # Calculate how many actions should have happened
        # Every 3-5 in-game minutes (36-60 ticks) on average, but more NPCs = more frequent actions
        # At 12x speed: 3 game minutes = ~15 real-world seconds, so NPCs act more frequently
        action_interval = max(36, 72 - (num_npcs * 6))  # 36-72 ticks depending on NPC count
        
        # Show accumulated actions based on elapsed time
        # Allow more actions if more time has passed, but cap to avoid spam
        actions_to_show = elapsed_ticks // action_interval
        # Cap at reasonable number: allow up to 5-8 actions depending on NPC count
        max_actions_to_show = min(max(5, num_npcs * 2), 10)  # More NPCs = can show more actions
        actions_to_show = min(actions_to_show, max_actions_to_show)
        
        if actions_to_show > 0:
            from npc_actions import get_all_npc_actions_for_room
            npc_actions = get_all_npc_actions_for_room(current_room)
            
            if npc_actions:
                # Show actions (one per NPC if possible, or random selection)
                shown_count = 0
                action_list = list(npc_actions.items())
                random.shuffle(action_list)  # Randomize order
                
                for npc_id, action in action_list:
                    if shown_count >= actions_to_show:
                        break
                    
                    # Format with cyan color tag
                    action_text = f"[CYAN]{action}[/CYAN]"
                    
                    # Add to player's log
                    game.setdefault("log", [])
                    game["log"].append(action_text)
                    game["log"] = game["log"][-50:]
                    
                    # Broadcast to other players in the room
                    if broadcast_fn:
                        broadcast_fn(current_room, action_text)
                    
                    shown_count += 1
                
                # Update last action tick (space them out)
                room_state["last_action_tick"] = current_tick - (elapsed_ticks % action_interval)
    
    # Check for weather changes and NPC reactions
    last_weather_state = room_state.get("last_weather_state", {})
    last_weather_tick = room_state.get("last_weather_change_tick", current_tick)
    
    # Check if weather has changed significantly
    weather_changed = False
    if last_weather_state.get("type") != WEATHER_STATE.get("type") or \
       last_weather_state.get("intensity") != WEATHER_STATE.get("intensity"):
        weather_changed = True
        room_state["last_weather_change_tick"] = current_tick
        room_state["last_weather_state"] = WEATHER_STATE.copy()
    
    # Show NPC weather reactions when weather changes (for outdoor rooms)
    room_def = WORLD.get(current_room, {})
    if room_def.get("outdoor", False) and weather_changed and num_npcs > 0:
        season = get_season()
        
        # Show weather reaction for one NPC (if any have reactions)
        random.shuffle(npc_ids)
        
        for npc_id in npc_ids:
            # Sanity check: only show reaction if NPC actually has weather status effects
            if has_npc_weather_status(npc_id):
                reaction = get_npc_weather_reaction(npc_id, WEATHER_STATE, season, check_status=True)
                if reaction:
                    # Format with cyan color tag
                    reaction_text = f"[CYAN]{reaction}[/CYAN]"
                    
                    # Add to player's log
                    game.setdefault("log", [])
                    game["log"].append(reaction_text)
                    game["log"] = game["log"][-50:]
                    
                    # Broadcast to other players in outdoor rooms
                    if broadcast_fn:
                        broadcast_fn(current_room, reaction_text)
                    
                    # Only show one weather reaction per change
                    break
    
    # Also check for periodic weather reactions (not just on change)
    # Show weather reaction occasionally (every ~30 ticks if weather is significant)
    if room_def.get("outdoor", False) and num_npcs > 0:
        wtype = WEATHER_STATE.get("type", "clear")
        intensity = WEATHER_STATE.get("intensity", "none")
        
        # Only for significant weather (not just clear)
        if wtype != "clear" and intensity in ["moderate", "heavy"]:
            # Show weather reaction every ~30 ticks (30% chance per command)
            if random.random() < 0.3:
                season = get_season()
                random.shuffle(npc_ids)
                
                for npc_id in npc_ids:
                    # Sanity check: only show reaction if NPC actually has weather status effects
                    if has_npc_weather_status(npc_id):
                        reaction = get_npc_weather_reaction(npc_id, WEATHER_STATE, season, check_status=True)
                        if reaction:
                            reaction_text = f"[CYAN]{reaction}[/CYAN]"
                            game.setdefault("log", [])
                            game["log"].append(reaction_text)
                            game["log"] = game["log"][-50:]
                            
                            if broadcast_fn:
                                broadcast_fn(current_room, reaction_text)
                            break

# --- World Clock (tracks in-game time) ---
# In-game time: 1 in-game hour = 1 real-world hour (configurable)
# 1 in-game day = 2 real-world hours (daybreak at hour 0, nightfall at hour 1, repeat)
WORLD_CLOCK = {
    "start_time": datetime.now().isoformat(),  # When the world clock started
    "in_game_hours": 0,  # Total in-game hours elapsed
    "last_restock": {},  # {npc_id: last_restock_in_game_hour}
    "current_period": "day",  # "day" or "night"
    "last_period_change_hour": 0,  # Last in-game hour when period changed
    "lunar_cycle_start_day": 0,  # Day when current lunar cycle started (for moon phase tracking)
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


# --- Weather and Season System ---

# Time constants for weather system
TICKS_PER_MINUTE = 1
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_YEAR = 120  # Short in-game year for gameplay

# GAME_TIME tracks continuous global time progression based purely on real-world time
# Time is calculated dynamically from a start timestamp, independent of player actions
GAME_TIME = {
    "start_timestamp": None,  # Real-world timestamp when game time started (ISO format string)
    "last_season": None,  # Track previous season for transition detection
}

# WEATHER_STATE tracks current global weather
WEATHER_STATE = {
    "type": "clear",      # "clear", "windy", "rain", "storm", "snow", "sleet", "overcast", "heatwave"
    "intensity": "none",  # "none", "light", "moderate", "heavy"
    "temperature": "mild",  # "cold", "chilly", "mild", "warm", "hot"
    "last_update_tick": 0,
}

# Weather messages by type and intensity
WEATHER_MESSAGES = {
    "windy": {
        "light": [
            "A gentle breeze rustles through the area.",
            "The wind picks up slightly, carrying a few leaves along the ground.",
        ],
        "moderate": [
            "A brisk wind tugs at your clothes.",
            "The wind is picking up, carrying leaves and dust along the ground.",
        ],
        "heavy": [
            "It's blowing a gale. Debris whips past you – you should find shelter.",
            "Strong winds howl around you, making it hard to keep your footing.",
        ],
    },
    "rain": {
        "light": [
            "A light rain patters gently around you.",
            "Drizzle falls softly, barely noticeable at first.",
        ],
        "moderate": [
            "Rain falls steadily, soaking the road and your clothes.",
            "The rain comes down in sheets, making everything slick and wet.",
        ],
        "heavy": [
            "Sheets of rain hammer the ground, making it hard to see far.",
            "Torrential rain lashes down, turning the ground to mud.",
        ],
    },
    "snow": {
        "light": [
            "A light snow floats gently to the ground, vanishing as it touches the earth.",
            "Delicate snowflakes drift down, dusting everything in white.",
        ],
        "moderate": [
            "Snow drifts down in thick flakes, softening the edges of the world.",
            "Steady snowfall blankets the ground, muffling all sound.",
        ],
        "heavy": [
            "A heavy snowfall blankets everything in white; your footprints fill in behind you.",
            "Blinding snow falls in thick curtains, obscuring the world around you.",
        ],
    },
    "sleet": {
        "moderate": [
            "Freezing sleet stings your face and soaks your clothes.",
            "Icy sleet pelts down, making the ground treacherous.",
        ],
        "heavy": [
            "Driving sleet cuts through the air like needles.",
            "The sleet comes down hard, coating everything in a layer of ice.",
        ],
    },
    "clear": {
        "none": {
            "dawn": [
                "The sky is clear in the pale morning light, with the rising sun just visible on the horizon.",
                "Clear skies stretch overhead as dawn breaks, promising a pleasant day.",
            ],
            "day": [
                "The sky is clear and bright, with the sun high above.",
                "Clear skies stretch overhead, promising a pleasant day.",
            ],
            "dusk": [
                "The sky is clear as evening approaches, with the sun setting in the west.",
                "Clear skies stretch overhead, the last rays of sunlight painting the horizon.",
            ],
            "night": [
                "The sky is clear and dark, with stars and the moon visible above.",
                "Clear skies stretch overhead, the moon and stars providing the only light.",
            ],
        },
    },
    "heatwave": {
        "moderate": [
            "It's hot and still; heat shimmers above the stone.",
            "The air is oppressive with heat, making every breath feel heavy.",
        ],
        "heavy": [
            "The heat is unbearable; the sun beats down mercilessly.",
            "Scorching heat radiates from every surface, making shade a precious commodity.",
        ],
    },
    "overcast": {
        "light": [
            "Grey clouds hang low overhead, muting the light.",
            "The sky is overcast, casting everything in a dull grey light.",
        ],
        "moderate": [
            "Thick clouds block out most of the sun, creating a somber atmosphere.",
            "Heavy clouds press down, making the day feel darker than it should.",
        ],
    },
    "storm": {
        "moderate": [
            "Thunder rumbles in the distance as dark clouds gather overhead.",
            "A storm is brewing; lightning flashes across the sky.",
        ],
        "heavy": [
            "A fierce storm rages, with thunder and lightning crashing all around.",
            "The storm unleashes its fury; you can barely see through the driving rain and wind.",
        ],
    },
}

# Seasonal overlays by feature and season
SEASONAL_OVERLAYS = {
    "autumn": {
        "trees": [
            "The leaves are starting to turn shades of red and yellow.",
            "Autumn colors paint the trees in brilliant hues.",
        ],
        "leaves": [
            "Fallen leaves swirl around your feet in the gusts.",
            "Crisp autumn leaves crunch underfoot.",
        ],
        "forest": [
            "The forest is awash with autumn colors, a final burst of beauty before winter.",
            "Autumn has transformed the forest into a tapestry of gold and crimson.",
        ],
    },
    "winter": {
        "trees": [
            "The trees stand bare, their branches etched dark against the sky.",
            "Bare branches reach skyward like skeletal fingers.",
        ],
        "village": [
            "A chill hangs in the air; your breath ghosts in front of you.",
            "The village looks stark and cold under the winter sky.",
        ],
        "market": [
            "The market stalls are quiet, their owners huddled against the cold.",
            "Winter has emptied the market; only the hardiest venture out.",
        ],
        "forest": [
            "The forest sleeps under a blanket of snow and silence.",
            "Winter has stripped the forest bare, leaving only the hardiest evergreens.",
        ],
    },
    "spring": {
        "trees": [
            "Fresh buds and blossoms dot the branches; new growth is everywhere.",
            "The trees are coming alive with new leaves and flowers.",
        ],
        "flowers": [
            "Wildflowers bloom along the paths, adding splashes of color.",
            "Spring flowers dot the landscape, a welcome sign of renewal.",
        ],
        "forest": [
            "Birdsong drifts through the air, bright and lively.",
            "The forest awakens with the sounds and scents of spring.",
        ],
    },
    "summer": {
        "fields": [
            "The air is warm, and the sky overhead is a deep, clear blue.",
            "Summer heat shimmers over the fields.",
        ],
        "village": [
            "The village basks in warm summer sunlight.",
            "Summer brings life and activity to the village streets.",
        ],
        "forest": [
            "The forest is lush and green, full of life and shade.",
            "Summer has filled the forest with vibrant green and dappled sunlight.",
        ],
    },
}


def get_current_game_minutes():
    """
    Calculate current game time in minutes based on elapsed real-world time.
    Time is purely continuous and global.
    
    Time conversion rate:
    - 1 in-game day = 2 real-world hours = 120 real-world minutes
    - 1 in-game day = 24 in-game hours = 1440 in-game minutes
    - Therefore: 1 in-game minute = 120/1440 = 1/12 real-world minutes = 5 real-world seconds
    - Or: 1 real-world minute = 12 in-game minutes
    
    Returns:
        int: Total in-game minutes elapsed since game start
    """
    global GAME_TIME
    from datetime import datetime
    
    # Initialize start timestamp if not set
    if GAME_TIME.get("start_timestamp") is None:
        GAME_TIME["start_timestamp"] = datetime.now().isoformat()
        return 0
    
    # Calculate elapsed real-world time since start
    start_time = datetime.fromisoformat(GAME_TIME["start_timestamp"])
    elapsed_real_seconds = (datetime.now() - start_time).total_seconds()
    elapsed_real_minutes = elapsed_real_seconds / 60.0
    
    # Convert to in-game minutes: 1 real-world minute = 12 in-game minutes
    # (because 1 in-game day = 1440 in-game minutes = 2 real-world hours = 120 real-world minutes)
    # So: 1440 game minutes / 120 real minutes = 12 game minutes per real minute
    elapsed_game_minutes = elapsed_real_minutes * 12.0
    
    # Return as integer (in-game minutes)
    return int(elapsed_game_minutes)


def get_current_game_tick():
    """
    Calculate current game tick based on elapsed real-world time.
    
    Returns:
        int: Current game tick count
    """
    minutes = get_current_game_minutes()
    return minutes * TICKS_PER_MINUTE


def advance_time(ticks=1):
    """
    Legacy function - time is now calculated dynamically and continuously.
    This function is kept for compatibility but does nothing.
    Time advances automatically based on real-world time.
    """
    # Time is now calculated dynamically from start_timestamp
    # No incremental advancement needed
    pass


def get_sunrise_sunset_times():
    """
    Get sunrise and sunset times in minutes for the current season.
    
    Returns:
        tuple: (sunrise_minutes, sunset_minutes)
    """
    season = get_season()
    
    # Sunrise times (in minutes from midnight)
    sunrise_times = {
        "spring": 6 * 60 + 30,    # 6:30am
        "summer": 6 * 60,          # 6:00am
        "autumn": 6 * 60 + 30,    # 6:30am
        "winter": 7 * 60,          # 7:00am
    }
    
    # Sunset times (in minutes from midnight)
    sunset_times = {
        "spring": 19 * 60 + 30,   # 7:30pm
        "summer": 20 * 60,         # 8:00pm
        "autumn": 19 * 60 + 30,   # 7:30pm
        "winter": 19 * 60,         # 7:00pm
    }
    
    return sunrise_times.get(season, 6 * 60), sunset_times.get(season, 20 * 60)


def get_current_hour_in_minutes():
    """
    Get current hour in minutes from midnight (0-1439).
    Uses continuous global time system.
    
    Returns:
        int: Current hour in minutes (0-1439)
    """
    total_minutes = get_current_game_minutes()
    minutes_in_day = total_minutes % (HOURS_PER_DAY * MINUTES_PER_HOUR)
    return int(minutes_in_day)


def set_npc_talk_cooldown(game, npc_id, duration_minutes: int):
    """
    Set a cooldown for an NPC refusing to talk to the player.
    
    Args:
        game: The game state dictionary
        npc_id: The NPC ID
        duration_minutes: Duration in in-game minutes
    """
    if "npc_cooldowns" not in game:
        game["npc_cooldowns"] = {}
    
    if npc_id not in game["npc_cooldowns"]:
        game["npc_cooldowns"][npc_id] = {}
    
    # Calculate the tick when the cooldown expires
    current_tick = GAME_TIME.get("tick", 0)
    ticks_per_minute = TICKS_PER_MINUTE
    cooldown_ticks = duration_minutes * ticks_per_minute
    expire_tick = current_tick + cooldown_ticks
    
    game["npc_cooldowns"][npc_id]["no_talk_until_tick"] = expire_tick


def is_npc_refusing_to_talk(game, npc_id) -> bool:
    """
    Check if an NPC is refusing to talk to the player.
    
    Args:
        game: The game state dictionary
        npc_id: The NPC ID
    
    Returns:
        bool: True if NPC is refusing to talk, False otherwise
    """
    if "npc_cooldowns" not in game:
        return False
    
    npc_cooldown = game["npc_cooldowns"].get(npc_id, {})
    no_talk_until = npc_cooldown.get("no_talk_until_tick")
    
    if no_talk_until is None:
        return False
    
    current_tick = GAME_TIME.get("tick", 0)
    return current_tick < no_talk_until


def get_current_hour_12h():
    """
    Get current hour in 12-hour format (1-12).
    
    Returns:
        int: Current hour (1-12)
    """
    total_minutes = get_current_game_minutes()
    minutes_in_day = total_minutes % (HOURS_PER_DAY * MINUTES_PER_HOUR)
    hour_24h = int(minutes_in_day // MINUTES_PER_HOUR)
    
    # Convert to 12-hour format
    if hour_24h == 0:
        return 12
    elif hour_24h <= 12:
        return hour_24h
    else:
        return hour_24h - 12


def get_time_of_day():
    """
    Get the time of day based on current in-game minutes and seasonal sunrise/sunset.
    
    Returns:
        str: "night", "dawn", "day", or "dusk"
    """
    minutes_in_day = get_current_hour_in_minutes()
    sunrise_min, sunset_min = get_sunrise_sunset_times()
    
    # Dawn: 30 minutes before sunrise to 30 minutes after sunrise
    dawn_start = max(0, sunrise_min - 30)
    dawn_end = sunrise_min + 30
    
    # Dusk: 30 minutes before sunset to 30 minutes after sunset
    dusk_start = max(0, sunset_min - 30)
    dusk_end = min(HOURS_PER_DAY * MINUTES_PER_HOUR, sunset_min + 30)
    
    if dawn_start <= minutes_in_day < dawn_end:
        return "dawn"
    elif dawn_end <= minutes_in_day < dusk_start:
        return "day"
    elif dusk_start <= minutes_in_day < dusk_end:
        return "dusk"
    else:
        return "night"


def get_day_of_year():
    """
    Get the current day of the year (0-based).
    
    Returns:
        int: Day of year (0 to DAYS_PER_YEAR-1)
    """
    total_minutes = get_current_game_minutes()
    days_elapsed = total_minutes // (HOURS_PER_DAY * MINUTES_PER_HOUR)
    return days_elapsed % DAYS_PER_YEAR


def get_season():
    """
    Get the current season based on day of year.
    
    Returns:
        str: "spring", "summer", "autumn", or "winter"
    """
    day = get_day_of_year()
    days_per_season = DAYS_PER_YEAR // 4
    
    if 0 <= day < days_per_season:
        return "spring"
    elif days_per_season <= day < days_per_season * 2:
        return "summer"
    elif days_per_season * 2 <= day < days_per_season * 3:
        return "autumn"
    else:
        return "winter"


def get_month():
    """
    Get the current month name based on day of year.
    Year has 12 months, each approximately 10 days (120 days / 12 months = 10 days/month).
    
    Returns:
        str: Month name (e.g., "Firstmoon", "Thawtide", etc.)
    """
    day = get_day_of_year()
    days_per_month = DAYS_PER_YEAR // 12
    month_index = day // days_per_month
    
    # Thematic month names for Hollowvale
    months = [
        "Firstmoon",    # Month 0 (Spring)
        "Thawtide",     # Month 1 (Spring)
        "Bloomtide",    # Month 2 (Spring)
        "Flameheart",   # Month 3 (Summer)
        "Suncrown",     # Month 4 (Summer)
        "Harvestmoon",  # Month 5 (Summer)
        "Fallowtide",   # Month 6 (Autumn)
        "Frostfall",    # Month 7 (Autumn)
        "Leafbare",     # Month 8 (Autumn)
        "Deepwinter",   # Month 9 (Winter)
        "Icetide",      # Month 10 (Winter)
        "Lastfrost",    # Month 11 (Winter)
    ]
    
    return months[month_index]


def get_day_of_month():
    """
    Get the current day of the month (1-based).
    
    Returns:
        int: Day of month (1 to ~10)
    """
    day = get_day_of_year()
    days_per_month = DAYS_PER_YEAR // 12
    day_of_month = (day % days_per_month) + 1
    return day_of_month


# --- Lunar Cycle System ---
# Moon phases cycle over ~30 in-game days (one month)

MOON_CYCLE_DAYS = 30  # Length of a full lunar cycle in in-game days

def get_moon_phase():
    """
    Get the current moon phase based on days elapsed.
    Moon phases: new, waxing_crescent, first_quarter, waxing_gibbous, 
                 full, waning_gibbous, last_quarter, waning_crescent
    
    Returns:
        str: Current moon phase name
    """
    day = get_day_of_year()
    
    # Initialize lunar cycle start day if needed
    if "lunar_cycle_start_day" not in WORLD_CLOCK:
        WORLD_CLOCK["lunar_cycle_start_day"] = day
    
    # Calculate days into current cycle
    days_in_cycle = (day - WORLD_CLOCK["lunar_cycle_start_day"]) % MOON_CYCLE_DAYS
    
    # Divide cycle into 8 phases (approx 3.75 days per phase)
    phase_length = MOON_CYCLE_DAYS / 8
    
    phase_index = int(days_in_cycle / phase_length) % 8
    
    phases = [
        "new",
        "waxing_crescent",
        "first_quarter",
        "waxing_gibbous",
        "full",
        "waning_gibbous",
        "last_quarter",
        "waning_crescent",
    ]
    
    return phases[phase_index]


def get_moon_phase_description():
    """
    Get a descriptive text about the current moon phase.
    
    Returns:
        str: Descriptive moon phase text
    """
    phase = get_moon_phase()
    phase_descriptions = {
        "new": "new moon",
        "waxing_crescent": "waxing crescent moon",
        "first_quarter": "waxing half moon",
        "waxing_gibbous": "waxing gibbous moon",
        "full": "full moon",
        "waning_gibbous": "waning gibbous moon",
        "last_quarter": "waning half moon",
        "waning_crescent": "waning crescent moon",
    }
    return phase_descriptions.get(phase, "moon")


def get_combined_time_weather_description(is_outdoor=True):
    """
    Get a combined time-of-day, moon phase, and weather description in a single coherent line.
    This replaces both the separate time-of-day/moon description and weather message.
    
    Args:
        is_outdoor: Whether the room is outdoor (affects descriptions)
    
    Returns:
        str: Combined time-of-day/moon/weather description
    """
    time_of_day = get_time_of_day()
    weather_type = WEATHER_STATE.get("type", "clear")
    weather_intensity = WEATHER_STATE.get("intensity", "none")
    moon_phase = get_moon_phase()
    moon_desc = get_moon_phase_description()
    
    # For indoor rooms, keep it simple
    if not is_outdoor:
        if time_of_day == "day":
            return "The day's light filters in from outside."
        elif time_of_day == "dawn":
            return "The pale light of dawn filters in through the windows."
        elif time_of_day == "dusk":
            return "Evening light fades as darkness settles outside."
        else:  # night
            return "The night is dark outside, little light reaching in."
    
    # Outdoor room descriptions - combine time, moon, and weather intelligently
    # Daytime
    if time_of_day == "day":
        if weather_type == "clear":
            return "The sun shines brightly overhead in clear skies, illuminating the land."
        elif weather_type == "overcast":
            return "The day is grey and muted under heavy overcast skies."
        elif weather_type == "rain":
            if weather_intensity == "heavy":
                return "The day is darkened by heavy rain and thick clouds that block out the sun."
            else:
                return "Rain falls steadily, darkening the day and soaking everything below."
        elif weather_type == "storm":
            return "A fierce storm darkens the day, with thunder and lightning crashing overhead."
        elif weather_type == "snow":
            if weather_intensity == "heavy":
                return "Heavy snow blankets the day, reducing visibility and muffling all sound."
            else:
                return "Snow drifts down steadily, softening the edges of the day."
        elif weather_type == "sleet":
            return "Freezing sleet falls through the day, making everything slick and treacherous."
        elif weather_type == "heatwave":
            return "The sun beats down mercilessly in the sweltering heat, baking the land."
        elif weather_type == "windy":
            if weather_intensity == "heavy":
                return "Strong winds howl through the day, making it hard to keep your footing."
            else:
                return "A brisk wind tugs at your clothes as the day progresses."
        elif weather_type == "fog":
            return "Thick fog obscures the day, reducing visibility to just a few paces."
        else:
            return "The day passes under an uncertain sky."
    
    # Dawn
    elif time_of_day == "dawn":
        if weather_type == "clear":
            return "Dawn breaks, painting the sky in shades of pink and gold with clear skies above."
        elif weather_type == "overcast":
            return "Dawn struggles through heavy grey clouds, casting everything in muted light."
        elif weather_type == "rain":
            return "Dawn breaks weakly through heavy clouds and steady rain."
        elif weather_type == "storm":
            return "Dawn battles against a raging storm, barely visible through the chaos."
        elif weather_type == "fog":
            return "Dawn light filters weakly through thick morning fog."
        else:
            return "Dawn breaks, though the weather obscures much of the morning light."
    
    # Dusk
    elif time_of_day == "dusk":
        if weather_type == "clear":
            return "Evening settles in with clear skies, the horizon painted in deep oranges and purples."
        elif weather_type == "overcast":
            return "Evening falls under heavy grey clouds, darkness coming early."
        elif weather_type == "rain":
            return "Evening arrives with steady rain, darkness deepened by the heavy weather."
        elif weather_type == "storm":
            return "Evening falls as the storm continues, darkness and chaos merging together."
        elif weather_type == "fog":
            return "Evening mist thickens as daylight fades, obscuring the horizon."
        else:
            return "Evening settles in, bringing darkness as the day ends."
    
    # Night (with moon phases)
    else:  # night
        moon_visible = moon_phase != "new" and weather_type not in ["overcast", "storm", "fog"]
        
        # Night with clear weather
        if weather_type == "clear":
            if moon_phase == "new":
                return "The night is pitch black under clear skies. The new moon provides no light, leaving only the faintest stars visible."
            elif moon_phase == "full":
                return "Clear skies stretch overhead, and the land is bathed in the bright silvery light of the full moon."
            elif moon_phase in ["waxing_gibbous", "waning_gibbous"]:
                return f"Clear skies stretch overhead, and the land is lit up by the bright light of the {moon_desc}."
            elif moon_phase in ["first_quarter", "last_quarter"]:
                return f"Clear skies stretch overhead, and the land is lit up by the eerie light of the {moon_desc}."
            elif moon_phase in ["waxing_crescent", "waning_crescent"]:
                return f"Clear skies stretch overhead. The {moon_desc} provides only dim light, leaving much of the land in shadow."
            else:
                return f"Clear skies stretch overhead, the {moon_desc} and stars providing the only light."
        
        # Night with overcast
        elif weather_type == "overcast":
            return "The night is pitch black, with thick clouds obscuring any light from above."
        
        # Night with rain
        elif weather_type == "rain":
            if weather_intensity == "heavy":
                return "The night is black as pitch, with heavy rain and thick clouds blocking out all light."
            else:
                return "The night is dark, with steady rain falling and clouds obscuring the sky above."
        
        # Night with storm
        elif weather_type == "storm":
            return "The night is black as pitch, with no light penetrating the storm clouds overhead."
        
        # Night with snow
        elif weather_type == "snow":
            if moon_visible:
                if moon_phase == "full":
                    return f"Snow falls steadily through the night, the full moon's light reflecting off the white ground."
                else:
                    return f"Snow drifts down through the night, the {moon_desc} casting an eerie glow on the falling flakes."
            else:
                return "Snow falls steadily through the dark night, reducing visibility to just a few paces."
        
        # Night with sleet
        elif weather_type == "sleet":
            return "Freezing sleet falls through the pitch black night, making the ground treacherous."
        
        # Night with fog
        elif weather_type == "fog":
            return "The night is lost in impenetrable fog, no light reaching through the thick mist."
        
        # Night with windy
        elif weather_type == "windy":
            if moon_visible:
                if moon_phase == "full":
                    return "A brisk wind tugs at your clothes as the full moon's light illuminates the restless night."
                else:
                    return f"A brisk wind tugs at your clothes under the {moon_desc}'s dim light."
            else:
                return "The night is dark and windy, with clouds scudding across the sky."
        
        # Default night (shouldn't happen, but fallback)
        else:
            if moon_phase == "new":
                return "The night is pitch black, the new moon providing no light."
            elif moon_visible:
                return f"The land is lit up by the light of the {moon_desc}."
            else:
                return "The night is dark and moonless."


def get_previous_season(current_season):
    """
    Get the previous season in the cycle.
    
    Args:
        current_season: Current season string
    
    Returns:
        str: Previous season string
    """
    season_order = ["spring", "summer", "autumn", "winter"]
    current_index = season_order.index(current_season)
    previous_index = (current_index - 1) % len(season_order)
    return season_order[previous_index]


def is_first_day_of_season():
    """
    Check if it's the first day of a new season.
    
    Returns:
        bool: True if it's the first day of a season
    """
    day = get_day_of_year()
    days_per_season = DAYS_PER_YEAR // 4
    return day % days_per_season == 0


def update_weather_if_needed():
    """
    Update weather state based on season and time.
    Called periodically to create weather transitions.
    """
    global WEATHER_STATE
    
    current_tick = get_current_game_tick()
    last_update = WEATHER_STATE.get("last_update_tick", 0)
    
    # Update weather every 10 ticks (roughly every 10 game minutes)
    if current_tick - last_update < 10:
        return
    
    WEATHER_STATE["last_update_tick"] = current_tick
    season = get_season()
    
    # Weather transition probabilities by season
    season_weather = {
        "spring": {
            "clear": 0.3,
            "rain": 0.4,
            "overcast": 0.2,
            "storm": 0.1,
        },
        "summer": {
            "clear": 0.5,
            "heatwave": 0.2,
            "storm": 0.2,
            "windy": 0.1,
        },
        "autumn": {
            "windy": 0.3,
            "rain": 0.3,
            "overcast": 0.2,
            "clear": 0.2,
        },
        "winter": {
            "snow": 0.4,
            "sleet": 0.2,
            "overcast": 0.2,
            "clear": 0.1,
            "windy": 0.1,
        },
    }
    
    # Temperature by season
    season_temp = {
        "spring": ["mild", "chilly"],
        "summer": ["warm", "hot"],
        "autumn": ["mild", "chilly"],
        "winter": ["cold", "chilly"],
    }
    
    # Get current weather type probabilities
    weather_probs = season_weather.get(season, season_weather["spring"])
    
    # Decide if weather should change (30% chance)
    if random.random() < 0.3:
        # Pick new weather type based on probabilities
        rand = random.random()
        cumulative = 0
        new_type = WEATHER_STATE["type"]  # Default: stay same
        
        for wtype, prob in weather_probs.items():
            cumulative += prob
            if rand <= cumulative:
                new_type = wtype
                break
        
        WEATHER_STATE["type"] = new_type
        
        # Set intensity based on weather type
        if new_type in ["rain", "snow", "sleet"]:
            intensities = ["light", "moderate", "heavy"]
            weights = [0.4, 0.4, 0.2]
            WEATHER_STATE["intensity"] = random.choices(intensities, weights=weights)[0]
        elif new_type == "windy":
            intensities = ["light", "moderate", "heavy"]
            weights = [0.3, 0.5, 0.2]
            WEATHER_STATE["intensity"] = random.choices(intensities, weights=weights)[0]
        elif new_type == "heatwave":
            intensities = ["moderate", "heavy"]
            weights = [0.6, 0.4]
            WEATHER_STATE["intensity"] = random.choices(intensities, weights=weights)[0]
        elif new_type == "storm":
            intensities = ["moderate", "heavy"]
            weights = [0.5, 0.5]
            WEATHER_STATE["intensity"] = random.choices(intensities, weights=weights)[0]
        elif new_type == "overcast":
            intensities = ["light", "moderate"]
            weights = [0.5, 0.5]
            WEATHER_STATE["intensity"] = random.choices(intensities, weights=weights)[0]
        else:
            WEATHER_STATE["intensity"] = "none"
    
    # Update temperature based on season and weather
    temp_options = season_temp.get(season, ["mild"])
    if WEATHER_STATE["type"] in ["snow", "sleet"]:
        WEATHER_STATE["temperature"] = "cold"
    elif WEATHER_STATE["type"] == "heatwave":
        WEATHER_STATE["temperature"] = "hot"
    else:
        WEATHER_STATE["temperature"] = random.choice(temp_options)


def get_weather_message():
    """
    Get a random weather message based on current weather state and time of day.
    
    Returns:
        str: Weather message or empty string
    """
    wtype = WEATHER_STATE.get("type", "clear")
    intensity = WEATHER_STATE.get("intensity", "none")
    time_of_day = get_time_of_day()
    
    if wtype not in WEATHER_MESSAGES:
        return ""
    
    # Check if this weather type has time-specific messages
    intensity_dict = WEATHER_MESSAGES[wtype].get(intensity, {})
    
    # If intensity_dict is a dict with time keys, use time-specific messages
    if isinstance(intensity_dict, dict) and time_of_day in intensity_dict:
        messages = intensity_dict[time_of_day]
    elif isinstance(intensity_dict, list):
        # Old format: list of messages
        messages = intensity_dict
    else:
        # Fallback to "none" intensity if available
        none_dict = WEATHER_MESSAGES[wtype].get("none", {})
        if isinstance(none_dict, dict) and time_of_day in none_dict:
            messages = none_dict[time_of_day]
        elif isinstance(none_dict, list):
            messages = none_dict
        else:
            messages = []
    
    if messages:
        return random.choice(messages)
    return ""


def apply_weather_to_description(description, time_of_day):
    """
    Apply weather-aware modifications to a room description.
    Modifies descriptions to reflect current weather conditions.
    
    Args:
        description: The base room description
        time_of_day: Current time of day (dawn/day/dusk/night)
    
    Returns:
        str: Modified description that reflects weather conditions
    """
    wtype = WEATHER_STATE.get("type", "clear")
    intensity = WEATHER_STATE.get("intensity", "none")
    temp = WEATHER_STATE.get("temperature", "mild")
    
    modified = description
    
    # Wind modifications
    if wtype == "windy":
        if intensity == "heavy":
            # Replace calm wind references with strong wind
            modified = modified.replace("The wind is", "The wind is")
            modified = modified.replace("wind whips", "wind howls and tears")
            modified = modified.replace("wind howls", "wind howls violently")
            modified = modified.replace("The air is still", "The wind howls around you")
            modified = modified.replace("still air", "howling wind")
        elif intensity == "moderate":
            modified = modified.replace("The air is still", "A brisk wind blows")
            modified = modified.replace("still air", "brisk wind")
        elif intensity == "light":
            modified = modified.replace("The air is still", "A gentle breeze stirs")
            modified = modified.replace("still air", "gentle breeze")
    elif wtype in ["clear", "heatwave"] and intensity == "none":
        # Still conditions - only modify if description mentions wind
        if "wind howls" in modified.lower() or "wind whips" in modified.lower():
            if time_of_day == "night":
                modified = modified.replace("wind howls", "air is still")
                modified = modified.replace("wind whips", "air is still")
            else:
                modified = modified.replace("wind howls", "wind is calm")
                modified = modified.replace("wind whips", "wind is calm")
    
    # Rain/snow/sleet modifications
    if wtype in ["rain", "snow", "sleet"]:
        if intensity == "heavy":
            # Heavy precipitation affects visibility
            if time_of_day == "night":
                modified = modified.replace("only the faintest lights", "no lights are visible through the")
                modified = modified.replace("faintest lights", "no lights visible")
                modified = modified.replace("horizon is lost", "horizon is completely obscured")
                modified = modified.replace("horizon is", "horizon is barely visible through the")
            else:
                modified = modified.replace("horizon is", "horizon is obscured by the")
                modified = modified.replace("you can see", "you can barely see")
        # Add precipitation context
        if "rain" in wtype and "rain" not in modified.lower():
            if time_of_day == "night":
                modified = modified.replace("pitch dark", "pitch dark, with rain lashing")
            else:
                modified = modified.replace("spreads out", "spreads out, though visibility is reduced by the rain")
    
    # Snow/sleet specific
    if wtype in ["snow", "sleet"]:
        if intensity == "heavy":
            if time_of_day == "night":
                modified = modified.replace("pitch dark", "pitch dark, with snow/sleet blinding")
                modified = modified.replace("sea of darkness", "blinding whiteout")
            else:
                modified = modified.replace("spreads out", "spreads out, though the snow/sleet makes it hard to see far")
    
    # Temperature modifications
    if temp == "hot" and time_of_day == "night":
        modified = modified.replace("cold beneath your feet", "warm, still radiating heat from the day")
        modified = modified.replace("stone is cold", "stone is still warm")
        modified = modified.replace("air is still", "air is hot and still, heavy with humidity")
    elif temp == "cold" and time_of_day == "night":
        modified = modified.replace("stone is cold", "stone is freezing cold")
        modified = modified.replace("cold beneath your feet", "bitterly cold beneath your feet")
    
    # Heatwave modifications
    if wtype == "heatwave":
        if time_of_day == "night":
            modified = modified.replace("pitch dark", "oppressively hot and dark")
            modified = modified.replace("air is still", "air is hot and heavy, making it hard to breathe")
        else:
            modified = modified.replace("spreads out", "spreads out, shimmering in the heat")
    
    # Storm modifications
    if wtype == "storm":
        if intensity == "heavy":
            if time_of_day == "night":
                modified = modified.replace("pitch dark", "pitch dark, with lightning illuminating")
                modified = modified.replace("horizon is lost", "horizon flashes with lightning")
            else:
                modified = modified.replace("spreads out", "spreads out, though the storm makes it hard to see")
    
    # Overcast modifications
    if wtype == "overcast":
        if time_of_day == "night":
            modified = modified.replace("pitch dark", "pitch dark, with clouds blocking any starlight")
            modified = modified.replace("moon and stars", "no moon or stars visible")
        else:
            modified = modified.replace("spreads out", "spreads out under the grey, overcast sky")
    
    return modified


def apply_weather_to_description(description, time_of_day):
    """
    Apply weather-aware modifications to a room description.
    Modifies descriptions to reflect current weather conditions.
    
    Args:
        description: The base room description
        time_of_day: Current time of day (dawn/day/dusk/night)
    
    Returns:
        str: Modified description that reflects weather conditions
    """
    wtype = WEATHER_STATE.get("type", "clear")
    intensity = WEATHER_STATE.get("intensity", "none")
    temp = WEATHER_STATE.get("temperature", "mild")
    
    modified = description
    
    # Wind modifications
    if wtype == "windy":
        if intensity == "heavy":
            # Replace calm wind references with strong wind
            modified = modified.replace("wind whips", "wind howls and tears")
            modified = modified.replace("wind howls", "wind howls violently")
            modified = modified.replace("The air is still", "The wind howls around you")
            modified = modified.replace("still air", "howling wind")
            modified = modified.replace("air is still", "wind howls")
        elif intensity == "moderate":
            modified = modified.replace("The air is still", "A brisk wind blows")
            modified = modified.replace("still air", "brisk wind")
            modified = modified.replace("air is still", "brisk wind blows")
        elif intensity == "light":
            modified = modified.replace("The air is still", "A gentle breeze stirs")
            modified = modified.replace("still air", "gentle breeze")
            modified = modified.replace("air is still", "gentle breeze stirs")
    elif wtype in ["clear", "heatwave"] and intensity == "none":
        # Still conditions - only modify if description mentions wind
        if "wind howls" in modified.lower() or "wind whips" in modified.lower():
            if time_of_day == "night":
                modified = modified.replace("wind howls", "air is still")
                modified = modified.replace("wind whips", "air is still")
            else:
                modified = modified.replace("wind howls", "wind is calm")
                modified = modified.replace("wind whips", "wind is calm")
    
    # Rain/snow/sleet modifications
    if wtype in ["rain", "snow", "sleet"]:
        if intensity == "heavy":
            # Heavy precipitation affects visibility
            if time_of_day == "night":
                # Fix visibility descriptions - do most specific first
                if "only the faintest lights from Hollowvale visible" in modified:
                    modified = modified.replace("only the faintest lights from Hollowvale visible", "no lights visible from Hollowvale")
                elif "faintest lights" in modified:
                    modified = modified.replace("faintest lights", "no lights visible")
                # Fix horizon descriptions - do most specific first
                if "horizon is lost in blackness" in modified:
                    modified = modified.replace("horizon is lost in blackness", "horizon is completely obscured")
                elif "horizon is lost" in modified:
                    modified = modified.replace("horizon is lost", "horizon is completely obscured")
                # Add precipitation context to "pitch dark of night" or "pitch dark"
                if "pitch dark of night" in modified and "rain" not in modified.lower() and "snow" not in modified.lower() and "sleet" not in modified.lower():
                    if wtype == "rain":
                        modified = modified.replace("pitch dark of night", "pitch dark of night, with torrential rain lashing down")
                    elif wtype == "snow":
                        modified = modified.replace("pitch dark of night", "pitch dark of night, with blinding snow")
                    elif wtype == "sleet":
                        modified = modified.replace("pitch dark of night", "pitch dark of night, with freezing sleet")
                elif "pitch dark" in modified and "rain" not in modified.lower() and "snow" not in modified.lower() and "sleet" not in modified.lower():
                    if wtype == "rain":
                        modified = modified.replace("pitch dark", "pitch dark, with torrential rain lashing down")
                    elif wtype == "snow":
                        modified = modified.replace("pitch dark", "pitch dark, with blinding snow")
                    elif wtype == "sleet":
                        modified = modified.replace("pitch dark", "pitch dark, with freezing sleet")
            else:
                modified = modified.replace("horizon is", "horizon is obscured by the")
                modified = modified.replace("you can see", "you can barely see")
                if "spreads out" in modified and "rain" not in modified.lower() and "snow" not in modified.lower():
                    if wtype == "rain":
                        modified = modified.replace("spreads out", "spreads out, though visibility is reduced by the driving rain")
                    elif wtype == "snow":
                        modified = modified.replace("spreads out", "spreads out, though the heavy snow makes it hard to see far")
                    elif wtype == "sleet":
                        modified = modified.replace("spreads out", "spreads out, though the freezing sleet obscures your view")
    
    # Temperature modifications
    if temp == "hot" and time_of_day == "night":
        modified = modified.replace("cold beneath your feet", "warm, still radiating heat from the day")
        modified = modified.replace("stone is cold", "stone is still warm")
        if "air is still" in modified:
            modified = modified.replace("air is still", "air is hot and still, heavy with humidity")
    elif temp == "cold" and time_of_day == "night":
        modified = modified.replace("stone is cold", "stone is freezing cold")
        if "cold beneath your feet" in modified:
            modified = modified.replace("cold beneath your feet", "bitterly cold beneath your feet")
        elif "stone is freezing cold" in modified and "bitterly" not in modified:
            # Avoid double modification
            pass
    
    # Heatwave modifications
    if wtype == "heatwave":
        if time_of_day == "night":
            if "pitch dark of night" in modified:
                modified = modified.replace("pitch dark of night", "oppressively hot and dark night")
            elif "pitch dark" in modified:
                modified = modified.replace("pitch dark", "oppressively hot and dark")
            if "air is still" in modified:
                modified = modified.replace("air is still", "air is hot and heavy, making it hard to breathe")
        else:
            modified = modified.replace("spreads out", "spreads out, shimmering in the heat")
    
    # Storm modifications
    if wtype == "storm":
        if intensity == "heavy":
            if time_of_day == "night":
                if "pitch dark of night" in modified:
                    modified = modified.replace("pitch dark of night", "pitch dark of night, with lightning illuminating the sky")
                elif "pitch dark" in modified:
                    modified = modified.replace("pitch dark", "pitch dark, with lightning illuminating the sky")
                modified = modified.replace("horizon is lost", "horizon flashes with lightning")
            else:
                modified = modified.replace("spreads out", "spreads out, though the storm makes it hard to see")
    
    # Overcast modifications
    if wtype == "overcast":
        if time_of_day == "night":
            if "pitch dark of night" in modified:
                modified = modified.replace("pitch dark of night", "pitch dark of night, with clouds blocking any starlight")
            elif "pitch dark" in modified:
                modified = modified.replace("pitch dark", "pitch dark, with clouds blocking any starlight")
            modified = modified.replace("moon and stars", "no moon or stars visible")
        else:
            modified = modified.replace("spreads out", "spreads out under the grey, overcast sky")
    
    return modified


def calculate_room_distance(start_room_id, target_room_id, max_distance=10):
    """
    Calculate the shortest path distance between two rooms using BFS.
    
    Args:
        start_room_id: Starting room ID
        target_room_id: Target room ID
        max_distance: Maximum distance to search (default: 10)
    
    Returns:
        int: Distance in rooms, or None if unreachable within max_distance
    """
    if start_room_id == target_room_id:
        return 0
    
    if start_room_id not in WORLD or target_room_id not in WORLD:
        return None
    
    # BFS to find shortest path
    queue = [(start_room_id, 0)]
    visited = {start_room_id}
    
    while queue:
        current_room, distance = queue.pop(0)
        
        if distance >= max_distance:
            continue
        
        if current_room not in WORLD:
            continue
        
        room_def = WORLD[current_room]
        exits = room_def.get("exits", {})
        
        for direction, next_room_id in exits.items():
            if next_room_id == target_room_id:
                return distance + 1
            
            if next_room_id not in visited and next_room_id in WORLD:
                visited.add(next_room_id)
                queue.append((next_room_id, distance + 1))
    
    return None


def get_rooms_within_distance(center_room_id, max_distance=5):
    """
    Get all rooms within a certain distance from a center room.
    
    Args:
        center_room_id: Center room ID
        max_distance: Maximum distance (default: 5)
    
    Returns:
        list: List of (room_id, distance) tuples
    """
    rooms_within = []
    
    for room_id in WORLD.keys():
        distance = calculate_room_distance(center_room_id, room_id, max_distance + 1)
        if distance is not None and distance <= max_distance:
            rooms_within.append((room_id, distance))
    
    return rooms_within


def check_sunrise_sunset_transitions(broadcast_fn=None, who_fn=None):
    """
    Check for sunrise/sunset transitions and broadcast notifications.
    Only sends to players with notify time on.
    
    Args:
        broadcast_fn: Optional callback(room_id, message) for broadcasting
        who_fn: Optional callback() -> list[dict] for getting active players
    
    Returns:
        list: List of (room_id, message) tuples for notifications
    """
    notifications = []
    
    # Track last sunrise/sunset in GAME_TIME
    if "last_sunrise_minute" not in GAME_TIME:
        GAME_TIME["last_sunrise_minute"] = -1
    if "last_sunset_minute" not in GAME_TIME:
        GAME_TIME["last_sunset_minute"] = -1
    
    current_minutes = get_current_hour_in_minutes()
    sunrise_min, sunset_min = get_sunrise_sunset_times()
    season = get_season()
    
    # Check for sunrise (within 1 minute window)
    if abs(current_minutes - sunrise_min) <= 1 and GAME_TIME["last_sunrise_minute"] != sunrise_min:
        GAME_TIME["last_sunrise_minute"] = sunrise_min
        season_name = season.capitalize()
        
        # Get weather-aware sunrise message
        wtype = WEATHER_STATE.get("type", "clear")
        intensity = WEATHER_STATE.get("intensity", "none")
        temp = WEATHER_STATE.get("temperature", "mild")
        
        if wtype == "rain":
            if intensity == "heavy":
                message = f"[CYAN]The sun struggles to rise through heavy clouds and driving rain, marking the start of a new {season_name} day.[/CYAN]"
            elif intensity == "moderate":
                message = f"[CYAN]The sun rises behind a curtain of rain, its light diffused and grey, marking the start of a new {season_name} day.[/CYAN]"
            else:
                message = f"[CYAN]The sun rises through light rain, its rays breaking through the clouds, marking the start of a new {season_name} day.[/CYAN]"
        elif wtype == "snow":
            if intensity == "heavy":
                message = f"[CYAN]The sun rises weakly through heavy snowfall, casting a pale light over the white landscape, marking the start of a new {season_name} day.[/CYAN]"
            elif intensity == "moderate":
                message = f"[CYAN]The sun rises through falling snow, its light soft and muted, marking the start of a new {season_name} day.[/CYAN]"
            else:
                message = f"[CYAN]The sun rises through light snow, its rays catching the flakes, marking the start of a new {season_name} day.[/CYAN]"
        elif wtype == "sleet":
            message = f"[CYAN]The sun rises weakly through freezing sleet, its light barely visible, marking the start of a new {season_name} day.[/CYAN]"
        elif wtype == "overcast":
            if intensity == "moderate":
                message = f"[CYAN]The sun rises behind thick clouds, its light muted and grey, marking the start of a new {season_name} day.[/CYAN]"
            else:
                message = f"[CYAN]The sun rises through overcast skies, its light soft and diffused, marking the start of a new {season_name} day.[/CYAN]"
        elif wtype == "storm":
            if intensity == "heavy":
                message = f"[CYAN]The sun struggles to rise through a fierce storm, lightning illuminating the dark clouds, marking the start of a new {season_name} day.[/CYAN]"
            else:
                message = f"[CYAN]The sun rises behind storm clouds, its light broken by flashes of lightning, marking the start of a new {season_name} day.[/CYAN]"
        elif wtype == "windy":
            if intensity == "heavy":
                message = f"[CYAN]The sun rises over Hollowvale as strong winds whip through the valley, marking the start of a new {season_name} day.[/CYAN]"
            elif intensity == "moderate":
                message = f"[CYAN]The sun rises over Hollowvale, its light carried on a brisk wind, marking the start of a new {season_name} day.[/CYAN]"
            else:
                message = f"[CYAN]The sun rises over Hollowvale, a gentle breeze stirring the morning air, marking the start of a new {season_name} day.[/CYAN]"
        elif wtype == "heatwave":
            message = f"[CYAN]The sun rises hot and bright over Hollowvale, the air already heavy with heat, marking the start of a new {season_name} day.[/CYAN]"
        else:  # clear
            if temp == "hot":
                message = f"[CYAN]The sun rises bright and warm over Hollowvale, promising a hot {season_name} day.[/CYAN]"
            elif temp == "cold":
                message = f"[CYAN]The sun rises cold and clear over Hollowvale, marking the start of a new {season_name} day.[/CYAN]"
            else:
                message = f"[CYAN]The sun rises over Hollowvale, marking the start of a new {season_name} day.[/CYAN]"
        
        # Check if it's the first day of a new season and append transition message
        if is_first_day_of_season():
            previous_season = GAME_TIME.get("last_season")
            current_season = season
            
            # Only show transition if season actually changed
            if previous_season and previous_season != current_season:
                previous_season_name = previous_season.capitalize()
                current_season_name = current_season.capitalize()
                
                # Generate weather-aware seasonal transition message
                transition_messages = []
                
                if current_season == "spring":
                    if wtype == "rain":
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and the rain brings new life to the awakening world.",
                            f" As {previous_season_name} gives way to {current_season_name}, the gentle rain nourishes the earth, and new growth stirs beneath the soil.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives with rain-washed promise.",
                        ]
                    elif wtype == "snow":
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, though winter's last snow still clings to the ground.",
                            f" As {previous_season_name} gives way to {current_season_name}, the lingering snow reminds us that change comes slowly.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives, but winter's touch remains.",
                        ]
                    else:
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and the world awakens with new life.",
                            f" As {previous_season_name} gives way to {current_season_name}, the first buds appear and the air fills with promise.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives, bringing renewal to Hollowvale.",
                        ]
                elif current_season == "summer":
                    if wtype == "heatwave":
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and the heat settles over the land like a heavy blanket.",
                            f" As {previous_season_name} gives way to {current_season_name}, the oppressive heat announces the long days ahead.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives with scorching intensity.",
                        ]
                    elif wtype == "rain":
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and warm rains promise abundance.",
                            f" As {previous_season_name} gives way to {current_season_name}, the rain brings life to fields and forests.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives with fertile promise.",
                        ]
                    else:
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and the days grow long and warm.",
                            f" As {previous_season_name} gives way to {current_season_name}, the sun's warmth fills the valley with life.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives, bringing warmth and growth.",
                        ]
                elif current_season == "autumn":
                    if wtype == "rain":
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and the rain begins to strip the leaves from the trees.",
                            f" As {previous_season_name} gives way to {current_season_name}, the rain-washed air carries the scent of change.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives with rain and falling leaves.",
                        ]
                    elif wtype == "windy":
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and the wind carries the first fallen leaves.",
                            f" As {previous_season_name} gives way to {current_season_name}, the brisk winds herald the coming change.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives on a gust of wind.",
                        ]
                    else:
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and the first leaves begin to change color.",
                            f" As {previous_season_name} gives way to {current_season_name}, the air grows crisp and the harvest approaches.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives, painting the world in gold and red.",
                        ]
                else:  # winter
                    if wtype == "snow":
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and the first snow settles over Hollowvale.",
                            f" As {previous_season_name} gives way to {current_season_name}, the falling snow blankets the world in white.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives with snow and silence.",
                        ]
                    elif wtype == "cold" or temp == "cold":
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and a deep cold settles over the land.",
                            f" As {previous_season_name} gives way to {current_season_name}, the biting cold announces the long nights ahead.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives with frost and stillness.",
                        ]
                    else:
                        transition_messages = [
                            f" The seasons turn from {previous_season_name} to {current_season_name}, and the world grows quiet and still.",
                            f" As {previous_season_name} gives way to {current_season_name}, the days shorten and the cold begins to bite.",
                            f" The wheel of seasons turns: {previous_season_name} fades, and {current_season_name} arrives, bringing rest to the land.",
                        ]
                
                # Select a random transition message
                import random
                transition_text = random.choice(transition_messages)
                message = message.replace("[/CYAN]", transition_text + "[/CYAN]")
                
                # Update last_season
                GAME_TIME["last_season"] = current_season
            elif not previous_season:
                # First time tracking - just set it
                GAME_TIME["last_season"] = current_season
        else:
            # Not first day, but update last_season if it changed
            current_season = season
            if GAME_TIME.get("last_season") != current_season:
                GAME_TIME["last_season"] = current_season
        
        # Broadcast to all outdoor rooms (filtered by notify time in app.py)
        if broadcast_fn and who_fn:
            active_players = who_fn()
            outdoor_rooms = set()
            
            for player in active_players:
                loc_id = player.get("location", "town_square")
                if loc_id in WORLD and WORLD[loc_id].get("outdoor", False):
                    outdoor_rooms.add(loc_id)
            
            for room_id in outdoor_rooms:
                broadcast_fn(room_id, message)
                notifications.append((room_id, message))
    
    # Check for sunset (within 1 minute window)
    if abs(current_minutes - sunset_min) <= 1 and GAME_TIME["last_sunset_minute"] != sunset_min:
        GAME_TIME["last_sunset_minute"] = sunset_min
        season_name = season.capitalize()
        
        # Get weather-aware sunset message
        wtype = WEATHER_STATE.get("type", "clear")
        intensity = WEATHER_STATE.get("intensity", "none")
        temp = WEATHER_STATE.get("temperature", "mild")
        
        if wtype == "rain":
            if intensity == "heavy":
                message = f"[CYAN]The sun sets behind heavy clouds and driving rain, bringing {season_name} night.[/CYAN]"
            elif intensity == "moderate":
                message = f"[CYAN]The sun sets behind a curtain of rain, its light fading into grey, bringing {season_name} night.[/CYAN]"
            else:
                message = f"[CYAN]The sun sets through light rain, its last rays breaking through the clouds, bringing {season_name} night.[/CYAN]"
        elif wtype == "snow":
            if intensity == "heavy":
                message = f"[CYAN]The sun sets weakly through heavy snowfall, casting a pale glow over the white landscape, bringing {season_name} night.[/CYAN]"
            elif intensity == "moderate":
                message = f"[CYAN]The sun sets through falling snow, its light soft and muted, bringing {season_name} night.[/CYAN]"
            else:
                message = f"[CYAN]The sun sets through light snow, its rays catching the flakes, bringing {season_name} night.[/CYAN]"
        elif wtype == "sleet":
            message = f"[CYAN]The sun sets weakly through freezing sleet, its light barely visible, bringing {season_name} night.[/CYAN]"
        elif wtype == "overcast":
            if intensity == "moderate":
                message = f"[CYAN]The sun sets behind thick clouds, its light muted and grey, bringing {season_name} night.[/CYAN]"
            else:
                message = f"[CYAN]The sun sets through overcast skies, its light soft and diffused, bringing {season_name} night.[/CYAN]"
        elif wtype == "storm":
            if intensity == "heavy":
                message = f"[CYAN]The sun sets behind a fierce storm, lightning illuminating the dark clouds, bringing {season_name} night.[/CYAN]"
            else:
                message = f"[CYAN]The sun sets behind storm clouds, its light broken by flashes of lightning, bringing {season_name} night.[/CYAN]"
        elif wtype == "windy":
            if intensity == "heavy":
                message = f"[CYAN]The sun sets over Hollowvale as strong winds whip through the valley, bringing {season_name} night.[/CYAN]"
            elif intensity == "moderate":
                message = f"[CYAN]The sun sets over Hollowvale, its light carried on a brisk wind, bringing {season_name} night.[/CYAN]"
            else:
                message = f"[CYAN]The sun sets over Hollowvale, a gentle breeze stirring the evening air, bringing {season_name} night.[/CYAN]"
        elif wtype == "heatwave":
            message = f"[CYAN]The sun sets hot and heavy over Hollowvale, the air still warm from the day, bringing {season_name} night.[/CYAN]"
        else:  # clear
            if temp == "hot":
                message = f"[CYAN]The sun sets warm and bright over Hollowvale, the heat of the day lingering, bringing {season_name} night.[/CYAN]"
            elif temp == "cold":
                message = f"[CYAN]The sun sets cold and clear over Hollowvale, bringing {season_name} night.[/CYAN]"
            else:
                message = f"[CYAN]The sun sets over Hollowvale, bringing {season_name} night.[/CYAN]"
        
        # Broadcast to all outdoor rooms (filtered by notify time in app.py)
        if broadcast_fn and who_fn:
            active_players = who_fn()
            outdoor_rooms = set()
            
            for player in active_players:
                loc_id = player.get("location", "town_square")
                if loc_id in WORLD and WORLD[loc_id].get("outdoor", False):
                    outdoor_rooms.add(loc_id)
            
            for room_id in outdoor_rooms:
                broadcast_fn(room_id, message)
                notifications.append((room_id, message))
    
    return notifications


def check_bell_tolling(broadcast_fn=None, who_fn=None):
    """
    Check if it's time for the bell to toll (on the hour) and broadcast messages.
    
    Args:
        broadcast_fn: Optional callback(room_id, message) for broadcasting
        who_fn: Optional callback() -> list[dict] for getting active players
    
    Returns:
        list: List of notifications sent
    """
    notifications = []
    
    # Track last bell toll hour
    if "last_bell_hour" not in GAME_TIME:
        GAME_TIME["last_bell_hour"] = -1
    
    current_minutes = get_current_hour_in_minutes()
    current_hour_24h = int(current_minutes // MINUTES_PER_HOUR)
    current_minute = int(current_minutes % MINUTES_PER_HOUR)
    
    # Only toll on the hour (minute 0)
    if current_minute == 0 and GAME_TIME["last_bell_hour"] != current_hour_24h:
        GAME_TIME["last_bell_hour"] = current_hour_24h
        hour_12h = get_current_hour_12h()
        
        # Get all rooms within 5 steps of town_square
        belltower_room = "town_square"
        rooms_within = get_rooms_within_distance(belltower_room, max_distance=5)
        
        if broadcast_fn and who_fn:
            active_players = who_fn()
            
            # Group players by room
            players_by_room = {}
            for player in active_players:
                loc_id = player.get("location", "town_square")
                if loc_id not in players_by_room:
                    players_by_room[loc_id] = []
                players_by_room[loc_id].append(player)
            
            # Send messages based on distance
            for room_id, distance in rooms_within:
                if room_id in players_by_room:
                    if distance == 0:
                        # In town square - direct message
                        message = f"[CYAN]The bell in the tower on the square tolls {hour_12h} time{'s' if hour_12h > 1 else ''}.[/CYAN]"
                    elif distance == 1:
                        # Very close
                        message = f"[CYAN]A bell tolls {hour_12h} time{'s' if hour_12h > 1 else ''} nearby, its sound clear and strong.[/CYAN]"
                    elif distance == 2:
                        # Close
                        message = f"[CYAN]A bell tolls {hour_12h} time{'s' if hour_12h > 1 else ''} in the distance, its sound carrying clearly.[/CYAN]"
                    elif distance == 3:
                        # Medium distance
                        message = f"[CYAN]A bell tolls {hour_12h} time{'s' if hour_12h > 1 else ''} in the distance.[/CYAN]"
                    elif distance == 4:
                        # Far
                        message = f"[CYAN]A faint bell tolls {hour_12h} time{'s' if hour_12h > 1 else ''} in the distance.[/CYAN]"
                    else:  # distance == 5
                        # Very far
                        message = f"[CYAN]A distant bell tolls {hour_12h} time{'s' if hour_12h > 1 else ''}, barely audible.[/CYAN]"
                    
                    broadcast_fn(room_id, message)
                    notifications.append((room_id, message))
    
    return notifications


def get_seasonal_room_overlay(room_def, season, weather_state):
    """
    Get seasonal overlay text based on room features.
    
    Args:
        room_def: Room definition dict
        season: Current season string
        weather_state: Current weather state dict
    
    Returns:
        str: Overlay text or empty string
    """
    features = room_def.get("features", [])
    if not features:
        return ""
    
    overlays = SEASONAL_OVERLAYS.get(season, {})
    if not overlays:
        return ""
    
    # Find matching feature
    for feature in features:
        if feature in overlays:
            messages = overlays[feature]
            return random.choice(messages)
    
    return ""


def has_npc_weather_status(npc_id):
    """
    Check if an NPC currently has weather status effects (wetness, cold, or heat > 0).
    This is a sanity check to ensure NPCs only react to weather if they're actually affected.
    
    Args:
        npc_id: NPC identifier
    
    Returns:
        bool: True if NPC has weather status effects, False otherwise
    """
    if npc_id not in NPC_STATE:
        return False
    
    npc_state = NPC_STATE[npc_id]
    if "weather_status" not in npc_state:
        return False
    
    status = npc_state["weather_status"]
    wetness = status.get("wetness", 0)
    cold = status.get("cold", 0)
    heat = status.get("heat", 0)
    
    # Check if any weather status is present
    return max(wetness, cold, heat) > 0


def get_npc_weather_reaction(npc_id, weather_state, season, check_status=True):
    """
    Get an NPC's reaction to current weather/season.
    
    Args:
        npc_id: NPC ID
        weather_state: Current weather state dict
        season: Current season string
        check_status: If True, only return reaction if NPC has weather status effects (default: True)
    
    Returns:
        str or None: Reaction message or None
    """
    # Sanity check: only react if NPC actually has weather status effects
    if check_status and not has_npc_weather_status(npc_id):
        return None
    
    wtype = weather_state.get("type", "clear")
    intensity = weather_state.get("intensity", "none")
    
    reactions = {
        "old_storyteller": {
            ("heatwave", "moderate"): "The Old Storyteller wipes sweat from his brow. 'These summers grow warmer every year,' he murmurs.",
            ("heatwave", "heavy"): "The Old Storyteller fans himself with a weathered hand. 'This heat is unbearable. I remember when summers were gentler.'",
            ("snow", "heavy"): "The Old Storyteller shivers slightly. 'Winter's grip tightens. Stay warm, traveler.'",
            ("rain", "heavy"): "The Old Storyteller pulls his robes closer. 'The rain tells stories of its own, if you know how to listen.'",
        },
        "innkeeper": {
            ("rain", "heavy"): "'Good night for staying inside,' Mara says, glancing toward the rain-streaked windows.",
            ("snow", "moderate"): "Mara looks out at the falling snow. 'At least it'll keep the troublemakers indoors tonight.'",
            ("heatwave", "moderate"): "Mara wipes her brow. 'This heat makes the ale taste better, at least.'",
        },
        "patrolling_guard": {
            ("rain", "moderate"): "The Patrolling Guard grumbles, adjusting their cloak. 'You'd think they'd issue us umbrellas for this job.'",
            ("sleet", "moderate"): "The Patrolling Guard shivers. 'This sleet is worse than snow. At least snow doesn't soak through everything.'",
            ("snow", "heavy"): "The Patrolling Guard stamps their feet. 'Standing watch in this weather is no joke.'",
        },
        "forest_spirit": {
            ("rain", "light"): "The Forest Spirit seems to dance with the falling rain, its form rippling with delight.",
            ("rain", "moderate"): "The Forest Spirit moves through the rain as if it were part of the water itself.",
            ("windy", "moderate"): "The Forest Spirit sways with the wind, its form blending with the rustling leaves.",
        },
        "nervous_farmer": {
            ("windy", "heavy"): "The Nervous Farmer peers anxiously at the trees. 'Wind like this always brings trouble from the woods,' they mutter.",
            ("storm", "moderate"): "The Nervous Farmer looks skyward nervously. 'Storms make the forest restless. Best stay away.'",
            ("snow", "heavy"): "The Nervous Farmer shivers. 'When the snow falls this heavy, you never know what's hiding beneath it.'",
        },
        "blacksmith": {
            ("snow", "moderate"): "The Blacksmith works the forge harder. 'At least the fire keeps me warm in this weather.'",
            ("heatwave", "moderate"): "The Blacksmith wipes sweat from their brow. 'This heat makes the forge unbearable, but work must go on.'",
        },
    }
    
    npc_reactions = reactions.get(npc_id, {})
    key = (wtype, intensity)
    
    if key in npc_reactions:
        return npc_reactions[key]
    
    return None


def update_player_weather_status(game):
    """
    Update player's weather exposure status based on current location and weather.
    
    Args:
        game: Player's game state dict (will be mutated)
    """
    if "weather_status" not in game:
        game["weather_status"] = {
            "wetness": 0,
            "cold": 0,
            "heat": 0,
            "last_update_tick": 0,
        }
    
    status = game["weather_status"]
    current_tick = get_current_game_tick()
    last_update = status.get("last_update_tick", 0)
    
    # Update every tick
    if current_tick <= last_update:
        return
    
    status["last_update_tick"] = current_tick
    
    # Get player's current room
    loc_id = game.get("location", "town_square")
    if loc_id not in WORLD:
        return
    
    room_def = WORLD[loc_id]
    is_outdoor = room_def.get("outdoor", False)
    
    if not is_outdoor:
        # Indoor: gradually decay all status
        if status["wetness"] > 0:
            status["wetness"] = max(0, status["wetness"] - 1)
        if status["cold"] > 0:
            status["cold"] = max(0, status["cold"] - 1)
        if status["heat"] > 0:
            status["heat"] = max(0, status["heat"] - 1)
        return
    
    # Outdoor: apply weather effects
    wtype = WEATHER_STATE.get("type", "clear")
    intensity = WEATHER_STATE.get("intensity", "none")
    temp = WEATHER_STATE.get("temperature", "mild")
    season = get_season()
    
    # Wetness from rain/snow/sleet
    if wtype in ["rain", "snow", "sleet"]:
        if intensity == "light":
            status["wetness"] = min(10, status["wetness"] + 1)
        elif intensity == "moderate":
            status["wetness"] = min(10, status["wetness"] + 2)
        elif intensity == "heavy":
            status["wetness"] = min(10, status["wetness"] + 3)
    else:
        # Gradually dry off if not in precipitation
        if status["wetness"] > 0:
            status["wetness"] = max(0, status["wetness"] - 1)
    
    # Cold from winter/snow/sleet/cold temps
    if season == "winter" or wtype in ["snow", "sleet"] or temp in ["cold", "chilly"]:
        if wtype == "snow" and intensity == "heavy":
            status["cold"] = min(10, status["cold"] + 2)
        elif temp == "cold":
            status["cold"] = min(10, status["cold"] + 1)
        else:
            status["cold"] = min(10, status["cold"] + 1)
    else:
        # Gradually warm up
        if status["cold"] > 0:
            status["cold"] = max(0, status["cold"] - 1)
    
    # Heat from summer/heatwave/hot temps
    if season == "summer" or wtype == "heatwave" or temp == "hot":
        if wtype == "heatwave" and intensity == "heavy":
            status["heat"] = min(10, status["heat"] + 2)
        elif temp == "hot":
            status["heat"] = min(10, status["heat"] + 1)
        else:
            status["heat"] = min(10, status["heat"] + 1)
    else:
        # Gradually cool down
        if status["heat"] > 0:
            status["heat"] = max(0, status["heat"] - 1)


def get_player_weather_description(game, pronouns=None):
    """
    Get weather condition description for a player.
    
    Args:
        game: Player's game state dict
        pronouns: Optional dict with "pronoun" key (default: "they")
    
    Returns:
        str: Weather description or empty string
    """
    if "weather_status" not in game:
        return ""
    
    status = game["weather_status"]
    pronoun = (pronouns or {}).get("pronoun", "they") if pronouns else "they"
    
    wetness = status.get("wetness", 0)
    cold = status.get("cold", 0)
    heat = status.get("heat", 0)
    
    # Find dominant condition
    max_condition = max(wetness, cold, heat)
    if max_condition == 0:
        return ""
    
    # Use proper verb conjugation based on pronoun
    if pronoun == "you":
        verb_look = "look"
        verb_be = "are"
        verb_have = "have"
    elif pronoun in ["he", "she", "it"]:
        verb_look = "looks"
        verb_be = "is"
        verb_have = "has"
    else:  # they
        verb_look = "look"
        verb_be = "are"
        verb_have = "have"
    
    # Generate description for dominant condition
    if wetness == max_condition:
        if wetness <= 2:
            if pronoun == "you":
                return "You look a bit damp."
            return f"{pronoun.capitalize()} {verb_look} a bit damp."
        elif wetness <= 4:
            if pronoun == "you":
                return "You can tell you have been standing in the rain for a while."
            return f"You can tell {pronoun} {verb_have} been standing in the rain for a while."
        elif wetness <= 7:
            if pronoun == "you":
                return "You look thoroughly soaked through."
            return f"{pronoun.capitalize()} {verb_look} thoroughly soaked through."
        else:
            if pronoun == "you":
                return "You are absolutely drenched from head to toe."
            return f"{pronoun.capitalize()} {verb_be} absolutely drenched from head to toe."
    elif cold == max_condition:
        if cold <= 2:
            if pronoun == "you":
                return "You look a little chilled."
            return f"{pronoun.capitalize()} {verb_look} a little chilled."
        elif cold <= 4:
            if pronoun == "you":
                return "You are shivering slightly in the cold."
            return f"{pronoun.capitalize()} {verb_be} shivering slightly in the cold."
        elif cold <= 7:
            if pronoun == "you":
                return "You look very cold and uncomfortable."
            return f"{pronoun.capitalize()} {verb_look} very cold and uncomfortable."
        else:
            if pronoun == "you":
                return "You are shivering violently, lips tinged blue."
            return f"{pronoun.capitalize()} {verb_be} shivering violently, lips tinged blue."
    else:  # heat
        if heat <= 2:
            if pronoun == "you":
                return "You look a touch flushed from the heat."
            return f"{pronoun.capitalize()} {verb_look} a touch flushed from the heat."
        elif heat <= 4:
            if pronoun == "you":
                return "A sheen of sweat glistens on your skin."
            return f"A sheen of sweat glistens on {pronoun} skin."
        elif heat <= 7:
            if pronoun == "you":
                return "You look overheated and unsteady."
            return f"{pronoun.capitalize()} {verb_look} overheated and unsteady."
        else:
            if pronoun == "you":
                return "You are drenched in sweat and look ready to collapse from the heat."
            return f"{pronoun.capitalize()} {verb_be} drenched in sweat and {verb_look} ready to collapse from the heat."


def get_npc_weather_description(npc_id, npc):
    """
    Get weather condition description for an NPC.
    
    Args:
        npc_id: NPC identifier
        npc: NPC object
    
    Returns:
        str: Weather description or empty string
    """
    if npc_id not in NPC_STATE:
        return ""
    
    state = NPC_STATE[npc_id]
    if "weather_status" not in state:
        return ""
    
    status = state["weather_status"]
    pronoun = getattr(npc, 'pronoun', 'they') if hasattr(npc, 'pronoun') else 'they'
    
    wetness = status.get("wetness", 0)
    cold = status.get("cold", 0)
    heat = status.get("heat", 0)
    
    # Find dominant condition
    max_condition = max(wetness, cold, heat)
    if max_condition == 0:
        return ""
    
    # Use proper verb conjugation based on pronoun
    if pronoun in ["he", "she", "it"]:
        verb_look = "looks"
        verb_be = "is"
        verb_have = "has"
    else:  # they
        verb_look = "look"
        verb_be = "are"
        verb_have = "have"
    
    # Generate description (same logic as player weather, but third person)
    if wetness == max_condition:
        if wetness <= 2:
            return f"{npc.name} {verb_look} a bit damp."
        elif wetness <= 4:
            return f"You can tell {npc.name} {verb_have} been standing in the rain for a while."
        elif wetness <= 7:
            return f"{npc.name} {verb_look} thoroughly soaked through."
        else:
            return f"{npc.name} {verb_be} absolutely drenched from head to toe."
    elif cold == max_condition:
        if cold <= 2:
            return f"{npc.name} {verb_look} a little chilled."
        elif cold <= 4:
            return f"{npc.name} {verb_be} shivering slightly in the cold."
        elif cold <= 7:
            return f"{npc.name} {verb_look} very cold and uncomfortable."
        else:
            return f"{npc.name} {verb_be} shivering violently, lips tinged blue."
    else:  # heat
        if heat <= 2:
            return f"{npc.name} {verb_look} a touch flushed from the heat."
        elif heat <= 4:
            return f"A sheen of sweat glistens on {npc.name}'s skin."
        elif heat <= 7:
            return f"{npc.name} {verb_look} overheated and unsteady."
        else:
            return f"{npc.name} {verb_be} drenched in sweat and {verb_look} ready to collapse from the heat."


def update_npc_weather_statuses():
    """
    Update weather exposure status for all NPCs based on their current location and weather.
    Similar to update_player_weather_status but for NPCs.
    """
    global NPC_STATE
    
    current_tick = get_current_game_tick()
    
    for npc_id, npc_state in NPC_STATE.items():
        # Initialize weather_status if not present
        if "weather_status" not in npc_state:
            npc_state["weather_status"] = {
                "wetness": 0,
                "cold": 0,
                "heat": 0,
                "last_update_tick": 0,
            }
        
        status = npc_state["weather_status"]
        last_update = status.get("last_update_tick", 0)
        
        # Update every tick
        if current_tick <= last_update:
            continue
        
        status["last_update_tick"] = current_tick
        
        # Get NPC's current room
        room_id = npc_state.get("room", "town_square")
        if room_id not in WORLD:
            continue
        
        room_def = WORLD[room_id]
        is_outdoor = room_def.get("outdoor", False)
        
        if not is_outdoor:
            # Indoor: gradually decay all status
            if status["wetness"] > 0:
                status["wetness"] = max(0, status["wetness"] - 1)
            if status["cold"] > 0:
                status["cold"] = max(0, status["cold"] - 1)
            if status["heat"] > 0:
                status["heat"] = max(0, status["heat"] - 1)
            continue
        
        # Outdoor: apply weather effects (same logic as players)
        wtype = WEATHER_STATE.get("type", "clear")
        intensity = WEATHER_STATE.get("intensity", "none")
        temp = WEATHER_STATE.get("temperature", "mild")
        season = get_season()
        
        # Wetness from rain/snow/sleet
        if wtype in ["rain", "snow", "sleet"]:
            if intensity == "light":
                status["wetness"] = min(10, status["wetness"] + 1)
            elif intensity == "moderate":
                status["wetness"] = min(10, status["wetness"] + 2)
            elif intensity == "heavy":
                status["wetness"] = min(10, status["wetness"] + 3)
        else:
            # Gradually dry off if not in precipitation
            if status["wetness"] > 0:
                status["wetness"] = max(0, status["wetness"] - 1)
        
        # Cold from winter/snow/sleet/cold temps
        if season == "winter" or wtype in ["snow", "sleet"] or temp in ["cold", "freezing"]:
            if intensity in ["moderate", "heavy"] or temp == "freezing":
                status["cold"] = min(10, status["cold"] + 2)
            else:
                status["cold"] = min(10, status["cold"] + 1)
        else:
            # Gradually warm up
            if status["cold"] > 0:
                status["cold"] = max(0, status["cold"] - 1)
        
        # Heat from summer/hot temps
        if season == "summer" or temp in ["hot", "scorching"]:
            if temp == "scorching":
                status["heat"] = min(10, status["heat"] + 3)
            elif temp == "hot":
                status["heat"] = min(10, status["heat"] + 2)
            else:
                status["heat"] = min(10, status["heat"] + 1)
        else:
            # Gradually cool down
            if status["heat"] > 0:
                status["heat"] = max(0, status["heat"] - 1)


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
                    "status": "idle",
                    "weather_status": {
                        "wetness": 0,
                        "cold": 0,
                        "heat": 0,
                        "last_update_tick": 0,
                    }
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


def resolve_room_detail(game, target_text):
    """
    Resolve a room detail/fixture target from user input.
    
    Args:
        game: Game state dict
        target_text: User input (e.g., "hammers", "anvils", "forge")
    
    Returns:
        tuple: (detail_id, detail_dict, room_id) or (None, None, None) if not found
    """
    loc_id = game.get("location", "town_square")
    
    if loc_id not in WORLD:
        return None, None, None
    
    room_def = WORLD[loc_id]
    details = room_def.get("details", {})
    
    target_lower = target_text.lower()
    
    # Search through all details
    for detail_id, detail in details.items():
        # Check detail ID
        if detail_id.lower() == target_lower:
            return detail_id, detail, loc_id
        
        # Check detail name
        detail_name = detail.get("name", "").lower()
        if detail_name == target_lower:
            return detail_id, detail, loc_id
        
        # Check aliases
        aliases = detail.get("aliases", [])
        for alias in aliases:
            if alias.lower() == target_lower:
                return detail_id, detail, loc_id
    
    return None, None, None


def invoke_room_detail_callback(action, game, username, room_id, detail_id):
    """
    Invoke a callback function for a room detail interaction.
    
    Args:
        action: The action being performed (e.g., "touch", "smell", "use", "on_look")
        game: The game state dictionary (can be mutated by callback)
        username: The username of the player
        room_id: The room ID where this detail is located
        detail_id: The detail ID that was interacted with
    
    Returns:
        str or None: Response message from callback, or None if no callback found/executed
    """
    if room_id not in WORLD:
        return None
    
    room = WORLD.get(room_id, {})
    details = room.get("details", {})
    detail = details.get(detail_id)
    
    if not detail:
        return None
    
    callbacks = detail.get("callbacks", {})
    callback_name = callbacks.get(action)
    
    if not callback_name:
        return None
    
    # Import room_callbacks module
    try:
        import room_callbacks
    except ImportError:
        # If module doesn't exist, return None gracefully
        return None
    
    # Resolve callback function
    callback_func = getattr(room_callbacks, callback_name, None)
    
    if not callback_func:
        # Callback function not found
        return None
    
    # Invoke callback
    try:
        result = callback_func(game, username, room_id, detail_id)
        return result
    except Exception as e:
        # Log error but don't crash - return generic error message
        print(f"Error invoking room detail callback {callback_name}: {e}", file=sys.stderr)
        return "Something unexpected happens, but you're not sure what."


def _format_detail_look(detail_id, detail, room_id, game=None):
    """
    Format a player-facing description of a room detail/fixture.
    
    Args:
        detail_id: The detail ID
        detail: The detail dict from room JSON
        room_id: The room ID (for context)
        game: Optional game state dict (for noticeboard quest display)
    
    Returns:
        str: Player-facing description
    """
    description = detail.get("description", "You see nothing special about it.")
    
    # Special handling for noticeboard - show quest postings
    detail_name_lower = detail.get("name", "").lower()
    if detail_id == "notice_board" or "notice board" in detail_name_lower or "noticeboard" in detail_name_lower:
        import quests
        from game_engine import GAME_TIME
        current_tick = GAME_TIME.get("tick", 0)
        
        if game is not None:
            # Get username from game state if available
            quest_username = game.get("username", "adventurer")
            # Pass who_fn if available (will need to be passed through function signature)
            # For now, we'll call without it and availability will work based on QUEST_GLOBAL_STATE
            available_quests = quests.get_noticeboard_quests_for_room(game, room_id, current_tick, username=quest_username)
            
            if available_quests:
                description += "\n\nSeveral notices are pinned to the board:"
                for idx, template in enumerate(available_quests, 1):
                    description += f"\n  {idx}. {template.name} ({template.difficulty})"
                    if template.timed:
                        description += f" - Time limit: {template.time_limit_minutes} minutes"
                description += "\n\n(Type 'read quest <number>' to read a posting, or 'take quest <number>' to accept it.)"
            else:
                description += "\n\nThe board is currently empty - no quests are posted right now."
    
    # Optionally add extra hints from stat block if relevant
    stat = detail.get("stat", {})
    extra_hints = []
    
    if stat.get("temperature") == "hot":
        extra_hints.append("It radiates heat.")
    elif stat.get("temperature") == "cold":
        extra_hints.append("It feels cold to the touch.")
    
    if stat.get("quality") == "well-used":
        extra_hints.append("It shows signs of frequent use.")
    
    if extra_hints:
        description += " " + " ".join(extra_hints)
    
    return description


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
        
        # Add weather description for NPCs
        weather_desc = get_npc_weather_description(npc_id, npc)
        if weather_desc:
            lines.append(weather_desc)
    
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
    
    # Add weather description (first person: "You look...")
    weather_desc = get_player_weather_description(game, pronouns={"pronoun": "you", "pronoun_cap": "You"})
    if weather_desc:
        lines.append(weather_desc)
    
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
        pronoun = "he"
        lines.append(f"{target_username} is an adventurer in Hollowvale.")
    
    # Add weather description for other player
    weather_desc = get_player_weather_description(target_game, pronouns={"pronoun": pronoun})
    if weather_desc:
        lines.append(weather_desc)
    
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


def _format_detail_stat(detail_id, detail, room_id):
    """
    Format an admin-facing detailed stat view of a room detail/fixture.
    
    Args:
        detail_id: Detail identifier
        detail: Detail dict from room JSON
        room_id: Room ID where this detail is located
    
    Returns:
        str: Admin stat view
    """
    lines = ["Room Detail/Fixture:"]
    lines.append(f"Room ID: {room_id}")
    lines.append(f"Detail ID: {detail_id}")
    lines.append(f"Name: {detail.get('name', detail_id)}")
    
    aliases = detail.get("aliases", [])
    if aliases:
        lines.append(f"Aliases: {', '.join(aliases)}")
    
    description = detail.get("description", "")
    if description:
        lines.append(f"Description: {description}")
    
    stat = detail.get("stat", {})
    if stat:
        lines.append("Stat properties:")
        for key, value in stat.items():
            lines.append(f"  {key}: {value}")
    
    callbacks = detail.get("callbacks", {})
    if callbacks:
        lines.append("Callbacks:")
        for action, callback_name in callbacks.items():
            lines.append(f"  {action}: {callback_name}")
    
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


# --- Exit Accessibility System ---
# Track dynamic exit states (locked, hidden, etc.)
# Format: {room_id: {direction: {locked: bool, hidden: bool, reason: str}}}
EXIT_STATES = {}


def is_exit_accessible(room_id, direction, actor_type="player", actor_id=None, game=None):
    """
    Check if an exit is accessible to an actor (player or NPC).
    
    Args:
        room_id: Room ID
        direction: Direction (e.g., "north", "south")
        actor_type: "player" or "npc"
        actor_id: Actor identifier (username or npc_id)
        game: Player's game state (for checking keys, abilities, etc.)
    
    Returns:
        tuple: (is_accessible: bool, reason: str or None)
    """
    if room_id not in WORLD:
        return False, "That room doesn't exist."
    
    room_def = WORLD[room_id]
    exits = room_def.get("exits", {})
    exit_def = exits.get(direction)
    
    if exit_def is None:
        return False, "You can't go that way."
    
    # Check dynamic exit state FIRST (locked/hidden by time or other conditions)
    # This applies to both string and dict exits
    if room_id in EXIT_STATES and direction in EXIT_STATES[room_id]:
        exit_state = EXIT_STATES[room_id][direction]
        if exit_state.get("locked", False):
            reason = exit_state.get("reason", "The way is locked.")
            return False, reason
        if exit_state.get("hidden", False):
            reason = exit_state.get("reason", "You don't see a way in that direction.")
            return False, reason
    
    # Handle string exits (backward compatible - accessible if not locked/hidden)
    if isinstance(exit_def, str):
        return True, None
    
    # Handle dict exits
    if not isinstance(exit_def, dict):
        return False, "You can't go that way."
    
    target = exit_def.get("target")
    if not target:
        return False, "You can't go that way."
    
    # Check static exit properties
    if exit_def.get("locked", False):
        # Check if actor has required key or ability
        key_required = exit_def.get("key_required")
        if key_required:
            if actor_type == "player" and game:
                inventory = game.get("inventory", [])
                if key_required not in inventory:
                    return False, f"You need a {key_required} to go that way."
            elif actor_type == "npc":
                # NPCs can have keys in their state or be exempt
                npc_can_unlock = exit_def.get("npc_can_unlock", False)
                if not npc_can_unlock:
                    return False, "The way is locked."
        else:
            return False, "The way is locked."
    
    if exit_def.get("hidden", False):
        # Check if actor has perception or ability to see hidden exits
        perception_required = exit_def.get("perception_required", 0)
        if actor_type == "player" and game:
            # For now, assume players can't see hidden exits without special ability
            # This can be extended later with perception stats
            return False, "You don't see a way in that direction."
        elif actor_type == "npc":
            npc_can_see = exit_def.get("npc_can_see_hidden", False)
            if not npc_can_see:
                return False, "The way is hidden."
    
    return True, None


def set_exit_state(room_id, direction, locked=None, hidden=None, reason=None):
    """
    Set the dynamic state of an exit (locked/hidden).
    
    Args:
        room_id: Room ID
        direction: Direction
        locked: Optional bool to set locked state
        hidden: Optional bool to set hidden state
        reason: Optional reason message
    """
    if room_id not in EXIT_STATES:
        EXIT_STATES[room_id] = {}
    if direction not in EXIT_STATES[room_id]:
        EXIT_STATES[room_id][direction] = {}
    
    if locked is not None:
        EXIT_STATES[room_id][direction]["locked"] = locked
    if hidden is not None:
        EXIT_STATES[room_id][direction]["hidden"] = hidden
    if reason:
        EXIT_STATES[room_id][direction]["reason"] = reason


def get_accessible_exits(room_id, actor_type="player", actor_id=None, game=None):
    """
    Get list of accessible exits for an actor.
    Ensures at least one exit is always available to prevent getting stuck.
    
    Args:
        room_id: Room ID
        actor_type: "player" or "npc"
        actor_id: Actor identifier
        game: Player's game state
    
    Returns:
        list: List of accessible direction strings
    """
    if room_id not in WORLD:
        return []
    
    room_def = WORLD[room_id]
    exits = room_def.get("exits", {})
    accessible = []
    
    for direction in exits.keys():
        is_accessible, _ = is_exit_accessible(room_id, direction, actor_type, actor_id, game)
        if is_accessible:
            accessible.append(direction)
    
    # Safety check: if no exits are accessible, make all exits accessible
    # This prevents actors from getting stuck
    if not accessible and exits:
        # Log this as a safety fallback
        import logging
        logging.warning(f"Safety fallback: All exits made accessible in {room_id} for {actor_type} {actor_id}")
        accessible = list(exits.keys())
    
    return accessible


# --- NPC Route System ---
# Define routes for NPCs that should move between rooms
# Format: {npc_id: [list of room_ids in order, cycling]}
NPC_ROUTES = {
    "patrolling_guard": ["town_square", "market_lane", "town_square", "forest_edge", "town_square"],
    "old_storyteller": ["town_square", "tavern", "town_square"],
    "darin": ["watchtower", "watchtower_path", "town_square", "watchtower_path", "watchtower"],
}

# Track NPC route positions (which room in their route they're at)
NPC_ROUTE_POSITIONS = {}


def get_npc_route(npc_id):
    """Get the route for an NPC, or None if they don't have one."""
    return NPC_ROUTES.get(npc_id)


def get_next_room_in_route(npc_id, current_room_id):
    """
    Get the next room in an NPC's route.
    
    Args:
        npc_id: NPC identifier
        current_room_id: Current room ID
    
    Returns:
        tuple: (next_room_id, direction) or (None, None) if no route or can't find path
    """
    route = get_npc_route(npc_id)
    if not route:
        return None, None
    
    # Find current position in route
    if npc_id not in NPC_ROUTE_POSITIONS:
        # Initialize to first room in route
        if current_room_id in route:
            NPC_ROUTE_POSITIONS[npc_id] = route.index(current_room_id)
        else:
            # Start at beginning
            NPC_ROUTE_POSITIONS[npc_id] = 0
    
    current_index = NPC_ROUTE_POSITIONS[npc_id]
    
    # Check if NPC is at expected position
    if current_room_id != route[current_index]:
        # NPC is off-route, find nearest route point
        if current_room_id in route:
            NPC_ROUTE_POSITIONS[npc_id] = route.index(current_room_id)
            current_index = NPC_ROUTE_POSITIONS[npc_id]
        else:
            # Not on route at all, try to find path to route
            # For now, just move to next route point
            pass
    
    # Get next room in route (cycle)
    next_index = (current_index + 1) % len(route)
    next_room_id = route[next_index]
    
    # Find direction from current room to next room
    if current_room_id not in WORLD or next_room_id not in WORLD:
        return None, None
    
    current_room = WORLD[current_room_id]
    exits = current_room.get("exits", {})
    
    # Find direction that leads to next room
    for direction, target_room in exits.items():
        # Check if exit is accessible for NPCs
        is_accessible, _ = is_exit_accessible(current_room_id, direction, "npc", npc_id, None)
        if not is_accessible:
            continue
        
        # Handle both string and dict exits
        if isinstance(target_room, str):
            if target_room == next_room_id:
                return next_room_id, direction
        elif isinstance(target_room, dict):
            if target_room.get("target") == next_room_id:
                return next_room_id, direction
    
    # If no direct exit, try to find path (for now, return None)
    return None, None


def move_npc_along_route(npc_id, broadcast_fn=None):
    """
    Move an NPC along their route if they have one.
    
    Args:
        npc_id: NPC identifier
        broadcast_fn: Optional callback(room_id: str, text: str) for broadcasting
    
    Returns:
        bool: True if NPC was moved, False otherwise
    """
    if npc_id not in NPC_STATE:
        return False
    
    npc_state = NPC_STATE[npc_id]
    current_room_id = npc_state.get("room")
    
    if not current_room_id:
        return False
    
    next_room_id, direction = get_next_room_in_route(npc_id, current_room_id)
    
    if not next_room_id or not direction:
        return False
    
    # Move NPC
    old_room_id = current_room_id
    npc_state["room"] = next_room_id
    
    # Update route position
    route = get_npc_route(npc_id)
    if route:
        NPC_ROUTE_POSITIONS[npc_id] = route.index(next_room_id)
    
    # Get NPC name
    from npc import NPCS
    npc = NPCS.get(npc_id)
    npc_name = npc.name if npc else npc_id
    
    # Broadcast exit message to old room
    if broadcast_fn:
        exit_msg = get_entrance_exit_message(old_room_id, next_room_id, direction, npc_name, is_exit=True, is_npc=True)
        if exit_msg:
            broadcast_fn(old_room_id, exit_msg)
    
    # Broadcast entrance message to new room
    if broadcast_fn:
        opposite_direction = OPPOSITE_DIRECTION.get(direction, "somewhere")
        entrance_msg = get_entrance_exit_message(next_room_id, old_room_id, opposite_direction, npc_name, is_exit=False, is_npc=True)
        if entrance_msg:
            broadcast_fn(next_room_id, entrance_msg)
    
    return True


def process_npc_movements(broadcast_fn=None):
    """
    Process NPC movements along their routes.
    Moves NPCs periodically based on elapsed time.
    
    Args:
        broadcast_fn: Optional callback(room_id: str, text: str) for broadcasting
    """
    global NPC_ROUTE_POSITIONS, GAME_TIME
    
    current_tick = GAME_TIME.get("tick", 0)
    
    # Initialize last movement tick tracking if needed
    if not hasattr(process_npc_movements, "last_movement_tick"):
        process_npc_movements.last_movement_tick = {}
    
    last_movement_tick = process_npc_movements.last_movement_tick
    
    # NPCs move every 30-60 ticks (30-60 commands)
    movement_interval = 45
    
    for npc_id in NPC_ROUTES.keys():
        if npc_id not in NPC_STATE:
            continue
        
        last_tick = last_movement_tick.get(npc_id, 0)
        elapsed = current_tick - last_tick
        
        if elapsed >= movement_interval:
            # Try to move NPC
            if move_npc_along_route(npc_id, broadcast_fn=broadcast_fn):
                last_movement_tick[npc_id] = current_tick


def process_time_based_exit_states(broadcast_fn=None, who_fn=None):
    """
    Process time-based exit state changes (e.g., tavern door locking/unlocking).
    Handles Mara's closing/opening behavior at 1am and 10am.
    
    Args:
        broadcast_fn: Optional callback(room_id: str, text: str) for broadcasting
        who_fn: Optional callback() -> list[dict] for getting active players
    """
    global EXIT_STATES, GAME_TIME
    
    current_tick = get_current_game_tick()
    # Use the same time system as the time display (GAME_TIME, not WORLD_CLOCK)
    # This ensures door locking matches what players see when they check the time
    current_minutes = get_current_hour_in_minutes()
    hour_of_day = int(current_minutes // MINUTES_PER_HOUR) % 24
    
    # Track last processed hour to avoid duplicate messages
    if not hasattr(process_time_based_exit_states, "last_processed_hour"):
        process_time_based_exit_states.last_processed_hour = {}
    
    last_hour = process_time_based_exit_states.last_processed_hour
    
    # Tavern door: Lock at 1am, unlock at 10am
    # The door should remain locked between 1am and 10am
    tavern_room_id = "tavern"
    tavern_door_direction = "north"  # Door to town square
    town_square_to_tavern = "south"  # Entrance from town_square to tavern
    
    # Determine if door should be locked (between 1am and 10am, inclusive of 1am, exclusive of 10am)
    should_be_locked = (hour_of_day >= 1 and hour_of_day < 10)
    
    # Check current door state - both doors should be checked independently
    tavern_exit_state = EXIT_STATES.get(tavern_room_id, {}).get(tavern_door_direction, {})
    town_square_exit_state = EXIT_STATES.get("town_square", {}).get(town_square_to_tavern, {})
    tavern_door_locked = tavern_exit_state.get("locked", False)
    town_square_door_locked = town_square_exit_state.get("locked", False)
    both_doors_locked = tavern_door_locked and town_square_door_locked
    
    # Always ensure door state is correct for the current hour
    if should_be_locked:
        # Door should be locked - ensure both doors are locked
        if not tavern_door_locked:
            set_exit_state(tavern_room_id, tavern_door_direction, locked=True,
                          reason="The heavy wooden door is locked for the night.")
        if not town_square_door_locked:
            set_exit_state("town_square", town_square_to_tavern, locked=True,
                          reason="The heavy wooden door is locked for the night.")
    else:
        # Door should be unlocked - ensure both doors are unlocked
        if tavern_door_locked:
            set_exit_state(tavern_room_id, tavern_door_direction, locked=False)
        if town_square_door_locked:
            set_exit_state("town_square", town_square_to_tavern, locked=False)
    
    # Check if we need to lock the door (1am transition) - for special events
    if hour_of_day == 1 and last_hour.get("tavern_locked") != 1:
        # Lock the door FROM tavern (north exit to town_square)
        set_exit_state(tavern_room_id, tavern_door_direction, locked=True, 
                      reason="The heavy wooden door is locked for the night.")
        # Also lock the entrance TO tavern from town_square (south exit)
        set_exit_state("town_square", town_square_to_tavern, locked=True,
                      reason="The heavy wooden door is locked for the night.")
        last_hour["tavern_locked"] = 1
        
        # Mara kicks everyone out and says closing message
        if broadcast_fn and who_fn:
            # Get all players in the tavern
            active_players = who_fn()
            players_in_tavern = [p for p in active_players if p.get("location") == tavern_room_id]
            
            # Mara's closing message
            closing_message = "[CYAN]Mara calls out: 'Alright, everyone out! The tavern's closed for the night. Come back in the morning!'[/CYAN]"
            broadcast_fn(tavern_room_id, closing_message)
            
            # Move all players to town square (graceful - they can't get stuck)
            from app import ACTIVE_GAMES
            for player in players_in_tavern:
                username = player.get("username")
                if username and username in ACTIVE_GAMES:
                    player_game = ACTIVE_GAMES[username]
                    old_loc = player_game.get("location")
                    player_game["location"] = "town_square"
                    
                    # Broadcast exit message
                    exit_msg = get_entrance_exit_message(old_loc, "town_square", "north", 
                                                        username, is_exit=True, is_npc=False)
                    if exit_msg:
                        broadcast_fn(old_loc, exit_msg)
                    
                    # Broadcast entrance message
                    entrance_msg = get_entrance_exit_message("town_square", old_loc, "south", 
                                                            username, is_exit=False, is_npc=False)
                    if entrance_msg:
                        broadcast_fn("town_square", entrance_msg)
                    
                    # Add message to player's log
                    player_game.setdefault("log", [])
                    player_game["log"].append("[CYAN]Mara ushers you out of the tavern, closing the door behind you.[/CYAN]")
                    player_game["log"] = player_game["log"][-50:]
            
            # Move NPCs out of tavern (except Mara, who stays)
            npc_ids = get_npcs_in_room(tavern_room_id)
            for npc_id in npc_ids:
                if npc_id != "innkeeper":  # Mara stays
                    npc_state = NPC_STATE.get(npc_id, {})
                    if npc_state.get("room") == tavern_room_id:
                        # Move NPC to town square
                        move_npc(npc_id, "town_square", from_room_id=tavern_room_id, 
                                direction="north", broadcast_fn=broadcast_fn)
    
    # Check if we need to unlock the door (10am transition)
    elif hour_of_day == 10 and last_hour.get("tavern_unlocked") != 10:
        # Unlock the door FROM tavern (north exit to town_square)
        set_exit_state(tavern_room_id, tavern_door_direction, locked=False)
        # Also unlock the entrance TO tavern from town_square (south exit)
        set_exit_state("town_square", town_square_to_tavern, locked=False)
        last_hour["tavern_unlocked"] = 10
        # Clear the locked flag so it can lock again the next night
        if "tavern_locked" in last_hour:
            del last_hour["tavern_locked"]
        
        # Mara's opening message
        if broadcast_fn:
            opening_message = "[CYAN]Mara calls out: 'The tavern's open! Come on in, travelers!'[/CYAN]"
            broadcast_fn(tavern_room_id, opening_message)
            # Also broadcast to town square so people know
            broadcast_fn("town_square", opening_message)
    
    # Update last processed hour
    process_time_based_exit_states.last_processed_hour = last_hour


def move_npc(npc_id, new_room_id, from_room_id=None, direction=None, is_teleport=False, broadcast_fn=None):
    """
    Move an NPC to a new room, with optional entrance/exit messages.
    
    Args:
        npc_id: NPC identifier
        new_room_id: Target room ID
        from_room_id: Source room ID (for exit message)
        direction: Direction of movement (for messages)
        is_teleport: If True, this is a teleport (admin) and uses different messages
        broadcast_fn: Optional callback(room_id: str, text: str) for broadcasting
    """
    if npc_id not in NPC_STATE:
        return
    
    npc_state = NPC_STATE[npc_id]
    old_room_id = npc_state.get("room")
    
    # Update NPC location
    npc_state["room"] = new_room_id
    
    # Get NPC name
    from npc import NPCS
    npc = NPCS.get(npc_id)
    npc_name = npc.name if npc else npc_id
    
    # Broadcast exit message from old room
    if broadcast_fn and old_room_id and old_room_id != new_room_id:
        if is_teleport:
            exit_msg = f"[CYAN]{npc_name} vanishes.[/CYAN]"
        elif direction:
            exit_msg = get_entrance_exit_message(old_room_id, new_room_id, direction, npc_name, is_exit=True, is_npc=True)
        else:
            exit_msg = f"[CYAN]{npc_name} leaves.[/CYAN]"
        
        if exit_msg:
            broadcast_fn(old_room_id, exit_msg)
    
    # Broadcast entrance message to new room
    if broadcast_fn and new_room_id:
        if is_teleport:
            entrance_msg = f"[CYAN]{npc_name} appears suddenly.[/CYAN]"
        elif direction:
            opposite_direction = OPPOSITE_DIRECTION.get(direction, "somewhere")
            entrance_msg = get_entrance_exit_message(new_room_id, old_room_id, opposite_direction, npc_name, is_exit=False, is_npc=True)
        else:
            entrance_msg = f"[CYAN]{npc_name} arrives.[/CYAN]"
        
        if entrance_msg:
            broadcast_fn(new_room_id, entrance_msg)


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
        "npc_cooldowns": {},  # Track NPC interaction cooldowns: {npc_id: {"no_talk_until_tick": int}}
        "notify": {
            "login": False,  # player can enable with 'notify login'
            "time": False,  # player can enable with 'notify time'
        },
        "weather_status": {
            "wetness": 0,
            "cold": 0,
            "heat": 0,
            "last_update_tick": 0,
        },
        "quests": {},  # Active quest instances: {quest_id: instance_dict}
        "completed_quests": {},  # Completed/failed quests: {quest_id: instance_dict}
        "pending_quest_offer": None,  # Pending quest offer: {quest_id, source, offered_at_tick}
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
    
    # Get current in-game time using the same system as format_time_message
    # Use get_current_hour_in_minutes() for consistency
    current_minutes = get_current_hour_in_minutes()
    hour_24h = int(current_minutes // MINUTES_PER_HOUR)
    minutes = int(current_minutes % MINUTES_PER_HOUR)
    
    # Determine AM/PM and format hour for 12-hour display
    period = "AM" if hour_24h < 12 else "PM"
    display_hour = hour_24h if hour_24h <= 12 else hour_24h - 12
    if display_hour == 0:
        display_hour = 12
    
    # Format time string with exact minutes (e.g., "6:05AM", "12:30PM")
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
    # describe_location returns a formatted string with room name, description, exits, items, NPCs
    # We want to add it as-is to the log
    room_description = describe_location(game)
    # describe_location returns a single string, so add it directly
    if isinstance(room_description, str):
        game["log"].append(room_description)


# generate_npc_line moved to npc.py

def handle_emote(verb, args, game, username=None, broadcast_fn=None, who_fn=None):
    """
    Handle social/emote verbs like 'nod' or 'smile'.
    
    Args:
        verb: The command word, e.g. 'nod'
        args: List of remaining tokens, e.g. ['guard']
        game: The game state dictionary
        username: Optional username of the player
        broadcast_fn: Optional callback(room_id: str, text: str) for broadcasting to room
        who_fn: Optional callback() -> list[dict] for getting active players
    
    Returns:
        tuple: (response_string, updated_game_state)
    """
    # Look up verb in EMOTES
    if verb not in EMOTES:
        return "You flail about uncertainly.", game
    
    # Determine actor name and possessive form
    actor_name = username or "Someone"
    # Simple possessive: add 's to name (works for most names)
    actor_possessive = actor_name + "'s" if actor_name != "Someone" else "their"
    loc_id = game.get("location", "town_square")
    
    # No target (e.g. command is just "nod")
    if not args:
        response = EMOTES[verb]["self"]
        # Broadcast emote to other players in the room
        if broadcast_fn is not None and loc_id in WORLD:
            room_message = EMOTES[verb]["room"].format(actor=actor_name, actor_possessive=actor_possessive)
            broadcast_fn(loc_id, room_message)
        return response, game
    
    # With target (e.g. "nod guard" or "nod watch guard")
    target_text = " ".join(args).lower()
    
    if loc_id not in WORLD:
        return "You feel disoriented for a moment.", game
    
    room_def = WORLD[loc_id]
    npc_ids = get_npcs_in_room(loc_id)
    
    # Use centralized NPC matching
    matched_npc_id, matched_npc = match_npc_in_room(npc_ids, target_text)
    
    if matched_npc:
        # Targeting an NPC
        target_name = matched_npc.name or matched_npc.title or "someone"
        
        # Generate player view using self_target template
        player_view = EMOTES[verb]["self_target"].format(target=target_name)
        
        # Broadcast player emote to other players in the room
        if broadcast_fn is not None:
            room_message = EMOTES[verb]["room_target"].format(actor=actor_name, actor_possessive=actor_possessive, target=target_name)
            broadcast_fn(loc_id, room_message)
        
        # Get NPC reaction if available
        reaction = get_npc_reaction(matched_npc_id, verb)
        
        if reaction:
            response = player_view + "\n" + reaction
            # Broadcast NPC reaction to all players in the room
            if broadcast_fn is not None:
                broadcast_fn(loc_id, reaction)
        else:
            response = player_view
        
        return response, game
    
    # Not an NPC - check if it's another player
    if who_fn is not None:
        active_players = who_fn()
        for player_info in active_players:
            player_username = player_info.get("username", "")
            if player_username.lower() == target_text and player_info.get("location") == loc_id and player_username != username:
                # Found another player in the same room
                target_name = player_username
                
                # Generate player view using self_target template
                player_view = EMOTES[verb]["self_target"].format(target=target_name)
                
                # Broadcast to other players (including the target)
                if broadcast_fn is not None:
                    # General room message for everyone (including the target)
                    room_message = EMOTES[verb]["room_target"].format(actor=actor_name, actor_possessive=actor_possessive, target=target_name)
                    broadcast_fn(loc_id, room_message)
                    # Note: For a personalized "nods at you" message, we'd need to enhance
                    # broadcast_to_room in app.py to handle target-specific messages
                
                response = player_view
                return response, game
    
    # Invalid target
    return "You do not see anyone like that here.", game


def get_entrance_exit_message(room_id, from_room_id, direction, actor_name, is_exit=True, is_npc=False, custom_message=None, is_teleport=False):
    """
    Get entrance or exit message for a room.
    
    Args:
        room_id: The room ID
        from_room_id: The room being left/entered from
        direction: The direction (e.g., "north", "south")
        actor_name: Name of the actor (player or NPC)
        is_exit: If True, this is an exit message; if False, entrance message
        is_npc: If True, actor is an NPC; if False, player
        custom_message: Optional custom message override
        is_teleport: If True, this is a teleport (admin goto)
    
    Returns:
        str: Formatted message (with [CYAN] tags for NPCs, HTML for players)
    """
    if custom_message:
        return custom_message
    
    # Handle teleport messages
    if is_teleport:
        if is_exit:
            return f"[CYAN]{actor_name} vanishes in a flash of light.[/CYAN]"
        else:
            return f"[CYAN]{actor_name} appears suddenly from nowhere.[/CYAN]"
    
    if room_id not in WORLD:
        # Fallback
        if is_exit:
            return f"{actor_name} leaves {direction}." if is_npc else f"[CYAN]{actor_name} leaves {direction}.[/CYAN]"
        else:
            return f"{actor_name} arrives from the {direction}." if is_npc else f"[CYAN]{actor_name} arrives from the {direction}.[/CYAN]"
    
    room_def = WORLD[room_id]
    
    # Check for custom entrance/exit messages
    if is_exit:
        exit_messages = room_def.get("exit_messages", {})
        if direction in exit_messages:
            msg_template = exit_messages[direction]
            if callable(msg_template):
                msg = msg_template(actor_name, direction, is_npc)
            else:
                msg = msg_template.format(actor=actor_name, direction=direction)
        else:
            # Default exit message
            msg = f"{actor_name} leaves {direction}."
    else:
        entrance_messages = room_def.get("entrance_messages", {})
        if direction in entrance_messages:
            msg_template = entrance_messages[direction]
            if callable(msg_template):
                msg = msg_template(actor_name, direction, is_npc)
            else:
                msg = msg_template.format(actor=actor_name, direction=direction)
        else:
            # Default entrance message
            room_name = room_def.get("name", room_id)
            # Try to make it contextual
            if is_teleport:
                # Teleport entrance message (will be overridden by custom message if set)
                msg = f"{actor_name} appears suddenly."
            elif "tavern" in room_id.lower():
                msg = f"{actor_name} enters the tavern, closing the heavy wooden door behind {'him' if is_npc else 'you'}."
            elif "smithy" in room_id.lower():
                msg = f"{actor_name} enters the smithy, the sound of the forge filling the air."
            elif "watchtower" in room_id.lower():
                msg = f"{actor_name} climbs up into the watchtower."
            else:
                msg = f"{actor_name} arrives from the {direction}."
    
    # Format based on actor type
    if is_npc:
        return f"[CYAN]{msg}[/CYAN]"
    else:
        return f'<span style="color: #006400;">{msg}</span>'


def get_movement_message(target_room_id, direction):
    """
    Get the movement message when entering a room (for player's own movement).
    
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
    Uses seasonal sunrise/sunset times.
    
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
    
    # Get current time using GAME_TIME (tick-based system)
    current_minutes = get_current_hour_in_minutes()
    hour_24h = int(current_minutes // MINUTES_PER_HOUR)
    minutes = int(current_minutes % MINUTES_PER_HOUR)
    
    # Determine AM/PM and format hour for 12-hour display
    period = "AM" if hour_24h < 12 else "PM"
    display_hour = hour_24h if hour_24h <= 12 else hour_24h - 12
    if display_hour == 0:
        display_hour = 12
    
    # Format time string with exact minutes (e.g., "6:05AM", "12:30PM")
    time_str = f"{display_hour}:{minutes:02d}{period}"
    
    # Get time of day, season, month, and day info
    time_of_day = get_time_of_day()
    season = get_season()
    season_name = season.capitalize()
    month = get_month()
    day_of_month = get_day_of_month()
    day_of_year = get_day_of_year()
    
    # Format date string (e.g., "Day 45 of Firstmoon, Spring")
    date_str = f"Day {day_of_month} of {month}, {season_name}"
    
    # Create creative messages with variations
    # Only include bell-related messages if it's actually on the hour (minute 0)
    # Otherwise, the actual bell tolling is handled by check_bell_tolling()
    messages = []
    
    if minutes == 0:
        # On the hour - bell messages are appropriate
        messages.extend([
            f"At the third stroke, the clock in {location_name} will strike {time_str}.",
            f"The bells of {location_name} chime, marking the hour of {time_str}.",
            f"You hear the distant tolling of a bell: it is {time_str} in {location_name}.",
        ])
    
    # Always include non-bell messages with date info
    messages.extend([
        f"A voice calls out from somewhere nearby: 'The time in {location_name} is {time_str}. It is {date_str}.'",
        f"Glancing at the sky, you estimate it to be {time_str} in {location_name}. Today is {date_str}.",
        f"The shadows and light tell you it is {time_str} in {location_name}. The calendar shows it is {date_str}.",
        f"You check the time: it is {time_str} in {location_name}. The date is {date_str}.",
        f"The position of the sun tells you it is {time_str} in {location_name}. It is {date_str}.",
    ])
    
    # Add time-of-day specific messages with date info
    if time_of_day == "dawn":
        messages.extend([
            f"In the pale light of dawn, the time in {location_name} is {time_str}. Today is {date_str}.",
            f"As the sun rises, you know it is {time_str} in {location_name}. It is {date_str}.",
        ])
    elif time_of_day == "day":
        messages.extend([
            f"Under the bright {season_name} sun, the time in {location_name} is {time_str}. Today is {date_str}.",
            f"The sun's position confirms it is {time_str} in {location_name}. The date is {date_str}.",
        ])
    elif time_of_day == "dusk":
        messages.extend([
            f"As evening approaches, the time in {location_name} is {time_str}. Today is {date_str}.",
            f"In the fading light, you know it is {time_str} in {location_name}. It is {date_str}.",
        ])
    else:  # night
        messages.extend([
            f"Beneath the {season_name} night sky, the time in {location_name} is {time_str}. Today is {date_str}.",
            f"The moon and stars mark the hour as {time_str} in {location_name}. The date is {date_str}.",
        ])
    
    # Use deterministic selection based on hour to avoid randomness
    message_index = hour_24h % len(messages)
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

    # Get time-appropriate description
    time_of_day = get_time_of_day()
    descriptions_by_time = room_def.get("descriptions_by_time", {})
    
    # Use time-specific description if available, otherwise fall back to base description
    if descriptions_by_time and time_of_day in descriptions_by_time:
        desc = descriptions_by_time[time_of_day]
    else:
        desc = room_def["description"]
    
    # Apply weather-aware modifications to the description (for outdoor rooms)
    if room_def.get("outdoor", False):
        desc = apply_weather_to_description(desc, time_of_day)
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

    # Get combined time-of-day/moon/weather description (replaces room title and weather line)
    is_outdoor = room_def.get("outdoor", False)
    combined_time_weather = get_combined_time_weather_description(is_outdoor=is_outdoor)
    
    # Style the combined time/weather description in dark yellow (#b8860b)
    combined_time_weather_text = f"<span style='color: #b8860b;'>{combined_time_weather}</span>"
    
    # Get seasonal overlay for outdoor rooms
    seasonal_overlay = ""
    npc_weather_reaction = ""
    
    if room_def.get("outdoor", False):
        # Get seasonal overlay
        season = get_season()
        seasonal_overlay = get_seasonal_room_overlay(room_def, season, WEATHER_STATE)
        
        # Occasionally add NPC weather reaction (10% chance)
        # Only show if NPC actually has weather status effects
        if npc_ids and random.random() < 0.1:
            for npc_id in npc_ids:
                # Sanity check: only show reaction if NPC actually has weather status effects
                if has_npc_weather_status(npc_id):
                    reaction = get_npc_weather_reaction(npc_id, WEATHER_STATE, season, check_status=True)
                    if reaction:
                        npc_weather_reaction = reaction
                        break
    
    # Format exits line properly
    exit_list = list(room_def["exits"].keys())
    if len(exit_list) == 0:
        exits_text = "There are no obvious exits."
    elif len(exit_list) == 1:
        exits_text = f"There is one obvious exit: {exit_list[0]}."
    elif len(exit_list) == 2:
        exits_text = f"There are two obvious exits: {exit_list[0]} and {exit_list[1]}."
    else:
        # Format: "There are X obvious exits: dir1, dir2, dir3 and dir4."
        all_but_last = ", ".join(exit_list[:-1])
        exits_text = f"There are {len(exit_list)} obvious exits: {all_but_last} and {exit_list[-1]}."
    
    # Style exits text in dark green (#006400)
    exits_text = f"<span style='color: #006400;'>{exits_text}</span>"
    
    # Combine all parts (room title removed, replaced with combined time/weather description)
    parts = [
        desc,  # Room description
    ]
    
    # Add seasonal overlay after main description
    if seasonal_overlay:
        parts.append(seasonal_overlay)
    
    # Add combined time-of-day/weather/moon description (styled dark yellow)
    parts.append(combined_time_weather_text)
    
    # Add exits (styled dark green)
    parts.append(exits_text)
    
    # Add items
    parts.append(items_text)
    
    # Add NPCs
    if npcs_text:
        parts.append(npcs_text)
    
    # Add NPC weather reaction if present
    if npc_weather_reaction:
        parts.append(npc_weather_reaction)
    
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
    # Get NPC name (handle both NPC objects and dicts for backwards compatibility)
    npc = NPCS.get(npc_id)
    if npc:
        if hasattr(npc, 'name'):
            npc_name = npc.name
        else:
            npc_name = npc.get('name', 'them') if isinstance(npc, dict) else 'them'
    else:
        npc_name = 'them'
    
    message = None
    if amount > 0:
        if amount >= 20:
            message = f"Your reputation with {npc_name} has greatly improved!"
        elif amount >= 10:
            message = f"Your reputation with {npc_name} has significantly improved."
        elif amount >= 5:
            message = f"Your reputation with {npc_name} has improved."
        else:
            message = None  # Small changes don't need messages to avoid spam
    elif amount < 0:
        if amount <= -20:
            message = f"Your reputation with {npc_name} has greatly deteriorated!"
        elif amount <= -10:
            message = f"Your reputation with {npc_name} has significantly worsened."
        elif amount <= -5:
            message = f"Your reputation with {npc_name} has worsened."
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


def _get_npc_charity_system_prompt(items_text, reputation, personality):
    """Load and format the NPC charity decision system prompt."""
    fallback = f"""You are a merchant NPC analyzing a player's message to determine if they are asking for help because they cannot afford something.

Available items for sale:
{items_text}

Player's current reputation with you: {reputation} (range: -100 to +200)
- Reputation >= 50: Very strong positive relationship - you trust and like them a great deal
- Reputation >= 25: Positive relationship - you trust and like them
- Reputation >= 15: Moderately positive impression - you think well of them
- Reputation >= 10: Slightly positive impression - they seem decent
- Reputation > 0: Neutral-to-positive impression
- Reputation == 0: You don't know them well yet
- Reputation < 0: Negative impression - you're wary or dislike them

Your task:
1. Determine if the player is expressing that they CANNOT AFFORD something (not just complaining about price)
2. If yes, identify which item they're referring to (use the exact 'key' from the list above, or null if not specified)
3. Based on your reputation with them, decide if you want to help them:
   - High reputation (>= 50): You might give them the item for free, acknowledging your relationship
   - Medium reputation (15-49): You might give them a cheaper item or express sympathy but decline
   - Low reputation (0-14): You express sympathy but explain you have a business to run
   - Negative reputation (< 0): You dismiss them or tell them to leave

IMPORTANT:
- Only help if the player is genuinely expressing inability to afford (not just haggling)
- Examples of "can't afford" pleas: "I can't afford that", "I'm so hungry but I don't have enough", "I really need this but I'm broke"
- Examples of NOT "can't afford": "That's too expensive", "Can you lower the price?", "I want a discount"
- If item is not specified, you can choose an appropriate item to give (e.g., cheapest item, most basic food item)
- You can only give ONE item per request (quantity always 1 for charity)
- Be in character - your personality is: {personality}

Return your response as JSON only, in this exact format:
{{"is_plea": true/false, "item_key": "item_key_or_null", "will_help": true/false, "reason": "brief explanation of your decision"}}

If is_plea is false, set item_key to null, will_help to false, and reason to empty string."""
    
    return load_prompt("npc_charity_system.txt", fallback_text=fallback, items_text=items_text, reputation=reputation, personality=personality)


def _get_npc_charity_user_message(text, reputation):
    """Load and format the NPC charity user message."""
    fallback = f"Player message: \"{text}\"\n\nAnalyze this message to determine if the player is asking for help because they cannot afford something. Consider their reputation with you ({reputation}) when deciding whether to help.\n\nReturn JSON with your analysis and decision."
    return load_prompt("npc_charity_user.txt", fallback_text=fallback, text=text, reputation=reputation)


def _parse_charity_plea_ai(text, merchant_items, npc, room_def, game, username, user_id=None, db_conn=None, npc_id=None):
    """
    Use AI to detect if player is making a "can't afford" plea and if NPC will help.
    Also checks if player actually has enough money (scam detection).
    
    Returns: (is_plea, item_key, will_help, reason, is_scam) or (False, None, False, "", False)
    """
    if not generate_npc_reply:
        return False, None, False, "", False
    
    # Get reputation
    reputation = game.get("reputation", {}).get(npc_id, 0) if npc_id else 0
    
    # Get player's current currency
    from economy.currency import get_currency, format_currency, currency_to_copper, copper_to_currency
    from economy.economy_manager import get_item_price
    
    player_currency = get_currency(game)
    player_currency_formatted = format_currency(player_currency)
    player_total_copper = currency_to_copper(player_currency)
    
    # Build list of available items for the AI, including whether player can afford each
    items_list = []
    for item_key, item_info in merchant_items.items():
        display_name = item_info.get("display_name", item_key.replace("_", " "))
        try:
            if npc_id:
                price_copper = get_item_price(item_key, npc_id, game)
                price_currency = copper_to_currency(price_copper)
                price_str = format_currency(price_currency)
                can_afford = player_total_copper >= price_copper
                affordability = "can afford" if can_afford else "cannot afford"
            else:
                price_str = "varies"
                affordability = "unknown"
        except Exception:
            price_str = "varies"
            affordability = "unknown"
        items_list.append(f"- {display_name} (key: {item_key}, price: {price_str}, player {affordability})")
    
    items_text = "\n".join(items_list)
    
    # Get NPC personality
    personality = npc.personality if hasattr(npc, 'personality') else npc.get('personality', 'friendly')
    
    # Create AI prompt for charity decision
    try:
        from ai_client import OpenAI, OPENAI_AVAILABLE
        if not OPENAI_AVAILABLE:
            return False, None, False, "", False
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        system_prompt = _get_npc_charity_system_prompt(items_text, reputation, personality, player_currency_formatted)
        user_message = _get_npc_charity_user_message(text, reputation, player_currency_formatted)
        
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            temperature=0.7,  # Slightly higher for more natural decisions
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        import re
        
        json_match = re.search(r'\{[^}]+\}', ai_response)
        if json_match:
            result = json.loads(json_match.group(0))
            
            is_plea = result.get("is_plea", False)
            item_key = result.get("item_key")
            will_help = result.get("will_help", False)
            reason = result.get("reason", "")
            
            # Check if this is a scam attempt (player claims can't afford but actually can)
            is_scam = False
            if is_plea and item_key and item_key in merchant_items:
                try:
                    price_copper = get_item_price(item_key, npc_id, game)
                    if player_total_copper >= price_copper:
                        # Player has enough money - this is a scam attempt
                        is_scam = True
                        will_help = False  # NPC won't help if it's a scam
                except Exception:
                    pass
            
            # Validate item_key if provided
            if item_key and item_key not in merchant_items:
                # If item not found but will_help is true, let NPC choose (item_key can be null)
                if will_help:
                    item_key = None  # NPC will choose
                else:
                    return False, None, False, "", False
            
            return is_plea, item_key, will_help, reason, is_scam
        
        return False, None, False, "", False
        
    except Exception as e:
        print(f"AI charity plea parsing failed: {e}")
        return False, None, False, "", False


def _can_receive_charity(game, npc_id):
    """
    Check if player can receive charity from this NPC (cooldown/limit check).
    
    Returns: (can_receive, reason_message)
    """
    if "npc_charity_tracking" not in game:
        game["npc_charity_tracking"] = {}
    
    tracking = game["npc_charity_tracking"].setdefault(npc_id, {
        "last_charity_tick": 0,
        "charity_count_today": 0,
    })
    
    current_tick = GAME_TIME.get("tick", 0)
    
    # Cooldown: 1 in-game hour between charity requests (60 minutes = 3600 ticks)
    ticks_per_hour = 60 * TICKS_PER_MINUTE
    last_charity_tick = tracking.get("last_charity_tick", 0)
    
    if current_tick - last_charity_tick < ticks_per_hour:
        minutes_remaining = ((ticks_per_hour - (current_tick - last_charity_tick)) // TICKS_PER_MINUTE) + 1
        return False, f"You've already asked for help recently. Try again in about {minutes_remaining} minutes."
    
    # Daily limit: Max 3 charity items per NPC per day
    # Reset count at start of each day (every 24 hours = 1440 minutes = 86400 ticks)
    ticks_per_day = HOURS_PER_DAY * MINUTES_PER_HOUR * TICKS_PER_MINUTE
    days_since_last = (current_tick - tracking.get("last_charity_tick", 0)) // ticks_per_day
    if days_since_last > 0:
        tracking["charity_count_today"] = 0  # Reset daily count
    
    charity_count_today = tracking.get("charity_count_today", 0)
    if charity_count_today >= 3:
        return False, "You've already received enough help today. The merchant can't keep giving things away."
    
    return True, None


def _record_charity_given(game, npc_id):
    """Record that charity was given to prevent exploitation."""
    if "npc_charity_tracking" not in game:
        game["npc_charity_tracking"] = {}
    
    tracking = game["npc_charity_tracking"].setdefault(npc_id, {
        "last_charity_tick": 0,
        "charity_count_today": 0,
    })
    
    current_tick = GAME_TIME.get("tick", 0)
    tracking["last_charity_tick"] = current_tick
    tracking["charity_count_today"] = tracking.get("charity_count_today", 0) + 1


def _choose_charity_item(merchant_items, game, npc_id):
    """
    Choose an appropriate item to give for charity (if player didn't specify).
    Prefers cheaper, basic food items.
    """
    from economy.economy_manager import get_item_price
    
    # Get prices for all items
    items_with_prices = []
    for item_key, item_info in merchant_items.items():
        try:
            price_copper = get_item_price(item_key, npc_id, game)
            items_with_prices.append((item_key, item_info, price_copper))
        except Exception:
            continue
    
    if not items_with_prices:
        return None
    
    # Sort by price (cheapest first), prefer food items
    def sort_key(item_tuple):
        item_key, item_info, price = item_tuple
        display_name = item_info.get("display_name", "").lower()
        is_food = any(word in display_name for word in ["bread", "stew", "ale", "food", "meal"])
        # Food items get priority, then by price
        return (0 if is_food else 1, price)
    
    items_with_prices.sort(key=sort_key)
    
    # Return cheapest food item, or cheapest item overall
    return items_with_prices[0][0]  # Return item_key


def _get_npc_charity_system_prompt(items_text, reputation, personality):
    """Load and format the NPC charity decision system prompt."""
    fallback = f"""You are a merchant NPC analyzing a player's message to determine if they are asking for help because they cannot afford something.

Available items for sale:
{items_text}

Player's current reputation with you: {reputation} (range: -100 to +200)
- Reputation >= 50: Very strong positive relationship - you trust and like them a great deal
- Reputation >= 25: Positive relationship - you trust and like them
- Reputation >= 15: Moderately positive impression - you think well of them
- Reputation >= 10: Slightly positive impression - they seem decent
- Reputation > 0: Neutral-to-positive impression
- Reputation == 0: You don't know them well yet
- Reputation < 0: Negative impression - you're wary or dislike them

Your task:
1. Determine if the player is expressing that they CANNOT AFFORD something (not just complaining about price)
2. If yes, identify which item they're referring to (use the exact 'key' from the list above, or null if not specified)
3. Based on your reputation with them, decide if you want to help them:
   - High reputation (>= 50): You might give them the item for free, acknowledging your relationship
   - Medium reputation (15-49): You might give them a cheaper item or express sympathy but decline
   - Low reputation (0-14): You express sympathy but explain you have a business to run
   - Negative reputation (< 0): You dismiss them or tell them to leave

IMPORTANT:
- Only help if the player is genuinely expressing inability to afford (not just haggling)
- Examples of "can't afford" pleas: "I can't afford that", "I'm so hungry but I don't have enough", "I really need this but I'm broke"
- Examples of NOT "can't afford": "That's too expensive", "Can you lower the price?", "I want a discount"
- If item is not specified, you can choose an appropriate item to give (e.g., cheapest item, most basic food item)
- You can only give ONE item per request (quantity always 1 for charity)
- Be in character - your personality is: {personality}

Return your response as JSON only, in this exact format:
{{"is_plea": true/false, "item_key": "item_key_or_null", "will_help": true/false, "reason": "brief explanation of your decision"}}

If is_plea is false, set item_key to null, will_help to false, and reason to empty string."""
    
    return load_prompt("npc_charity_system.txt", fallback_text=fallback, items_text=items_text, reputation=reputation, personality=personality)


def _get_npc_charity_user_message(text, reputation):
    """Load and format the NPC charity user message."""
    fallback = f"Player message: \"{text}\"\n\nAnalyze this message to determine if the player is asking for help because they cannot afford something. Consider their reputation with you ({reputation}) when deciding whether to help.\n\nReturn JSON with your analysis and decision."
    return load_prompt("npc_charity_user.txt", fallback_text=fallback, text=text, reputation=reputation)


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


def _handle_help_command(
    verb,
    tokens,
    game,
    username=None,
    user_id=None,
    db_conn=None,
    broadcast_fn=None,
    who_fn=None,
):
    """
    Thematic help command with beautiful formatting.
    """
    response = (
        "╔═══════════════════════════════════════════════════════════════╗\n"
        "║                  📜 THE TRAVELER'S GUIDE 📜                  ║\n"
        "║              A Companion for Adventurers in Hollowvale       ║\n"
        "╚═══════════════════════════════════════════════════════════════╝\n\n"
        "🌍 MOVEMENT & EXPLORATION\n"
        "  • look, l, examine          - Observe your surroundings\n"
        "  • go <direction>            - Travel north, south, east, west\n"
        "  • n, s, e, w                - Quick movement shortcuts\n"
        "  • search, scavenge, loot    - Find hidden treasures\n\n"
        "🎒 INVENTORY & ITEMS\n"
        "  • inventory, inv, i         - View what you carry\n"
        "  • take <item>               - Pick up an item\n"
        "  • take all                  - Gather all items in the room\n"
        "  • drop <item>               - Leave an item behind\n"
        "  • drop all                  - Drop all droppable items\n"
        "  • bury <item>               - Permanently dispose of an item\n"
        "  • bury all                  - Bury all buryable items\n"
        "  • recover <item>            - Recover a recently buried item\n\n"
        "💬 COMMUNICATION & INTERACTION\n"
        "  • talk <npc>                - Converse with an NPC\n"
        "  • say <message>             - Speak to everyone in the room\n"
        "  • give <item> to <npc>      - Offer a gift to an NPC\n"
        "  • touch <thing>             - Interact with objects or NPCs\n"
        "  • look <thing>              - Examine items, NPCs, or yourself\n"
        "  • look me                   - View your own character\n\n"
        "😊 EMOTES & EXPRESSIONS\n"
        "  • nod, smile, wave          - Express yourself\n"
        "  • shrug, stare, laugh       - Show your feelings\n"
        "  • bow, salute, clap         - Social gestures\n"
        "  • Use alone or target NPCs: 'nod mara' or 'wave guard'\n"
        "  • Over 140 emotes available! Try: sit, rest, sleep, jump, shout\n\n"
        "💰 TRADING & ECONOMY\n"
        "  • list                      - See what merchants offer\n"
        "  • buy <item>                - Purchase from a merchant\n"
        "  • buy <item> from <npc>     - Buy from a specific merchant\n"
        "  • gold, money, currency     - Check your wealth\n"
        "  • Say natural language: 'I'd like some stew' to merchants\n\n"
        "⚔️ COMBAT & INTERACTION\n"
        "  • attack <npc>              - Engage in combat (if attackable)\n"
        "  • hit, strike               - Alternative attack commands\n\n"
        "📋 QUESTS & ADVENTURES\n"
        "  • quests                    - View your active quests\n"
        "  • quests detail <number>    - See detailed quest information\n"
        "  • accept quest              - Take on a pending quest\n"
        "  • decline quest             - Refuse a quest offer\n"
        "  • board, noticeboard        - Check quest postings\n"
        "  • read quest <number>      - Read a quest from the board\n\n"
        "🌐 WORLD & INFORMATION\n"
        "  • who                       - See who else is online\n"
        "  • time                      - Check the in-game time\n"
        "  • weather                   - View weather and season info\n"
        "  • notify                    - Manage your notifications\n"
        "  • describe <text>           - Set your character description\n\n"
        "🎮 GAME MANAGEMENT\n"
        "  • help, ?                   - Show this guide\n"
        "  • restart, reset            - Start a new adventure\n"
        "  • quit, logout, exit        - Leave the realm\n\n"
        "💡 TIPS FOR SUCCESS\n"
        "  • NPCs remember your actions and conversations\n"
        "  • Your reputation affects prices and NPC reactions\n"
        "  • Some items are quest-bound and cannot be dropped\n"
        "  • The world has day/night cycles and weather\n"
        "  • Explore everywhere—secrets await the curious\n"
        "  • Be polite and helpful to build your reputation\n\n"
        "For more detailed information, visit the Player's Guide in your browser.\n"
        "May your journey through Hollowvale be filled with adventure! ⚔️✨"
    )
    return response, game


def _handle_quests_command(
    verb,
    tokens,
    game,
    username=None,
    user_id=None,
    db_conn=None,
    broadcast_fn=None,
    who_fn=None,
):
    """
    Extracted from the 'quests' branch.
    """
    import quests
    if len(tokens) == 1:
        response = quests.render_quest_list(game)
    elif len(tokens) >= 3 and tokens[1] in ["detail", "details"]:
        index_or_id = tokens[2]
        response = quests.render_quest_detail(game, index_or_id)
    else:
        response = "Usage: 'quests' to list active quests, or 'quests detail <number>' to see details."
    return response, game


def dispatch_command(
    verb: str,
    tokens: list,
    raw_command: str,
    game: dict,
    username=None,
    user_id=None,
    db_conn=None,
    broadcast_fn=None,
    who_fn=None,
):
    """
    Dispatch a command using the command registry if a handler is registered.
    If there is no registered handler, fall back to the legacy inline logic.
    
    Args:
        verb: The command verb (first token)
        tokens: List of command tokens (lowercased)
        raw_command: The original command text
        game: The current game state dictionary (will be mutated)
        username: Optional username
        user_id: Optional user ID
        db_conn: Optional database connection
        broadcast_fn: Optional callback for broadcasting
        who_fn: Optional callback for getting active players
    
    Returns:
        tuple: (response_string, updated_game_state)
    """
    handler = get_handler(verb)
    if handler:
        return handler(
            verb,
            tokens,
            game,
            username,
            user_id,
            db_conn,
            broadcast_fn,
            who_fn,
        )
    
    # Fallback: use legacy inline logic for commands we haven't migrated yet.
    return _legacy_handle_command_body(
        verb,
        tokens,
        raw_command,
        game,
        username,
        user_id,
        db_conn,
        broadcast_fn,
        who_fn,
    )


def _legacy_handle_command_body(
    verb,
    tokens,
    command,
    game,
    username=None,
    user_id=None,
    db_conn=None,
    broadcast_fn=None,
    who_fn=None,
):
    """
    Legacy command handler - contains the original if/elif chain logic.
    
    This function is gradually being replaced by the command registry system.
    Commands are moved to separate handlers (registered in command_registry)
    as they are refactored.
    
    Args:
        verb: The command verb (first token, already lowercased)
        tokens: List of command tokens (lowercased)
        command: The original command text
        game: The current game state dictionary (will be mutated)
        username: Optional username
        user_id: Optional user ID
        db_conn: Optional database connection
        broadcast_fn: Optional callback for broadcasting
        who_fn: Optional callback for getting active players
    
    Returns:
        tuple: (response_string, updated_game_state)
    """
    # Advance game time and update weather
    advance_time(ticks=1)
    update_weather_if_needed()
    update_player_weather_status(game)
    # Update NPC weather status for all NPCs
    update_npc_weather_statuses()
    
    # Clean up old buried items periodically (every command)
    cleanup_buried_items()
    
    # Process NPC periodic actions and weather reactions
    # This shows accumulated NPC actions based on elapsed time since last action
    process_npc_periodic_actions(game, broadcast_fn=broadcast_fn, who_fn=who_fn)
    
    # Process time-based exit states (e.g., tavern door locking)
    process_time_based_exit_states(broadcast_fn=broadcast_fn, who_fn=who_fn)
    
    # Process NPC movements along routes
    process_npc_movements(broadcast_fn=broadcast_fn)
    
    # Process room ambiance (contextual environmental messages based on time, weather, room)
    # Show accumulated messages based on elapsed time since last check
    import ambiance
    current_tick = get_current_game_tick()
    current_room = game.get("location", "town_square")
    accumulated_count = ambiance.get_accumulated_ambiance_messages(current_room, current_tick, game)
    
    if accumulated_count > 0:
        # Generate and show accumulated ambiance messages
        ambiance_messages = []
        for _ in range(accumulated_count):
            msg = ambiance.process_room_ambiance(game, broadcast_fn=broadcast_fn)
            if msg:
                ambiance_messages.extend(msg)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_messages = []
        for msg in ambiance_messages:
            if msg not in seen:
                seen.add(msg)
                unique_messages.append(msg)
        
        if unique_messages:
            game.setdefault("log", [])
            for msg in unique_messages:
                game["log"].append(msg)
            game["log"] = game["log"][-50:]
            # Update the tick tracker
            ambiance.update_ambiance_tick(current_room, current_tick, messages_shown=len(unique_messages))
    
    # Tick quests (check for expired quests)
    import quests
    quests.tick_quests(game, get_current_game_tick())
    
    text = command.strip()
    if not text:
        return "You say nothing.", game

    tokens = text.lower().split()
    verb = tokens[0]
    args = tokens[1:]

    response = ""  # Initialize response variable
    
    # Emote / social commands (check before other commands)
    if verb in EMOTES:
        response, game = handle_emote(verb, args, game, username=username or "adventurer", broadcast_fn=broadcast_fn, who_fn=who_fn)

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
                    # Try to resolve in order: item, NPC, room detail
                    item_id, source, container = resolve_item_target(game, target_text)
                    if item_id:
                        response = _format_item_look(item_id, source)
                    else:
                        npc_id, npc = resolve_npc_target(game, target_text)
                        if npc_id and npc:
                            response = _format_npc_look(npc_id, npc, game)
                        else:
                            # Try room details/fixtures
                            detail_id, detail, room_id = resolve_room_detail(game, target_text)
                            if detail_id and detail:
                                # Check if there's a look callback
                                callback_result = invoke_room_detail_callback("look", game, username or "adventurer", room_id, detail_id)
                                if callback_result:
                                    response = callback_result
                                else:
                                    response = _format_detail_look(detail_id, detail, room_id, game)
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
            
            # CRITICAL: Ensure door states are correct before checking accessibility
            # This double-checks in case process_time_based_exit_states wasn't called or state was lost
            process_time_based_exit_states(broadcast_fn=broadcast_fn, who_fn=who_fn)
            
            # Check exit accessibility
            is_accessible, reason = is_exit_accessible(loc_id, full_direction, "player", username, game)
            
            if not is_accessible:
                response = reason or "You can't go that way."
            else:
                # Support both string (backward compatible) and dict exits
                if exit_def is None:
                    target = None
                elif isinstance(exit_def, str):
                    target = exit_def
                elif isinstance(exit_def, dict):
                    target = exit_def.get("target")
                else:
                    target = None
                
                if target:
                    old_loc = loc_id
                    game["location"] = target
                    
                    # Broadcast leave message to old room
                    if broadcast_fn is not None:
                        actor_name = username or "Someone"
                        leave_msg = get_entrance_exit_message(old_loc, target, full_direction, actor_name, is_exit=True, is_npc=False)
                        broadcast_fn(old_loc, leave_msg)
                    
                    # Broadcast arrive message to new room
                    if broadcast_fn is not None:
                        actor_name = username or "Someone"
                        opposite = OPPOSITE_DIRECTION.get(full_direction, "somewhere")
                        arrive_msg = get_entrance_exit_message(target, old_loc, opposite, actor_name, is_exit=False, is_npc=False)
                        broadcast_fn(target, arrive_msg)
                    
                    # Get movement message and room description
                    movement_msg = get_movement_message(target, full_direction)
                    location_desc = describe_location(game)
                    response = f"{movement_msg}\n{location_desc}"
                    
                    # Trigger quest event for entering room
                    import quests
                    event = quests.QuestEvent(
                        type="enter_room",
                        room_id=target,
                        username=username or "adventurer"
                    )
                    quests.handle_quest_event(game, event)
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
            
            # CRITICAL: Ensure door states are correct before checking accessibility
            # This double-checks in case process_time_based_exit_states wasn't called or state was lost
            process_time_based_exit_states(broadcast_fn=broadcast_fn, who_fn=who_fn)
            
            # Check exit accessibility
            is_accessible, reason = is_exit_accessible(loc_id, full_direction, "player", username, game)
            
            if not is_accessible:
                response = reason or "You can't go that way."
            else:
                # Support both string (backward compatible) and dict exits
                if exit_def is None:
                    target = None
                elif isinstance(exit_def, str):
                    target = exit_def
                elif isinstance(exit_def, dict):
                    target = exit_def.get("target")
                else:
                    target = None
                
                if target:
                    old_loc = loc_id
                    game["location"] = target
                    
                    # Broadcast leave message to old room
                    if broadcast_fn is not None:
                        actor_name = username or "Someone"
                        leave_msg = get_entrance_exit_message(old_loc, target, full_direction, actor_name, is_exit=True, is_npc=False)
                        broadcast_fn(old_loc, leave_msg)
                    
                    # Broadcast arrive message to new room
                    if broadcast_fn is not None:
                        actor_name = username or "Someone"
                        opposite = OPPOSITE_DIRECTION.get(full_direction, "somewhere")
                        arrive_msg = get_entrance_exit_message(target, old_loc, opposite, actor_name, is_exit=False, is_npc=False)
                        broadcast_fn(target, arrive_msg)
                    
                    # Get movement message and room description
                    movement_msg = get_movement_message(target, full_direction)
                    location_desc = describe_location(game)
                    response = f"{movement_msg}\n{location_desc}"
                    
                    # Trigger quest event for entering room
                    import quests
                    event = quests.QuestEvent(
                        type="enter_room",
                        room_id=target,
                        username=username or "adventurer"
                    )
                    quests.handle_quest_event(game, event)
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
                    
                    # Trigger quest event for taking item
                    import quests
                    event = quests.QuestEvent(
                        type="take_item",
                        room_id=loc_id,
                        item_id=matched_item,
                        username=username or "adventurer"
                    )
                    quests.handle_quest_event(game, event)
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
                        
                        # Check if quest item
                        if is_quest_item(matched_item):
                            response = "You cannot get rid of that. It seems bound to your story."
                        elif not item_def.get("droppable", True):
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

    elif tokens[0] == "bury" and len(tokens) >= 2:
        # Bury command: permanently remove an item from the game
        item_input = " ".join(tokens[1:]).lower()
        loc_id = game.get("location", "town_square")
        inventory = game.get("inventory", [])
        
        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
        else:
            room_state = ROOM_STATE.setdefault(loc_id, {"items": []})
            room_items = room_state["items"]
            
            if item_input in ["all", "everything"]:
                # Bury all buryable items in the room
                buried_items = []
                non_buryable_items = []
                current_tick = GAME_TIME.get("tick", 0)
                current_minutes = GAME_TIME.get("minutes", 0)
                
                # Initialize buried items tracking for this room if needed
                if loc_id not in BURIED_ITEMS:
                    BURIED_ITEMS[loc_id] = []
                
                # Check each item in the room
                for item_id in room_items[:]:  # Use slice to iterate over copy
                    can_bury, reason = is_item_buryable(item_id)
                    if can_bury:
                        buried_items.append(item_id)
                        room_items.remove(item_id)
                        # Add to buried items with timestamp
                        BURIED_ITEMS[loc_id].append({
                            "item_id": item_id,
                            "buried_at_tick": current_tick,
                            "buried_at_minutes": current_minutes,
                        })
                    else:
                        non_buryable_items.append(item_id)
                
                room_state["items"] = room_items
                
                # Build response
                if buried_items:
                    item_names = [render_item_name(item_id) for item_id in buried_items]
                    if len(buried_items) == 1:
                        response = f"You dig a small hole and bury the {item_names[0]}, covering it with earth. You can recover it within a day."
                    else:
                        response = f"You dig a hole and bury {len(buried_items)} items, covering them with earth. You can recover them within a day.\nBuried: {', '.join(item_names)}."
                    
                    if non_buryable_items:
                        non_buryable_names = [render_item_name(item_id) for item_id in non_buryable_items]
                        response += f"\n(You cannot bury: {', '.join(non_buryable_names)}.)"
                    
                    # Broadcast to room if other players are present
                    if broadcast_fn is not None:
                        actor_name = username or "Someone"
                        if len(buried_items) == 1:
                            broadcast_message = f"{actor_name} digs a hole and buries something in the ground."
                        else:
                            broadcast_message = f"{actor_name} digs a hole and buries several items in the ground."
                        broadcast_fn(loc_id, broadcast_message)
                else:
                    if non_buryable_items:
                        non_buryable_names = [render_item_name(item_id) for item_id in non_buryable_items]
                        response = f"There's nothing buryable here. ({', '.join(non_buryable_names)} cannot be buried.)"
                    else:
                        response = "There's nothing here to bury."
            else:
                # Bury a specific item - try inventory first, then room
                matched_item = None
                source = None
                
                # Check inventory
                matched_item = match_item_name_in_collection(item_input, inventory)
                if matched_item:
                    source = "inventory"
                else:
                    # Check room
                    matched_item = match_item_name_in_collection(item_input, room_items)
                    if matched_item:
                        source = "room"
                
                if not matched_item:
                    response = f"You don't see a '{item_input}' here to bury."
                else:
                    # Check if item is buryable
                    can_bury, reason = is_item_buryable(matched_item)
                    
                    if not can_bury:
                        response = reason
                    else:
                        # Bury item (store with timestamp for recovery)
                        item_def = get_item_def(matched_item)
                        display_name = render_item_name(matched_item)
                        current_tick = GAME_TIME.get("tick", 0)
                        current_minutes = GAME_TIME.get("minutes", 0)
                        
                        if source == "inventory":
                            inventory.remove(matched_item)
                            game["inventory"] = inventory
                            # Items buried from inventory go to the room's buried items
                            if loc_id not in BURIED_ITEMS:
                                BURIED_ITEMS[loc_id] = []
                            BURIED_ITEMS[loc_id].append({
                                "item_id": matched_item,
                                "buried_at_tick": current_tick,
                                "buried_at_minutes": current_minutes,
                            })
                            response = f"You dig a small hole and bury the {display_name}, covering it with earth. You can recover it within a day."
                        elif source == "room":
                            room_items.remove(matched_item)
                            room_state["items"] = room_items
                            # Store in buried items tracking
                            if loc_id not in BURIED_ITEMS:
                                BURIED_ITEMS[loc_id] = []
                            BURIED_ITEMS[loc_id].append({
                                "item_id": matched_item,
                                "buried_at_tick": current_tick,
                                "buried_at_minutes": current_minutes,
                            })
                            response = f"You dig a small hole and bury the {display_name}, covering it with earth. You can recover it within a day."
                        
                        # Broadcast to room if other players are present
                        if broadcast_fn is not None:
                            actor_name = username or "Someone"
                            broadcast_message = f"{actor_name} digs a hole and buries something in the ground."
                            broadcast_fn(loc_id, broadcast_message)

    elif tokens[0] == "recover" and len(tokens) >= 2:
        # Recover command: dig up buried items
        item_input = " ".join(tokens[1:]).lower()
        loc_id = game.get("location", "town_square")
        inventory = game.get("inventory", [])
        
        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
        else:
            # Clean up old buried items first
            cleanup_buried_items()
            
            # Get buried items in this room
            buried_items = get_buried_items_in_room(loc_id)
            
            if not buried_items:
                response = "There's nothing buried here to recover."
            else:
                if item_input in ["all", "everything"]:
                    # Recover all buried items
                    recovered_items = []
                    
                    # Check inventory weight capacity
                    max_weight = game.get("max_carry_weight", 20.0)
                    current_weight = calculate_inventory_weight(inventory)
                    
                    for buried_item in buried_items[:]:  # Use slice to iterate over copy
                        item_id = buried_item["item_id"]
                        item_def = get_item_def(item_id)
                        item_weight = item_def.get("weight", 0.1)
                        
                        if current_weight + item_weight <= max_weight:
                            # Remove from buried items
                            BURIED_ITEMS[loc_id].remove(buried_item)
                            # Add to inventory
                            inventory.append(item_id)
                            recovered_items.append(item_id)
                            current_weight += item_weight
                        else:
                            # Not enough capacity
                            break
                    
                    game["inventory"] = inventory
                    
                    # Update buried items list (remove empty room)
                    if loc_id in BURIED_ITEMS and not BURIED_ITEMS[loc_id]:
                        del BURIED_ITEMS[loc_id]
                    
                    if recovered_items:
                        item_names = [render_item_name(item_id) for item_id in recovered_items]
                        if len(recovered_items) == 1:
                            response = f"You dig carefully and recover the {item_names[0]}."
                        else:
                            response = f"You dig carefully and recover {len(recovered_items)} items: {', '.join(item_names)}."
                        
                        if len(recovered_items) < len(buried_items):
                            response += "\n(You couldn't carry all the buried items - you're at capacity.)"
                        
                        # Broadcast to room if other players are present
                        if broadcast_fn is not None:
                            actor_name = username or "Someone"
                            broadcast_message = f"{actor_name} digs carefully and recovers something from the ground."
                            broadcast_fn(loc_id, broadcast_message)
                    else:
                        response = "You couldn't recover any items - your inventory is too full!"
                else:
                    # Recover a specific item
                    matched_buried_item = None
                    for buried_item in buried_items:
                        item_id = buried_item["item_id"]
                        display_name = render_item_name(item_id).lower()
                        if item_input in display_name or display_name in item_input:
                            matched_buried_item = buried_item
                            break
                    
                    if not matched_buried_item:
                        response = f"You don't see a '{item_input}' buried here."
                    else:
                        item_id = matched_buried_item["item_id"]
                        item_def = get_item_def(item_id)
                        item_weight = item_def.get("weight", 0.1)
                        max_weight = game.get("max_carry_weight", 20.0)
                        current_weight = calculate_inventory_weight(inventory)
                        
                        if current_weight + item_weight > max_weight:
                            response = "You can't carry that - your inventory is too full!"
                        else:
                            # Remove from buried items
                            BURIED_ITEMS[loc_id].remove(matched_buried_item)
                            # Add to inventory
                            inventory.append(item_id)
                            game["inventory"] = inventory
                            
                            # Update buried items list (remove empty room)
                            if loc_id in BURIED_ITEMS and not BURIED_ITEMS[loc_id]:
                                del BURIED_ITEMS[loc_id]
                            
                            display_name = render_item_name(item_id)
                            response = f"You dig carefully and recover the {display_name}."
                            
                            # Broadcast to room if other players are present
                            if broadcast_fn is not None:
                                actor_name = username or "Someone"
                                broadcast_message = f"{actor_name} digs carefully and recovers something from the ground."
                                broadcast_fn(loc_id, broadcast_message)

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
                        
                        # Trigger quest event for giving item
                        import quests
                        event = quests.QuestEvent(
                            type="give_item",
                            room_id=loc_id,
                            npc_id=matched_npc_id,
                            item_id=item_found,
                            username=username or "adventurer"
                        )
                        quests.handle_quest_event(game, event)
                        
                        # Also trigger talk_to_npc event (giving counts as interaction)
                        event2 = quests.QuestEvent(
                            type="talk_to_npc",
                            room_id=loc_id,
                            npc_id=matched_npc_id,
                            username=username or "adventurer"
                        )
                        quests.handle_quest_event(game, event2)

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
        # Preserve original message formatting (don't lowercase)
        original_command = command.strip()
        # Extract message part after "say "
        say_index = original_command.lower().find("say ")
        if say_index != -1:
            message = original_command[say_index + 4:]  # +4 for "say "
        else:
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
                            ai_response = None
                            error_message = None
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
                                
                                # Broadcast AI response to all players in the room
                                if broadcast_fn is not None:
                                    broadcast_fn(loc_id, ai_response)
                                
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
                            # Check if this is a "can't afford" plea that might trigger charity
                            if npc_id in MERCHANT_ITEMS and (npc.use_ai if hasattr(npc, 'use_ai') else npc.get("use_ai", False)):
                                merchant_items = MERCHANT_ITEMS[npc_id]
                                is_plea, charity_item_key, will_help, reason, is_scam = _parse_charity_plea_ai(
                                    message, merchant_items, npc, room_def, game,
                                    username or "adventurer", user_id, db_conn, npc_id
                                )
                                
                                if is_plea and is_scam:
                                    # Player tried to scam - call them out and decrease reputation
                                    game["_current_npc_id"] = npc_id
                                    npc_dict = npc.to_dict() if hasattr(npc, 'to_dict') else npc
                                    scam_response, error_message = generate_npc_reply(
                                        npc_dict, room_def, game, username or "adventurer",
                                        message, recent_log=game.get("log", [])[-10:],
                                        user_id=user_id, db_conn=db_conn
                                    )
                                    
                                    # Decrease reputation for scam attempt
                                    adjust_reputation(game, npc_id, -10, "scam attempt")
                                    
                                    # Update memory
                                    if npc_id not in game.get("npc_memory", {}):
                                        game.setdefault("npc_memory", {})[npc_id] = []
                                    game["npc_memory"][npc_id].append({
                                        "type": "scam_attempt",
                                        "message": message,
                                        "response": scam_response or "Your wallet looks pretty full to me... what do you take me for?",
                                    })
                                    if len(game["npc_memory"][npc_id]) > 20:
                                        game["npc_memory"][npc_id] = game["npc_memory"][npc_id][-20:]
                                    
                                    response = f"You say: \"{message}\"\n{scam_response or 'Your wallet looks pretty full to me... what do you take me for?'}"
                                    
                                    # Broadcast scam response
                                    if broadcast_fn is not None and scam_response:
                                        broadcast_fn(loc_id, scam_response)
                                    
                                    purchase_processed = True
                                    break
                                
                                if is_plea and will_help:
                                    # Check cooldown/limits
                                    can_receive, cooldown_msg = _can_receive_charity(game, npc_id)
                                    
                                    if can_receive:
                                        # NPC will help - give item for free
                                        # If item not specified, NPC chooses
                                        if not charity_item_key:
                                            charity_item_key = _choose_charity_item(merchant_items, game, npc_id)
                                        
                                        # Ensure we have a valid item key - if not, choose one
                                        if not charity_item_key or charity_item_key not in merchant_items:
                                            charity_item_key = _choose_charity_item(merchant_items, game, npc_id)
                                        
                                        if charity_item_key and charity_item_key in merchant_items:
                                            item_info = merchant_items[charity_item_key]
                                            item_given = item_info.get("item_given")
                                            
                                            if not item_given:
                                                # Fallback: use the item_key itself if item_given is missing
                                                item_given = charity_item_key
                                            
                                            # Add item to inventory
                                            inventory = game.get("inventory", [])
                                            inventory.append(item_given)
                                            game["inventory"] = inventory
                                            
                                            # Record charity given
                                            _record_charity_given(game, npc_id)
                                            
                                            # Generate AI response explaining the charity
                                            game["_current_npc_id"] = npc_id
                                            npc_dict = npc.to_dict() if hasattr(npc, 'to_dict') else npc
                                            charity_response, error_message = generate_npc_reply(
                                                npc_dict, room_def, game, username or "adventurer",
                                                message, recent_log=game.get("log", [])[-10:],
                                                user_id=user_id, db_conn=db_conn
                                            )
                                            
                                            # Update memory
                                            if npc_id not in game.get("npc_memory", {}):
                                                game.setdefault("npc_memory", {})[npc_id] = []
                                            game["npc_memory"][npc_id].append({
                                                "type": "charity",
                                                "item": charity_item_key,
                                                "response": charity_response or "Here, take this.",
                                            })
                                            if len(game["npc_memory"][npc_id]) > 20:
                                                game["npc_memory"][npc_id] = game["npc_memory"][npc_id][-20:]
                                            
                                            item_display = item_info.get("display_name", charity_item_key.replace("_", " "))
                                            # Add explicit message about receiving the item
                                            if charity_response:
                                                response = f"You say: \"{message}\"\n{charity_response}\n{npc.name} hands you a {item_display}."
                                            else:
                                                response = f"You say: \"{message}\"\n{npc.name} gives you a {item_display} for free."
                                            
                                            # Broadcast charity response and item handover
                                            if broadcast_fn is not None:
                                                if charity_response:
                                                    broadcast_fn(loc_id, charity_response)
                                                broadcast_fn(loc_id, f"{npc.name} hands {username or 'someone'} a {item_display}.")
                                            
                                            purchase_processed = True
                                            break
                                        else:
                                            # NPC wanted to help but item not available - this shouldn't happen often
                                            response = f"You say: \"{message}\"\n{purchase_response}\n{npc.name} looks around but doesn't seem to have anything to give you right now."
                                            purchase_processed = True
                                            break
                                    else:
                                        # Cooldown/limit reached - show cooldown message but still process as failed purchase
                                        response = f"You say: \"{message}\"\n{purchase_response}\n{cooldown_msg}"
                                        purchase_processed = True
                                        break
                            
                            # Normal failed purchase response
                            response = f"You say: \"{message}\"\n{purchase_response}"
                            purchase_processed = True
                            break
            
            if not purchase_processed:
                # Normal say command - no purchase detected
                # But check for charity pleas even when no purchase intent
                charity_processed = False
                for npc_id in npc_ids:
                    if npc_id in NPCS and npc_id in MERCHANT_ITEMS:
                        npc = NPCS[npc_id]
                        if (npc.use_ai if hasattr(npc, 'use_ai') else npc.get("use_ai", False)):
                            merchant_items = MERCHANT_ITEMS[npc_id]
                            is_plea, charity_item_key, will_help, reason, is_scam = _parse_charity_plea_ai(
                                message, merchant_items, npc, room_def, game,
                                username or "adventurer", user_id, db_conn, npc_id
                            )
                            
                            if is_plea and is_scam:
                                # Player tried to scam - call them out and decrease reputation
                                game["_current_npc_id"] = npc_id
                                npc_dict = npc.to_dict() if hasattr(npc, 'to_dict') else npc
                                scam_response, error_message = generate_npc_reply(
                                    npc_dict, room_def, game, username or "adventurer",
                                    message, recent_log=game.get("log", [])[-10:],
                                    user_id=user_id, db_conn=db_conn
                                )
                                
                                # Decrease reputation for scam attempt
                                adjust_reputation(game, npc_id, -10, "scam attempt")
                                
                                # Update memory
                                if npc_id not in game.get("npc_memory", {}):
                                    game.setdefault("npc_memory", {})[npc_id] = []
                                game["npc_memory"][npc_id].append({
                                    "type": "scam_attempt",
                                    "message": message,
                                    "response": scam_response or "Your wallet looks pretty full to me... what do you take me for?",
                                })
                                if len(game["npc_memory"][npc_id]) > 20:
                                    game["npc_memory"][npc_id] = game["npc_memory"][npc_id][-20:]
                                
                                response = f"You say: \"{message}\"\n{scam_response or 'Your wallet looks pretty full to me... what do you take me for?'}"
                                
                                # Broadcast scam response
                                if broadcast_fn is not None and scam_response:
                                    broadcast_fn(loc_id, scam_response)
                                
                                charity_processed = True
                                break
                            
                            if is_plea and will_help:
                                # Check cooldown/limits
                                can_receive, cooldown_msg = _can_receive_charity(game, npc_id)
                                
                                if can_receive:
                                    # NPC will help - give item for free
                                    if not charity_item_key:
                                        charity_item_key = _choose_charity_item(merchant_items, game, npc_id)
                                    
                                    # Ensure we have a valid item key - if not, choose one
                                    if not charity_item_key or charity_item_key not in merchant_items:
                                        charity_item_key = _choose_charity_item(merchant_items, game, npc_id)
                                    
                                    if charity_item_key and charity_item_key in merchant_items:
                                        item_info = merchant_items[charity_item_key]
                                        item_given = item_info.get("item_given")
                                        
                                        if not item_given:
                                            # Fallback: use the item_key itself if item_given is missing
                                            item_given = charity_item_key
                                        
                                        # Add item to inventory
                                        inventory = game.get("inventory", [])
                                        inventory.append(item_given)
                                        game["inventory"] = inventory
                                        
                                        # Record charity given
                                        _record_charity_given(game, npc_id)
                                        
                                        # Generate AI response
                                        game["_current_npc_id"] = npc_id
                                        npc_dict = npc.to_dict() if hasattr(npc, 'to_dict') else npc
                                        charity_response, error_message = generate_npc_reply(
                                            npc_dict, room_def, game, username or "adventurer",
                                            message, recent_log=game.get("log", [])[-10:],
                                            user_id=user_id, db_conn=db_conn
                                        )
                                        
                                        # Update memory
                                        if npc_id not in game.get("npc_memory", {}):
                                            game.setdefault("npc_memory", {})[npc_id] = []
                                        game["npc_memory"][npc_id].append({
                                            "type": "charity",
                                            "item": charity_item_key,
                                            "response": charity_response or "Here, take this.",
                                        })
                                        if len(game["npc_memory"][npc_id]) > 20:
                                            game["npc_memory"][npc_id] = game["npc_memory"][npc_id][-20:]
                                        
                                        item_display = item_info.get("display_name", charity_item_key.replace("_", " "))
                                        # Add explicit message about receiving the item
                                        if charity_response:
                                            response = f"You say: \"{message}\"\n{charity_response}\n{npc.name} hands you a {item_display}."
                                        else:
                                            response = f"You say: \"{message}\"\n{npc.name} gives you a {item_display} for free."
                                        
                                        # Broadcast charity response and item handover
                                        if broadcast_fn is not None:
                                            if charity_response:
                                                broadcast_fn(loc_id, charity_response)
                                            broadcast_fn(loc_id, f"{npc.name} hands {username or 'someone'} a {item_display}.")
                                        
                                        charity_processed = True
                                        break
                
                if not charity_processed:
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
                                    
                                    # Broadcast AI reaction to all players in the room
                                    if broadcast_fn is not None:
                                        broadcast_fn(loc_id, ai_response)
                                    
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
                    
                    # Check for quest offers from NPCs (if player spoke to an NPC)
                    import quests
                    from game_engine import GAME_TIME
                    current_tick = GAME_TIME.get("tick", 0)
                    
                    # Check each NPC in the room to see if they should offer a quest
                    for npc_id in npc_ids:
                        if npc_id in NPCS:
                            quest_offer_text = quests.maybe_offer_npc_quest(game, username or "adventurer", npc_id, message, current_tick, active_players_fn=who_fn)
                            if quest_offer_text:
                                response += "\n" + quest_offer_text
                                
                            # Trigger quest event for saying to NPC
                            event = quests.QuestEvent(
                                type="say_to_npc",
                                room_id=loc_id,
                                npc_id=npc_id,
                                text=message,
                                username=username or "adventurer"
                            )
                            quests.handle_quest_event(game, event)
                    
                    # Broadcast say message to other players in the room (in cyan)
                if broadcast_fn is not None:
                    # Preserve original formatting and capitalize properly
                    formatted_message = f"[CYAN]{player_message}[/CYAN]"
                    broadcast_fn(loc_id, formatted_message)

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
                    # Resolve NPC target
                    npc_id, npc = resolve_npc_target(game, npc_target)
                    
                    if not npc_id or not npc:
                        response = f"You don't see anyone like '{npc_target}' here to talk to."
                    elif is_npc_refusing_to_talk(game, npc_id):
                        # NPC is refusing to talk due to cooldown
                        npc_name = npc.name if hasattr(npc, 'name') else npc_id
                        response = f"{npc_name} pointedly ignores you and refuses to talk."
                    else:
                        # Normal talk processing
                        # Generate dialogue for the NPC
                        response = generate_npc_line(npc_id, game, username, user_id=user_id, db_conn=db_conn)
                        
                        # Trigger quest event for talking to NPC
                        import quests
                        from game_engine import GAME_TIME
                        current_tick = GAME_TIME.get("tick", 0)
                        
                        event = quests.QuestEvent(
                            type="talk_to_npc",
                            room_id=loc_id,
                            npc_id=npc_id,
                            username=username or "adventurer"
                        )
                        quests.handle_quest_event(game, event)
                        
                        # Broadcast NPC dialogue to all players in the room
                        if broadcast_fn is not None and response and response.strip():
                            # Only broadcast if it's actual dialogue (not error messages)
                            if not response.startswith("There's no one") and not response.startswith("You can't"):
                                broadcast_fn(loc_id, response)

    elif tokens[0] in ["attack", "hit", "strike"] and len(tokens) >= 2:
        # Attack command
        target_text = " ".join(tokens[1:]).lower()
        loc_id = game.get("location", "town_square")
        
        # Default message constant
        DEFAULT_CANT_ATTACK_MESSAGE = "You can't attack {name}."
        
        # Resolve NPC target
        npc_id, npc = resolve_npc_target(game, target_text)
        
        if not npc_id or not npc:
            # Check if it's a player (for now, disallow)
            if who_fn:
                active_players = who_fn()
                for player_info in active_players:
                    player_username = player_info.get("username", "")
                    if player_username.lower() == target_text and player_info.get("location") == loc_id:
                        response = "You can't attack other players yet."
                        return response, game
            
            response = "You don't see anyone like that here to attack."
        else:
            # Check if NPC is attackable
            attackable = getattr(npc, "attackable", False)
            
            if not attackable:
                # Non-attackable NPC - check for on_attack callback
                from npc import get_npc_on_attack_callback
                callback = get_npc_on_attack_callback(npc_id)
                
                if callback:
                    # Call the callback
                    callback_message = callback(game, username or "adventurer", npc_id)
                    response = callback_message
                    
                    # Note: The callback handles reputation, movement, and cooldown internally
                    # via imports from game_engine, so we don't need to do it here
                else:
                    # Default message
                    npc_name = npc.name if hasattr(npc, 'name') else npc_id
                    response = DEFAULT_CANT_ATTACK_MESSAGE.format(name=npc_name)
            else:
                # Attackable NPC - implement combat
                # Initialize or get NPC state
                if npc_id not in NPC_STATE:
                    # Initialize NPC state
                    npc_home = getattr(npc, "home", None) or loc_id
                    max_hp = npc.stats.get("max_hp", 10) if hasattr(npc, "stats") and npc.stats else 10
                    NPC_STATE[npc_id] = {
                        "room": loc_id,
                        "home_room": npc_home,
                        "hp": max_hp,
                        "alive": True,
                    }
                
                npc_state = NPC_STATE[npc_id]
                
                # Check if NPC is already dead
                if not npc_state.get("alive", True):
                    npc_name = npc.name if hasattr(npc, 'name') else npc_id
                    response = f"{npc_name} is already dead."
                else:
                    # Calculate damage
                    player_stats = game.get("character", {}).get("stats", {})
                    player_str = player_stats.get("str", 1)
                    base_damage = max(1, player_str)
                    
                    npc_defense = npc.stats.get("defense", 0) if hasattr(npc, "stats") and npc.stats else 0
                    damage = max(1, base_damage - npc_defense)
                    
                    # Apply damage
                    current_hp = npc_state.get("hp", npc.stats.get("max_hp", 10) if hasattr(npc, "stats") and npc.stats else 10)
                    new_hp = max(0, current_hp - damage)
                    npc_state["hp"] = new_hp
                    
                    npc_name = npc.name if hasattr(npc, 'name') else npc_id
                    
                    if new_hp <= 0:
                        # NPC dies
                        npc_state["alive"] = False
                        response = f"You strike {npc_name} a final blow. {npc_name} collapses and dies."
                        
                        # Remove NPC from room (move to a "dead" state or remove from room)
                        # For now, just mark as dead - they'll still appear but won't be interactive
                        # TODO: Could move to a special "corpse" room or remove from room entirely
                        
                        # Broadcast death to room
                        if broadcast_fn:
                            broadcast_fn(loc_id, f"{npc_name} collapses and dies.")
                    else:
                        # NPC still alive
                        response = f"You strike {npc_name} for {damage} damage. {npc_name} has {new_hp} HP remaining."
                        
                        # Broadcast attack to room
                        if broadcast_fn:
                            broadcast_fn(loc_id, f"{username or 'Someone'} attacks {npc_name}!")
                    
                    # Check for on_attack callback (for attackable NPCs, this runs after combat)
                    from npc import get_npc_on_attack_callback
                    callback = get_npc_on_attack_callback(npc_id)
                    if callback:
                        callback_message = callback(game, username or "adventurer", npc_id)
                        response += " " + callback_message

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
                # Try to resolve in order: item, NPC, room detail
                item_id, source, container = resolve_item_target(game, target_text)
                if item_id:
                    response = _format_item_stat(item_id, source)
                else:
                    npc_id, npc = resolve_npc_target(game, target_text)
                    if npc_id and npc:
                        response = _format_npc_stat(npc_id, npc)
                    else:
                        # Try room details/fixtures
                        detail_id, detail, room_id = resolve_room_detail(game, target_text)
                        if detail_id and detail:
                            response = _format_detail_stat(detail_id, detail, room_id)
                        else:
                            response = f"You see nothing like '{target_text}' to examine."
        else:
            response = "Usage: stat <target> or stat me"

    elif tokens[0] == "goto" and len(tokens) >= 2:
        # Admin-only goto command: goto <player_name|npc_name>
        if not is_admin_user(username, game):
            response = "You don't have permission to do that."
        else:
            target_text = " ".join(tokens[1:]).lower()
            target_room = None
            target_name = None
            
            # Try to find as a player first
            if who_fn:
                try:
                    active_players = who_fn()
                    for player_info in active_players:
                        player_username = player_info.get("username", "")
                        if player_username.lower() == target_text:
                            target_room = player_info.get("location")
                            target_name = player_username
                            break
                except Exception:
                    pass
            
            # If not found as player, try NPC
            if not target_room:
                npc_id, npc = resolve_npc_target(game, target_text)
                if npc_id and npc:
                    if npc_id in NPC_STATE:
                        target_room = NPC_STATE[npc_id].get("room")
                        target_name = npc.name
                    else:
                        response = f"{npc.name} is not currently in the world."
                else:
                    response = f"Could not find player or NPC '{target_text}'. Use: goto <player_name|npc_name>"
            
            # If we found a target, teleport there
            if target_room:
                if target_room not in WORLD:
                    response = f"{target_name} is in an invalid location: {target_room}"
                else:
                    old_loc = game.get("location", "town_square")
                    game["location"] = target_room
                    
                    # Get custom teleport messages from admin stats if set
                    teleport_exit_msg = game.get("teleport_exit_message")
                    teleport_entrance_msg = game.get("teleport_entrance_message")
                    
                    # Broadcast exit message from old room
                    if broadcast_fn and old_loc != target_room:
                        if teleport_exit_msg:
                            exit_msg = f"[CYAN]{teleport_exit_msg.replace('{name}', username or 'Admin')}[/CYAN]"
                        else:
                            exit_msg = get_entrance_exit_message(
                                old_loc, target_room, "somewhere", username or "Admin",
                                is_exit=True, is_npc=False, is_teleport=True
                            )
                        broadcast_fn(old_loc, exit_msg)
                    
                    # Broadcast entrance message to new room
                    if broadcast_fn:
                        if teleport_entrance_msg:
                            entrance_msg = f"[CYAN]{teleport_entrance_msg.replace('{name}', username or 'Admin')}[/CYAN]"
                        else:
                            entrance_msg = get_entrance_exit_message(
                                target_room, old_loc, "somewhere", username or "Admin",
                                is_exit=False, is_npc=False, is_teleport=True
                            )
                        broadcast_fn(target_room, entrance_msg)
                    
                    # Get room description for admin
                    location_desc = describe_location(game)
                    room_name = WORLD[target_room].get("name", target_room)
                    response = f"You teleport to {target_name}'s location: {room_name}.\n{location_desc}"
                    
                    # Trigger quest event for entering room
                    import quests
                    event = quests.QuestEvent(
                        type="enter_room",
                        room_id=target_room,
                        username=username or "adventurer"
                    )
                    quests.handle_quest_event(game, event)
                # else: target_room not in WORLD - response already set above

    elif tokens[0] == "set" and len(tokens) >= 4:
        # Admin-only set command: set <target> <property> <value>
        if not is_admin_user(username, game):
            response = "You don't have permission to do that."
        else:
            target_text = tokens[1].lower()
            property_name = tokens[2].lower()
            value_text = " ".join(tokens[3:])  # Allow multi-word values
            
            # Try to parse value as appropriate type
            def parse_value(val_str):
                """Try to parse value as int, float, bool, or keep as string."""
                val_lower = val_str.lower().strip()
                
                # Boolean values
                if val_lower in ["true", "yes", "on", "1"]:
                    return True
                if val_lower in ["false", "no", "off", "0"]:
                    return False
                
                # Try integer
                try:
                    return int(val_str)
                except ValueError:
                    pass
                
                # Try float
                try:
                    return float(val_str)
                except ValueError:
                    pass
                
                # Return as string
                return val_str
            
            value = parse_value(value_text)
            
            # Handle "me" or current player
            if target_text in ["me", "self"] or target_text == (username or "").lower():
                # Set property on current player's game state
                if property_name in ["location", "max_carry_weight", "user_description"]:
                    if property_name == "location":
                        if value in WORLD:
                            game["location"] = value
                            response = f"Set your location to {value}."
                        else:
                            response = f"Invalid room: {value}"
                    elif property_name == "max_carry_weight":
                        if isinstance(value, (int, float)) and value > 0:
                            game["max_carry_weight"] = float(value)
                            response = f"Set your max_carry_weight to {value}."
                        else:
                            response = "max_carry_weight must be a positive number."
                    elif property_name == "user_description":
                        if len(value_text) <= 500:
                            game["user_description"] = value_text
                            response = f"Set your description to: {value_text}"
                        else:
                            response = "Description must be 500 characters or less."
                elif property_name.startswith("character."):
                    # Set character property: character.stats.str, character.race, etc.
                    char_prop = property_name.split(".", 1)[1]
                    if "character" not in game:
                        game["character"] = {}
                    
                    if char_prop == "race":
                        game["character"]["race"] = value_text
                        response = f"Set character.race to {value_text}."
                    elif char_prop == "gender":
                        game["character"]["gender"] = value_text
                        response = f"Set character.gender to {value_text}."
                    elif char_prop.startswith("stats."):
                        stat_name = char_prop.split(".", 1)[1]
                        if "stats" not in game["character"]:
                            game["character"]["stats"] = {}
                        if isinstance(value, int):
                            game["character"]["stats"][stat_name] = value
                            response = f"Set character.stats.{stat_name} to {value}."
                        else:
                            response = f"Stat values must be integers."
                    else:
                        game["character"][char_prop] = value_text
                        response = f"Set character.{char_prop} to {value_text}."
                elif property_name.startswith("reputation."):
                    # Set reputation with NPC: reputation.innkeeper
                    npc_id = property_name.split(".", 1)[1]
                    if "reputation" not in game:
                        game["reputation"] = {}
                    if isinstance(value, int):
                        game["reputation"][npc_id] = value
                        response = f"Set reputation.{npc_id} to {value}."
                    else:
                        response = "Reputation values must be integers."
                elif property_name in ["teleport_exit_message", "teleport_entrance_message"]:
                    # Custom teleport messages for admin goto command
                    game[property_name] = value_text  # Keep as string to allow {name} placeholder
                    response = f"Set {property_name} to: {value_text}"
                else:
                    # Generic property set
                    game[property_name] = value
                    response = f"Set {property_name} to {value}."
            
            # Try to resolve as another player
            elif who_fn:
                try:
                    active_players = who_fn()
                    target_player = None
                    target_username = None
                    
                    for player_info in active_players:
                        player_username = player_info.get("username", "")
                        if player_username.lower() == target_text:
                            target_username = player_username
                            from app import ACTIVE_GAMES
                            if player_username in ACTIVE_GAMES:
                                target_player = ACTIVE_GAMES[player_username]
                            break
                    
                    if target_player:
                        # Set property on another player's game state
                        if property_name in ["location", "max_carry_weight", "user_description"]:
                            if property_name == "location":
                                if value in WORLD:
                                    target_player["location"] = value
                                    response = f"Set {target_username}'s location to {value}."
                                else:
                                    response = f"Invalid room: {value}"
                            elif property_name == "max_carry_weight":
                                if isinstance(value, (int, float)) and value > 0:
                                    target_player["max_carry_weight"] = float(value)
                                    response = f"Set {target_username}'s max_carry_weight to {value}."
                                else:
                                    response = "max_carry_weight must be a positive number."
                            elif property_name == "user_description":
                                if len(value_text) <= 500:
                                    target_player["user_description"] = value_text
                                    response = f"Set {target_username}'s description to: {value_text}"
                                else:
                                    response = "Description must be 500 characters or less."
                        elif property_name.startswith("character."):
                            char_prop = property_name.split(".", 1)[1]
                            if "character" not in target_player:
                                target_player["character"] = {}
                            
                            if char_prop == "race":
                                target_player["character"]["race"] = value_text
                                response = f"Set {target_username}'s character.race to {value_text}."
                            elif char_prop == "gender":
                                target_player["character"]["gender"] = value_text
                                response = f"Set {target_username}'s character.gender to {value_text}."
                            elif char_prop.startswith("stats."):
                                stat_name = char_prop.split(".", 1)[1]
                                if "stats" not in target_player["character"]:
                                    target_player["character"]["stats"] = {}
                                if isinstance(value, int):
                                    target_player["character"]["stats"][stat_name] = value
                                    response = f"Set {target_username}'s character.stats.{stat_name} to {value}."
                                else:
                                    response = "Stat values must be integers."
                            else:
                                target_player["character"][char_prop] = value_text
                                response = f"Set {target_username}'s character.{char_prop} to {value_text}."
                        else:
                            target_player[property_name] = value
                            response = f"Set {target_username}'s {property_name} to {value}."
                    else:
                        # Not a player, try NPC
                        npc_id, npc = resolve_npc_target(game, target_text)
                        if npc_id and npc:
                            # Set property on NPC state
                            if npc_id not in NPC_STATE:
                                NPC_STATE[npc_id] = {}
                            
                            npc_state = NPC_STATE[npc_id]
                            
                            if property_name == "hp":
                                if isinstance(value, int) and value >= 0:
                                    npc_state["hp"] = value
                                    response = f"Set {npc.name}'s HP to {value}."
                                else:
                                    response = "HP must be a non-negative integer."
                            elif property_name == "alive":
                                if isinstance(value, bool):
                                    npc_state["alive"] = value
                                    response = f"Set {npc.name}'s alive status to {value}."
                                else:
                                    response = "alive must be true or false."
                            elif property_name == "room":
                                if value in WORLD or value == "":
                                    npc_state["room"] = value if value else None
                                    response = f"Set {npc.name}'s room to {value}."
                                else:
                                    response = f"Invalid room: {value}"
                            elif property_name == "home_room":
                                if value in WORLD or value == "":
                                    npc_state["home_room"] = value if value else None
                                    response = f"Set {npc.name}'s home_room to {value}."
                                else:
                                    response = f"Invalid room: {value}"
                            else:
                                npc_state[property_name] = value
                                response = f"Set {npc.name}'s {property_name} to {value}."
                        else:
                            response = f"Could not find target '{target_text}'. Use: set <player/npc> <property> <value>"
                except Exception as e:
                    response = f"Error setting property: {e}"
            else:
                # No who_fn, can't resolve players - try NPC
                npc_id, npc = resolve_npc_target(game, target_text)
                if npc_id and npc:
                    if npc_id not in NPC_STATE:
                        NPC_STATE[npc_id] = {}
                    
                    npc_state = NPC_STATE[npc_id]
                    
                    if property_name == "hp":
                        if isinstance(value, int) and value >= 0:
                            npc_state["hp"] = value
                            response = f"Set {npc.name}'s HP to {value}."
                        else:
                            response = "HP must be a non-negative integer."
                    elif property_name == "alive":
                        if isinstance(value, bool):
                            npc_state["alive"] = value
                            response = f"Set {npc.name}'s alive status to {value}."
                        else:
                            response = "alive must be true or false."
                    elif property_name == "room":
                        if value in WORLD or value == "":
                            npc_state["room"] = value if value else None
                            response = f"Set {npc.name}'s room to {value}."
                        else:
                            response = f"Invalid room: {value}"
                    else:
                        npc_state[property_name] = value
                        response = f"Set {npc.name}'s {property_name} to {value}."
                else:
                    response = f"Could not find target '{target_text}'. Use: set <player/npc> <property> <value>"

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
    
    elif tokens[0] in ["board", "noticeboard", "read board"]:
        # Noticeboard interaction command
        import quests
        from game_engine import GAME_TIME
        loc_id = game.get("location", "town_square")
        current_tick = GAME_TIME.get("tick", 0)
        
        if loc_id not in WORLD:
            response = "You feel disoriented for a moment."
        else:
            # Check if this room has a noticeboard
            room_def = WORLD[loc_id]
            details = room_def.get("details", {})
            has_noticeboard = any(
                detail_id in ["notice_board", "noticeboard", "board"] or 
                detail.get("name", "").lower() in ["notice board", "noticeboard", "board"]
                for detail_id, detail in details.items()
            )
            
            if not has_noticeboard and loc_id != "town_square":
                # Town square always has a noticeboard, but check other rooms
                response = "There's no noticeboard here."
            else:
                if len(tokens) == 1:
                    # Just "board" - show the noticeboard
                    response = quests.render_noticeboard(game, loc_id, current_tick, username=username or "adventurer", active_players_fn=who_fn)
                elif len(tokens) >= 2:
                    # "board <number>" - read a specific posting
                    try:
                        posting_num = int(tokens[1])
                        available_quests = quests.get_noticeboard_quests_for_room(game, loc_id, current_tick, username=username or "adventurer", active_players_fn=who_fn)
                        
                        if 1 <= posting_num <= len(available_quests):
                            template = available_quests[posting_num - 1]
                            # Offer the quest
                            response = quests.offer_quest_to_player(game, username or "adventurer", template.id, f"noticeboard:{loc_id}")
                        else:
                            response = f"There's no posting number {posting_num} on the noticeboard."
                    except ValueError:
                        response = "Usage: 'board' to see postings, or 'board <number>' to read a specific posting."
                else:
                    response = "Usage: 'board' to see postings, or 'board <number>' to read a specific posting."
    
    # Note: 'quests' command is now handled by _handle_quests_command via the registry
    
    elif tokens[0] == "accept" and len(tokens) >= 2 and tokens[1] == "quest":
        # Accept pending quest offer
        import quests
        response = quests.accept_pending_quest(game, username or "adventurer", active_players_fn=who_fn)
    
    elif tokens[0] == "decline" and len(tokens) >= 2 and tokens[1] == "quest":
        # Decline pending quest offer
        import quests
        response = quests.decline_pending_quest(game, username or "adventurer")
    
    # Note: 'help' command is now handled by _handle_help_command via the registry
    
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

    elif tokens[0] == "touch" and len(tokens) >= 2:
        # Touch command for interacting with room details/fixtures
        target_text = " ".join(tokens[1:]).lower()
        
        # Handle "me" or "self" - touching yourself
        if target_text in ["me", "self"] or target_text == (username or "").lower():
            response = "You touch yourself. You feel solid and real."
            return response, game
        
        # Try to resolve as room detail
        detail_id, detail, room_id = resolve_room_detail(game, target_text)
        if detail_id and detail:
            # Check if there's a touch callback
            callback_result = invoke_room_detail_callback("touch", game, username or "adventurer", room_id, detail_id)
            if callback_result:
                response = callback_result
            else:
                # Default response based on stat properties
                detail_name = detail.get("name", detail_id)
                stat = detail.get("stat", {})
                
                # Check temperature property
                temperature = stat.get("temperature")
                if temperature == "hot":
                    response = f"You reach out to touch the {detail_name}, but pull your hand back quickly. It's very hot!"
                elif temperature == "cold":
                    response = f"You touch the {detail_name}. It's cold to the touch, sending a chill through your fingers."
                elif temperature == "warm":
                    response = f"You touch the {detail_name}. It's pleasantly warm."
                else:
                    # Default response if no special properties
                    material = stat.get("material", "")
                    quality = stat.get("quality", "")
                    
                    if material and quality:
                        response = f"You touch the {detail_name}. It's made of {material} and feels {quality}."
                    elif material:
                        response = f"You touch the {detail_name}. It's made of {material}."
                    elif quality:
                        response = f"You touch the {detail_name}. It feels {quality}."
                    else:
                        response = f"You touch the {detail_name}. It feels solid and real."
        else:
            # Not a room detail - check if it's an item or NPC
            item_id, source, container = resolve_item_target(game, target_text)
            if item_id:
                response = f"You touch the {item_id.replace('_', ' ')}. It feels like an ordinary item."
            else:
                npc_id, npc = resolve_npc_target(game, target_text)
                if npc_id and npc:
                    # Use NPC's pronoun with proper verb conjugation
                    pronoun = getattr(npc, 'pronoun', 'they')
                    npc_name = npc.name or "someone"
                    # Conjugate "step" based on pronoun
                    if pronoun in ["he", "she", "it"]:
                        verb = "steps"
                    else:  # they
                        verb = "step"
                    response = f"You reach out to touch {npc_name}, but {pronoun} {verb} back slightly. Perhaps that's not appropriate."
                else:
                    response = f"You don't see anything like '{target_text}' to touch here."

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

    elif tokens[0] == "weather":
        # Weather command - show current weather and season info
        season = get_season()
        time_of_day = get_time_of_day()
        day_of_year = get_day_of_year()
        wtype = WEATHER_STATE.get("type", "clear")
        intensity = WEATHER_STATE.get("intensity", "none")
        temp = WEATHER_STATE.get("temperature", "mild")
        
        response = (
            f"Current Season: {season.capitalize()}\n"
            f"Time of Day: {time_of_day.capitalize()}\n"
            f"Day of Year: {day_of_year + 1} / {DAYS_PER_YEAR}\n"
            f"Weather: {wtype.capitalize()} ({intensity})\n"
            f"Temperature: {temp.capitalize()}"
        )

    else:
        # Any other command clears pending quit
        game.pop("pending_quit", None)
        response = "You mutter some nonsense. (Try 'help' for ideas.)"

    # Note: Logging is now handled centrally in handle_command() after dispatch
    # to avoid duplicate logging for registry vs legacy commands

    return response, game


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
    
    This function now handles time/weather ticking and uses a dispatcher for commands.
    
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
    # Advance game time and update weather
    advance_time(ticks=1)
    update_weather_if_needed()
    update_player_weather_status(game)
    # Update NPC weather status for all NPCs
    update_npc_weather_statuses()
    
    # Clean up old buried items periodically (every command)
    cleanup_buried_items()
    
    # Process NPC periodic actions and weather reactions
    # This shows accumulated NPC actions based on elapsed time since last action
    process_npc_periodic_actions(game, broadcast_fn=broadcast_fn, who_fn=who_fn)
    
    # Process time-based exit states (e.g., tavern door locking)
    process_time_based_exit_states(broadcast_fn=broadcast_fn, who_fn=who_fn)
    
    # Process NPC movements along routes
    process_npc_movements(broadcast_fn=broadcast_fn)
    
    # Process room ambiance (contextual environmental messages based on time, weather, room)
    # Show accumulated messages based on elapsed time since last check
    import ambiance
    current_tick = get_current_game_tick()
    current_room = game.get("location", "town_square")
    accumulated_count = ambiance.get_accumulated_ambiance_messages(current_room, current_tick, game)
    
    if accumulated_count > 0:
        # Generate and show accumulated ambiance messages
        ambiance_messages = []
        for _ in range(accumulated_count):
            msg = ambiance.process_room_ambiance(game, broadcast_fn=broadcast_fn)
            if msg:
                ambiance_messages.extend(msg)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_messages = []
        for msg in ambiance_messages:
            if msg not in seen:
                seen.add(msg)
                unique_messages.append(msg)
        
        if unique_messages:
            game.setdefault("log", [])
            for msg in unique_messages:
                game["log"].append(msg)
            game["log"] = game["log"][-50:]
            # Update the tick tracker
            ambiance.update_ambiance_tick(current_room, current_tick, messages_shown=len(unique_messages))
    
    # Tick quests (check for expired quests)
    import quests
    quests.tick_quests(game, get_current_game_tick())
    
    text = command.strip()
    if not text:
        return "You say nothing.", game

    tokens = text.lower().split()
    verb = tokens[0]
    
    # Normalise tokens to lower case where needed, but keep the original text for content
    lower_tokens = [t.lower() for t in tokens]
    
    # Dispatch the command (handles both registry and legacy commands)
    response, game = dispatch_command(
        verb=lower_tokens[0],
        tokens=lower_tokens,
        raw_command=text,
        game=game,
        username=username,
        user_id=user_id,
        db_conn=db_conn,
        broadcast_fn=broadcast_fn,
        who_fn=who_fn,
    )
    
    # Log the interaction (skip logging for logout confirmation)
    # This ensures ALL commands (both registry and legacy) get logged
    if response != "__LOGOUT__":
        game.setdefault("log", [])
        game["log"].append(f"> {text}")  # Use original command text, not lowercased
        game["log"].append(response)
        # Keep log from growing forever
        game["log"] = game["log"][-50:]
    
    return response, game


def get_global_state_snapshot():
    """
    Returns a JSON-serialisable dict containing global state (ROOM_STATE, NPC_STATE, GAME_TIME, WEATHER_STATE, BURIED_ITEMS, QUEST_GLOBAL_STATE).
    
    Returns:
        dict: {"room_state": ROOM_STATE, "npc_state": NPC_STATE, "game_time": GAME_TIME, "weather_state": WEATHER_STATE, "buried_items": BURIED_ITEMS, "quest_global_state": QUEST_GLOBAL_STATE}
    """
    # Clean up old buried items before saving
    cleanup_buried_items()
    
    return {
        "room_state": ROOM_STATE,
        "npc_state": NPC_STATE,
        "game_time": GAME_TIME,
        "weather_state": WEATHER_STATE,
        "buried_items": BURIED_ITEMS,
        "quest_global_state": QUEST_GLOBAL_STATE,
        "npc_actions_state": NPC_ACTIONS_STATE,
        "npc_route_positions": NPC_ROUTE_POSITIONS,
        "exit_states": EXIT_STATES,
    }


def load_global_state_snapshot(snapshot):
    """
    Updates ROOM_STATE, NPC_STATE, WORLD_CLOCK, GAME_TIME, WEATHER_STATE, BURIED_ITEMS, and QUEST_GLOBAL_STATE from a snapshot dict.
    Backfills missing fields for backward compatibility.
    
    Args:
        snapshot: dict with optional "room_state", "npc_state", "world_clock", "game_time", "weather_state", "buried_items", and "quest_global_state" keys
    """
    global ROOM_STATE, NPC_STATE, WORLD_CLOCK, GAME_TIME, WEATHER_STATE, BURIED_ITEMS, QUEST_GLOBAL_STATE, NPC_ACTIONS_STATE, EXIT_STATES
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
    
    if "game_time" in snapshot and isinstance(snapshot["game_time"], dict):
        GAME_TIME.update(snapshot["game_time"])
        # Ensure required fields exist
        # For backward compatibility, migrate old format to new format
        if "start_timestamp" not in GAME_TIME:
            # If we have old format, try to preserve it or initialize new
            if GAME_TIME.get("last_update_timestamp"):
                # Migrate from old incremental system
                GAME_TIME["start_timestamp"] = GAME_TIME.pop("last_update_timestamp", None)
            if "start_timestamp" not in GAME_TIME or GAME_TIME["start_timestamp"] is None:
                # Initialize with current time if not present
                from datetime import datetime
                GAME_TIME["start_timestamp"] = datetime.now().isoformat()
        # Remove old fields if they exist
        GAME_TIME.pop("tick", None)
        GAME_TIME.pop("minutes", None)
        GAME_TIME.pop("last_update_timestamp", None)
    
    if "weather_state" in snapshot and isinstance(snapshot["weather_state"], dict):
        WEATHER_STATE.update(snapshot["weather_state"])
        # Ensure required fields exist
        if "type" not in WEATHER_STATE:
            WEATHER_STATE["type"] = "clear"
        if "intensity" not in WEATHER_STATE:
            WEATHER_STATE["intensity"] = "none"
        if "temperature" not in WEATHER_STATE:
            WEATHER_STATE["temperature"] = "mild"
        if "last_update_tick" not in WEATHER_STATE:
            WEATHER_STATE["last_update_tick"] = 0
    
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
    
    if "buried_items" in snapshot and isinstance(snapshot["buried_items"], dict):
        BURIED_ITEMS = snapshot["buried_items"]
        # Clean up any items that are too old when loading
        cleanup_buried_items()
    
    if "quest_global_state" in snapshot and isinstance(snapshot["quest_global_state"], dict):
        QUEST_GLOBAL_STATE = snapshot["quest_global_state"]
        # Ensure structure is correct
        for quest_id, quest_state in QUEST_GLOBAL_STATE.items():
            if "active_players" not in quest_state:
                quest_state["active_players"] = []
            if "completions" not in quest_state:
                quest_state["completions"] = {}
            if "first_taken_at" not in quest_state:
                quest_state["first_taken_at"] = None
    
    if "npc_actions_state" in snapshot and isinstance(snapshot["npc_actions_state"], dict):
        NPC_ACTIONS_STATE = snapshot["npc_actions_state"]
        # Ensure structure is correct for each room
        for room_id, room_state in NPC_ACTIONS_STATE.items():
            if "last_action_tick" not in room_state:
                room_state["last_action_tick"] = GAME_TIME.get("tick", 0)
            if "last_weather_change_tick" not in room_state:
                room_state["last_weather_change_tick"] = GAME_TIME.get("tick", 0)
            if "last_weather_state" not in room_state:
                room_state["last_weather_state"] = WEATHER_STATE.copy()
    
    if "npc_route_positions" in snapshot and isinstance(snapshot["npc_route_positions"], dict):
        NPC_ROUTE_POSITIONS = snapshot["npc_route_positions"]
    
    if "exit_states" in snapshot and isinstance(snapshot["exit_states"], dict):
        EXIT_STATES = snapshot["exit_states"]


# Register command handlers
# This is done at module level after all handler functions are defined
register_command("help", _handle_help_command, aliases=["?"])
register_command("quests", _handle_quests_command, aliases=["questlog"])


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
        # Handle [DARK_GREEN]...[/DARK_GREEN] tags if present (convert to HTML)
        if "[DARK_GREEN]" in entry and "[/DARK_GREEN]" in entry:
            entry = re.sub(
                r'\[DARK_GREEN\](.*?)\[/DARK_GREEN\]',
                r'<span style="color: #006400;">\1</span>',
                entry
            )
        # Handle [CYAN]...[/CYAN] tags if present (convert to HTML)
        if "[CYAN]" in entry and "[/CYAN]" in entry:
            entry = re.sub(
                r'\[CYAN\](.*?)\[\/CYAN\]',
                r'<span style="color: #00ffff; font-weight: 500;">\1</span>',
                entry
            )
        processed.append(entry)
    return processed

