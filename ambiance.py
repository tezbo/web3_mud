"""
Ambiance system for rooms and NPCs.

Generates contextual environmental messages based on:
- Time of day
- Weather
- Room type and description
- Room features

These messages make the world feel alive and dynamic.
"""

import random
from typing import Dict, List, Optional

# Room ambiance messages organized by room type, time of day, and weather
ROOM_AMBIENCE: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    # Generic indoor room ambiance
    "indoor": {
        "dawn": {
            "clear": [
                "A beam of early morning light filters through a window, illuminating dust motes dancing in the air.",
                "The first rays of sunlight creep in, casting long shadows across the floor.",
                "Morning light streams through the windows, warming the room gradually.",
            ],
            "rain": [
                "Raindrops tap softly against the windows in the early morning light.",
                "The sound of gentle rain against glass fills the quiet dawn hours.",
                "Morning light struggles through rain-streaked windows.",
            ],
            "storm": [
                "Thunder rumbles in the distance as dawn breaks, the sound muffled by the walls.",
                "Lightning flashes outside the windows, briefly illuminating the room.",
                "The building creaks slightly as wind buffets against it in the early morning storm.",
            ],
            "windy": [
                "Wind whistles around the building, making the windows rattle softly.",
                "A gust of wind makes the shutters creak in the early morning.",
                "The sound of wind outside contrasts with the stillness inside.",
            ],
            "default": [
                "The room is quiet in the early morning hours.",
                "Dawn light gradually brightens the space.",
            ],
        },
        "day": {
            "clear": [
                "Sunlight streams through the windows, creating warm pools of light.",
                "A gentle breeze makes the curtains flutter slightly.",
                "The room is filled with bright, cheerful light.",
            ],
            "rain": [
                "Rain patters steadily against the windows.",
                "The sound of rain creates a soothing rhythm in the background.",
                "Water runs in rivulets down the windowpanes.",
            ],
            "storm": [
                "Thunder echoes through the building, making the windows shake.",
                "Lightning flashes outside, casting brief, stark shadows across the room.",
                "The storm rages outside, but you're safe within these walls.",
            ],
            "windy": [
                "Wind howls around the building, making the structure groan.",
                "A strong gust rattles the windows and doors.",
                "The wind outside makes the building creak and settle.",
            ],
            "default": [
                "The room feels peaceful and quiet.",
                "Time seems to pass slowly here.",
            ],
        },
        "dusk": {
            "clear": [
                "The light fades gradually, painting the room in warm, golden tones.",
                "Long shadows stretch across the floor as evening approaches.",
                "The last rays of sunlight cast a warm glow through the windows.",
            ],
            "rain": [
                "Evening rain taps against the windows as daylight fades.",
                "The sound of rain grows more pronounced as the room darkens.",
                "Raindrops glisten on the windows in the fading light.",
            ],
            "storm": [
                "Thunder rolls as evening falls, the storm intensifying.",
                "Lightning illuminates the room in brief, dramatic flashes.",
                "The evening storm makes the building feel like a small refuge.",
            ],
            "windy": [
                "Wind picks up as evening falls, making the shutters rattle.",
                "The building groans under the evening wind.",
                "A gust of wind makes the windows shudder.",
            ],
            "default": [
                "Evening settles in, bringing a sense of calm.",
                "The room grows darker as daylight fades.",
            ],
        },
        "night": {
            "clear": [
                "Moonlight filters through the windows, casting silvery patterns on the floor.",
                "Shadows move subtly in the corners as clouds drift past the moon outside.",
                "The room is dark, lit only by faint starlight through the windows.",
            ],
            "rain": [
                "Rain continues to fall outside, its sound more noticeable in the quiet night.",
                "The steady patter of rain against the windows is the only sound.",
                "Rain streaks the windows, distorting the view of the dark night outside.",
            ],
            "storm": [
                "Thunder crashes outside, shaking the windows in their frames.",
                "Lightning strikes nearby, briefly lighting the room in stark white.",
                "The night storm makes the building feel like a small, fragile shelter.",
            ],
            "windy": [
                "Wind moans around the building in the darkness.",
                "The windows rattle as gusts of wind buffet the structure.",
                "The building creaks and groans in the night wind.",
            ],
            "default": [
                "The room is dark and quiet in the night.",
                "Shadows seem to shift and move in the corners.",
            ],
        },
    },
    # Generic outdoor room ambiance
    "outdoor": {
        "dawn": {
            "clear": [
                "A gentle morning breeze rustles through the area, carrying the scent of dew.",
                "The first light of dawn casts long, dramatic shadows that seem to move as you watch.",
                "Birds begin to sing as the sky lightens overhead.",
                "Mist rises from the ground in the cool morning air.",
            ],
            "rain": [
                "Light rain falls steadily, each drop creating ripples on the wet ground.",
                "The morning rain makes everything glisten with moisture.",
                "A cool, wet breeze carries the fresh scent of rain-soaked earth.",
            ],
            "storm": [
                "Thunder rumbles overhead as dawn breaks through the storm clouds.",
                "Lightning flashes, briefly illuminating everything in stark relief.",
                "The morning storm rages, wind whipping through the area.",
            ],
            "windy": [
                "A strong breeze sweeps through, making leaves dance and branches sway.",
                "Wind whips past, carrying leaves and dust through the air.",
                "Gusts of wind create patterns in the grass and make branches creak.",
            ],
            "fog": [
                "Thick fog clings to the ground, obscuring details and making shapes seem to move.",
                "Morning mist drifts through the area, creating an otherworldly atmosphere.",
                "The fog moves and shifts, sometimes revealing, sometimes concealing.",
            ],
            "default": [
                "Morning light gradually illuminates the area.",
                "The world slowly wakes up around you.",
            ],
        },
        "day": {
            "clear": [
                "A soft breeze drifts past, rustling leaves and carrying scents on the air.",
                "Shadows shift slightly as clouds pass overhead.",
                "Birds can be heard in the distance, going about their day.",
                "Sunlight dapples through any nearby vegetation, creating patterns of light and shadow.",
            ],
            "rain": [
                "Rain falls steadily, creating a rhythmic sound as it hits the ground and foliage.",
                "Water drips from leaves and branches, creating a constant patter.",
                "The rain makes the air feel fresh and clean.",
            ],
            "storm": [
                "Thunder booms overhead, and rain falls in sheets.",
                "Lightning flashes, followed by the crash of thunder.",
                "The storm rages around you, wind and rain combining in a fierce display.",
            ],
            "windy": [
                "A strong wind blows through, making everything sway and move.",
                "Leaves and small debris swirl in the air as gusts pass by.",
                "The wind creates a constant rustling and creaking from nearby trees and structures.",
            ],
            "heatwave": [
                "The heat shimmers in the air, making distant objects appear to waver.",
                "Even the breeze feels warm, offering little relief from the sun.",
                "Everything seems to move slowly in the oppressive heat.",
            ],
            "fog": [
                "Fog drifts through the area, creating an eerie, muted atmosphere.",
                "Visibility is reduced, and shapes in the mist seem to move and shift.",
                "The fog muffles sounds, making everything feel distant.",
            ],
            "default": [
                "The area feels peaceful and alive.",
                "Time seems to move at its own pace here.",
            ],
        },
        "dusk": {
            "clear": [
                "Evening shadows lengthen and stretch across the ground.",
                "A cool breeze picks up as the day comes to an end.",
                "The light takes on a warm, golden quality as evening approaches.",
                "Birds begin to settle down as twilight descends.",
            ],
            "rain": [
                "Evening rain continues to fall, each drop catching the last light.",
                "The rain intensifies slightly as daylight fades.",
                "Wet surfaces glisten in the fading evening light.",
            ],
            "storm": [
                "The evening storm shows no signs of letting up.",
                "Lightning illuminates the darkening sky in brief, dramatic flashes.",
                "Thunder rumbles as evening falls, the storm becoming more ominous in the darkness.",
            ],
            "windy": [
                "Evening winds pick up, creating a constant rustling and movement.",
                "Gusts of wind become more frequent as the day ends.",
                "The wind carries the chill of approaching night.",
            ],
            "default": [
                "Evening settles in, bringing a sense of peace.",
                "The world begins to quiet down as day turns to night.",
            ],
        },
        "night": {
            "clear": [
                "A cool night breeze whispers past, making shadows dance in the moonlight.",
                "Something moves in the corner of your eye—just a shadow, or perhaps something more?",
                "The night is alive with subtle sounds: rustling leaves, distant animals, the whisper of wind.",
                "Moonlight creates shifting patterns as clouds drift across the sky.",
                "Shadows seem to move and shift at the edges of your vision.",
            ],
            "rain": [
                "Rain continues to fall in the darkness, its sound amplified in the quiet night.",
                "Each raindrop glistens briefly when lightning or moonlight catches it.",
                "The steady rhythm of rain creates a hypnotic background to the night.",
            ],
            "storm": [
                "The night storm rages, with lightning illuminating everything in stark, brief flashes.",
                "Thunder crashes overhead, so loud it seems to shake the ground.",
                "The darkness makes the storm feel more threatening and wild.",
            ],
            "windy": [
                "Wind howls through the night, creating an eerie, restless atmosphere.",
                "The night wind carries strange sounds from far away.",
                "Gusts of wind make everything sway and creak in the darkness.",
            ],
            "fog": [
                "Thick fog blankets everything, reducing visibility to mere feet.",
                "Shapes drift and shift in the fog, some real, some perhaps imagined.",
                "The night fog makes everything feel disconnected and mysterious.",
            ],
            "default": [
                "The night is dark and full of subtle sounds and movements.",
                "Shadows seem to have a life of their own in the darkness.",
            ],
        },
    },
}

