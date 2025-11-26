from typing import Dict, Optional

class ReputationSystem:
    """
    Manages reputation and standing with various factions.
    """
    
    def __init__(self):
        # Faction ID -> Score (0-100)
        # 0-20: Hated
        # 21-40: Disliked
        # 41-60: Neutral
        # 61-80: Liked
        # 81-100: Revered
        self.standings: Dict[str, int] = {}
        
        # Default starting values
        self.defaults = {
            "townsfolk": 50,
            "guards": 50,
            "thieves_guild": 20,
            "mages_guild": 40
        }

    def initialize(self, existing_data: Optional[Dict[str, int]] = None):
        """Initialize with existing data or defaults."""
        if existing_data:
            self.standings = existing_data.copy()
        else:
            self.standings = self.defaults.copy()

    def modify_reputation(self, faction: str, amount: int) -> int:
        """
        Modify reputation with a faction. Returns new value.
        """
        current = self.standings.get(faction, 50)
        new_val = max(0, min(100, current + amount))
        self.standings[faction] = new_val
        return new_val

    def get_standing(self, faction: str) -> int:
        """Get raw reputation score."""
        return self.standings.get(faction, 50)

    def get_status(self, faction: str) -> str:
        """Get text description of standing."""
        score = self.get_standing(faction)
        if score <= 20: return "Hated"
        if score <= 40: return "Disliked"
        if score <= 60: return "Neutral"
        if score <= 80: return "Liked"
        return "Revered"

    def to_dict(self) -> Dict[str, int]:
        """Serialize for saving."""
        return self.standings
