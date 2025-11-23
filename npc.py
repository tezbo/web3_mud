"""
NPC system for Tiny Web MUD.

This module defines the NPC class and provides NPC matching and interaction logic.
"""

from collections import defaultdict
from typing import Optional, Tuple

# Safe import of AI client (optional)
try:
    from ai_client import generate_npc_reply
except ImportError:
    generate_npc_reply = None


class NPC:
    """Represents a non-player character in the game."""
    
    def __init__(self, npc_id: str, name: str, title: Optional[str] = None,
                 description: str = "", personality: str = "",
                 reactions: dict = None, home: Optional[str] = None,
                 use_ai: bool = False, shortname: Optional[str] = None,
                 stats: dict = None, traits: dict = None, pronoun: str = "they",
                 attackable: bool = False, hostile: bool = False):
        self.id = npc_id
        self.name = name
        self.title = title
        self.description = description
        self.personality = personality
        self.reactions = reactions or {}
        self.home = home
        self.use_ai = use_ai
        self.stats = stats or {}
        self.traits = traits or {}
        self.pronoun = pronoun  # "he", "she", "they", "it"
        self.attackable = attackable  # Whether this NPC can be attacked
        self.hostile = hostile  # Whether this NPC is hostile (for future aggro)
        
        # Auto-generate shortname if not provided (last word of name, lowercased)
        if shortname is None:
            name_words = name.split()
            self.shortname = name_words[-1].lower() if name_words else name.lower()
        else:
            self.shortname = shortname
    
    def to_dict(self):
        """Convert NPC to dictionary format for backward compatibility."""
        result = {
            "name": self.name,
            "title": self.title or self.name,
            "description": self.description,
            "personality": self.personality,
            "reactions": self.reactions,
        }
        if self.home:
            result["home"] = self.home
        if self.use_ai:
            result["use_ai"] = True
        if self.stats:
            result["stats"] = self.stats
        if self.traits:
            result["traits"] = self.traits
        return result


# Reaction counters for deterministic NPC reactions
_reaction_counters = defaultdict(int)


