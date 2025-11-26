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
    
    def update(self) -> bool:
        """
        Update all atmospheric systems.
        Should be called on every player command.
        
        Returns:
            bool: True if weather changed
        """
        current_tick = self.time.get_current_tick()
        day_of_year = self.time.get_day_of_year()
        season = self.seasons.get_season(day_of_year)
        
        # Update weather (may change based on season)
        weather_changed = self.weather.update(current_tick, season)
        
        return weather_changed
    
    def get_combined_description(self, is_outdoor: bool = True) -> str:
        """
        Get a combined time-of-day,moon phase, and weather description in a single coherent line.
        This is displayed in the weather line (dark yellow) for outdoor rooms.
        
        Args:
            is_outdoor: Whether the room is outdoor
        
        Returns:
            str: Combined atmospheric description
        """
        day_of_year = self.time.get_day_of_year()
        season = self.seasons.get_season(day_of_year)
        time_of_day = self.time.get_time_of_day(season)
        
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
        weather_state = self.weather.get_state()
        weather_type = weather_state["type"]
        weather_intensity = weather_state["intensity"]
        
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
                    message = f"[CYAN]The sun struggles to rise through heavy clouds and driving rain, marking the start of a new {season_name} day.[/CYAN]"
                else:
                    message = f"[CYAN]The sun rises through rain, its light diffused by clouds, marking the start of a new {season_name} day.[/CYAN]"
            elif wtype == "snow":
                message = f"[CYAN]The sun rises through falling snow, its light soft and muted, marking the start of a new {season_name} day.[/CYAN]"
            elif wtype == "clear":
                message = f"[CYAN]The sun rises over Hollowvale, marking the start of a new {season_name} day.[/CYAN]"
            else:
                message = f"[CYAN]The sun rises, marking the start of a new {season_name} day.[/CYAN]"
            
            notifications.append(("sunrise", message))
        
        # Check for sunset (within 1 minute window)
        if abs(current_minutes - sunset_min) <= 1 and self.last_sunset_minute != sunset_min:
            self.last_sunset_minute = sunset_min
            season_name = season.capitalize()
            
            # Generate weather-aware sunset message
            if wtype == "clear":
                message = f"[CYAN]The sun sets over Hollowvale, painting the sky in brilliant colors as {season_name} evening arrives.[/CYAN]"
            elif wtype == "overcast":
                message = f"[CYAN]The sun sets behind thick clouds, darkness falling quickly as {season_name} evening arrives.[/CYAN]"
            else:
                message = f"[CYAN]The sun sets, and {season_name} evening settles over the land.[/CYAN]"
            
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
    if _atmospheric_manager is None:
        _atmospheric_manager = AtmosphericManager()
    return _atmospheric_manager
