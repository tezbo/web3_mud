from .base_room import BaseRoom

class ForestRoom(BaseRoom):
    def __init__(self):
        super().__init__(
            name='Forest',
            description='A dense forest filled with towering trees and underbrush.',
            smells=['fresh pine', 'damp earth'],
            sounds=['rustling leaves', 'birds chirping'],
            textures=['rough bark', 'soft moss']
        )

