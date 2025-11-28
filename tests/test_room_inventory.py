"""
Tests for Room Model integration with Inventory System.
"""
import unittest
from game.models.room import Room
from game.models.item import Item
from game.systems.inventory_system import InventorySystem

class TestRoomInventory(unittest.TestCase):
    def setUp(self):
        self.room = Room("town_square", "Town Square", "A busy square.")
        self.sword = Item("sword", "Iron Sword")
        self.rock = Item("rock", "Heavy Rock")

    def test_inventory_initialization(self):
        """Test room starts with inventory system."""
        self.assertIsInstance(self.room.inventory, InventorySystem)
        self.assertEqual(self.room.inventory.max_weight, float('inf'))

    def test_add_item_to_room(self):
        """Test adding items to room inventory."""
        self.room.inventory.add(self.sword)
        self.assertIn(self.sword, self.room.inventory.contents)
        # Check legacy compatibility
        self.assertIn(self.sword, self.room.items)

    def test_remove_item_from_room(self):
        """Test removing items from room inventory."""
        self.room.inventory.add(self.sword)
        self.room.inventory.remove(self.sword)
        self.assertNotIn(self.sword, self.room.inventory.contents)

    def test_tick_removes_destroyed_items(self):
        """Test that tick() cleans up destroyed items."""
        self.room.inventory.add(self.sword)
        
        # Mark sword as destroyed
        self.sword.destroyed = True
        
        # Run tick
        self.room.tick()
        
        self.assertNotIn(self.sword, self.room.inventory.contents)

if __name__ == '__main__':
    unittest.main()