# Room-specific ambiance overrides (for special rooms)
ROOM_SPECIFIC_AMBIENCE: Dict[str, Dict[str, List[str]]] = {
    "tavern": {
        "day": [
            "The hearth crackles, sending sparks dancing up the chimney.",
            "Footsteps can be heard from the floor above as someone moves about.",
            "The scent of cooking food wafts from the kitchen.",
            "A tankard clinks against a table somewhere nearby.",
        ],
        "night": [
            "The fire in the hearth roars, casting flickering shadows that dance across the walls.",
            "Laughter and conversation create a warm, convivial atmosphere.",
            "The sound of tankards clinking fills the air.",
            "Shadows from the firelight create moving patterns on the ceiling.",
        ],
    },
    "town_square": {
        "day": [
            "The fountain's water creates a soothing, constant trickle.",
            "Footsteps echo on the cobblestones as people go about their business.",
            "The belltower's shadow moves slowly across the square as the day progresses.",
            "A breeze makes the notice board's parchment flutter and rustle.",
        ],
        "night": [
            "The fountain's water sounds louder in the quiet night.",
            "Moonlight reflects off the wet cobblestones after the evening's activities.",
            "Shadows from the belltower stretch across the square like reaching fingers.",
            "The notice board creaks softly in the night breeze.",
        ],
    },
    "forest_edge": {
        "day": [
            "Leaves rustle in the breeze, creating a constant, whispery sound.",
            "Birds can be heard calling from deeper in the forest.",
            "Shadows from the trees create shifting patterns on the ground.",
            "The forest seems to watch and wait just beyond the edge.",
        ],
        "night": [
            "The forest at night seems alive with unseen movement.",
            "Something rustles in the underbrush—perhaps just an animal, but it's hard to be sure.",
            "The darkness between the trees feels deep and impenetrable.",
            "Shadows shift at the edge of the forest, making you question what you see.",
        ],
    },
    "whispering_trees": {
        "day": [
            "The trees seem to whisper to each other as wind moves through their branches.",
            "Dappled sunlight filters through the canopy, creating shifting patterns.",
            "The forest floor rustles with small creatures going about their day.",
        ],
        "night": [
            "The forest seems to come alive in the darkness, full of sounds and movements.",
            "Shadows move between the trees, some natural, some perhaps not.",
            "The whispering of the trees takes on an almost sentient quality in the night.",
        ],
    },
    "watchtower": {
        "day": [
            "A strong wind blows at this height, making the tower creak slightly.",
            "The view from here is expansive, with the valley spread out below.",
            "Flags or banners flutter in the wind if any are present.",
        ],
        "night": [
            "The tower sways slightly in the night wind, a reminder of how high you are.",
            "The darkness below seems vast and mysterious from this height.",
            "Wind howls around the tower's edges, creating an eerie sound.",
        ],
    },
    "smithy": {
        "day": [
            "The forge radiates heat, making the air shimmer around it.",
            "The sound of hammer on metal echoes through the space.",
            "Sparks fly from the forge as fuel is added.",
        ],
        "night": [
            "Even at night, the forge may still glow with banked coals.",
            "Metal tools clink softly as they cool in the evening air.",
            "The smithy feels different at night, quiet but still holding the day's heat.",
        ],
    },
    "market_lane": {
        "day": [
            "The sounds of commerce fill the air—voices, footsteps, the clink of coins.",
            "Canvas awnings flutter in the breeze over empty stalls.",
            "The scent of various goods—spices, flowers, goods—hangs in the air.",
        ],
        "night": [
            "The empty stalls cast long shadows in the moonlight.",
            "Canvas covers rustle in the night breeze, creating soft, ghostly sounds.",
            "The market is quiet now, waiting for morning to bring life back.",
        ],
    },
    "shrine_of_the_forgotten": {
        "day": [
            "An atmosphere of peace and reverence fills the space.",
            "The light here seems softer, more gentle than elsewhere.",
            "Ancient symbols seem to catch and hold the light in interesting ways.",
        ],
        "night": [
            "The shrine feels more mysterious in the darkness.",
            "Moonlight creates strange patterns on the ancient carvings.",
            "There's a sense that something watches from the shadows—perhaps just the old gods.",
        ],
    },
}


