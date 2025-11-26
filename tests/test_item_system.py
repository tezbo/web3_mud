
import sys
import os
import unittest

# Add current directory to path
sys.path.append(os.getcwd())

from game.models.item import Item, Weapon, Container
from game.models.player import Player
from game.models.room import Room
from game.world.manager import WorldManager
from game_engine import new_game_state, ITEM_DEFS

class TestItemSystem(unittest.TestCase):
    def setUp(self):
        self.wm = WorldManager.get_instance()
        self.game_state = new_game_state("ItemTester")
        self.player = Player("ItemTester")
        self.player.load_from_state(self.game_state)
        
        # Setup a test room
        self.room = Room("test_room", "Test Room", "A room for testing.")
        self.player.location = self.room
        
        # Mock ITEM_DEFS for testing
        ITEM_DEFS["test_sword"] = {
            "name": "test sword",
            "type": "weapon",
            "weight": 2.0,
            "damage": 5
        }
        ITEM_DEFS["test_rock"] = {
            "name": "test rock",
            "type": "misc",
            "weight": 1.0
        }

    def test_item_factory(self):
        """Test that WorldManager creates correct item subclasses."""
        sword = self.wm.get_item("test_sword")
        self.assertIsInstance(sword, Weapon)
        self.assertEqual(sword.name, "test sword")
        self.assertEqual(sword.damage, 5)
        
        rock = self.wm.get_item("test_rock")
        self.assertIsInstance(rock, Item)
        self.assertEqual(rock.name, "test rock")

    def test_take_drop_item(self):
        """Test taking and dropping items."""
        # Setup: Put rock in room
        rock = self.wm.get_item("test_rock")
        self.room.items.append(rock)
        
        # Take
        success, msg = self.player.take_item("test_rock", self.room)
        self.assertTrue(success, f"Failed to take item: {msg}")
        self.assertIn(rock, self.player.inventory)
        self.assertNotIn(rock, self.room.items)
        
        # Drop
        success, msg = self.player.drop_item("test_rock", self.room)
        self.assertTrue(success, f"Failed to drop item: {msg}")
        self.assertNotIn(rock, self.player.inventory)
        self.assertIn(rock, self.room.items)

    def test_give_item(self):
        """Test giving items to another entity."""
        # Setup: Player has sword
        sword = self.wm.get_item("test_sword")
        self.player.inventory.append(sword)
        
        # Target player
        target = Player("Recipient")
        target.location = self.room
        
        # Give
        success, msg = self.player.give_item("test_sword", target, self.game_state)
        self.assertTrue(success, f"Failed to give item: {msg}")
        self.assertNotIn(sword, self.player.inventory)
        self.assertIn(sword, target.inventory)

if __name__ == "__main__":
    unittest.main()
