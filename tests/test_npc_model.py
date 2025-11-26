import unittest
from models.npc import NPC

class TestNPC(unittest.TestCase):
    def setUp(self):
        self.npc = NPC('npc1', 'Goblin')

    def test_set_and_get_state(self):
        self.npc.set_state({'health': 100})
        self.assertEqual(self.npc.get_state(), {'health': 100})

if __name__ == '__main__':
    unittest.main()