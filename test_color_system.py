
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

# Mock app module BEFORE importing game_engine
mock_app = MagicMock()
sys.modules["app"] = mock_app

from game_engine import handle_command
from color_system import get_color_settings, set_color_for_type, DEFAULT_COLORS

class TestColorSystem(unittest.TestCase):
    def setUp(self):
        self.game = {
            "username": "testuser",
            "location": "town_square"
            # color_settings intentionally missing to test default initialization
        }
        
    def test_default_colors(self):
        """Test that default colors are returned correctly."""
        settings = get_color_settings(self.game)
        self.assertEqual(settings["say"], "cyan")
        self.assertEqual(DEFAULT_COLORS["exits"], "darkgreen")
        self.assertEqual(DEFAULT_COLORS["weather"], "white")
        self.assertEqual(DEFAULT_COLORS["weather_desc"], "white")
        self.assertEqual(DEFAULT_COLORS["npc"], "white")
        self.assertEqual(DEFAULT_COLORS["room_descriptions"], "white")
        
    def test_set_color(self):
        """Test setting a color."""
        # Initialize settings first
        get_color_settings(self.game)
        
        success, msg = set_color_for_type(self.game, "say", "red")
        self.assertTrue(success)
        self.assertEqual(self.game["color_settings"]["say"], "red")
        
    def test_invalid_color(self):
        """Test setting an invalid color."""
        get_color_settings(self.game)
        success, msg = set_color_for_type(self.game, "say", "invalid_color")
        self.assertFalse(success)
        
    def test_invalid_type(self):
        """Test setting an invalid type."""
        get_color_settings(self.game)
        success, msg = set_color_for_type(self.game, "invalid_type", "red")
        self.assertFalse(success)
        
    def test_colour_command(self):
        """Test the colour command handler."""
        # Test listing
        response, _ = handle_command("colour", self.game, "testuser", "123")
        self.assertIn("Current Colour Settings:", response)
        
        # Test setting
        response, _ = handle_command("colour say green", self.game, "testuser", "123")
        self.assertIn("Color for say set to green", response)
        self.assertEqual(self.game["color_settings"]["say"], "green")
        
        # Verify persistence was called on the mock app
        self.assertTrue(mock_app.save_game.called)
        self.assertTrue(mock_app.save_state_to_disk.called)
        
    def test_reset_color(self):
        """Test resetting a color to default."""
        # Initialize and set to non-default
        get_color_settings(self.game)
        set_color_for_type(self.game, "say", "red")
        
        # Reset
        mock_app.reset_mock()
        response, _ = handle_command("colour say default", self.game, "testuser", "123")
            
        self.assertIn("Reset colour for 'say' to default", response)
        self.assertNotIn("say", self.game["color_settings"])
        
        # Verify persistence
        self.assertTrue(mock_app.save_game.called)
        self.assertTrue(mock_app.save_state_to_disk.called)

if __name__ == '__main__':
    unittest.main()
