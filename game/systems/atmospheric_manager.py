"""
Atmospheric Manager - Coordinates time, weather, seasons, and lunar systems.

This unified manager provides a single interface for all atmospheric systems
and handles complex interactions like sunrise/sunset notifications.
"""
from typing import Dict, Any, List, Tuple, Optional
from game.systems.time_system import TimeSystem
from game.systems.season_system import SeasonSystem
from game.systems.lunar_system import LunarSystem
from game.systems.weather import WeatherSystem


class AtmosphericManager:
    """Manages all atmospheric systems in a coordinated fashion."""
    
    def __init__(self):
        self.time = TimeSystem()
        self.seasons = SeasonSystem()
        self.lunar = LunarSystem()
        self.weather = WeatherSystem()
        
        # Tracking for notifications
        self.last_sunrise_minute: int = -1
        self.last_sunset_minute: int = -1
    
    def update(self) -> Tuple[bool, Optional[str]]:
        """
        Update all atmospheric systems.
        Should be called on every player command.
        
        Returns:
            Tuple[bool, Optional[str]]: (True if weather changed, transition_message or None)
        """
        from game.state import WEATHER_STATE
        
        # If weather is locked (manually set), sync WeatherSystem FROM WEATHER_STATE
        # instead of allowing automatic changes
        if WEATHER_STATE.get("locked", False):
            # Sync WeatherSystem to match WEATHER_STATE (locked weather takes precedence)
            weather_data = {
                "type": WEATHER_STATE.get("type", "clear"),
                "intensity": WEATHER_STATE.get("intensity", "none"),
                "temperature": WEATHER_STATE.get("temperature", "mild"),
                "last_update_tick": WEATHER_STATE.get("last_update_tick", 0),
            }
            self.weather.from_dict(weather_data)
            return False, None  # No change when locked
        
        current_tick = self.time.get_current_tick()
        day_of_year = self.time.get_day_of_year()
        season = self.seasons.get_season(day_of_year)
        
        # Update weather (may change based on season)
        weather_changed, transition_message = self.weather.update(current_tick, season)
        
        # Sync to global WEATHER_STATE if weather changed
        if weather_changed:
            WEATHER_STATE.update(self.weather.to_dict())
        
        return weather_changed, transition_message
    
    def get_combined_description(self, is_outdoor: bool = True) -> str:
        """
        Get a combined time-of-day,moon phase, and weather description in a single coherent line.
        This is displayed in the weather line (dark yellow) for outdoor rooms.
        
        Args:
            is_outdoor: Whether the room is outdoor
        
        Returns:
            str: Combined atmospheric description
        """
        # Read weather from WEATHER_STATE BEFORE updating (to preserve manually set weather)
        # This ensures descriptions match what the weather command shows
        from game.state import WEATHER_STATE
        weather_type = WEATHER_STATE.get("type", "clear")
        weather_intensity = WEATHER_STATE.get("intensity", "none")
        
        # DEBUG: Log what we're reading
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[WEATHER_DESC_DEBUG] Reading weather_type={weather_type}, intensity={weather_intensity} from WEATHER_STATE")
        
        # Update atmospheric systems to ensure current time
        # Note: update() may change weather, but we use the pre-update value for consistency
        self.update()
        
        # DEBUG: Log after update
        logger.info(f"[WEATHER_DESC_DEBUG] After update: WEATHER_STATE={WEATHER_STATE.get('type')}, using weather_type={weather_type} (preserved from before update)")
        
        # Use legacy time functions directly to ensure perfect sync with time command
        from game_engine import get_current_hour_in_minutes, get_time_of_day, get_season, get_day_of_year
        
        # Force sync TimeSystem timestamp before using legacy functions
        from game.state import GAME_TIME
        if GAME_TIME.get("start_timestamp") and self.time.start_timestamp != GAME_TIME["start_timestamp"]:
            self.time.start_timestamp = GAME_TIME["start_timestamp"]
            self.time.from_dict({"start_timestamp": GAME_TIME["start_timestamp"]})
        
        # Use legacy functions for minutes/season/day, but calculate time_of_day directly to ensure correctness
        minutes = get_current_hour_in_minutes()
        season = get_season()
        day_of_year = get_day_of_year()
        
        # Calculate time_of_day directly from minutes (don't trust legacy function)
        from game_engine import get_sunrise_sunset_times
        sunrise_min, sunset_min = get_sunrise_sunset_times()
        dawn_start = max(0, sunrise_min - 30)
        dawn_end = sunrise_min + 30
        dusk_start = max(0, sunset_min - 30)
        dusk_end = min(24 * 60, sunset_min + 30)
        
        # Calculate time_of_day directly from minutes
        if dawn_start <= minutes < dawn_end:
            time_of_day = "dawn"
        elif dawn_end <= minutes < dusk_start:
            time_of_day = "day"
        elif dusk_start <= minutes < dusk_end:
            time_of_day = "dusk"
        else:
            time_of_day = "night"
        
        # Debug: Log time calculation
        hour = minutes // 60
        minute = minutes % 60
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[WEATHER_DEBUG] minutes={minutes} ({hour:02d}:{minute:02d}), time_of_day={time_of_day}, season={season}")
        
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
        
        # Outdoor rooms - combine time, moon, and weather
        # Use the FRESH weather state from self.weather (which was just updated)
        # This ensures the description matches the actual current state, even if it just changed
        weather_state = self.weather.get_state()
        weather_type = weather_state.get("type", "clear")
        weather_intensity = weather_state.get("intensity", "none")
        
        moon_phase = self.lunar.get_moon_phase(day_of_year)
        moon_desc = self.lunar.get_moon_phase_description(day_of_year)
        
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
            elif weather_type == "heatwave":
                return "The sun beats down mercilessly in the sweltering heat, baking the land."
            elif weather_type == "windy":
                if weather_intensity == "heavy":
                    return "Strong winds howl through the day, making it hard to keep your footing."
                else:
                    return "A brisk wind tugs at your clothes as the day progresses."
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
            else:
                return "Evening settles in, bringing darkness as the day ends."
        
        # Night (with moon phases)
        else:
            moon_visible = moon_phase != "new" and weather_type not in ["overcast", "storm", "fog"]
            
            if weather_type == "clear":
                if moon_phase == "new":
                    return "The night is pitch black under clear skies. The new moon provides no light, leaving only the faintest stars visible."
                elif moon_phase == "full":
                    return "Clear skies stretch overhead, and the land is bathed in the bright silvery light of the full moon."
                elif moon_phase in ["waxing_gibbous", "waning_gibbous"]:
                    return f"Clear skies stretch overhead, and the land is lit up by the bright light of the {moon_desc}."
                else:
                    return f"Clear skies stretch overhead, the {moon_desc} and stars providing the only light."
            elif weather_type == "snow" and moon_visible:
                if moon_phase == "full":
                    return "Snow falls steadily through the night, the full moon's light reflecting off the white ground."
                else:
                    return f"Snow drifts down through the night, the {moon_desc} casting an eerie glow on the falling flakes."
            elif weather_type == "rain":
                if weather_intensity == "heavy":
                    return "Heavy rain pounds down through the darkness, soaking everything below."
                else:
                    return "Rain falls steadily through the night, pattering against the ground."
            elif weather_type == "storm":
                return "A fierce storm rages through the night, thunder and lightning illuminating the darkness."
            elif weather_type == "sleet":
                return "Icy sleet pelts down through the night, making the darkness even more miserable."
            elif weather_type == "fog":
                return "Thick fog blankets the night, reducing visibility to almost nothing."
            elif weather_type == "windy":
                temp_desc = self.weather.current_temperature
                if weather_intensity == "heavy":
                    return f"A howling {temp_desc} wind tears through the darkness, the only sound in the night."
                else:
                    return f"A {temp_desc} wind blows through the night, rustling unseen leaves."
            elif weather_type == "overcast":
                return "The night is dark under heavy cloud cover, blocking out stars and moon alike."
            else:
                return "The night is dark and moonless."
    
    def check_sunrise_sunset_transitions(self) -> List[Tuple[str, str]]:
        """
        Check for sunrise/sunset transitions and generate notification messages.
        
        Returns:
            list: List of (message_type, message_text) tuples for notifications
        """
        notifications = []
        
        current_minutes = self.time.get_current_hour_in_minutes()
        day_of_year = self.time.get_day_of_year()
        season = self.seasons.get_season(day_of_year)
        sunrise_min, sunset_min = self.time.get_sunrise_sunset_times(season)
        
        weather_state = self.weather.get_state()
        wtype = weather_state["type"]
        intensity = weather_state["intensity"]
        
        # Check for sunrise (within 1 minute window)
        if abs(current_minutes - sunrise_min) <= 1 and self.last_sunrise_minute != sunrise_min:
            self.last_sunrise_minute = sunrise_min
            season_name = season.capitalize()
            
            # Generate weather-aware sunrise message
            if wtype == "rain":
                if intensity == "heavy":
                    message = f"[WEATHER]The sun struggles to rise through heavy clouds and driving rain, marking the start of a new {season_name} day.[/WEATHER]"
                else:
                    message = f"[WEATHER]The sun rises through rain, its light diffused by clouds, marking the start of a new {season_name} day.[/WEATHER]"
            elif wtype == "snow":
                message = f"[WEATHER]The sun rises through falling snow, its light soft and muted, marking the start of a new {season_name} day.[/WEATHER]"
            elif wtype == "clear":
                message = f"[WEATHER]The sun rises over Hollowvale, marking the start of a new {season_name} day.[/WEATHER]"
            else:
                message = f"[WEATHER]The sun rises, marking the start of a new {season_name} day.[/WEATHER]"
            
            notifications.append(("sunrise", message))
        
        # Check for sunset (within 1 minute window)
        if abs(current_minutes - sunset_min) <= 1 and self.last_sunset_minute != sunset_min:
            self.last_sunset_minute = sunset_min
            season_name = season.capitalize()
            
            # Generate weather-aware sunset message
            if wtype == "clear":
                message = f"[WEATHER]The sun sets over Hollowvale, painting the sky in brilliant colors as {season_name} evening arrives.[/WEATHER]"
            elif wtype == "overcast":
                message = f"[WEATHER]The sun sets behind thick clouds, darkness falling quickly as {season_name} evening arrives.[/WEATHER]"
            else:
                message = f"[WEATHER]The sun sets, and {season_name} evening settles over the land.[/WEATHER]"
            
            notifications.append(("sunset", message))
        
        return notifications
    
    def apply_weather_to_description(self, description: str) -> str:
        """
        Apply weather modifications to a room description.
        
        Args:
            description: Base room description
        
        Returns:
            str: Weather-modified description
        """
        day_of_year = self.time.get_day_of_year()
        season = self.seasons.get_season(day_of_year)
        time_of_day = self.time.get_time_of_day(season)
        
        return self.weather.apply_to_description(description, time_of_day)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize all systems to dictionary for persistence."""
        return {
            "time": self.time.to_dict(),
            "lunar": self.lunar.to_dict(),
            "weather": self.weather.to_dict(),
            "last_sunrise_minute": self.last_sunrise_minute,
            "last_sunset_minute": self.last_sunset_minute
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load all systems from dictionary."""
        if "time" in data:
            self.time.from_dict(data["time"])
        if "lunar" in data:
            self.lunar.from_dict(data["lunar"])
        if "weather" in data:
            self.weather.from_dict(data["weather"])
        self.last_sunrise_minute = data.get("last_sunrise_minute", -1)
        self.last_sunset_minute = data.get("last_sunset_minute", -1)


