"""
Entity Model (Living Things)
"""
from game.models.base import GameObject
from game.systems.inventory_system import InventorySystem

class Entity(GameObject):
    """Base class for Players and NPCs."""
    def __init__(self, oid: str, name: str):
        super().__init__(oid, name)
        self.stats = {
            "hp": 10,
            "max_hp": 10,
            "str": 10,
            "agi": 10,
            "int": 10
        }
        self.inventory = InventorySystem(self)

    def move(self, direction: str) -> bool:
        """Attempt to move in a direction."""
        # Check encumbrance
        if self.inventory.current_weight >= self.inventory.max_weight:
            # If player, they get a message via return value handling in command
            # If NPC, we need to handle it. 
            # For now, return False.
            # We can also print a message if it's a player or if we want debug info.
            return False

        if not self.location:
            return False
        
        # Logic to check exit, handle locks, etc.
        # This will eventually replace the big if/else in game_engine
        return True

    def say(self, message: str):
        """Speak to the room."""
        if self.location:
            # Format: "Name says: message"
            # TODO: Use color settings from player if available
            formatted_msg = f"[CYAN]{self.name} says: \"{message}\"[/CYAN]"
            self.location.broadcast(formatted_msg, exclude_oid=self.oid)
            
    def emote(self, action: str):
        """Perform an emote."""
        if self.location:
            # Format: "Name action"
            formatted_msg = f"{self.name} {action}"
            self.location.broadcast(formatted_msg, exclude_oid=self.oid)

    @property
    def is_dead(self) -> bool:
        return self.stats["hp"] <= 0

    def get_weapon(self):
        """Get the currently equipped weapon (simplified: best weapon in inventory)."""
        from game.models.item import Weapon
        weapons = [item for item in self.inventory.contents if isinstance(item, Weapon)]
        if not weapons:
            return None
        # Return weapon with highest damage
        return max(weapons, key=lambda w: w.damage)

    def get_defense(self) -> int:
        """Get total defense from armor (simplified: sum of all armor)."""
        from game.models.item import Armor
        armors = [item for item in self.inventory.contents if isinstance(item, Armor)]
        base_ac = 0
        for armor in armors:
            base_ac += armor.ac
        
        # Agility bonus to defense
        agi_bonus = (self.stats.get("agi", 10) - 10) // 2
        return max(0, base_ac + agi_bonus)

    def take_damage(self, amount: int, source: GameObject = None):
        self.stats["hp"] -= amount
        if self.stats["hp"] <= 0:
            self.stats["hp"] = 0 # Cap at 0
            self.die(source)

    def die(self, source: GameObject = None):
        pass
