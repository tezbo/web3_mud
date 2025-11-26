"""
Lunar System - Manages moon phases and lunar cycles.

Tracks 8 moon phases over a 30-day cycle.
"""
from typing import Dict, Any

# Lunar cycle constants
MOON_CYCLE_DAYS = 30  # Length of a full lunar cycle in in-game days


class LunarSystem:
    """Manages moon phases and lunar cycles."""
    
    # 8 moon phases
    PHASES = [
        "new",
        "waxing_crescent",
        "first_quarter",
        "waxing_gibbous",
        "full",
        "waning_gibbous",
        "last_quarter",
        "waning_crescent",
    ]
    
    # Human-readable phase descriptions
    PHASE_DESCRIPTIONS = {
        "new": "new moon",
        "waxing_crescent": "waxing crescent moon",
        "first_quarter": "waxing half moon",
        "waxing_gibbous": "waxing gibbous moon",
        "full": "full moon",
        "waning_gibbous": "waning gibbous moon",
        "last_quarter": "waning half moon",
        "waning_crescent": "waning crescent moon",
    }
    
    def __init__(self):
        self.lunar_cycle_start_day: int = 0
    
    def get_moon_phase(self, day_of_year: int) -> str:
        """
        Get the current moon phase based on days elapsed.
        
        Args:
            day_of_year: Current day of the year
        
        Returns:
            str: Current moon phase name
        """
        # Initialize lunar cycle start day if needed (first call)
        if self.lunar_cycle_start_day == 0:
            self.lunar_cycle_start_day = day_of_year
        
        # Calculate days into current cycle
        days_in_cycle = (day_of_year - self.lunar_cycle_start_day) % MOON_CYCLE_DAYS
        
        # Divide cycle into 8 phases (approx 3.75 days per phase)
        phase_length = MOON_CYCLE_DAYS / 8
        phase_index = int(days_in_cycle / phase_length) % 8
        
        return self.PHASES[phase_index]
    
    def get_moon_phase_description(self, day_of_year: int) -> str:
        """
        Get a descriptive text about the current moon phase.
        
        Args:
            day_of_year: Current day of the year
        
        Returns:
            str: Descriptive moon phase text
        """
        phase = self.get_moon_phase(day_of_year)
        return self.PHASE_DESCRIPTIONS.get(phase, "moon")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence."""
        return {
            "lunar_cycle_start_day": self.lunar_cycle_start_day
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load from dictionary."""
        self.lunar_cycle_start_day = data.get("lunar_cycle_start_day", 0)
