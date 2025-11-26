"""
Weather System - Manages dynamic weather with seasonal variations.

Provides 8 weather types with intensity levels, temperature tracking,
and season-based probability transitions.
"""
import random
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
    
    def update(self, current_tick: int, season: str) -> bool:
        """
        Update weather state based on season and time.
        Called periodically to create weather transitions.
        
        Args:
            current_tick: Current game tick
            season: Current season ("spring", "summer", "autumn", "winter")
        
        Returns:
            bool: True if weather changed, False otherwise
        """
        # Update weather every 10 ticks (roughly every 10 game minutes)
        if current_tick - self.last_update_tick < 10:
            return False
        
        self.last_update_tick = current_tick
        
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
            new_type = self.current_type  # Default: stay same
            
            for wtype, prob in weather_probs.items():
                cumulative += prob
                if rand <= cumulative:
                    new_type = wtype
                    break
            
            old_type = self.current_type
            self.current_type = new_type
            
            # Set intensity based on weather type
            if new_type in ["rain", "snow", "sleet"]:
                intensities = ["light", "moderate", "heavy"]
                weights = [0.4, 0.4, 0.2]
                self.current_intensity = random.choices(intensities, weights=weights)[0]
            elif new_type == "windy":
                intensities = ["light", "moderate", "heavy"]
                weights = [0.3, 0.5, 0.2]
                self.current_intensity = random.choices(intensities, weights=weights)[0]
            elif new_type == "heatwave":
                intensities = ["moderate", "heavy"]
                weights = [0.6, 0.4]
                self.current_intensity = random.choices(intensities, weights=weights)[0]
            elif new_type == "storm":
                intensities = ["moderate", "heavy"]
                weights = [0.5, 0.5]
                self.current_intensity = random.choices(intensities, weights=weights)[0]
            elif new_type == "overcast":
                intensities = ["light", "moderate"]
                weights = [0.5, 0.5]
                self.current_intensity = random.choices(intensities, weights=weights)[0]
            else:
                self.current_intensity = "none"
            
            # Update temperature based on season and weather
            temp_options = season_temp.get(season, ["mild"])
            if self.current_type in ["snow", "sleet"]:
                self.current_temperature = "cold"
            elif self.current_type == "heatwave":
                self.current_temperature = "hot"
            else:
                self.current_temperature = random.choice(temp_options)
            
            return old_type != new_type
        
        return False
    
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
    
    def __init__(self):
        self.wetness: int = 0  # 0-10 scale
        self.cold: int = 0     # 0-10 scale
        self.heat: int = 0     # 0-10 scale
        self.last_update_tick: int = 0
    
    def update(self, current_tick: int, is_outdoor: bool, weather_state: Dict[str, str], season: str) -> None:
        """
        Update status based on current location and weather.
        
        Args:
            current_tick: Current game tick
            is_outdoor: Whether entity is in an outdoor room
            weather_state: Current weather state dict
            season: Current season
        """
        if current_tick <= self.last_update_tick:
            return
        
        self.last_update_tick = current_tick
        
        if not is_outdoor:
            # Indoor: gradually decay all status
            if self.wetness > 0:
                self.wetness = max(0, self.wetness - 1)
            if self.cold > 0:
                self.cold = max(0, self.cold - 1)
            if self.heat > 0:
                self.heat = max(0, self.heat - 1)
            return
        
        # Outdoor: apply weather effects
        wtype = weather_state.get("type", "clear")
        intensity = weather_state.get("intensity", "none")
        temp = weather_state.get("temperature", "mild")
        
        # Wetness from rain/snow/sleet
        if wtype in ["rain", "snow", "sleet"]:
            if intensity == "light":
                self.wetness = min(10, self.wetness + 1)
            elif intensity == "moderate":
                self.wetness = min(10, self.wetness + 2)
            elif intensity == "heavy":
                self.wetness = min(10, self.wetness + 3)
        else:
            # Gradually dry off
            if self.wetness > 0:
                self.wetness = max(0, self.wetness - 1)
        
        # Cold from winter/snow/sleet/cold temps
        if season == "winter" or wtype in ["snow", "sleet"] or temp in ["cold", "chilly"]:
            if intensity in ["moderate", "heavy"] or temp == "cold":
                self.cold = min(10, self.cold + 2)
            else:
                self.cold = min(10, self.cold + 1)
        else:
            # Gradually warm up
            if self.cold > 0:
                self.cold = max(0, self.cold - 1)
        
        # Heat from summer/hot temps
        if season == "summer" or temp in ["hot", "warm"]:
            if temp == "hot":
                self.heat = min(10, self.heat + 2)
            else:
                self.heat = min(10, self.heat + 1)
        else:
            # Gradually cool down
            if self.heat > 0:
                self.heat = max(0, self.heat - 1)
    
    def has_status(self) -> bool:
        """Check if entity has any weather status effects."""
        return max(self.wetness, self.cold, self.heat) > 0
    
    def to_dict(self) -> Dict[str, int]:
        """Serialize to dictionary."""
        return {
            "wetness": self.wetness,
            "cold": self.cold,
            "heat": self.heat,
            "last_update_tick": self.last_update_tick
        }
    
    def from_dict(self, data: Dict[str, int]) -> None:
        """Load from dictionary."""
        self.wetness = data.get("wetness", 0)
        self.cold = data.get("cold", 0)
        self.heat = data.get("heat", 0)
        self.last_update_tick = data.get("last_update_tick", 0)
