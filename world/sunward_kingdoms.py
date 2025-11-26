class SunwardKingdoms:
    def __init__(self):
        self.name = 'Sunward Kingdoms'
        self.rooms = self.create_rooms()

    def create_rooms(self):
        return {
            'golden_path': 'A golden path stretches before you, lined with blooming flowers.',
            'sunlit_market': 'The bustling market is full of vibrant colors and lively chatter.',
            'royal_castle': 'The magnificent castle towers imposingly with shining towers.',
            'lush_gardens': 'The gardens are filled with exotic plants and the scent of fresh fruit.',
            'ancient_ruins': 'Weathered stones tell tales of the kingdoms long past.',
            'the_forbidden_forest': 'This magical forest hums with unseen energy, inviting and intimidating.',
            'sunset_cliffs': 'You stand on the cliffs, the sunset bathing the world in golden hues.',
            'crystal_lake': 'A pristine lake reflects the skies, rumored to have mystical properties.',
            'twilight_crossroads': 'As dusk falls, paths converge at this mystical intersection.',
        }

    def describe_room(self, room_name):
        return self.rooms.get(room_name, 'Room not found.')