"""
Admin Commands - Commands for administrators and testing.
"""
from typing import Tuple, Dict, Any, Optional, List

def handle_setweather_command(
    verb: str,
    tokens: List[str],
    game: Dict[str, Any],
    username: str,
    user_id: Optional[str] = None,
    db_conn: Optional[Any] = None,
    broadcast_fn: Optional[Any] = None,
    who_fn: Optional[Any] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Admin command to set weather for testing.
    Usage: setweather <type> [intensity] | setweather unlock | setweather lock
    
    Types: clear, rain, snow, storm, fog, windy, sleet, heatwave
    Intensities: none, light, moderate, heavy
    
    Special commands:
    - setweather unlock - Unlock weather to allow automatic transitions
    - setweather lock - Lock weather to prevent automatic changes
    """
    # Check if user is admin (for now, allow all for testing)
    # TODO: Add proper admin check
    
    if len(tokens) < 2:
        return """Usage: setweather <type> [intensity] | setweather unlock | setweather lock

Types: clear, rain, snow, storm, fog, windy, sleet, heatwave
Intensities: none, light, moderate, heavy

Special commands:
  setweather unlock - Unlock weather to allow automatic transitions
  setweather lock - Lock weather to prevent automatic changes

Examples:
  setweather rain heavy
  setweather snow light
  setweather clear
  setweather unlock""", game
    
    weather_type = tokens[1].lower()
    
    # Handle special unlock/lock commands
    if weather_type == "unlock":
        from game.state import WEATHER_STATE
        WEATHER_STATE['locked'] = False
        return "Weather unlocked. Automatic transitions are now enabled.", game
    
    if weather_type == "lock":
        from game.state import WEATHER_STATE
        WEATHER_STATE['locked'] = True
        return "Weather locked. Automatic transitions are now disabled.", game
    
    intensity = tokens[2].lower() if len(tokens) > 2 else "moderate"
    
    # Validate weather type
    valid_types = ["clear", "rain", "snow", "storm", "fog", "windy", "sleet", "heatwave"]
    if weather_type not in valid_types:
        return f"Invalid weather type '{weather_type}'. Valid types: {', '.join(valid_types)}", game
    
    # Validate intensity
    valid_intensities = ["none", "light", "moderate", "heavy"]
    if intensity not in valid_intensities:
        return f"Invalid intensity '{intensity}'. Valid intensities: {', '.join(valid_intensities)}", game
    
    # Special case: clear weather should have 'none' intensity
    if weather_type == "clear":
        intensity = "none"
    
    # Update WEATHER_STATE first
    from game.state import WEATHER_STATE, GAME_TIME
    WEATHER_STATE['type'] = weather_type
    WEATHER_STATE['intensity'] = intensity
    WEATHER_STATE['locked'] = True  # Lock weather to prevent automatic changes
    # Preserve temperature if it exists, otherwise use default
    if 'temperature' not in WEATHER_STATE:
        WEATHER_STATE['temperature'] = 'mild'
    
    # Update the Atmospheric Manager's WeatherSystem to match
    from game.systems.atmospheric_manager import get_atmospheric_manager
    atmos = get_atmospheric_manager()
    
    # Get current tick to set last_update_tick (prevents immediate random changes)
    current_tick = GAME_TIME.get("tick", 0)
    
    # Fully sync WeatherSystem from WEATHER_STATE, but update last_update_tick to current
    # This prevents update() from immediately overriding manually set weather
    weather_data = WEATHER_STATE.copy()
    weather_data['last_update_tick'] = current_tick
    atmos.weather.from_dict(weather_data)
    
    # Broadcast to all outdoor rooms if broadcast function available
    if broadcast_fn:
        message = f"The weather suddenly shifts to {weather_type}"
        if intensity != "none":
            message += f" ({intensity})"
        message += "!"
        
        # Get all active players and broadcast to outdoor rooms
        if who_fn:
            from game_engine import WORLD
            players = who_fn()
            rooms_notified = set()
            for player_info in players:
                player_location = player_info.get("location", "town_square")
                if player_location in rooms_notified:
                    continue
                # Check if room is outdoor
                if player_location in WORLD:
                    room_def = WORLD[player_location]
                    if room_def.get("outdoor", False):
                        broadcast_fn(player_location, message)
                        rooms_notified.add(player_location)
    
    return f"Weather set to {weather_type} ({intensity}).", game
