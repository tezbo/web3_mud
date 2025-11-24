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


def belltower_touch(game, username, room_id, detail_id):
    """
    Callback for touching the belltower.
    
    Args:
        game: The game state dictionary (can be mutated)
        username: The username of the player
        room_id: The room ID where this detail is located
        detail_id: The detail ID that was interacted with
    
    Returns:
        str: Response message to display to the player
    """
    from game_engine import get_current_hour_12h, get_time_of_day
    
    hour = get_current_hour_12h()
    time_of_day = get_time_of_day()
    
    messages = [
        f"You touch the cool stone of the belltower. The bell hangs silently above, last tolling at {hour} o'clock.",
        f"You run your hand along the weathered stone. The belltower stands solid and ancient, a keeper of time.",
        f"You feel the rough texture of the stone. The bell above is still, waiting for the next hour to strike.",
    ]
    
    import random
    return random.choice(messages)


def belltower_look(game, username, room_id, detail_id):
    """
    Callback for looking at the belltower specifically.
    
    Args:
        game: The game state dictionary (can be mutated)
        username: The username of the player
        room_id: The room ID where this detail is located
        detail_id: The detail ID that was interacted with
    
    Returns:
        str: Response message to display to the player
    """
    from game_engine import get_current_hour_12h, get_time_of_day
    
    hour = get_current_hour_12h()
    time_of_day = get_time_of_day()
    
    time_desc = {
        "dawn": "The bell catches the first rays of morning light.",
        "day": "The bell is clearly visible in the open arches.",
        "dusk": "The bell is silhouetted against the darkening sky.",
        "night": "The bell is a dark shape against the night sky.",
    }
    
    return (
        f"A stone belltower rises from the center of the square, its weathered stone showing the passage of time. "
        f"The bell hangs within open arches, visible from below. {time_desc.get(time_of_day, '')} "
        f"It's clearly old, but well-maintained, and serves as both a landmark and timekeeper for Hollowvale."
    )


def old_road_signpost_look(game, username, room_id, detail_id):
    """
    Callback for looking at the signpost on the old road.
    
    Args:
        game: The game state dictionary (can be mutated)
        username: The username of the player
        room_id: The room ID where this detail is located
        detail_id: The detail ID that was interacted with
    
    Returns:
        str: Response message to display to the player
    """
    return (
        "An old, weathered signpost stands at the side of the road. Its wooden surface is worn by years of exposure "
        "to the elements, but the markings are still readable despite the fading paint. "
        "(Type 'read signpost' to read what it says.)"
    )


def old_road_signpost_read(game, username, room_id, detail_id):
    """
    Callback for reading the signpost on the old road.
    
    Args:
        game: The game state dictionary (can be mutated)
        username: The username of the player
        room_id: The room ID where this detail is located
        detail_id: The detail ID that was interacted with
    
    Returns:
        str: Response message to display to the player
    """
    return (
        "You step closer to the weathered signpost and squint at the faded markings. "
        "The paint has worn away in places, but you can still make out the words:\n\n"
        "  'EASTWARD ROAD'\n"
        "  'To the Kingdoms Beyond'\n"
        "  'Travelers Beware'\n\n"
        "Below that, someone has carved a small warning: 'The road grows dangerous past the horizon. "
        "Only the brave or foolish venture further.'"
    )


# Add more callbacks here as needed
# Example structure:
# def <room>_<action>_<detail>(game, username, room_id, detail_id):
#     # Your callback logic here
#     return "Response message"

