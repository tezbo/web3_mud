"""
Inventory System - Manages item containment, weight limits, and hierarchy.

This module implements a robust container system inspired by Discworld MUD's
/std/container.c, adapted for Python composition.

Key Features:
- Recursive weight calculation (Container weight = Self + Contents)
- Capacity limits (Weight and Item Count)
- Circular dependency prevention
- Transactional add/remove operations
"""
from typing import List, Optional, Protocol, Any, Dict

class Weighable(Protocol):
    """Protocol for any object that has weight."""
    @property
    def total_weight(self) -> float: ...
    
    @property
    def name(self) -> str: ...

class InventorySystem:
    """
    A composable system that allows an entity to hold other items.
    Attach this to Rooms, Players, NPCs, or Container Items (bags).
    """
    def __init__(self, owner: Any, max_weight: float = 100.0, max_items: int = 50):
        self.owner = owner
        self.contents: List[Weighable] = []
        self.max_weight = max_weight
        self.max_items = max_items
        
        # Cache for performance, invalidated on modification
        self._cached_weight: Optional[float] = None

    @property
    def current_weight(self) -> float:
        """Calculate total weight of all contents."""
        if self._cached_weight is None:
            self._cached_weight = sum(item.total_weight for item in self.contents)
        return self._cached_weight

    @property
    def current_item_count(self) -> int:
        """Return number of items directly in this inventory."""
        return len(self.contents)

    def can_add(self, item: Weighable) -> bool:
        """
        Check if an item can be added to this inventory.
        
        Checks:
        1. Weight limits
        2. Item count limits
        3. Circular dependency (prevent putting a bag inside itself)
        """
        # 1. Check item count
        if len(self.contents) >= self.max_items:
            return False
            
        # 2. Check weight limit
        if self.current_weight + item.total_weight > self.max_weight:
            return False
            
        # 3. Check circular dependency
        # If the item being added is a container, check if WE are inside IT
        if hasattr(item, 'inventory') and item.inventory:
            if self._is_inside(item):
                return False
                
        return True

    def add(self, item: Weighable) -> bool:
        """
        Add an item to the inventory.
        Returns True if successful, False if failed (e.g. full).
        """
        if not self.can_add(item):
            return False
            
        self.contents.append(item)
        self._invalidate_cache()
        return True

    def remove(self, item: Weighable) -> bool:
        """
        Remove an item from the inventory.
        Returns True if successful, False if item not found.
        """
        if item in self.contents:
            self.contents.remove(item)
            self._invalidate_cache()
            return True
        return False

    def _invalidate_cache(self):
        """Invalidate weight cache for self and parents."""
        self._cached_weight = None
        # Propagate up the chain if our owner is inside something else
        # This requires the owner to know its location (parent)
        if hasattr(self.owner, 'location') and self.owner.location:
             # Assuming the location has an inventory system
             if hasattr(self.owner.location, 'inventory') and self.owner.location.inventory:
                 self.owner.location.inventory._invalidate_cache()

    def _is_inside(self, container: Any) -> bool:
        """
        Recursive check to see if self.owner is inside 'container'.
        Used to prevent circular inclusion (Bag A inside Bag B inside Bag A).
        """
        # This is complex because we need to traverse UP the tree.
        # For now, we'll assume a simpler check:
        # If the item being added IS the owner, that's bad.
        if container == self.owner:
            return True
            
        # If the item being added contains the owner
        if hasattr(container, 'inventory') and container.inventory:
            # Check if owner is in container's contents
            if self.owner in container.inventory.contents:
                return True
            # Recurse down (if container has sub-containers)
            # Actually, circular dependency is usually:
            # I am adding 'Bag B' to 'Bag A'.
            # I need to check if 'Bag A' is already inside 'Bag B'.
            for item in container.inventory.contents:
                if self._is_inside(item):
                    return True
                    
        return False

    def __iter__(self):
        """Allow iteration over contents."""
        return iter(self.contents)

    def __len__(self):
        """Return number of items."""
        return len(self.contents)

    def __contains__(self, item):
        """Check if item is in inventory."""
        return item in self.contents

    def to_dict(self) -> Dict[str, Any]:
        """Serialize inventory state (list of item IDs/data)."""
        # This assumes items can serialize themselves
        return {
            "max_weight": self.max_weight,
            "max_items": self.max_items,
            "items": [item.to_dict() for item in self.contents if hasattr(item, 'to_dict')]
        }
