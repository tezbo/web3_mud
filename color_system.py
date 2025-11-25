"""
Color system for Tiny Web MUD.

Provides customizable color preferences for different message types.
Users can set colors via the 'colour' command, and preferences persist in game state.
"""

from typing import Dict, Optional

# Default color settings
DEFAULT_COLORS = {
    "say": "cyan",           # Player/NPC speech
    "emote": "white",        # Social gestures
    "tell": "yellow",        # Private messages
    "exits": "darkgreen",    # Exit descriptions
    "weather": "darkyellow", # Weather messages
    "room_descriptions": "white",  # Location descriptions
    "command": "blue",       # Command prompts ("> ")
    "error": "red",          # Error messages
    "success": "green",      # Success messages
    "npc": "orange",         # NPC messages
    "system": "gray",        # System messages
    "wallet": "lightgreen",  # Wallet info
    "quest": "lightblue",    # Quest messages
    "ambiance": "lightgray", # Ambient room messages
}

# Valid color names that can be used
VALID_COLORS = {
    "black", "white", "gray", "grey", "lightgray", "lightgrey", "darkgray", "darkgrey",
    "red", "darkred", "lightred", "pink", "darkpink",
    "green", "darkgreen", "lightgreen", "lime",
    "blue", "darkblue", "lightblue", "cyan",
    "yellow", "darkyellow", "lightyellow", "gold",
    "orange", "darkorange", "lightorange",
    "purple", "darkpurple", "lightpurple", "magenta",
    "brown", "tan", "beige",
}

# Map of color names to hex codes for frontend
COLOR_HEX_MAP = {
    "black": "#000000",
    "white": "#ffffff",
    "gray": "#808080",
    "grey": "#808080",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "red": "#ff0000",
    "darkred": "#8b0000",
    "lightred": "#ff6b6b",
    "pink": "#ffc0cb",
    "darkpink": "#c71585",
    "green": "#00ff00",
    "darkgreen": "#006400",
    "lightgreen": "#90ee90",
    "lime": "#00ff00",
    "blue": "#0000ff",
    "darkblue": "#00008b",
    "lightblue": "#add8e6",
    "cyan": "#00ffff",
    "yellow": "#ffff00",
    "darkyellow": "#b8860b",
    "lightyellow": "#ffffe0",
    "gold": "#ffd700",
    "orange": "#ffa500",
    "darkorange": "#ff8c00",
    "lightorange": "#ffd4a3",
    "purple": "#800080",
    "darkpurple": "#4b0082",
    "lightpurple": "#d8bfd8",
    "magenta": "#ff00ff",
    "brown": "#a52a2a",
    "tan": "#d2b48c",
    "beige": "#f5f5dc",
}


def get_color_settings(game: Dict) -> Dict[str, str]:
    """
    Get color settings for a player, with defaults if not set.
    
    Args:
        game: Game state dictionary
    
    Returns:
        dict: Color settings dictionary
    """
    if "color_settings" not in game:
        game["color_settings"] = DEFAULT_COLORS.copy()
    return game["color_settings"]


def get_color_for_type(game: Dict, color_type: str) -> str:
    """
    Get the color for a specific message type.
    
    Args:
        game: Game state dictionary
        color_type: Type of message (e.g., "say", "emote", "tell")
    
    Returns:
        str: Color name (defaults to "white" if not found)
    """
    settings = get_color_settings(game)
    return settings.get(color_type, DEFAULT_COLORS.get(color_type, "white"))


def set_color_for_type(game: Dict, color_type: str, color: str):
    """
    Set the color for a specific message type.
    
    Args:
        game: Game state dictionary
        color_type: Type of message (e.g., "say", "emote", "tell")
        color: Color name (must be valid)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if color_type not in DEFAULT_COLORS:
        return False, f"Unknown color type: {color_type}. Valid types: {', '.join(sorted(DEFAULT_COLORS.keys()))}"
    
    color_lower = color.lower()
    if color_lower not in VALID_COLORS:
        return False, f"Unknown color: {color}. Valid colors: {', '.join(sorted(VALID_COLORS))}"
    
    settings = get_color_settings(game)
    settings[color_type] = color_lower
    return True, f"Color for {color_type} set to {color_lower}."


def reset_colors(game: Dict) -> str:
    """
    Reset all colors to defaults.
    
    Args:
        game: Game state dictionary
    
    Returns:
        str: Confirmation message
    """
    game["color_settings"] = DEFAULT_COLORS.copy()
    return "All colors reset to defaults."


def wrap_with_color_tag(text: str, color_type: str, game: Dict) -> str:
    """
    Wrap text with appropriate color tag based on user's color preference.
    
    Args:
        text: Text to wrap
        color_type: Type of message (e.g., "say", "emote", "tell")
        game: Game state dictionary
    
    Returns:
        str: Text wrapped with color tag (e.g., "[CYAN]text[/CYAN]")
    """
    color = get_color_for_type(game, color_type)
    
    # Use the semantic type as the tag name (e.g., [SAY], [TELL])
    # This allows the frontend to apply the correct user-configured color
    tag_name = color_type.upper()
    
    # Wrap text with semantic tag
    return f"[{tag_name}]{text}[/{tag_name}]"


def get_color_hex(color_name: str) -> str:
    """
    Get hex color code for a color name.
    
    Args:
        color_name: Color name (e.g., "cyan", "yellow")
    
    Returns:
        str: Hex color code (defaults to white if not found)
    """
    return COLOR_HEX_MAP.get(color_name.lower(), "#ffffff")
