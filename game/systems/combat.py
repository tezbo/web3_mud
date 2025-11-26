"""
Combat System
Handles combat mechanics, damage calculation, and round resolution.
"""
import random
from typing import Optional, Tuple, List, Dict
from game.models.entity import Entity
from game.models.item import Weapon, Armor

class CombatSystem:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
        
    def calculate_hit_chance(self, attacker: Entity, defender: Entity) -> float:
        """
        Calculate percentage chance to hit (0.0 to 1.0).
        Based on Attacker Agility vs Defender Agility.
        """
        att_agi = attacker.stats.get("agi", 10)
        def_agi = defender.stats.get("agi", 10)
        
        # Base 50% chance
        chance = 0.5
        
        # Adjust by difference (e.g. +5 agi = +10% chance)
        diff = att_agi - def_agi
        chance += (diff * 0.02)
        
        # Clamp between 5% and 95%
        return max(0.05, min(0.95, chance))
        
    def calculate_damage(self, attacker: Entity, defender: Entity) -> Tuple[int, bool]:
        """
        Calculate damage dealt.
        Returns (damage, is_crit).
        """
        # Get weapon damage
        weapon = attacker.get_weapon()
        base_dmg = weapon.damage if weapon else 1 # Unarmed damage
        
        # Strength bonus
        att_str = attacker.stats.get("str", 10)
        str_bonus = att_str // 5
        
        # Random variance (0.8 to 1.2)
        variance = random.uniform(0.8, 1.2)
        
        raw_damage = (base_dmg + str_bonus) * variance
        
        # Critical hit check (based on Agility)
        att_agi = attacker.stats.get("agi", 10)
        crit_chance = att_agi * 0.01 # 10 agi = 10% crit
        is_crit = random.random() < crit_chance
        
        if is_crit:
            raw_damage *= 1.5
            
        # Mitigation
        defense = defender.get_defense()
        final_damage = max(1, int(raw_damage - defense))
        
        return final_damage, is_crit
        
    def resolve_round(self, attacker: Entity, defender: Entity) -> List[str]:
        """
        Execute one round of combat.
        Returns a list of messages describing the outcome.
        """
        messages = []
        
        # Check hit
        hit_chance = self.calculate_hit_chance(attacker, defender)
        if random.random() > hit_chance:
            # Miss
            msgs = self._get_miss_messages(attacker, defender)
            messages.extend(msgs)
            return messages
            
        # Hit
        damage, is_crit = self.calculate_damage(attacker, defender)
        
        # Apply damage
        defender.take_damage(damage, source=attacker)
        
        # Generate messages
        msgs = self._get_hit_messages(attacker, defender, damage, is_crit)
        messages.extend(msgs)
        
        if defender.is_dead:
            messages.append(f"{defender.name} has been defeated!")
            # Handle death logic (loot, xp, etc) - usually handled by Entity.die()
            
        return messages
        
    def _get_miss_messages(self, attacker: Entity, defender: Entity) -> List[str]:
        """Flavor text for misses."""
        return [f"{attacker.name} attacks {defender.name} but misses!"]
        
    def _get_hit_messages(self, attacker: Entity, defender: Entity, damage: int, is_crit: bool) -> List[str]:
        """Flavor text for hits."""
        crit_str = " CRITICALLY" if is_crit else ""
        return [f"{attacker.name}{crit_str} hits {defender.name} for {damage} damage!"]
