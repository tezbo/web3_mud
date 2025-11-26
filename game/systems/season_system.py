"""
Season System - Manages seasonal cycles and calendar.

Provides 4 seasons and 12 thematic month names for the Hollowvale world.
"""
from typing import Tuple

# Time constants
DAYS_PER_YEAR = 120  # Must match time_system.py


class SeasonSystem:
    """Manages seasonal progression and calendar."""
    
    # Thematic month names for Hollowvale
    MONTH_NAMES = [
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
    
    def __init__(self):
        pass
    
    def get_season(self, day_of_year: int) -> str:
        """
        Get the current season based on day of year.
        
        Args:
            day_of_year: Day of the year (0 to DAYS_PER_YEAR-1)
        
        Returns:
            str: "spring", "summer", "autumn", or "winter"
        """
        days_per_season = DAYS_PER_YEAR // 4
        
        if 0 <= day_of_year < days_per_season:
            return "spring"
        elif days_per_season <= day_of_year < days_per_season * 2:
            return "summer"
        elif days_per_season * 2 <= day_of_year < days_per_season * 3:
            return "autumn"
        else:
            return "winter"
    
    def get_month(self, day_of_year: int) -> str:
        """
        Get the current month name based on day of year.
        Year has 12 months, each approximately 10 days (120 days / 12 months = 10 days/month).
        
        Args:
            day_of_year: Day of the year (0 to DAYS_PER_YEAR-1)
        
        Returns:
            str: Month name (e.g., "Firstmoon", "Thawtide", etc.)
        """
        days_per_month = DAYS_PER_YEAR // 12
        month_index = day_of_year // days_per_month
        return self.MONTH_NAMES[month_index]
    
    def get_day_of_month(self, day_of_year: int) -> int:
        """
        Get the current day of the month (1-based).
        
        Args:
            day_of_year: Day of the year (0 to DAYS_PER_YEAR-1)
        
        Returns:
            int: Day of month (1 to ~10)
        """
        days_per_month = DAYS_PER_YEAR // 12
        day_of_month = (day_of_year % days_per_month) + 1
        return day_of_month
    
    def is_first_day_of_season(self, day_of_year: int) -> bool:
        """
        Check if it's the first day of a new season.
        
        Args:
            day_of_year: Day of the year (0 to DAYS_PER_YEAR-1)
        
        Returns:
            bool: True if it's the first day of a season
        """
        days_per_season = DAYS_PER_YEAR // 4
        return day_of_year % days_per_season == 0
    
    def get_previous_season(self, current_season: str) -> str:
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
