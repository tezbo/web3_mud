"""
Game State Module
Holds the mutable global state of the game.
"""
import os
from datetime import datetime
from game.world.data import WORLD

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
QUEST_GLOBAL_STATE = {}

# --- Quest-Specific Items (items only visible to quest owners) ---
QUEST_SPECIFIC_ITEMS = {}



# --- NPC Route Positions ---
NPC_ROUTE_POSITIONS = {}

# --- Exit States (locked/unlocked/timed) ---
EXIT_STATES = {}

# --- NPC State (relationships, memory) ---
NPC_STATE = {}

# --- World Clock (tracks in-game time) ---
WORLD_CLOCK = {
    "start_time": datetime.now().isoformat(),
    "last_restock": {},
    "current_period": "day",
    "last_period_change_hour": 0
}

IN_GAME_HOUR_DURATION = float(os.environ.get("IN_GAME_HOUR_DURATION", "1.0"))
IN_GAME_DAY_DURATION = float(os.environ.get("IN_GAME_DAY_DURATION", "2.0"))

# --- Game Time State ---
GAME_TIME = {
    "start_timestamp": datetime.now().isoformat(),
}

# --- Weather State ---
WEATHER_STATE = {
    "type": "clear",
    "intensity": "none",
    "temperature": "mild",
    "last_update_tick": 0,
    "next_change_tick": 100,  # Initial change after 100 ticks
    "wind_direction": "none",
    "wind_speed": "calm",
    "locked": False  # If True, weather cannot be automatically changed by update()
}
