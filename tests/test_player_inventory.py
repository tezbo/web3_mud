"""
Tests for Player Model integration with Inventory System.
"""
import unittest
from game.models.player import Player
from game.models.item import Item
from game.systems.inventory_system import InventorySystem

class MockRoom:
    def __init__(self, oid):
        self.oid = oid
        self.items = []
        self.npcs = []

class TestPlayerInventory(unittest.TestCase):
    def setUp(self):
        self.player = Player("TestPlayer")
        self.room = MockRoom("test_room")
        self.player.location = self.room
        
        self.sword = Item("sword", "Iron Sword")
        self.sword.weight = 5.0
        
        self.rock = Item("rock", "Heavy Rock")
        self.rock.weight = 25.0 # Heavier than max carry

    def test_inventory_initialization(self):
        """Test player starts with inventory system."""
        self.assertIsInstance(self.player.inventory, InventorySystem)
        self.assertEqual(self.player.inventory.max_weight, 20.0)

    def test_take_item_success(self):
        """Test taking an item works."""
        self.room.items.append(self.sword)
        
        success, msg = self.player.take_item("sword", self.room)
        
        self.assertTrue(success)
        self.assertIn(self.sword, self.player.inventory.contents)
        self.assertNotIn(self.sword, self.room.items)

    def test_take_item_too_heavy(self):
        """Test taking an item that exceeds weight limit."""
        self.room.items.append(self.rock)
        
        success, msg = self.player.take_item("rock", self.room)
        
        self.assertFalse(success)
        self.assertIn("can't carry that much", msg)
        self.assertNotIn(self.rock, self.player.inventory.contents)
        self.assertIn(self.rock, self.room.items)

    def test_drop_item(self):
        """Test dropping an item."""
        self.player.inventory.add(self.sword)
        
        success, msg = self.player.drop_item("sword", self.room)
        
        self.assertTrue(success)
        self.assertNotIn(self.sword, self.player.inventory.contents)
        self.assertIn(self.sword, self.room.items)

if __name__ == '__main__':
    unittest.main()
