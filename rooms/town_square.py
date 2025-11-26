from .base_room import BaseRoom

class TownSquare(BaseRoom):
    def __init__(self):
        super().__init__(
            name='Town Square',
            description='A bustling town square filled with vendors.',
            smells=['fresh bread', 'grilled meat'],
            sounds=['chattering crowds', 'music from a nearby tavern'],
            textures=['smooth cobblestones', 'soft grass']
        )

