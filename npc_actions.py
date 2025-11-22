"""
NPC periodic actions system.

This module handles NPC idle actions that cycle through based on their location.
Actions are room-appropriate and broadcast to all players in the room.
"""

import random
from typing import Dict, List, Optional
from npc import NPCS

# NPC actions by room - each NPC has a list of actions for each room they can be in
NPC_ACTIONS: Dict[str, Dict[str, List[str]]] = {
    "innkeeper": {
        "tavern": [
            "Mara squints at you quizzically, then returns to her work.",
            "Mara straightens the signboard hanging near the entrance.",
            "Mara picks up a cloth and wipes down a bench, humming quietly to herself.",
            "Mara checks the fire in the hearth, adjusting the logs.",
            "Mara arranges tankards on a shelf, making sure everything is in order.",
            "Mara glances around the room, making sure all is well.",
            "Mara wipes her hands on her apron and looks around the tavern.",
        ],
        # Generic actions for other rooms (if Mara ever leaves the tavern)
        "default": [
            "Mara looks around, seeming slightly out of place.",
            "Mara adjusts her clothing and looks around.",
        ],
    },
    "old_storyteller": {
        "town_square": [
            "The Old Storyteller strokes his beard thoughtfully, lost in memory.",
            "The Old Storyteller gazes at the fountain, as if seeing stories in the water.",
            "The Old Storyteller adjusts his robes and settles into a comfortable position.",
            "The Old Storyteller looks up at the watchtower, a knowing smile on his face.",
            "The Old Storyteller traces patterns in the air with his finger, as if recounting an old tale.",
            "The Old Storyteller closes his eyes briefly, as if listening to voices only he can hear.",
        ],
        "default": [
            "The Old Storyteller looks around, taking in his surroundings.",
            "The Old Storyteller adjusts his robes and settles in.",
        ],
    },
    "blacksmith": {
        "smithy": [
            "The Blacksmith examines a piece of metal, turning it over in their hands.",
            "The Blacksmith wipes sweat from their brow with the back of their hand.",
            "The Blacksmith adjusts the tools on the wall, organizing them by size.",
            "The Blacksmith stokes the forge, sending sparks flying.",
            "The Blacksmith tests the edge of a blade, running a thumb along it carefully.",
            "The Blacksmith takes a moment to stretch, working out the kinks in their back.",
            "The Blacksmith checks the temperature of the forge, nodding in satisfaction.",
        ],
        "default": [
            "The Blacksmith looks around, their hands still covered in soot.",
            "The Blacksmith flexes their hands, as if missing their tools.",
        ],
    },
    "herbalist": {
        "market_lane": [
            "The Herbalist carefully examines a bundle of herbs, checking their quality.",
            "The Herbalist arranges plants on their stall, making sure each is properly labeled.",
            "The Herbalist sniffs a leaf, then nods in approval.",
            "The Herbalist gently touches the petals of a flower, a soft smile on their face.",
            "The Herbalist checks the soil of a potted plant, adjusting its position.",
            "The Herbalist writes something in a small notebook, then looks up thoughtfully.",
        ],
        "default": [
            "The Herbalist looks around, as if searching for plants.",
            "The Herbalist adjusts their robes and looks about.",
        ],
    },
    "quiet_acolyte": {
        "shrine_of_the_forgotten": [
            "The Quiet Acolyte kneels before the shrine, their lips moving in silent prayer.",
            "The Quiet Acolyte traces the ancient carvings with reverent fingers.",
            "The Quiet Acolyte lights a small candle, the flame casting gentle shadows.",
            "The Quiet Acolyte arranges offerings at the base of the shrine.",
            "The Quiet Acolyte closes their eyes and breathes deeply, finding peace.",
            "The Quiet Acolyte studies the runes on the shrine, lost in contemplation.",
        ],
        "default": [
            "The Quiet Acolyte looks around, their expression serene.",
            "The Quiet Acolyte adjusts their robes and settles into a meditative pose.",
        ],
    },
    "nervous_farmer": {
        "forest_edge": [
            "The Nervous Farmer glances toward the forest, then quickly looks away.",
            "The Nervous Farmer shifts uneasily, keeping one eye on the trees.",
            "The Nervous Farmer mutters something under their breath, too quiet to hear.",
            "The Nervous Farmer checks their tools, as if preparing to leave quickly.",
            "The Nervous Farmer looks over their shoulder, then relaxes slightly.",
            "The Nervous Farmer wipes their hands on their trousers, looking nervous.",
        ],
        "default": [
            "The Nervous Farmer looks around anxiously.",
            "The Nervous Farmer shifts from foot to foot, seeming uneasy.",
        ],
    },
    "forest_spirit": {
        "whispering_trees": [
            "The Forest Spirit seems to move between the trees, barely visible.",
            "A sense of watchfulness emanates from the Forest Spirit, as if it's observing everything.",
            "The Forest Spirit's presence makes the leaves rustle in a pattern that almost sounds like speech.",
            "The Forest Spirit drifts closer, then fades back into the shadows.",
            "The Forest Spirit seems to glow faintly, its ethereal form shifting.",
            "The Forest Spirit reaches out with an otherworldly hand, touching a tree trunk gently.",
        ],
        "default": [
            "The Forest Spirit's presence feels out of place here.",
            "The Forest Spirit drifts, its form barely visible.",
        ],
    },
    "patrolling_guard": {
        "watchtower_path": [
            "The Patrolling Guard scans the path ahead, hand resting on their weapon.",
            "The Patrolling Guard checks the horizon, looking for any signs of trouble.",
            "The Patrolling Guard adjusts their armor, making sure everything is secure.",
            "The Patrolling Guard pauses to rest, but remains alert.",
            "The Patrolling Guard marks something in a small notebook, then continues watching.",
            "The Patrolling Guard stands at attention, their eyes constantly moving.",
        ],
        "default": [
            "The Patrolling Guard looks around, remaining alert.",
            "The Patrolling Guard checks their equipment and looks about.",
        ],
    },
    "watch_guard": {
        "watchtower": [
            "Darin peers through a spyglass, scanning the horizon methodically.",
            "Darin leans against the tower wall, taking a brief moment to rest.",
            "Darin checks the wind direction, then returns to watching.",
            "Darin makes a note in a logbook, then looks up at the sky.",
            "Darin stretches, working out the stiffness from long hours of watching.",
            "Darin adjusts the spyglass, then continues scanning the valley below.",
        ],
        "default": [
            "Darin looks around, maintaining his watchful posture.",
            "Darin checks his equipment and remains alert.",
        ],
    },
    "wandering_trader": {
        "old_road": [
            "The Wandering Trader organizes goods in their pack, checking each item carefully.",
            "The Wandering Trader looks down the road, as if expecting someone.",
            "The Wandering Trader counts coins, then tucks them away safely.",
            "The Wandering Trader adjusts their hat and looks around with interest.",
            "The Wandering Trader examines a trinket, holding it up to the light.",
            "The Wandering Trader hums a traveling tune, their eyes scanning the horizon.",
        ],
        "default": [
            "The Wandering Trader looks around, as if assessing the area.",
            "The Wandering Trader adjusts their pack and looks about.",
        ],
    },
}


def get_npc_action(npc_id: str, room_id: str) -> Optional[str]:
    """
    Get a random action for an NPC in a specific room.
    
    Args:
        npc_id: The NPC ID
        room_id: The current room ID
    
    Returns:
        str or None: A random action string, or None if no actions are defined
    """
    npc_actions = NPC_ACTIONS.get(npc_id)
    if not npc_actions:
        return None
    
    # Try room-specific actions first
    actions = npc_actions.get(room_id)
    
    # Fall back to default actions if no room-specific actions
    if not actions:
        actions = npc_actions.get("default")
    
    if not actions:
        return None
    
    # Return a random action
    return random.choice(actions)


def get_all_npc_actions_for_room(room_id: str) -> Dict[str, str]:
    """
    Get actions for all NPCs currently in a room.
    
    Args:
        room_id: The room ID
    
    Returns:
        dict: Mapping of npc_id -> action_string for NPCs that have actions
    """
    from game_engine import NPC_STATE
    
    actions = {}
    for npc_id, npc_state in NPC_STATE.items():
        if npc_state.get("room") == room_id and npc_state.get("alive", True):
            action = get_npc_action(npc_id, room_id)
            if action:
                actions[npc_id] = action
    
    return actions

