"""
Time System - Manages continuous time progression and day/night cycles.

This system tracks game time at 12x real-world speed:
- 1 in-game day = 2 real-world hours
- 1 real-world minute = 12 in-game minutes
"""
from datetime import datetime
from typing import Tuple, Dict, Any


# Time constants
TICKS_PER_MINUTE = 1
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_YEAR = 120  # Short in-game year for gameplay


class TimeSystem:
    """Manages continuous global time progression."""
    
    def __init__(self):
        self.start_timestamp: str = datetime.now().isoformat()
        self.last_season: str = None
        
    def get_current_minutes(self) -> int:
        """
        Calculate current game time in minutes based on elapsed real-world time.
        Uses GAME_TIME from game.state to ensure consistency with legacy system.
        
        Time conversion rate:
        - 1 in-game day = 2 real-world hours = 120 real-world minutes
        - 1 in-game day = 24 in-game hours = 1440 in-game minutes
        - Therefore: 1 in-game minute = 1/12 real-world minutes = 5 real-world seconds
        - Or: 1 real-world minute = 12 in-game minutes
        
        Returns:
            int: Total in-game minutes elapsed since game start
        """
        # Use GAME_TIME from game.state (shared with legacy system) to ensure perfect sync
        from game.state import GAME_TIME
        
        # Ensure start_timestamp is synced
        if not self.start_timestamp or (GAME_TIME.get("start_timestamp") and GAME_TIME["start_timestamp"] != self.start_timestamp):
            if GAME_TIME.get("start_timestamp"):
                self.start_timestamp = GAME_TIME["start_timestamp"]
            elif self.start_timestamp:
                GAME_TIME["start_timestamp"] = self.start_timestamp
        
        # Use GAME_TIME timestamp if available, otherwise use self.start_timestamp
        timestamp_to_use = GAME_TIME.get("start_timestamp") or self.start_timestamp
        
        # Calculate elapsed real-world time since start
        start_time = datetime.fromisoformat(timestamp_to_use)
        elapsed_real_seconds = (datetime.now() - start_time).total_seconds()
        elapsed_real_minutes = elapsed_real_seconds / 60.0
        
        # Convert to in-game minutes: 1 real-world minute = 12 in-game minutes
        elapsed_game_minutes = elapsed_real_minutes * 12.0
        
        return int(elapsed_game_minutes)
    
    def get_current_tick(self) -> int:
        """
        Calculate current game tick based on elapsed real-world time.
        
        Returns:
            int: Current game tick count
        """
        minutes = self.get_current_minutes()
        return minutes * TICKS_PER_MINUTE
    
    def get_current_hour_in_minutes(self) -> int:
        """
        Get current hour in minutes from midnight (0-1439).
        
        Returns:
            int: Current hour in minutes (0-1439)
        """
        total_minutes = self.get_current_minutes()
        minutes_in_day = total_minutes % (HOURS_PER_DAY * MINUTES_PER_HOUR)
        return int(minutes_in_day)
    
    def get_current_hour_12h(self) -> int:
        """
        Get current hour in 12-hour format (1-12).
        
        Returns:
            int: Current hour (1-12)
        """
        total_minutes = self.get_current_minutes()
        minutes_in_day = total_minutes % (HOURS_PER_DAY * MINUTES_PER_HOUR)
        hour_24h = int(minutes_in_day // MINUTES_PER_HOUR)
        
        # Convert to 12-hour format
        if hour_24h == 0:
            return 12
        elif hour_24h <= 12:
            return hour_24h
        else:
            return hour_24h - 12
    
    def get_day_of_year(self) -> int:
        """
        Get the current day of the year (0-based).
        
        Returns:
            int: Day of year (0 to DAYS_PER_YEAR-1)
        """
        total_minutes = self.get_current_minutes()
        days_elapsed = total_minutes // (HOURS_PER_DAY * MINUTES_PER_HOUR)
        return days_elapsed % DAYS_PER_YEAR
    
    def get_sunrise_sunset_times(self, season: str) -> Tuple[int, int]:
        """
        Get sunrise and sunset times in minutes for the given season.
        
        Args:
            season: Current season string ("spring", "summer", "autumn", "winter")
        
        Returns:
            tuple: (sunrise_minutes, sunset_minutes) from midnight
        """
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
        
        return (sunrise_times.get(season, 6 * 60), 
                sunset_times.get(season, 20 * 60))
    
    def get_time_of_day(self, season: str) -> str:
        """
        Get the time of day based on current in-game minutes and seasonal sunrise/sunset.
        
        Args:
            season: Current season string
        
        Returns:
            str: "night", "dawn", "day", or "dusk"
        """
        minutes_in_day = self.get_current_hour_in_minutes()
        sunrise_min, sunset_min = self.get_sunrise_sunset_times(season)
        
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence."""
        return {
            "start_timestamp": self.start_timestamp,
            "last_season": self.last_season
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load from dictionary."""
        self.start_timestamp = data.get("start_timestamp", self.start_timestamp)
        self.last_season = data.get("last_season")
