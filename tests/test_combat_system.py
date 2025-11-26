
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

from game.models.entity import Entity
from game.models.npc import NPC
from game.models.item import Weapon, Armor
from game.systems.combat import CombatSystem

class TestCombatSystem(unittest.TestCase):
    def setUp(self):
        self.combat = CombatSystem.get_instance()
        
        # Create attacker
        self.attacker = Entity("attacker", "Attacker")
        self.attacker.stats = {"str": 15, "agi": 12, "hp": 20}
        
        # Create defender
        self.defender = Entity("defender", "Defender")
        self.defender.stats = {"str": 10, "agi": 10, "hp": 20}
        
    def test_equipment_stats(self):
        """Test that equipment stats are calculated correctly."""
        # Weapon
        sword = Weapon("sword", "Sword")
        sword.damage = 5
        self.attacker.inventory.append(sword)
        
        self.assertEqual(self.attacker.get_weapon(), sword)
        
        # Armor
        plate = Armor("plate", "Plate Mail")
        plate.ac = 8
        self.defender.inventory.append(plate)
        
        # Defense = AC + Agi bonus ((10-10)//2 = 0) = 8
        self.assertEqual(self.defender.get_defense(), 8)
        
    def test_damage_calculation(self):
        """Test damage math."""
        # Attacker: Str 15 (+3 bonus), Weapon 5. Total base ~8.
        # Defender: Defense 0.
        sword = Weapon("sword", "Sword")
        sword.damage = 5
        self.attacker.inventory.append(sword)
        
        dmg, is_crit = self.combat.calculate_damage(self.attacker, self.defender)
        
        # Expected: (5 + 3) * variance(0.8-1.2)
        # Range: 6.4 to 9.6
        self.assertTrue(6 <= dmg <= 10) # Allowing for rounding
        
    def test_mitigation(self):
        """Test armor mitigation."""
        sword = Weapon("sword", "Sword")
        sword.damage = 10
        self.attacker.inventory.append(sword)
        
        plate = Armor("plate", "Plate")
        plate.ac = 5
        self.defender.inventory.append(plate)
        
        # Attacker: Str 15 (+3). Base ~13.
        # Defender: AC 5.
        # Expected: ~13 - 5 = ~8.
        dmg, _ = self.combat.calculate_damage(self.attacker, self.defender)
        self.assertTrue(dmg < 13) # Should be reduced
        
    def test_combat_round(self):
        """Test full round resolution."""
        # Ensure hit (high agi)
        self.attacker.stats["agi"] = 100
        
        msgs = self.combat.resolve_round(self.attacker, self.defender)
        
        self.assertTrue(len(msgs) >= 1)
        self.assertIn("hits Defender", msgs[0])
        self.assertTrue(self.defender.stats["hp"] < 20)
        
    def test_npc_integration(self):
        """Test NPC.on_attacked."""
        npc = NPC("dummy", "Dummy")
        npc.attackable = True
        npc.stats = {"hp": 10, "agi": 10}
        
        # Mock combat system to return fixed result
        # But easier to just run it since it's deterministic enough
        
        result = npc.on_attacked(self.attacker, {})
        self.assertIn("hits Dummy", result)
        self.assertTrue(npc.stats["hp"] < 10)

if __name__ == "__main__":
    unittest.main()
