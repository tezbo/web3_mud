import unittest
from world import World

class TestWorld(unittest.TestCase):
    def setUp(self):
        self.world = World()

    def test_area_initialization(self):
        self.assertEqual(len(self.world.areas), 2)

    def test_shadowfen_descriptions(self):
        self.assertIn('You stand at the edge of a murky swamp.', self.world.get_room_description('Shadowfen', 'swamp_edge'))

    def test_sunward_kingdom_descriptions(self):
        self.assertIn('A golden path stretches before you, lined with blooming flowers.', self.world.get_room_description('Sunward Kingdoms', 'golden_path'))

if __name__ == '__main__':
    unittest.main()