# NPC definitions (static metadata) - moved from game_engine.py
_NPCS_DICT = {
    "old_storyteller": {
        "name": "Old Storyteller",
        "title": "Old Storyteller",
        "description": "An elderly figure with kind eyes, known for sharing tales of the past.",
        "personality": "wise, patient, loves stories",
        "pronoun": "he",
        "stats": {
            "max_hp": 15,
            "attack": 1,
            "defense": 1,
            "speed": 1,
            "faction": "villagers",
        },
        "traits": {
            "authority": 0.3,
            "kindness": 0.8,
            "aggression": 0.1,
            "curiosity": 0.7,
        },
        "reactions": {
            "nod": [
                "The Old Storyteller returns your nod with a knowing smile.",
                "The Old Storyteller nods slowly, as if acknowledging something deeper.",
            ],
            "smile": [
                "The Old Storyteller's eyes crinkle with warmth as they smile back.",
            ],
            "wave": [
                "The Old Storyteller raises a weathered hand in greeting.",
            ],
        },
    },
    "innkeeper": {
        "name": "Mara",
        "title": "Innkeeper of the Rusty Tankard",
        "description": "A friendly, bustling figure who keeps the tavern running smoothly.",
        "personality": "gruff but kind, keeps a sharp eye on trouble",
        "home": "tavern",
        "use_ai": True,
        "pronoun": "she",
        "stats": {
            "max_hp": 18,
            "attack": 2,
            "defense": 2,
            "speed": 2,
            "faction": "villagers",
        },
        "traits": {
            "authority": 0.5,
            "kindness": 0.6,
            "aggression": 0.2,
            "curiosity": 0.4,
        },
        "reactions": {
            "nod": [
                "Mara gives you a short, approving nod.",
                "Mara tilts her head in acknowledgment.",
            ],
            "smile": [
                "Mara's stern face softens for a moment before she looks away.",
            ],
            "wave": [
                "Mara waves back while continuing to wipe down a table.",
            ],
        },
    },
    "blacksmith": {
        "name": "Blacksmith",
        "title": "Blacksmith",
        "description": "A burly figure with soot-stained hands, master of the forge.",
        "personality": "practical, straightforward, takes pride in work",
        "pronoun": "they",
        "stats": {
            "max_hp": 25,
            "attack": 4,
            "defense": 3,
            "speed": 2,
            "faction": "villagers",
        },
        "traits": {
            "authority": 0.4,
            "kindness": 0.5,
            "aggression": 0.3,
            "curiosity": 0.3,
        },
        "reactions": {
            "nod": [
                "The Blacksmith gives you a brief nod without pausing their work.",
            ],
            "wave": [
                "The Blacksmith raises a soot-stained hand in greeting.",
            ],
        },
    },
    "herbalist": {
        "name": "Herbalist",
        "title": "Herbalist",
        "description": "A quiet person with knowledge of plants and their uses.",
        "personality": "quiet, observant, gentle",
        "pronoun": "they",
        "stats": {
            "max_hp": 12,
            "attack": 1,
            "defense": 1,
            "speed": 2,
            "faction": "villagers",
        },
        "traits": {
            "authority": 0.2,
            "kindness": 0.7,
            "aggression": 0.1,
            "curiosity": 0.6,
        },
        "reactions": {
            "nod": [
                "The Herbalist gives you a quiet, gentle nod.",
            ],
            "smile": [
                "The Herbalist offers a small, shy smile.",
            ],
        },
    },
    "quiet_acolyte": {
        "name": "Quiet Acolyte",
        "title": "Quiet Acolyte",
        "description": "A robed figure who tends the shrine with quiet devotion.",
        "personality": "serene, contemplative, speaks rarely",
        "pronoun": "they",
        "stats": {
            "max_hp": 15,
            "attack": 1,
            "defense": 2,
            "speed": 1,
            "faction": "villagers",
        },
        "traits": {
            "authority": 0.3,
            "kindness": 0.7,
            "aggression": 0.1,
            "curiosity": 0.5,
        },
        "reactions": {
            "nod": [
                "The Quiet Acolyte inclines their head slightly in acknowledgment.",
            ],
            "smile": [
                "The Quiet Acolyte's expression softens with a peaceful smile.",
            ],
        },
    },
    "nervous_farmer": {
        "name": "Nervous Farmer",
        "title": "Nervous Farmer",
        "description": "A local farmer who seems uneasy near the forest edge.",
        "personality": "anxious, cautious, superstitious",
        "pronoun": "they",
        "stats": {
            "max_hp": 14,
            "attack": 2,
            "defense": 1,
            "speed": 2,
            "faction": "villagers",
        },
        "traits": {
            "authority": 0.2,
            "kindness": 0.5,
            "aggression": 0.2,
            "curiosity": 0.4,
        },
        "reactions": {
            "nod": [
                "The Nervous Farmer gives you a quick, nervous nod while glancing toward the forest.",
            ],
            "wave": [
                "The Nervous Farmer hesitantly raises a hand, looking around uneasily.",
            ],
        },
    },
    "forest_spirit": {
        "name": "Forest Spirit",
        "title": "Forest Spirit",
        "description": "An ethereal presence that seems to watch from the shadows of the trees.",
        "personality": "mysterious, ancient, otherworldly",
        "pronoun": "it",
        "attackable": True,  # Example attackable NPC for testing
        "stats": {
            "max_hp": 30,
            "attack": 3,
            "defense": 4,
            "speed": 3,
            "faction": "neutral",
        },
        "traits": {
            "authority": 0.4,
            "kindness": 0.6,
            "aggression": 0.2,
            "curiosity": 0.7,
            "patience": 0.9,
        },
        "reactions": {
            "nod": [
                "The Forest Spirit seems to acknowledge you, though you're not sure how.",
            ],
            "smile": [
                "There's a sense of warmth from the Forest Spirit, like sunlight through leaves.",
            ],
        },
    },
    "patrolling_guard": {
        "name": "Patrolling Guard",
        "title": "Patrolling Guard",
        "description": "A watchful figure keeping an eye on the path to the watchtower.",
        "personality": "alert, professional, duty-focused",
        "pronoun": "they",
        "stats": {
            "max_hp": 20,
            "attack": 3,
            "defense": 2,
            "speed": 2,
            "faction": "guards",
        },
        "traits": {
            "authority": 0.7,
            "kindness": 0.4,
            "aggression": 0.3,
            "curiosity": 0.3,
        },
        "reactions": {
            "nod": [
                "The Patrolling Guard gives you a brief, professional nod while continuing to scan the area.",
            ],
            "wave": [
                "The Patrolling Guard acknowledges your wave with a curt nod.",
            ],
        },
    },
    "watch_guard": {
        "name": "Darin",
        "title": "Watch Guard",
        "description": "A vigilant guard stationed at the watchtower, scanning the horizon.",
        "personality": "dutiful, dry sense of humour, a bit tired",
        "pronoun": "he",
        "stats": {
            "max_hp": 22,
            "attack": 3,
            "defense": 3,
            "speed": 2,
            "faction": "guards",
        },
        "traits": {
            "authority": 0.7,
            "kindness": 0.4,
            "aggression": 0.3,
            "curiosity": 0.5,
        },
        "reactions": {
            "nod": [
                "The Watch Guard raises an eyebrow, then nods back slightly.",
                "The Watch Guard gives you a brief, professional nod.",
            ],
            "smile": [
                "Darin cracks a small smile. 'Not much to smile about up here, but I appreciate the gesture.'",
            ],
        },
    },
    "wandering_trader": {
        "name": "Wandering Trader",
        "title": "Wandering Trader",
        "description": "A traveler with goods from distant lands, always ready to trade stories.",
        "personality": "friendly, talkative, always looking for business",
        "pronoun": "they",
        "stats": {
            "max_hp": 16,
            "attack": 2,
            "defense": 2,
            "speed": 3,
            "faction": "neutral",
        },
        "traits": {
            "authority": 0.3,
            "kindness": 0.6,
            "aggression": 0.2,
            "curiosity": 0.8,
        },
        "reactions": {
            "nod": [
                "The Wandering Trader nods enthusiastically. 'Good to see a friendly face!'",
            ],
            "smile": [
                "The Wandering Trader grins broadly. 'Ah, a smile! That's what I like to see.'",
            ],
            "wave": [
                "The Wandering Trader waves back with enthusiasm. 'Greetings, traveler!'",
            ],
        },
    },
}