def get_room_ambiance(room_id: str, room_def: Dict, time_of_day: str, weather_type: str, weather_intensity: str) -> Optional[str]:
    """
    Generate a contextual ambiance message for a room.
    
    Args:
        room_id: The room ID
        room_def: The room definition dict
        time_of_day: "dawn", "day", "dusk", or "night"
        weather_type: Weather type (e.g., "clear", "rain", "windy")
        weather_intensity: Weather intensity (e.g., "none", "light", "moderate", "heavy")
    
    Returns:
        str or None: An ambiance message, or None if no appropriate message
    """
    is_outdoor = room_def.get("outdoor", False)
    room_type = "outdoor" if is_outdoor else "indoor"
    
    # Check for room-specific ambiance first
    if room_id in ROOM_SPECIFIC_AMBIENCE:
        room_ambiance = ROOM_SPECIFIC_AMBIENCE[room_id]
        if time_of_day in room_ambiance:
            messages = room_ambiance[time_of_day]
            return random.choice(messages)
    
    # Use generic ambiance based on room type, time, and weather
    if room_type in ROOM_AMBIENCE:
        time_ambiance = ROOM_AMBIENCE[room_type].get(time_of_day, {})
        
        # Try weather-specific messages first
        if weather_type in time_ambiance:
            messages = time_ambiance[weather_type]
            return random.choice(messages)
        
        # Fall back to default
        if "default" in time_ambiance:
            messages = time_ambiance["default"]
            return random.choice(messages)
    
    return None


