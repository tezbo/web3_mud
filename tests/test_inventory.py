"""
Tests for the Inventory System.
"""
import unittest
from game.systems.inventory_system import InventorySystem

class MockItem:
    def __init__(self, name, weight):
        self.name = name
        self._weight = weight
        self.inventory = None # Can be a container

    @property
    def total_weight(self):
        base = self._weight
        if self.inventory:
            base += self.inventory.current_weight
        return base

    def to_dict(self):
        return {"name": self.name}

class TestInventorySystem(unittest.TestCase):
    def setUp(self):
        self.bag = MockItem("Bag of Holding", 1.0)
        self.bag.inventory = InventorySystem(self.bag, max_weight=10.0, max_items=5)
        
        self.rock = MockItem("Heavy Rock", 5.0)
        self.pebble = MockItem("Pebble", 0.1)
        self.boulder = MockItem("Boulder", 20.0)

    def test_add_item(self):
        """Test adding items updates weight and count."""
        self.assertTrue(self.bag.inventory.add(self.rock))
        self.assertEqual(self.bag.inventory.current_item_count, 1)
        self.assertEqual(self.bag.inventory.current_weight, 5.0)
        self.assertEqual(self.bag.total_weight, 6.0) # 1.0 bag + 5.0 rock

    def test_weight_limit(self):
        """Test that weight limits are enforced."""
        self.assertFalse(self.bag.inventory.add(self.boulder)) # 20.0 > 10.0
        self.assertEqual(self.bag.inventory.current_item_count, 0)

    def test_item_count_limit(self):
        """Test that item count limits are enforced."""
        # Add 5 pebbles (max items = 5)
        for _ in range(5):
            self.assertTrue(self.bag.inventory.add(self.pebble))
        
        # Try adding 6th
        self.assertFalse(self.bag.inventory.add(self.pebble))
        self.assertEqual(self.bag.inventory.current_item_count, 5)

    def test_recursive_weight(self):
        """Test nested containers calculate weight correctly."""
        small_bag = MockItem("Small Bag", 0.5)
        small_bag.inventory = InventorySystem(small_bag, max_weight=5.0)
        
        # Put rock in small bag
        small_bag.inventory.add(self.rock) # 5.0
        self.assertEqual(small_bag.total_weight, 5.5) # 0.5 + 5.0
        
        # Put small bag in big bag
        self.assertTrue(self.bag.inventory.add(small_bag))
        
        # Big bag weight = 1.0 (self) + 5.5 (small bag total) = 6.5
        self.assertEqual(self.bag.total_weight, 6.5)

    def test_circular_dependency(self):
        """Test prevention of putting a bag inside itself."""
        # Try to put bag inside itself
        self.assertFalse(self.bag.inventory.add(self.bag))
        
        # Try indirect circular: Bag A -> Bag B -> Bag A
        bag_b = MockItem("Bag B", 1.0)
        bag_b.inventory = InventorySystem(bag_b)
        
        self.bag.inventory.add(bag_b)
        # Now try to put Bag A into Bag B
        self.assertFalse(bag_b.inventory.add(self.bag))

if __name__ == '__main__':
    unittest.main()
