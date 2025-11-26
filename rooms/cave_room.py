from .base_room import BaseRoom

class CaveRoom(BaseRoom):
    def __init__(self):
        super().__init__(
            name='Cave',
            description='A dark, musty cave with jagged rocks.',
            smells=['damp stone', 'mold'],
            sounds=['dripping water', 'echoes'],
            textures=['cold stone', 'smooth stalactites']
        )

