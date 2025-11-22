"""
Room detail callbacks for Tiny Web MUD.

This module contains callback functions that can be triggered when players
interact with room details/fixtures. Callbacks are referenced by name in
room JSON files and invoked via invoke_room_detail_callback().

Callbacks can:
- Return descriptive text to display to the player
- Mutate game state (inventory, room items, NPC state)
- Trigger side effects (reputation changes, status effects, etc.)

Keep functions pure with respect to WORLD (read-only), but allow mutation
of game, ROOM_STATE, or NPC_STATE as needed.
"""


def smithy_touch_hammers(game, username, room_id, detail_id):
    """
    Callback for touching hammers in the smithy.
    
    Args:
        game: The game state dictionary (can be mutated)
        username: The username of the player
        room_id: The room ID where this detail is located
        detail_id: The detail ID that was interacted with
    
    Returns:
        str: Response message to display to the player
    """
    # Example: maybe the blacksmith reacts, or we print a flavour line
    return "You run your hand along the worn handles of the hammers. The wood is smooth from years of use."


# Add more callbacks here as needed
# Example structure:
# def <room>_<action>_<detail>(game, username, room_id, detail_id):
#     # Your callback logic here
#     return "Response message"

