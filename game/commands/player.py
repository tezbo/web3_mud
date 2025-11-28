"""
Player Commands

Handles commands related to player settings and status:
- description (desc): Set player's custom description
"""

from typing import Tuple, Dict, Any, List, Optional
from game.models.player import Player

def handle_description_command(
    verb: str,
    tokens: List[str],
    game: Dict[str, Any],
    username: str,
    user_id: Optional[str] = None,
    db_conn: Optional[Any] = None,
    broadcast_fn: Optional[Any] = None,
    who_fn: Optional[Any] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Handle 'description' command.
    Usage: description <text>
    """
    if len(tokens) < 2:
        # Show current description with helpful guidance
        player = Player(username or "adventurer")
        player.load_from_state(game)
        
        help_text = """
HOW TO WRITE YOUR DESCRIPTION:

Write your description as if completing the sentence "You are..."
Don't include "is" or "are" at the start - the game adds this automatically.

GOOD EXAMPLES:
  description a friendly looking traveler with bright eyes
  description a grizzled warrior wearing battle-scarred armor
  description a mysterious figure cloaked in shadows

WHAT YOU'LL SEE:
  When you look at yourself: "You are a friendly looking traveler..."
  When others look at you: "He is a friendly looking traveler..." (or She/They)

BAD EXAMPLES:
  description is friendly (Don't start with 'is')
  description I am a traveler (Don't use 'I am')
"""
        
        if player.user_description:
            return f"Your current description:\nYou are {player.user_description}\n\n{help_text}To change it, type: description <new text>", game
        else:
            return f"You have no custom description set.\n{help_text}To set one, type: description <your description>", game

    new_description = " ".join(tokens[1:])
    
    # Validate and clean up the description
    # Remove leading "is/are/am" if present
    new_description = new_description.strip()
    if new_description.lower().startswith("is "):
        new_description = new_description[3:]
    elif new_description.lower().startswith("are "):
        new_description = new_description[4:]
    elif new_description.lower().startswith("am "):
        new_description = new_description[3:]
    
    # Update game state
    player = Player(username or "adventurer")
    player.load_from_state(game)
    
    player.user_description = new_description
    game["user_description"] = new_description
    
    return f"Description set!\n\nWhen you look at yourself:\n  You are {new_description}\n\nWhen others look at you:\n  He/She/They is/are {new_description}", game
