import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.models.player import Player

def test_player_stats_initialization():
    p = Player("testuser")
    assert p.level == 1
    assert p.hp == 20
    assert p.max_hp == 20
    assert p.stamina == 20
    assert p.strength == 10
    
def test_take_damage():
    p = Player("testuser")
    p.defense = 2
    
    # 10 damage - 2 defense = 8 actual
    damage, dead = p.take_damage(10)
    assert damage == 8
    assert p.hp == 12
    assert not dead
    
    # Lethal damage
    damage, dead = p.take_damage(20)
    assert p.hp == 0
    assert dead

def test_heal():
    p = Player("testuser")
    p.hp = 5
    
    healed = p.heal(10)
    assert healed == 10
    assert p.hp == 15
    
    # Overhealing
    healed = p.heal(100)
    assert p.hp == 20
    assert healed == 5  # Only healed 5 to reach max

def test_stamina():
    p = Player("testuser")
    
    assert p.use_stamina(5)
    assert p.stamina == 15
    
    assert not p.use_stamina(20) # Not enough
    assert p.stamina == 15 # Unchanged
    
    p.recover_stamina(2)
    assert p.stamina == 17

def test_level_up():
    p = Player("testuser")
    initial_hp = p.max_hp
    
    # Gain enough XP
    leveled = p.gain_xp(100)
    
    assert leveled
    assert p.level == 2
    assert p.max_hp > initial_hp
    assert p.hp == p.max_hp # Full heal on level up
    assert p.xp == 0 # Reset (or carry over if we implemented that logic, currently subtracts)