def load_npcs() -> dict:
    """
    Load NPCs from the static definitions and return a dict mapping npc_id -> NPC.
    
    Returns:
        dict: Dictionary mapping NPC IDs to NPC instances
    """
    npcs = {}
    for npc_id, npc_data in _NPCS_DICT.items():
        npc = NPC(
            npc_id=npc_id,
            name=npc_data["name"],
            title=npc_data.get("title"),
            description=npc_data.get("description", ""),
            personality=npc_data.get("personality", ""),
            reactions=npc_data.get("reactions", {}),
            home=npc_data.get("home"),
            use_ai=npc_data.get("use_ai", False),
            shortname=npc_data.get("shortname"),  # Allow explicit shortname override
            stats=npc_data.get("stats"),  # Optional stats dict
            traits=npc_data.get("traits"),  # Optional traits dict
            pronoun=npc_data.get("pronoun", "they"),  # Default to "they" if not specified
            attackable=npc_data.get("attackable", False),  # Default to False for backwards compatibility
            hostile=npc_data.get("hostile", False)  # Default to False
        )
        npcs[npc_id] = npc
    return npcs


# Load NPCs on module import
NPCS = load_npcs()


# NPC attack callback system
# Signature: (game, username, npc_id) -> str (message to show to the player)
NPC_ON_ATTACK: Dict[str, Callable[[dict, str, str], str]] = {}