# Global singleton instance
_atmospheric_manager: Optional[AtmosphericManager] = None

def get_atmospheric_manager() -> AtmosphericManager:
    """Get or create the global atmospheric manager instance."""
    global _atmospheric_manager
    from game.state import WEATHER_STATE, GAME_TIME
    
    if _atmospheric_manager is None:
        _atmospheric_manager = AtmosphericManager()
        
        # Load from global WEATHER_STATE if available
        if WEATHER_STATE:
            _atmospheric_manager.weather.from_dict(WEATHER_STATE)
    
    # ALWAYS sync TimeSystem start_timestamp with GAME_TIME (ensure they're always in sync)
    # Priority: Use GAME_TIME if it exists and is valid, otherwise use TimeSystem's timestamp
    if GAME_TIME and "start_timestamp" in GAME_TIME and GAME_TIME["start_timestamp"]:
        # Sync TimeSystem to GAME_TIME (legacy system is the source of truth)
        if _atmospheric_manager.time.start_timestamp != GAME_TIME["start_timestamp"]:
            _atmospheric_manager.time.from_dict({"start_timestamp": GAME_TIME["start_timestamp"]})
    else:
        # Sync GAME_TIME to TimeSystem's timestamp (newer system provides timestamp)
        if _atmospheric_manager.time.start_timestamp:
            GAME_TIME["start_timestamp"] = _atmospheric_manager.time.start_timestamp
    
    return _atmospheric_manager

def sync_weather_state():
    """Sync the atmospheric manager's weather state to global WEATHER_STATE."""
    from game.state import WEATHER_STATE
    atmos = get_atmospheric_manager()
    weather_data = atmos.weather.to_dict()
    WEATHER_STATE.update(weather_data)
