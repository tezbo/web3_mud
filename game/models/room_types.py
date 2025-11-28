"""
Room Types Module

Defines specialized Room classes that inherit from the base Room model.
This allows for shared logic (e.g., all OutdoorRooms having weather) while keeping
content defined in JSON.
"""
from game.models.room import Room

class OutdoorRoom(Room):
    """
    A room that is outdoors.
    Automatically applies weather effects and time-of-day lighting to descriptions.
    """
    def __init__(self, oid: str, name: str, description: str):
        super().__init__(oid, name, description)
        self.outdoor = True

    def _get_base_description(self) -> str:
        """Override to ensure weather is always applied."""
        # Get base description (potentially time-variant)
        from game.systems.atmospheric_manager import get_atmospheric_manager
        atmos = get_atmospheric_manager()
        
        # Use AtmosphericManager for time and weather
        # This ensures we use the single source of truth
        desc = self.description
        if self.descriptions_by_time:
            # We need the time of day from atmos manager
            # But Room.look() will handle the final description generation
            # This method is internal helper
            pass
            
        # For now, just delegate to atmos manager which handles time/weather application
        return atmos.apply_weather_to_description(self.description)

class CityRoom(OutdoorRoom):
    """
    A room in a city or town.
    Inherits from OutdoorRoom but adds city-specific logic.
    """
    def tick(self):
        super().tick()
        # City-specific ambient logic could go here
        # e.g., street lamps turning on at night
        pass

class IndoorRoom(Room):
    """
    A standard indoor room.
    Protected from weather.
    """
    def __init__(self, oid: str, name: str, description: str):
        super().__init__(oid, name, description)
        self.outdoor = False

class DungeonRoom(IndoorRoom):
    """
    A room in a dungeon/underground.
    """
    pass

# Registry mapping type names to classes
ROOM_TYPES = {
    "Room": Room,
    "OutdoorRoom": OutdoorRoom,
    "CityRoom": CityRoom,
    "IndoorRoom": IndoorRoom,
    "DungeonRoom": DungeonRoom,
}

def get_room_class(type_name: str):
    """Factory method to get the class for a given type name."""
    return ROOM_TYPES.get(type_name, Room)
