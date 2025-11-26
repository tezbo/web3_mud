from .shadowfen import Shadowfen
from .sunward_kingdoms import SunwardKingdoms

class World:
    def __init__(self):
        self.areas = {
            'shadowfen': Shadowfen(),
            'sunward_kingdoms': SunwardKingdoms()
        }

    def get_area(self, area_name):
        return self.areas.get(area_name)

    # Methods for loading and managing different game areas
