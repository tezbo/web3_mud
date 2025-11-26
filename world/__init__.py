from .shadowfen import Shadowfen
from .sunward_kingdoms import SunwardKingdoms

class World:
    def __init__(self):
        self.areas = [Shadowfen(), SunwardKingdoms()]

    def get_area_names(self):
        return [area.name for area in self.areas]

    def get_room_description(self, area_name, room_name):
        for area in self.areas:
            if area.name == area_name:
                return area.describe_room(room_name)
        return 'Area not found.'