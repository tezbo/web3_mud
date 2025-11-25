import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.systems.ambient import AmbientSystem
from game.models.room import Room

def test_ambient_system_tick():
    system = AmbientSystem()
    system.check_interval = 10
    system.chance_to_trigger = 1.0 # Force trigger for test
    
    # Mock WorldManager and Room
    mock_room = MagicMock(spec=Room)
    mock_room.ambient_messages = ["Test message"]
    mock_room.players = ["player1"] # Simulate active room
    
    with patch('game.world.manager.WorldManager.get_instance') as mock_wm_cls:
        mock_wm = mock_wm_cls.return_value
        mock_wm.active_rooms = {"room1": mock_room}
        
        with patch('game_engine.broadcast_to_room') as mock_broadcast:
            # Tick 1: Should not trigger (interval not met)
            system.tick({}, 5)
            mock_broadcast.assert_not_called()
            
            # Tick 2: Should trigger (interval met)
            system.tick({}, 15)
            mock_broadcast.assert_called_with("room1", "\n[Ambient] Test message\n")
            
            # Reset mock
            mock_broadcast.reset_mock()
            
            # Tick 3: Should not trigger (interval not met since last trigger)
            system.tick({}, 20)
            mock_broadcast.assert_not_called()

def test_ambient_system_no_messages():
    system = AmbientSystem()
    system.check_interval = 10
    system.chance_to_trigger = 1.0
    
    mock_room = MagicMock(spec=Room)
    mock_room.ambient_messages = [] # Empty
    
    with patch('game.world.manager.WorldManager.get_instance') as mock_wm_cls:
        mock_wm = mock_wm_cls.return_value
        mock_wm.active_rooms = {"room1": mock_room}
        
        with patch('game_engine.broadcast_to_room') as mock_broadcast:
            system.tick({}, 15)
            mock_broadcast.assert_not_called()