def get_npc_on_attack_callback(npc_id: str) -> Optional[Callable[[dict, str, str], str]]:
    """
    Get the on_attack callback for an NPC, if one exists.
    
    Args:
        npc_id: The NPC ID
    
    Returns:
        Callable or None: The callback function, or None if not found
    """
    return NPC_ON_ATTACK.get(npc_id)


def register_npc_on_attack_callback(npc_id: str, callback: Callable[[dict, str, str], str]):
    """
    Register an on_attack callback for an NPC.
    
    Args:
        npc_id: The NPC ID
        callback: Function that takes (game, username, npc_id) and returns a message string
    """
    NPC_ON_ATTACK[npc_id] = callback


def _innkeeper_on_attack(game: dict, username: str, npc_id: str) -> str:
    """
    Callback for when player attacks the innkeeper (Mara).
    Decreases reputation, moves NPC home, and sets talk cooldown.
    """
    # Import here to avoid circular imports
    from game_engine import adjust_reputation, NPC_STATE, set_npc_talk_cooldown
    
    # Decrease reputation
    adjust_reputation(game, npc_id, -10, "attacked")
    
    # Move NPC to home room
    npc = NPCS.get(npc_id)
    if npc and npc.home:
        if npc_id not in NPC_STATE:
            NPC_STATE[npc_id] = {}
        NPC_STATE[npc_id]["room"] = npc.home
    
    # Set talk cooldown for 1 in-game hour (60 minutes)
    set_npc_talk_cooldown(game, npc_id, 60)
    
    return "Mara looks shocked and disappointed that you'd even try that. She turns away and refuses to speak with you."


def _old_storyteller_on_attack(game: dict, username: str, npc_id: str) -> str:
    """
    Callback for when player attacks the Old Storyteller.
    Decreases reputation, moves NPC home, and sets talk cooldown.
    """
    # Import here to avoid circular imports
    from game_engine import adjust_reputation, NPC_STATE, set_npc_talk_cooldown
    
    # Decrease reputation
    adjust_reputation(game, npc_id, -15, "attacked")
    
    # Move NPC to home room
    npc = NPCS.get(npc_id)
    if npc and npc.home:
        if npc_id not in NPC_STATE:
            NPC_STATE[npc_id] = {}
        NPC_STATE[npc_id]["room"] = npc.home
    
    # Set talk cooldown for 1 in-game hour (60 minutes)
    set_npc_talk_cooldown(game, npc_id, 60)
    
    return "The Old Storyteller looks at you with deep sadness. 'Violence has no place here, child.' He turns and walks away, refusing to speak with you."


# Register the callbacks
register_npc_on_attack_callback("innkeeper", _innkeeper_on_attack)
register_npc_on_attack_callback("old_storyteller", _old_storyteller_on_attack)


def match_npc_in_room(room_npc_ids: list, target_text: str) -> Tuple[Optional[str], Optional[NPC]]:
    """
    Match a target text against NPCs present in a room.
    
    Matching rules (in order):
    1. Exact id match
    2. Exact full name match
    3. Exact shortname match
    4. Startswith match on id/name/shortname
    5. Word-level matches
    
    Args:
        room_npc_ids: List of NPC IDs present in the room
        target_text: The text to match against (lowercased)
    
    Returns:
        tuple: (npc_id, NPC) if match found, (None, None) otherwise
    """
    target_lower = target_text.lower().strip()
    
    for npc_id in room_npc_ids:
        if npc_id not in NPCS:
            continue
        
        npc = NPCS[npc_id]
        npc_id_lower = npc_id.lower()
        npc_name_lower = npc.name.lower()
        npc_shortname_lower = npc.shortname.lower()
        npc_title_lower = (npc.title or "").lower()
        
        # Rule 1: Exact id match
        if target_lower == npc_id_lower:
            return npc_id, npc
        
        # Rule 2: Exact full name match
        if target_lower == npc_name_lower:
            return npc_id, npc
        
        # Rule 3: Exact shortname match
        if target_lower == npc_shortname_lower:
            return npc_id, npc
        
        # Rule 4: Startswith match on id/name/shortname
        if (npc_id_lower.startswith(target_lower) or
            npc_name_lower.startswith(target_lower) or
            npc_shortname_lower.startswith(target_lower)):
            return npc_id, npc
        
        # Rule 5: Word-level matches
        target_words = set(target_lower.split())
        name_words = set(npc_name_lower.split())
        title_words = set(npc_title_lower.split())
        shortname_words = {npc_shortname_lower}
        
        if (target_words.intersection(name_words) or
            target_words.intersection(title_words) or
            target_words.intersection(shortname_words) or
            target_lower in npc_name_lower.split()):
            return npc_id, npc
    
    return None, None


