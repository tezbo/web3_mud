"""
Tests for the Item Model integration with Inventory System.
"""
import unittest
from game.models.item import Item, Container
from game.systems.inventory_system import InventorySystem

class TestItemInventory(unittest.TestCase):
    def setUp(self):
        self.backpack = Container("backpack", "Backpack")
        self.sword = Item("sword", "Iron Sword")
        self.sword.weight = 5.0
        
        self.potion = Item("potion", "Healing Potion")
        self.potion.weight = 0.5

    def test_container_initialization(self):
        """Test container has inventory system."""
        self.assertIsInstance(self.backpack.inventory, InventorySystem)
        self.assertEqual(self.backpack.inventory.owner, self.backpack)

    def test_add_item_to_container(self):
        """Test adding items via container methods."""
        self.assertTrue(self.backpack.add_item(self.sword))
        self.assertEqual(self.backpack.inventory.current_item_count, 1)
        self.assertIn(self.sword, self.backpack.inventory.contents)

    def test_total_weight_calculation(self):
        """Test recursive weight calculation on Item model."""
        # Backpack base weight is 0.1 (default)
        self.backpack.weight = 1.0
        
        self.backpack.add_item(self.sword) # +5.0
        self.backpack.add_item(self.potion) # +0.5
        
        # Total = 1.0 + 5.0 + 0.5 = 6.5
        self.assertEqual(self.backpack.total_weight, 6.5)

    def test_nested_containers(self):
        """Test containers inside containers."""
        pouch = Container("pouch", "Small Pouch")
        pouch.weight = 0.1
        pouch.add_item(self.potion) # +0.5
        
        self.backpack.weight = 1.0
        self.backpack.add_item(pouch) # +0.6 total
        
        # Total = 1.0 + 0.6 = 1.6
        self.assertEqual(self.backpack.total_weight, 1.6)

if __name__ == '__main__':
    unittest.main()