def process_room_ambiance(game: Dict, broadcast_fn=None) -> List[str]:
    """
    Process and return room ambiance messages for the player's current location.
    This should be called periodically (based on elapsed time, not commands).
    
    Args:
        game: Player's game state dict
        broadcast_fn: Optional callback for broadcasting to room
    
    Returns:
        list: List of ambiance messages to add to the log
    """
    from game_engine import WORLD, WEATHER_STATE, get_time_of_day
    
    loc_id = game.get("location", "town_square")
    if loc_id not in WORLD:
        return []
    
    room_def = WORLD[loc_id]
    time_of_day = get_time_of_day()
    weather_type = WEATHER_STATE.get("type", "clear")
    weather_intensity = WEATHER_STATE.get("intensity", "none")
    
    # Get ambiance message
    ambiance_msg = get_room_ambiance(loc_id, room_def, time_of_day, weather_type, weather_intensity)
    
    if ambiance_msg:
        # Format with cyan color tag for consistency
        return [f"[CYAN]{ambiance_msg}[/CYAN]"]
    
    return []


# Track when ambiance was last shown for each room
AMBIANCE_STATE: Dict[str, Dict[str, int]] = {}  # {room_id: {"last_ambiance_tick": int}}


def get_accumulated_ambiance_messages(room_id: str, current_tick: int, game: Dict) -> int:
    """
    Calculate how many ambiance messages should have accumulated since last check.
    Ambiance appears roughly every 15-25 in-game minutes (~1-2 real-world minutes).
    
    Args:
        room_id: The room ID
        current_tick: Current game tick
        game: Game state dict (for getting room ambiance)
    
    Returns:
        int: Number of ambiance messages that should be shown (0 or more)
    """
    if room_id not in AMBIANCE_STATE:
        AMBIANCE_STATE[room_id] = {"last_ambiance_tick": current_tick}
        return 1  # Show first message immediately
    
    last_tick = AMBIANCE_STATE[room_id].get("last_ambiance_tick", current_tick)
    elapsed_ticks = current_tick - last_tick
    
    # Show ambiance roughly every 15-25 game minutes
    # At 12x speed: 15 game minutes = 1.25 real-world minutes, 25 = ~2 minutes
    # This makes rooms feel more alive
    min_interval = 15  # 15 game minutes
    max_interval = 25  # 25 game minutes
    
    if elapsed_ticks >= min_interval:
        # Calculate how many messages should have accumulated
        # Each message appears every 15-25 ticks
        interval = (min_interval + max_interval) / 2  # Average ~20 ticks
        accumulated = int(elapsed_ticks / interval)
        
        # Cap at reasonable number to avoid spam (max 5 messages at once)
        return min(accumulated, 5)
    
    return 0


def update_ambiance_tick(room_id: str, current_tick: int, messages_shown: int = 1):
    """
    Update the last ambiance tick for a room.
    
    Args:
        room_id: The room ID
        current_tick: Current game tick
        messages_shown: Number of messages shown (to calculate proper interval)
    """
    if room_id not in AMBIANCE_STATE:
        AMBIANCE_STATE[room_id] = {}
    
    # Update based on how many messages were shown
    # Each message represents ~20 ticks of elapsed time
    interval_per_message = 20
    AMBIANCE_STATE[room_id]["last_ambiance_tick"] = current_tick - (current_tick % interval_per_message)

