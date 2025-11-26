import unittest
from npc_ai.ai_system import AISystem

class TestAISystem(unittest.TestCase):
    def setUp(self):
        self.ai_system = AISystem()

    def test_update_memory(self):
        self.ai_system.update_npc_memory('npc_1', 'greeted player')
        self.assertIn('greeted player', self.ai_system.memory['npc_1'])

    def test_recall_memory(self):
        self.ai_system.update_npc_memory('npc_1', 'greeted player')
        memory = self.ai_system.recall_memory('npc_1')
        self.assertEqual(memory, ['greeted player'])

if __name__ == '__main__':
    unittest.main()