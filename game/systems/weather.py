"""
Weather System - Manages dynamic weather with seasonal variations.

Provides 8 weather types with intensity levels, temperature tracking,
and season-based probability transitions.
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional


class WeatherSystem:
    """Manages comprehensive weather simulation."""
    
    # Weather types
    WEATHER_TYPES = [
        "clear", "windy", "rain", "storm", "snow", "sleet", "overcast", "heatwave"
    ]
    
    # Weather intensities
    INTENSITIES = ["none", "light", "moderate", "heavy"]
    
    # Temperature levels
    TEMPERATURES = ["cold", "chilly", "mild", "warm", "hot"]
    
    def __init__(self):
        self.current_type: str = "clear"
        self.current_intensity: str = "none"
        self.current_temperature: str = "mild"
        self.last_update_tick: int = 0
    
    def update(self, current_tick: int, season: str) -> Tuple[bool, Optional[str]]:
        """
        Update weather state based on season and time.
        Called periodically to create weather transitions.
        
        Args:
            current_tick: Current game tick
            season: Current season ("spring", "summer", "autumn", "winter")
        
        Returns:
            Tuple[bool, Optional[str]]: (True if weather changed, transition_message or None)
        """
        # Update weather every 10 ticks (roughly every 10 game minutes)
        if current_tick - self.last_update_tick < 10:
            return False, None
        
        self.last_update_tick = current_tick
        
        # Temperature by season
        season_temp = {
            "spring": ["mild", "chilly"],
            "summer": ["warm", "hot"],
            "autumn": ["mild", "chilly"],
            "winter": ["cold", "chilly"],
        }
        
        # Check if weather is locked (manually set via setweather)
        # If locked, don't allow automatic changes
        from game.state import WEATHER_STATE
        if WEATHER_STATE.get("locked", False):
            return False, None
        
        # Use realistic weather transitions instead of random changes
        from game.systems.weather_transitions import get_realistic_weather_transition
        from game_engine import get_time_of_day
        
        # Get realistic transition (returns (new_type, new_intensity, transition_message) or (None, None, None))
        new_type, new_intensity, transition_message = get_realistic_weather_transition(
            current_type=self.current_type,
            current_intensity=self.current_intensity,
            season=season,
            locked=False
        )
        
        if new_type or new_intensity:
            old_type = self.current_type
            old_intensity = self.current_intensity
            
            # Update type and/or intensity
            if new_type:
                self.current_type = new_type
            if new_intensity:
                self.current_intensity = new_intensity
            
            # Update temperature based on season and weather
            temp_options = season_temp.get(season, ["mild"])
            if self.current_type in ["snow", "sleet"]:
                self.current_temperature = "cold"
            elif self.current_type == "heatwave":
                self.current_temperature = "hot"
            else:
                self.current_temperature = random.choice(temp_options)
            
            # Return True if type or intensity changed, along with transition message
            changed = (old_type != self.current_type) or (old_intensity != self.current_intensity)
            return changed, transition_message
        
        return False, None
    
    def get_description(self) -> str:
        """
        Get a descriptive string for the current weather.
        
        Returns:
            str: Description of current weather (e.g., "It is raining heavily.")
        """
        wtype = self.current_type
        intensity = self.current_intensity
        temp = self.current_temperature
        
        if wtype == "clear":
            return f"The sky is clear and the air is {temp}."
        elif wtype == "overcast":
            return f"The sky is overcast and the air is {temp}."
        elif wtype == "windy":
            return f"It is {intensity} windy and {temp}."
        elif wtype == "rain":
            return f"It is raining ({intensity}) and {temp}."
        elif wtype == "storm":
            return f"A {intensity} storm is raging."
        elif wtype == "snow":
            return f"It is snowing ({intensity}) and {temp}."
        elif wtype == "sleet":
            return f"Sleet is falling ({intensity}) and it is {temp}."
        elif wtype == "heatwave":
            return f"A heatwave is in effect; it is sweltering."
            
        return f"The weather is {wtype}."

    def get_state(self) -> Dict[str, str]:
        """Get current weather state."""
        return {
            "type": self.current_type,
            "intensity": self.current_intensity,
            "temperature": self.current_temperature
        }
    
    def apply_to_description(self, description: str, time_of_day: str) -> str:
        """
        Apply weather-aware modifications to a room description.
        
        Args:
            description: The base room description
            time_of_day: Current time of day (dawn/day/dusk/night)
        
        Returns:
            str: Modified description that reflects weather conditions
        """
        wtype = self.current_type
        intensity = self.current_intensity
        temp = self.current_temperature
        
        modified = description
        
        # Wind modifications
        if wtype == "windy":
            if intensity == "heavy":
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
        
        # Rain/snow/sleet modifications
        if wtype in ["rain", "snow", "sleet"] and intensity == "heavy":
            if time_of_day == "night":
                if "pitch dark of night" in modified:
                    if wtype == "rain":
                        modified = modified.replace("pitch dark of night", "pitch dark of night, with torrential rain lashing down")
                    elif wtype == "snow":
                        modified = modified.replace("pitch dark of night", "pitch dark of night, with blinding snow")
                    elif wtype == "sleet":
                        modified = modified.replace("pitch dark of night", "pitch dark of night, with freezing sleet")
        
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
        
        return modified
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence."""
        return {
            "type": self.current_type,
            "intensity": self.current_intensity,
            "temperature": self.current_temperature,
            "last_update_tick": self.last_update_tick
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load from dictionary."""
        self.current_type = data.get("type", "clear")
        self.current_intensity = data.get("intensity", "none")
        self.current_temperature = data.get("temperature", "mild")
        self.last_update_tick = data.get("last_update_tick", 0)


class WeatherStatusTracker:
    """Tracks weather exposure status for entities (players/NPCs)."""
    
    # Minimum seconds between weather status updates (allows gradual decay/accumulation)
    UPDATE_INTERVAL_SECONDS = 5
    
    def __init__(self):
        self.wetness: int = 0  # 0-10 scale
        self.cold: int = 0     # 0-10 scale
        self.heat: int = 0     # 0-10 scale
        self.last_update_tick: int = 0
        self.last_update_time: Optional[str] = None  # ISO format timestamp
    
    def update(self, current_tick: int, is_outdoor: bool, weather_state: Dict[str, str], season: str) -> None:
        """
        Update status based on current location and weather.
        
        Args:
            current_tick: Current game tick
            is_outdoor: Whether entity is in an outdoor room
            weather_state: Current weather state dict
            season: Current season
        """
        now = datetime.now()
        
        # Check if enough time has passed since last update (time-based throttling)
        if self.last_update_time:
            try:
                last_update = datetime.fromisoformat(self.last_update_time)
                elapsed_seconds = (now - last_update).total_seconds()
                if elapsed_seconds < self.UPDATE_INTERVAL_SECONDS:
                    # Not enough time has passed, skip update
                    return
            except (ValueError, TypeError):
                # Invalid timestamp, allow update
                pass
        
        # Update timestamp
        self.last_update_time = now.isoformat()
        self.last_update_tick = current_tick
        
        # Get weather conditions
        wtype = weather_state.get("type", "clear")
        intensity = weather_state.get("intensity", "none")
        temp = weather_state.get("temperature", "mild")
        
        if not is_outdoor:
            # Indoor: faster decay for all status (shelter provides warmth/dryness)
            # Decay rate: 2 per update (faster than outdoor)
            if self.wetness > 0:
                self.wetness = max(0, self.wetness - 2)
            if self.cold > 0:
                # Wetness slows warming (wet clothes take longer to dry/warm)
                if self.wetness > 0:
                    self.cold = max(0, self.cold - 1)  # Slower if wet
                else:
                    self.cold = max(0, self.cold - 2)  # Faster if dry
            if self.heat > 0:
                self.heat = max(0, self.heat - 2)
            return
        
        # Outdoor: apply weather effects and conditional decay
        # Wetness from rain/snow/sleet/storm
        if wtype in ["rain", "snow", "sleet", "storm"]:
            if intensity == "light":
                self.wetness = min(10, self.wetness + 1)
            elif intensity == "moderate":
                self.wetness = min(10, self.wetness + 2)
            elif intensity == "heavy":
                self.wetness = min(10, self.wetness + 3)
        else:
            # Gradually dry off outdoors (slower than indoors)
            if self.wetness > 0:
                self.wetness = max(0, self.wetness - 1)
        
        # Cold accumulation and decay
        # Note: "chilly" is mild and doesn't accumulate cold, only "cold" does
        if season == "winter" or wtype in ["snow", "sleet"] or temp == "cold":
            # Accumulate cold from severe conditions
            if intensity in ["moderate", "heavy"] or temp == "cold":
                self.cold = min(10, self.cold + 2)
            else:
                self.cold = min(10, self.cold + 1)
        else:
            # Gradually warm up outdoors when conditions allow
            # Being wet slows warming (wet clothes conduct heat away), but body heat still works
            if self.cold > 0:
                # Always allow decay - wetness naturally slows it because you stay wet longer
                # The time-based update system (5 seconds) already provides natural rate limiting
                self.cold = max(0, self.cold - 1)
        
        # Heat accumulation and decay
        if season == "summer" or wtype == "heatwave" or temp in ["hot", "warm"]:
            if wtype == "heatwave" and intensity == "heavy":
                self.heat = min(10, self.heat + 2)
            elif temp == "hot" or (wtype == "heatwave" and intensity in ["moderate", "heavy"]):
                self.heat = min(10, self.heat + 2)
            else:
                self.heat = min(10, self.heat + 1)
        else:
            # Gradually cool down when conditions allow
            if self.heat > 0:
                # Wetness helps cool down faster (evaporation)
                if self.wetness > 0:
                    self.heat = max(0, self.heat - 2)  # Faster cooling if wet
                else:
                    self.heat = max(0, self.heat - 1)  # Normal cooling
    
    def has_status(self) -> bool:
        """Check if entity has any weather status effects."""
        return max(self.wetness, self.cold, self.heat) > 0
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "wetness": self.wetness,
            "cold": self.cold,
            "heat": self.heat,
            "last_update_tick": self.last_update_tick,
            "last_update_time": self.last_update_time
        }
    
    def from_dict(self, data: Dict) -> None:
        """Load from dictionary."""
        self.wetness = data.get("wetness", 0)
        self.cold = data.get("cold", 0)
        self.heat = data.get("heat", 0)
        self.last_update_tick = data.get("last_update_tick", 0)
        self.last_update_time = data.get("last_update_time")
