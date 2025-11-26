"""
Item Model System
Inspired by Discworld MUDlib's /std/object and /obj structure.
"""
from typing import Dict, Any, List, Optional
from game.models.base import GameObject

class Item(GameObject):
    """Represents an item in the game world."""
    
    def __init__(self, oid: str, name: str, description: str = ""):
        super().__init__(oid, name, description)
        self.item_type: str = "misc"
        self.weight: float = 0.1
        self.value: int = 0
        self.droppable: bool = True
        self.stackable: bool = False
        self.adjectives: List[str] = [] # For parsing (e.g., "rusty sword")
        self.destroyed: bool = False
        
    def load_from_def(self, item_def: Dict[str, Any]):
        """Hydrate item from ITEM_DEFS definition."""
        self.name = item_def.get("name", self.name)
        self.description = item_def.get("description", "")
        self.item_type = item_def.get("type", "misc")
        self.weight = item_def.get("weight", 0.1)
        self.value = item_def.get("value", 0)
        self.droppable = item_def.get("droppable", True)
        
        # Handle flags
        flags = item_def.get("flags", [])
        self.stackable = "stackable" in flags
        if "quest" in flags:
            self.flags.append("quest")
            
        # Parse adjectives from name if not provided
        if not self.adjectives and " " in self.name:
            parts = self.name.split()
            self.adjectives = parts[:-1] # All but the last word are adjectives
    
    def can_be_taken(self, by_entity: 'GameObject') -> tuple[bool, str]:
        """
        Check if this item can be taken by an entity.
        Returns (can_take, reason_if_not).
        """
        return True, ""
    
    def can_be_dropped(self, by_entity: 'GameObject') -> tuple[bool, str]:
        """
        Check if this item can be dropped by an entity.
        Returns (can_drop, reason_if_not).
        """
        if not self.droppable:
            return False, "You can't drop that item."
        return True, ""
    
    def on_take(self, taker: 'GameObject'):
        """Called when item is taken. Override for custom behavior."""
        pass
    
    def on_drop(self, dropper: 'GameObject'):
        """Called when item is dropped. Override for custom behavior."""
        pass
    
    def get_display_name(self) -> str:
        """Return the user-friendly display name."""
        # Import here to avoid circular dependency
        from game_engine import render_item_name
        return render_item_name(self.oid)
        
    def tick(self):
        """Called periodically to update item state."""
        pass

class Container(Item):
    def __init__(self, oid: str, name: str, description: str = ""):
        super().__init__(oid, name, description)
        self.inventory: List[Item] = []
        self.max_weight: float = 10.0
        self.closed: bool = False
        self.locked: bool = False
        self.key_id: Optional[str] = None
        
    def add_item(self, item: Item) -> bool:
        """Add item to container. Returns False if full."""
        current_weight = sum(i.weight for i in self.inventory)
        if current_weight + item.weight > self.max_weight:
            return False
        self.inventory.append(item)
        return True
        
    def remove_item(self, item: Item):
        """Remove item from container."""
        if item in self.inventory:
            self.inventory.remove(item)

class Weapon(Item):
    def __init__(self, oid: str, name: str, description: str = ""):
        super().__init__(oid, name, description)
        self.damage: int = 1
        self.weapon_type: str = "blunt" # slash, pierce, blunt
        
    def load_from_def(self, item_def: Dict[str, Any]):
        super().load_from_def(item_def)
        self.damage = item_def.get("damage", 1)
        self.weapon_type = item_def.get("weapon_type", "blunt")

class Armor(Item):
    def __init__(self, oid: str, name: str, description: str = ""):
        super().__init__(oid, name, description)
        self.ac: int = 1
        self.slot: str = "body" # head, body, legs, feet, hands
        
    def load_from_def(self, item_def: Dict[str, Any]):
        super().load_from_def(item_def)
        self.ac = item_def.get("ac", 1)
        self.slot = item_def.get("slot", "body")

class Consumable(Item):
    def __init__(self, oid: str, name: str, description: str = ""):
        super().__init__(oid, name, description)
        self.effects: Dict[str, Any] = {}
        self.charges: int = 1
        
    def load_from_def(self, item_def: Dict[str, Any]):
        super().load_from_def(item_def)
        self.effects = item_def.get("effects", {})
        self.charges = item_def.get("charges", 1)

    def tick(self):
        """Called periodically to update item state."""
        pass

class Corpse(Container):
    def __init__(self, oid: str, name: str, description: str = ""):
        super().__init__(oid, name, description)
        self.decay_ticks: int = 60 # Default decay time (e.g. 5 minutes if tick is 5s)
        self.decay_stage: int = 0
        
    def tick(self):
        self.decay_ticks -= 1
        if self.decay_ticks <= 0:
            self.decay()
            
    def decay(self):
        """Handle decay steps."""
        # Simple version: just disappear
        # In a full MUD, this might turn into a skeleton, then dust
        if self.decay_stage == 0:
            self.name = f"Rotting {self.name}"
            self.description = f"The rotting remains of {self.name.replace('Corpse of ', '').replace('Rotting ', '')}."
            self.decay_ticks = 30
            self.decay_stage = 1
            # Broadcast decay message? Needs room context.
        elif self.decay_stage == 1:
            self.name = f"Skeleton of {self.name.replace('Rotting Corpse of ', '')}"
            self.description = "A bleached skeleton."
            self.decay_ticks = 30
            self.decay_stage = 2
        else:
            # Destroy
            self.destroyed = True