def get_npc_reaction(npc_id: str, verb: str) -> Optional[str]:
    """
    Return a deterministic reaction line for a given npc_id and verb,
    or None if the NPC has no reaction defined.
    
    Args:
        npc_id: The NPC ID string
        verb: The emote verb (e.g., "nod", "smile")
    
    Returns:
        str or None: A reaction line, or None if no reaction is defined
    """
    npc = NPCS.get(npc_id)
    if not npc:
        return None

    reactions_for_verb = npc.reactions.get(verb)
    if not reactions_for_verb:
        return None

    # Simple round-robin through the list for determinism
    key = (npc_id, verb)
    idx = _reaction_counters.get(key, 0)
    text = reactions_for_verb[idx % len(reactions_for_verb)]
    _reaction_counters[key] = idx + 1
    return text


def generate_npc_line(npc_id: str, game: dict, username: Optional[str] = None,
                      user_id: Optional[int] = None, db_conn=None) -> str:
    """
    Generate a deterministic placeholder line of dialogue for an NPC.
    
    Args:
        npc_id: The NPC ID string
        game: The game state dictionary
        username: Optional username of the player talking to the NPC
        user_id: Optional user ID for token budget tracking
        db_conn: Optional database connection for token budget tracking
    
    Returns:
        str: A placeholder dialogue line from the NPC
    """
    if npc_id not in NPCS:
        return "Someone looks at you but says nothing."
    
    npc = NPCS[npc_id]
    
    # Check if this NPC uses AI
    if npc.use_ai and generate_npc_reply is not None:
        # Get current room - need to import WORLD from game_engine
        from game_engine import WORLD
        loc_id = game.get("location", "town_square")
        if loc_id in WORLD:
            room = WORLD[loc_id]
            
            # Build player_input string
            player_input = f"talk to {npc.name}"
            
            # Collect recent log lines (last 10 entries)
            recent_log = game.get("log", [])[-10:] if game.get("log") else None
            
            # Store NPC ID in game for AI client to access
            game["_current_npc_id"] = npc_id
            
            # Convert NPC to dict for AI client (backward compatibility)
            npc_dict = npc.to_dict()
            
            # Call AI function (now returns tuple: response, error_message)
            ai_response, error_message = generate_npc_reply(
                npc_dict, room, game, username or "adventurer", player_input, 
                recent_log, user_id=user_id, db_conn=db_conn
            )
            
            # If AI returned a non-empty string, use it
            if ai_response and ai_response.strip():
                # Update memory with this interaction
                if npc_id not in game.get("npc_memory", {}):
                    game.setdefault("npc_memory", {})[npc_id] = []
                game["npc_memory"][npc_id].append({
                    "type": "talked",
                    "player_input": player_input,
                    "response": ai_response,
                })
                # Keep memory from growing too large
                if len(game["npc_memory"][npc_id]) > 20:
                    game["npc_memory"][npc_id] = game["npc_memory"][npc_id][-20:]
                
                # If there's an error message, append it to the response
                if error_message:
                    return ai_response + f"\n[Note: {error_message}]"
                return ai_response
    
    # Fall back to existing deterministic behaviour
    # Generate dialogue based on NPC
    if npc_id == "old_storyteller":
        if username:
            return f"The Old Storyteller looks at you with knowing eyes. 'Ah, {username}, welcome. The tales of this place run deep, deeper than most know. Perhaps you'll add your own chapter to the story.'"
        return "The Old Storyteller looks at you with knowing eyes. 'Welcome, traveler. The tales of this place run deep, deeper than most know.'"
    
    elif npc_id == "innkeeper":
        if username:
            return f"The Innkeeper smiles warmly. 'Welcome, {username}! We've got warm stew and good ale. Make yourself at home—this is a place where stories are shared and friendships are made.'"
        return "The Innkeeper smiles warmly. 'Welcome! We've got warm stew and good ale. Make yourself at home—this is a place where stories are shared.'"
    
    elif npc_id == "blacksmith":
        if username:
            return f"The Blacksmith wipes sweat from their brow. 'Ah, {username}. Good to see you. If you need anything forged or repaired, I'm your person. Quality work, fair prices.'"
        return "The Blacksmith wipes sweat from their brow. 'Good to see you. If you need anything forged or repaired, I'm your person. Quality work, fair prices.'"
    
    elif npc_id == "herbalist":
        if username:
            return f"The Herbalist looks up from their plants. 'Hello, {username}. The forest provides many useful things, if you know where to look. I can help you identify herbs and their properties.'"
        return "The Herbalist looks up from their plants. 'Hello. The forest provides many useful things, if you know where to look. I can help you identify herbs and their properties.'"
    
    elif npc_id == "quiet_acolyte":
        if username:
            return f"The Quiet Acolyte speaks softly, their voice barely above a whisper. 'Peace be with you, {username}. This place holds old power, old memories. Some say the forgotten paths still lead somewhere, if one knows how to walk them.'"
        return "The Quiet Acolyte speaks softly, their voice barely above a whisper. 'Peace be with you. This place holds old power, old memories. Some say the forgotten paths still lead somewhere.'"
    
    elif npc_id == "nervous_farmer":
        if username:
            return f"The Nervous Farmer glances toward the forest. 'Oh, {username}... I don't like being this close to the woods. Strange things happen there, things that don't make sense. Best to stay in the village, I say.'"
        return "The Nervous Farmer glances toward the forest. 'I don't like being this close to the woods. Strange things happen there, things that don't make sense. Best to stay in the village, I say.'"
    
    elif npc_id == "forest_spirit":
        if username:
            return f"The Forest Spirit's voice seems to come from everywhere and nowhere. '{username}... you walk between worlds. The trees remember, and they watch. Perhaps you will understand, in time.'"
        return "The Forest Spirit's voice seems to come from everywhere and nowhere. 'You walk between worlds. The trees remember, and they watch. Perhaps you will understand, in time.'"
    
    elif npc_id == "patrolling_guard":
        if username:
            return f"The Patrolling Guard nods. '{username}. Keeping watch is important work. The watchtower sees far, and we need to know what's coming. Stay safe out there.'"
        return "The Patrolling Guard nods. 'Keeping watch is important work. The watchtower sees far, and we need to know what's coming. Stay safe out there.'"
    
    elif npc_id == "watch_guard":
        if username:
            return f"The Watch Guard scans the horizon. '{username}, welcome to the watchtower. From here, you can see the whole valley. It's a reminder that Hollowvale is just one small part of a much larger world.'"
        return "The Watch Guard scans the horizon. 'Welcome to the watchtower. From here, you can see the whole valley. It's a reminder that Hollowvale is just one small part of a much larger world.'"
    
    elif npc_id == "wandering_trader":
        if username:
            return f"The Wandering Trader grins. 'Ah, {username}! Always good to meet a fellow traveler. I've seen many places, heard many stories. The road goes on forever, and there's always something new just over the next hill.'"
        return "The Wandering Trader grins. 'Always good to meet a fellow traveler. I've seen many places, heard many stories. The road goes on forever, and there's always something new just over the next hill.'"
    
    else:
        # Generic fallback for any NPC not specifically handled
        if username:
            return f"{npc.name} looks at you. 'Hello, {username}. How can I help you?'"
        return f"{npc.name} looks at you. 'Hello. How can I help you?'"

