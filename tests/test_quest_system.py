
import sys
import os
import unittest
import time

# Add current directory to path
sys.path.append(os.getcwd())

from game.models.player import Player
from game.models.quest import Quest, QuestTemplate
from game.systems.quest_manager import QuestManager
from game_engine import new_game_state

class TestQuestSystem(unittest.TestCase):
    def setUp(self):
        self.qm = QuestManager.get_instance()
        # Reset templates for testing
        self.qm.templates = {}
        
        # Register a test quest
        self.test_quest = QuestTemplate(
            id="test_quest",
            name="Test Quest",
            description="A quest for testing.",
            giver_id="npc:tester",
            difficulty="Easy",
            category="Test",
            timed=False,
            time_limit_minutes=None,
            actors=["tester"],
            stages=[
                {
                    "id": "stage1",
                    "description": "Go to the test room.",
                    "objectives": [
                        {
                            "id": "obj1",
                            "type": "go_to_room",
                            "room_id": "test_room"
                        }
                    ]
                },
                {
                    "id": "stage2",
                    "description": "Talk to the tester.",
                    "objectives": [
                        {
                            "id": "obj2",
                            "type": "talk_to_npc",
                            "npc_id": "npc:tester"
                        }
                    ]
                }
            ],
            rewards={"currency": {"amount": 10}},
            offer_sources=[]
        )
        self.qm.register_template(self.test_quest)
        
        self.game_state = new_game_state("QuestTester")
        self.player = Player("QuestTester")
        self.player.load_from_state(self.game_state)

    def test_start_quest(self):
        """Test starting a quest."""
        success, msg = self.qm.start_quest(self.player, "test_quest")
        self.assertTrue(success, f"Failed to start quest: {msg}")
        self.assertIn("test_quest", self.player.quests)
        quest = self.player.quests["test_quest"]
        self.assertIsInstance(quest, Quest)
        self.assertEqual(quest.status, "active")
        self.assertEqual(quest.current_stage_index, 0)

    def test_quest_progression(self):
        """Test quest progression via events."""
        self.qm.start_quest(self.player, "test_quest")
        quest = self.player.quests["test_quest"]
        
        # Event 1: Go to wrong room
        event_wrong = {"type": "enter_room", "room_id": "wrong_room"}
        quest.update(event_wrong, self.game_state)
        self.assertEqual(quest.current_stage_index, 0)
        
        # Event 2: Go to correct room
        event_right = {"type": "enter_room", "room_id": "test_room"}
        quest.update(event_right, self.game_state)
        self.assertEqual(quest.current_stage_index, 1)
        self.assertIn("New Objective: Talk to the tester.", quest.notes[-1])
        
        # Event 3: Talk to NPC
        event_talk = {"type": "talk_to_npc", "npc_id": "npc:tester"}
        quest.update(event_talk, self.game_state)
        self.assertEqual(quest.current_stage_index, 2) # Finished last stage

    def test_persistence(self):
        """Test saving and loading quests."""
        self.qm.start_quest(self.player, "test_quest")
        quest = self.player.quests["test_quest"]
        quest.current_stage_index = 1
        
        # Save
        state = self.player.to_state()
        self.assertIn("test_quest", state["quests"])
        self.assertEqual(state["quests"]["test_quest"]["current_stage_index"], 1)
        
        # Load
        new_player = Player("QuestTester")
        new_player.load_from_state(state)
        self.assertIn("test_quest", new_player.quests)
        loaded_quest = new_player.quests["test_quest"]
        self.assertIsInstance(loaded_quest, Quest)
        self.assertEqual(loaded_quest.current_stage_index, 1)

if __name__ == "__main__":
    unittest.main()
