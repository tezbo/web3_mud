import unittest
from characters.npc import NPC

class TestNPC(unittest.TestCase):
    def setUp(self):
        self.npc = NPC('TestNPC')

    def test_update_state(self):
        self.npc.update_state('active')
        self.assertEqual(self.npc.state, 'active')

    def test_make_decision(self):
        game_state = {'threat_level': 3}
        decision = self.npc.make_decision(game_state)
        self.assertIn(decision, ['explore', 'interact', 'rest'])

if __name__ == '__main__':
    unittest.main()