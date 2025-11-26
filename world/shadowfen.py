class Shadowfen:
    def __init__(self):
        self.name = 'Shadowfen'
        self.rooms = self.create_rooms()

    def create_rooms(self):
        return {
            'swamp_edge': 'You stand at the edge of a murky swamp. The air is thick and heavy.',
            'misty_crossroads': 'A foggy crossroads appears before you. Paths lead in every direction.',
            'ancient_tree': 'An ancient tree towers over you, its gnarled branches twisting toward the sky.',
            'haunted_hollow': 'Whispers echo in this hollow, sending a chill down your spine.',
            'forgotten_cave': 'The entrance to a dark cave yawns open, something stirs within.',
            'shadowy_clearing': 'A small clearing opens up, shrouded in shadows.',
            'lost_village': 'The remnants of a long-lost village lie before you, overgrown and silent.',
            'echoing_pond': 'A serene pond reflects the moonlight, but something lurks beneath the surface.',
            'dark_forest': 'The forest thickens, and every step becomes a challenge through the underbrush.',
        }

    def describe_room(self, room_name):
        return self.rooms.get(room_name, 'Room not found.')