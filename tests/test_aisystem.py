import unittest
from ai.aisystem import AISystem

class TestAISystem(unittest.TestCase):
    def setUp(self):
        self.aisystem = AISystem()

    def test_memory_storage(self):
        self.aisystem.remember('npc1', 'greeting', 'Hello!')
        self.assertEqual(self.aisystem.recall('npc1', 'greeting'), 'Hello!')

    def test_act_method(self):
        npc = NPC('Goblin', 'aggressive')
        action = self.aisystem.act(npc)
        self.assertEqual(action, 'Goblin attacks!')

if __name__ == '__main__':
    unittest.main()