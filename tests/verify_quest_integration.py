
import sys
import os
import unittest

# Add current directory to path
sys.path.append(os.getcwd())

from game_engine import new_game_state
import quests
from game.systems.quest_manager import QuestManager
from game.models.player import Player

class TestQuestIntegration(unittest.TestCase):
    def setUp(self):
        # Initialize QuestManager
        self.qm = QuestManager.get_instance()
        self.qm.initialize_quests()
        
        self.game_state = new_game_state("IntegrationTester")
        self.username = "IntegrationTester"

    def test_legacy_bridge(self):
        """Test that legacy functions correctly use QuestManager."""
        
        # 1. Start Quest via legacy function
        msg = quests.start_quest(self.game_state, self.username, "lost_package", "test")
        print(f"Start Quest Message: {msg}")
        
        # Verify it's in the game state (legacy dict)
        self.assertIn("lost_package", self.game_state["quests"])
        self.assertEqual(self.game_state["quests"]["lost_package"]["status"], "active")
        
        # Verify it's in QuestManager/Player object world
        # We need to load a player to check
        player = Player(self.username)
        player.load_from_state(self.game_state)
        self.assertIn("lost_package", player.quests)
        self.assertEqual(player.quests["lost_package"].current_stage_index, 0)
        
        # 2. Trigger Event via legacy function
        # Objective: Talk to Mara
        event = {
            "type": "talk_to_npc",
            "npc_id": "innkeeper",
            "username": self.username
        }
        quests.handle_quest_event(self.game_state, event)
        
        # Verify progression in legacy dict
        # Note: The bridge updates the dict
        self.assertEqual(self.game_state["quests"]["lost_package"]["objectives_state"][0]["talk_to_mara_obj"], True)
        
        # Verify progression in OO world
        player.load_from_state(self.game_state) # Reload to see changes
        self.assertTrue(player.quests["lost_package"].objectives_state[0]["talk_to_mara_obj"])
        
        print("Legacy bridge verification successful!")

if __name__ == "__main__":
    unittest.main()
