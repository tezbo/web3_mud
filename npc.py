"""
NPC system for Tiny Web MUD.

This module defines the NPC class and provides NPC matching and interaction logic.
"""

from collections import defaultdict
from typing import Optional, Tuple, Callable, Dict, Any
from game.models.entity import Entity

# Safe import of AI client (optional)
try:
    from ai_client import generate_npc_reply
except ImportError:
    generate_npc_reply = None


class NPC(Entity):
    """Represents a non-player character in the game."""
    
    def __init__(self, npc_id: str, name: str, title: Optional[str] = None,
                 description: str = "", personality: str = "",
                 reactions: dict = None, home: Optional[str] = None,
                 use_ai: bool = False, shortname: Optional[str] = None,
                 stats: dict = None, traits: dict = None, pronoun: str = "they",
                 attackable: bool = False, hostile: bool = False,
                 inventory: list = None, weather_reactions: dict = None,
                 idle_actions: dict = None):
        super().__init__(npc_id, name) # Entity init sets up self.inventory = InventorySystem(self)
        self.id = npc_id
        
        self.title = title
        self.description = description
        self.personality = personality
        self.reactions = reactions or {}
        self.home = home
        self.use_ai = use_ai
        self.stats.update(stats or {})
        self.traits = traits or {}
        self.pronoun = pronoun
        self.attackable = attackable
        self.hostile = hostile
        self.idle_actions = idle_actions or {}
        
        # Weather Status (Phase 2)
        from game.systems.weather import WeatherStatusTracker
        self.weather_status = WeatherStatusTracker()
        
        # Weather reactions: {("rain", "heavy"): "message", ...}
        self.weather_reactions = {}
        if weather_reactions:
            for key_str, message in weather_reactions.items():
                parts = key_str.split("_", 1)
                if len(parts) == 2:
                    wtype, intensity = parts
                    self.weather_reactions[(wtype, intensity)] = message
        
        # Populate inventory
        if inventory:
            from game.models.item import Item
            from game.systems.inventory import get_item_def
            
            for item_id in inventory:
                # Create item instance
                item_def = get_item_def(item_id)
                item = Item(item_id, item_def["name"], item_def["description"])
                # Load other properties
                item.weight = item_def.get("weight", 0.1)
                item.detailed_description = item_def.get("detailed_description", "")
                item.is_held = item_def.get("is_held", False)
                
                # Handle container contents if needed (simple for now)
                if item_id == "herbal_satchel":
                    # Hardcode content for now or add 'contents' to item def?
                    # Let's just add dried herbs if it's the satchel
                    from game.systems.inventory_system import InventorySystem
                    item.inventory = InventorySystem(item, max_weight=item_def.get("capacity", 10.0))
                    
                    # Add dried herbs
                    herb_def = get_item_def("dried_herbs")
                    herb = Item("dried_herbs", herb_def["name"], herb_def["description"])
                    herb.weight = herb_def.get("weight", 0.1)
                    item.inventory.add(herb)
                
                self.inventory.add(item)
        
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
    
    def update_weather_status(self, atmos_manager):
        """Update weather status based on current location and atmospheric conditions."""
        if not self.location:
            return
        
        is_outdoor = getattr(self.location, 'outdoor', False)
        weather_state = atmos_manager.weather.get_state()
        day_of_year = atmos_manager.time.get_day_of_year()
        season = atmos_manager.seasons.get_season(day_of_year)
        current_tick = atmos_manager.time.get_current_tick()
        
        self.weather_status.update(current_tick, is_outdoor, weather_state, season)
    
    def get_weather_description(self, pronoun: str = None) -> str:
        """Get weather status description for this NPC."""
        if not pronoun:
            pronoun = self.pronoun
        
        if not self.weather_status.has_status():
            return ""
        
        wetness = self.weather_status.wetness
        cold = self.weather_status.cold
        heat = self.weather_status.heat
        
        # Find dominant condition
        max_condition = max(wetness, cold, heat)
        if max_condition == 0:
            return ""
        
        # Use proper verb conjugation
        if pronoun == "you":
            verb_look = "look"
            verb_be = "are"
            verb_have = "have"
        elif pronoun in ["he", "she", "it"]:
            verb_look = "looks"
            verb_be = "is"
            verb_have = "has"
        else:  # they
            verb_look = "look"
            verb_be = "are"
            verb_have = "have"
        
        # Generate description (same logic as Player/NPC model)
        if wetness == max_condition:
            if wetness <= 2:
                return f"{pronoun.capitalize()} {verb_look} a bit damp."
            elif wetness <= 4:
                return f"You can tell {pronoun} {verb_have} been standing in the rain for a while."
            elif wetness <= 7:
                return f"{pronoun.capitalize()} {verb_look} thoroughly soaked through."
            else:
                return f"{pronoun.capitalize()} {verb_be} absolutely drenched from head to toe."
        elif cold == max_condition:
            if cold <= 2:
                return f"{pronoun.capitalize()} {verb_look} a little chilled."
            elif cold <= 4:
                return f"{pronoun.capitalize()} {verb_be} shivering slightly in the cold."
            elif cold <= 7:
                return f"{pronoun.capitalize()} {verb_look} very cold and uncomfortable."
            else:
                return f"{pronoun.capitalize()} {verb_be} shivering violently, lips tinged blue."
        else:  # heat
            if heat <= 2:
                return f"{pronoun.capitalize()} {verb_look} a touch flushed from the heat."
            elif heat <= 4:
                return f"A sheen of sweat glistens on {pronoun} skin."
            elif heat <= 7:
                return f"{pronoun.capitalize()} {verb_look} overheated and unsteady."
            else:
                return f"{pronoun.capitalize()} {verb_be} drenched in sweat and {verb_look} ready to collapse from the heat."
    
    def get_weather_reaction(self, weather_state: Dict, season: str, time_of_day: str = None) -> Optional[str]:
        """Get NPC's reaction to current weather, if they have one."""
        wtype = weather_state.get("type", "clear")
        intensity = weather_state.get("intensity", "none")
        
        # Try exact match first (allows clear weather reactions even if status is neutral)
        key = (wtype, intensity)
        if key in self.weather_reactions:
            return self.weather_reactions[key]
            
        # Special handling for clear weather with time of day
        if wtype == "clear" and time_of_day:
            # Try ("clear", "day") or ("clear", "night")
            key = ("clear", time_of_day)
            if key in self.weather_reactions:
                return self.weather_reactions[key]
        
        # Only check generic status-based reactions if they are actually affected
        if not self.weather_status.has_status():
            return None
        
        # Fallback logic: Heavy -> Moderate -> Light
        # Also handle storm -> rain fallback
        
        # Define type fallbacks (e.g. storm is just heavy rain usually)
        type_fallbacks = {
            "storm": "rain",
            "drizzle": "rain",
            "blizzard": "snow",
            "flurries": "snow"
        }
        
        # List of types to check: [actual_type, fallback_type]
        types_to_check = [wtype]
        if wtype in type_fallbacks:
            types_to_check.append(type_fallbacks[wtype])
            
        # List of intensities to check in order
        intensities_to_check = [intensity]
        if intensity == "heavy":
            intensities_to_check.extend(["moderate", "light"])
        elif intensity == "moderate":
            intensities_to_check.append("light")
            
        # Check all combinations
        for check_type in types_to_check:
            for check_intensity in intensities_to_check:
                # Skip the exact match we already checked at the top
                if check_type == wtype and check_intensity == intensity:
                    continue
                    
                key = (check_type, check_intensity)
                if key in self.weather_reactions:
                    return self.weather_reactions[key]
            
        return None

    def get_idle_action(self, room_id: str, weather_state: Dict = None) -> Optional[str]:
        """
        Get a random idle action for this NPC based on room and weather.
        """
        import random
        
        # 1. Check for weather-aware idle actions (if outdoor)
        if weather_state and self.idle_actions.get("weather"):
            wtype = weather_state.get("type", "clear")
            intensity = weather_state.get("intensity", "none")
            
            # Try exact match
            key = f"{wtype}_{intensity}"
            actions = self.idle_actions["weather"].get(key)
            
            # Fallback to intensity-independent match if needed
            if not actions:
                for k, v in self.idle_actions["weather"].items():
                    if k.startswith(f"{wtype}_"):
                        actions = v
                        break
            
            if actions and random.random() < 0.6:  # 60% chance to use weather action if available
                return random.choice(actions)
        
        # 2. Check for room-specific actions
        if room_id in self.idle_actions:
            return random.choice(self.idle_actions[room_id])
            
        # 3. Fallback to default actions
        if "default" in self.idle_actions:
            return random.choice(self.idle_actions["default"])
            
        return None


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
        "inventory": ["carved_pipe", "tattered_journal"],
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
        "weather_reactions": {
            "heatwave_moderate": {
                "action": "The Old Storyteller wipes sweat from his brow.",
                "vocal": "These summers grow warmer every year."
            },
            "heatwave_heavy": {
                "action": "The Old Storyteller fans himself with a weathered hand.",
                "vocal": "This heat is unbearable. I remember when summers were gentler."
            },
            "snow_heavy": {
                "action": "The Old Storyteller shivers slightly.",
                "vocal": "Winter's grip tightens. Stay warm, traveler."
            },
            "rain_heavy": {
                "action": "The Old Storyteller pulls his robes closer.",
                "vocal": "The rain tells stories of its own, if you know how to listen."
            },
            "clear_night": {
                "action": "The Old Storyteller looks up at the stars.",
                "vocal": "The ancestors are watching closely tonight."
            },
            "clear_day": {
                "action": "The Old Storyteller smiles at the sunshine.",
                "vocal": "A fine day for a tale, isn't it?"
            },
        },
        "idle_actions": {
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
            "weather": {
                "rain_heavy": [
                    "The Old Storyteller pulls his robes tighter and moves closer to the fountain's shelter.",
                    "The Old Storyteller glances up at the heavy clouds. 'Rain has its own stories to tell,' he murmurs.",
                    "The Old Storyteller shakes water from his beard, looking thoughtful despite the downpour.",
                ],
                "rain_moderate": [
                    "The Old Storyteller adjusts his position to stay drier under the eaves.",
                    "The Old Storyteller watches the rain fall, his expression contemplative.",
                ],
                "snow_heavy": [
                    "The Old Storyteller stamps his feet and wraps his robes tighter. 'Winter's tales are the coldest,' he says to no one in particular.",
                    "The Old Storyteller's breath forms white clouds as he speaks, his hands tucked into his sleeves.",
                ],
                "heatwave_moderate": [
                    "The Old Storyteller wipes his brow and seeks shade near the fountain.",
                    "The Old Storyteller fans himself with a weathered hand. 'These summers grow warmer,' he muses.",
                ],
                "windy_moderate": [
                    "The Old Storyteller's robes flutter in the wind as he adjusts them.",
                    "The Old Storyteller squints against the wind, his eyes watering slightly.",
                ],
            },
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
        "inventory": ["herbal_satchel"],
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
        "weather_reactions": {
            "rain_heavy": {
                "action": "Mara glances toward the rain-streaked windows.",
                "vocal": "Good night for staying inside."
            },
            "snow_moderate": {
                "action": "Mara looks out at the falling snow.",
                "vocal": "At least it'll keep the troublemakers indoors tonight."
            },
            "heatwave_moderate": {
                "action": "Mara wipes her brow.",
                "vocal": "This heat makes the ale taste better, at least."
            },
            "storm_heavy": {
                "action": "Mara flinches at a crack of thunder.",
                "vocal": "Hope the roof holds up..."
            },
            "clear_day": {
                "action": "Mara opens a window to let in the fresh air.",
                "vocal": "Lovely day to air out the tavern."
            }
        },
        "idle_actions": {
            "tavern": [
                "Mara squints at you quizzically, then returns to her work.",
                "Mara straightens the signboard hanging near the entrance.",
                "Mara picks up a cloth and wipes down a bench, humming quietly to herself.",
                "Mara checks the fire in the hearth, adjusting the logs.",
                "Mara arranges tankards on a shelf, making sure everything is in order.",
                "Mara glances around the room, making sure all is well.",
                "Mara wipes her hands on her apron and looks around the tavern.",
            ],
            "default": [
                "Mara looks around, seeming slightly out of place.",
                "Mara adjusts her clothing and looks around.",
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
        "weather_reactions": {
            "heatwave_moderate": {
                "action": "The Blacksmith grunts.",
                "vocal": "Hot enough in the forge without the sun helping."
            },
            "rain_light": {
                "action": "The Blacksmith wipes their brow.",
                "vocal": "Good weather for cooling the steel."
            },
        },
        "idle_actions": {
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
        "weather_reactions": {
            "rain_light": {
                "action": "The Herbalist smiles faintly.",
                "vocal": "The plants are thirsty properly today."
            },
            "fog_moderate": {
                "action": "The Herbalist peers into the mist.",
                "vocal": "Some mushrooms only grow in this weather."
            },
            "clear_day": {
                "action": "The Herbalist hums softly while sorting herbs in the sunlight.",
                "vocal": "A beautiful day for gathering."
            }
        },
        "idle_actions": {
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
        "idle_actions": {
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
        "weather_reactions": {
            "storm_moderate": {
                "action": "The Nervous Farmer jumps at a thunderclap.",
                "vocal": "The spirits are angry tonight!"
            },
            "fog_moderate": {
                "action": "The Nervous Farmer shivers.",
                "vocal": "Nothing good comes out of the fog..."
            },
            "windy_heavy": {
                "action": "The Nervous Farmer looks around wildly.",
                "vocal": "Do you hear voices in the wind?"
            },
        },
        "idle_actions": {
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
        "idle_actions": {
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
    },
    "patrolling_guard": {
        "name": "Patrolling Guard",
        "title": "Patrolling Guard",
        "description": "A watchful figure keeping an eye on the path to the watchtower.",
        "personality": "alert, professional, duty-focused",
        "pronoun": "they",
        "inventory": ["steel_spear", "guard_badge"],
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
        "weather_reactions": {
            "rain_moderate": {
                "action": "The Patrolling Guard pulls their cloak tighter.",
                "vocal": "Just a bit of rain."
            },
            "rain_heavy": {
                "action": "The Patrolling Guard wipes water from their face.",
                "vocal": "This rain is relentless."
            },
            "sleet_moderate": {
                "action": "The Patrolling Guard shivers.",
                "vocal": "Nasty weather, this."
            },
            "snow_heavy": {
                "action": "The Patrolling Guard stamps their feet.",
                "vocal": "Standing watch in this weather is no joke."
            },
            "clear_night": {
                "action": "The Patrolling Guard scans the horizon.",
                "vocal": "Quiet night. I like quiet."
            },
            "clear_day": {
                "action": "The Patrolling Guard nods, appreciating the clear view.",
                "vocal": "Good visibility today."
            },
            "storm_heavy": {
                "action": "The Patrolling Guard braces against the wind.",
                "vocal": "This storm is getting worse."
            }
        },
        "idle_actions": {
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
            "weather": {
                "rain_heavy": [
                    {
                        "action": "The Patrolling Guard wipes water from their face and continues their watch.",
                        "vocal": "Duty regardless of weather."
                    },
                    "The Patrolling Guard's armor glistens with rainwater as they scan the horizon.",
                    {
                        "action": "The Patrolling Guard keeps patrolling.",
                        "vocal": "At least it's not snow."
                    }
                ],
                "snow_heavy": [
                    "The Patrolling Guard's breath is visible as they continue their patrol through the snow.",
                    {
                        "action": "The Patrolling Guard stamps their boots to stay warm.",
                        "vocal": "Can't feel my toes."
                    }
                ],
                "heatwave_moderate": [
                    "The Patrolling Guard wipes sweat from their brow but remains alert.",
                    {
                        "action": "The Patrolling Guard takes a swig from their water flask.",
                        "vocal": "Stay hydrated."
                    }
                ],
                "windy_moderate": [
                    "The Patrolling Guard squints against the wind, hand steady on their weapon.",
                    {
                        "action": "The Patrolling Guard adjusts their stance against the wind.",
                        "vocal": "Wind's picking up."
                    }
                ],
            },
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
        "weather_reactions": {
            "fog_moderate": {
                "action": "Darin squints into the distance.",
                "vocal": "Can't see a thing in this soup."
            },
            "windy_heavy": {
                "action": "Darin holds onto his hat.",
                "vocal": "Wind's picking up. Storm might be brewing."
            },
        },
        "idle_actions": {
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
            "weather": {
                "rain_heavy": [
                    "Darin peers through his spyglass despite the heavy rain, his duty unwavering.",
                    "Darin wipes water from the spyglass lens and continues scanning the horizon.",
                ],
                "windy_moderate": [
                    "Darin adjusts the spyglass against the wind, muttering about visibility.",
                    "Darin checks the wind direction in his logbook, noting the conditions.",
                ],
                "heatwave_moderate": [
                    "Darin shades his eyes from the sun, continuing his watch despite the heat.",
                    "Darin takes a break to wipe sweat from his face, then returns to scanning.",
                ],
            },
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
        },
        "weather_reactions": {
            "rain_light": {
                "action": "The Wandering Trader holds out a hand to catch the drizzle.",
                "vocal": "Good for the roots."
            },
            "clear_day": {
                "action": "The Wandering Trader hums, inspecting a sun-drenched leaf.",
                "vocal": "The plants are happy today."
            },
            "rain_moderate": {
                "action": "The Wandering Trader covers their wares.",
                "vocal": "A little rain never hurt business... much."
            },
        },
        "idle_actions": {
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
            hostile=npc_data.get("hostile", False),  # Default to False
            inventory=npc_data.get("inventory"),  # Optional inventory list
            weather_reactions=npc_data.get("weather_reactions", {}),  # Phase 2
            idle_actions=npc_data.get("idle_actions", {})  # Phase 3: Merged from npc_actions.py
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
        
        # Use WorldManager to get NPC with loaded state (includes weather_status)
        from game.world.manager import WorldManager
        wm = WorldManager.get_instance()
        npc = wm.get_npc(npc_id) or NPCS[npc_id]
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


def get_time_of_day_greeting():
    """
    Get appropriate greeting based on time of day.
    
    Returns:
        str: Greeting phrase like "good morning", "good afternoon", etc.
    """
    from game_engine import get_current_hour_in_minutes, MINUTES_PER_HOUR
    
    current_minutes = get_current_hour_in_minutes()
    hour_of_day = int(current_minutes // MINUTES_PER_HOUR) % 24
    
    if hour_of_day >= 5 and hour_of_day < 12:
        return "good morning"
    elif hour_of_day >= 12 and hour_of_day < 17:
        return "good afternoon"
    elif hour_of_day >= 17 and hour_of_day < 21:
        return "good evening"
    else:
        return "good night"


def detect_greeting(message: str) -> Tuple[Optional[str], bool]:
    """
    Detect if a message contains a greeting and return appropriate response type.
    
    Args:
        message: Player's message text
    
    Returns:
        tuple: (greeting_type: str or None, is_time_based: bool)
        greeting_type can be: "hello", "good_morning", "good_afternoon", "good_evening", "good_night", "greeting"
    """
    message_lower = message.lower().strip()
    
    # Check for time-based greetings first
    if "good morning" in message_lower or "morning" in message_lower and ("good" in message_lower or message_lower.startswith("morning")):
        return "good_morning", True
    elif "good afternoon" in message_lower or ("afternoon" in message_lower and "good" in message_lower):
        return "good_afternoon", True
    elif "good evening" in message_lower or ("evening" in message_lower and "good" in message_lower):
        return "good_evening", True
    elif "good night" in message_lower or "night" in message_lower and ("good" in message_lower or message_lower.startswith("night")):
        return "good_night", True
    
    # Check for general greetings
    greetings = ["hello", "hi", "hey", "greetings", "salutations", "howdy", "ahoy"]
    for greeting in greetings:
        if greeting in message_lower:
            return "greeting", False
    
    return None, False


def get_universal_npc_greeting_response(npc_id: str, greeting_type: str, game: Dict, username: str = None) -> Optional[str]:
    """
    Generate a universal greeting response for any NPC based on reputation and greeting type.
    Works for both AI-enhanced and regular NPCs.
    
    Args:
        npc_id: NPC ID
        greeting_type: Type of greeting ("greeting", "good_morning", "good_afternoon", "good_evening", "good_night")
        game: Game state dictionary
        username: Player username
    
    Returns:
        str or None: NPC greeting response, or None if no response
    """
    if npc_id not in NPCS:
        return None
    
    npc = NPCS[npc_id]
    npc_name = npc.name
    
    # Get reputation
    reputation = game.get("reputation", {}).get(npc_id, 0)
    
    # Determine reputation level
    if reputation >= 20:
        rep_level = "beloved"
    elif reputation >= 10:
        rep_level = "friendly"
    elif reputation >= 0:
        rep_level = "neutral"
    elif reputation >= -10:
        rep_level = "unfriendly"
    else:
        rep_level = "hostile"
    
    # Get personality traits
    personality = npc.personality.lower()
    is_gruff = "gruff" in personality or "grumpy" in personality
    is_kind = "kind" in personality or "warm" in personality or "friendly" in personality
    is_formal = "formal" in personality or "stuffy" in personality
    
    # Generate greeting response based on type and reputation
    responses = []
    
    # Add emote based on reputation and personality
    if rep_level == "beloved":
        if is_kind:
            responses.append(f"{npc_name} beams at you warmly, eyes lighting up.")
        elif is_gruff:
            responses.append(f"{npc_name} gives you a rare, genuine smile, {npc.pronoun if hasattr(npc, 'pronoun') else 'their'} gruff demeanor softening.")
        else:
            responses.append(f"{npc_name} smiles broadly, clearly happy to see you.")
    elif rep_level == "friendly":
        if is_kind:
            responses.append(f"{npc_name} smiles warmly and waves.")
        elif is_gruff:
            responses.append(f"{npc_name} gives you a gruff nod, but {npc.pronoun if hasattr(npc, 'pronoun') else 'their'} eyes show genuine warmth.")
        else:
            responses.append(f"{npc_name} nods and smiles.")
    elif rep_level == "neutral":
        if is_kind:
            responses.append(f"{npc_name} gives you a polite smile.")
        elif is_gruff:
            responses.append(f"{npc_name} looks at you briefly and gives a curt nod.")
        elif is_formal:
            responses.append(f"{npc_name} inclines {npc.pronoun if hasattr(npc, 'pronoun') else 'their'} head in a formal greeting.")
        else:
            responses.append(f"{npc_name} acknowledges you with a nod.")
    elif rep_level == "unfriendly":
        if is_gruff:
            responses.append(f"{npc_name} gives you a sidelong glance, {npc.pronoun if hasattr(npc, 'pronoun') else 'their'} expression wary.")
        else:
            responses.append(f"{npc_name} looks at you cautiously, not quite trusting.")
    else:  # hostile
        if is_gruff:
            responses.append(f"{npc_name} glares at you, {npc.pronoun if hasattr(npc, 'pronoun') else 'their'} expression darkening.")
        else:
            responses.append(f"{npc_name} eyes you warily, clearly not pleased to see you.")
    
    # Add verbal response
    if greeting_type == "good_morning":
        if rep_level == "beloved":
            friend_or_name = username if username else "friend"
            responses.append(f"'Good morning, {friend_or_name}! A fine day to you!'")
        elif rep_level == "friendly":
            name_or_there = username if username else "there"
            responses.append(f"'Good morning, {name_or_there}.'")
        elif rep_level == "neutral":
            responses.append(f"'Morning.'")
        elif rep_level == "unfriendly":
            responses.append(f"'Morning...'")
        else:
            responses.append(f"'What do you want?'")
    elif greeting_type == "good_afternoon":
        if rep_level == "beloved":
            friend_or_name = username if username else "friend"
            responses.append(f"'Good afternoon, {friend_or_name}! How goes your day?'")
        elif rep_level == "friendly":
            name_or_there = username if username else "there"
            responses.append(f"'Good afternoon, {name_or_there}.'")
        elif rep_level == "neutral":
            responses.append(f"'Afternoon.'")
        elif rep_level == "unfriendly":
            responses.append(f"'Afternoon...'")
        else:
            responses.append(f"'What do you want?'")
    elif greeting_type == "good_evening":
        if rep_level == "beloved":
            friend_or_name = username if username else "friend"
            responses.append(f"'Good evening, {friend_or_name}! A pleasant night to you.'")
        elif rep_level == "friendly":
            name_or_there = username if username else "there"
            responses.append(f"'Good evening, {name_or_there}.'")
        elif rep_level == "neutral":
            responses.append(f"'Evening.'")
        elif rep_level == "unfriendly":
            responses.append(f"'Evening...'")
        else:
            responses.append(f"'What do you want?'")
    elif greeting_type == "good_night":
        if rep_level == "beloved":
            friend_or_name = username if username else "friend"
            responses.append(f"'Good night, {friend_or_name}! Sleep well.'")
        elif rep_level == "friendly":
            name_or_there = username if username else "there"
            responses.append(f"'Good night, {name_or_there}.'")
        elif rep_level == "neutral":
            responses.append(f"'Night.'")
        elif rep_level == "unfriendly":
            responses.append(f"'Night...'")
        else:
            responses.append(f"'What do you want?'")
    else:  # general greeting
        if rep_level == "beloved":
            if is_kind:
                friend_or_name = username if username else "my friend"
                responses.append(f"'Hello, {friend_or_name}! How wonderful to see you again!'")
            elif is_gruff:
                look_who = username if username else "look who it is"
                responses.append(f"'Well, well, {look_who}. Good to see you, friend.'")
            else:
                friend_or_name = username if username else "friend"
                responses.append(f"'Hello there, {friend_or_name}! What can I do for you?'")
        elif rep_level == "friendly":
            if is_kind:
                name_or_there = username if username else "there"
                responses.append(f"'Hello, {name_or_there}! How can I help you today?'")
            elif is_gruff:
                name_or_you = username if username else "you"
                responses.append(f"'Hello, {name_or_you}. What do you need?'")
            else:
                name_or_there = username if username else "there"
                responses.append(f"'Hello, {name_or_there}.'")
        elif rep_level == "neutral":
            if is_kind:
                name_or_there = username if username else "there"
                responses.append(f"'Hello, {name_or_there}. How can I help you?'")
            elif is_gruff:
                responses.append(f"'Yeah, what do you want?'")
            elif is_formal:
                name_or_traveler = username if username else "traveler"
                responses.append(f"'Greetings, {name_or_traveler}. How may I assist you?'")
            else:
                responses.append(f"'Hello.'")
        elif rep_level == "unfriendly":
            if is_gruff:
                responses.append(f"'What do you want?'")
            else:
                responses.append(f"'Hello...'")
        else:  # hostile
            if is_gruff:
                responses.append(f"'What do you want? I don't have time for you.'")
            else:
                responses.append(f"'Can I help you with something?'")
    
    return "[CYAN]" + " ".join(responses) + "[/CYAN]"


def get_universal_npc_emote_reaction(npc_id: str, emote_verb: str, game: Dict, username: str = None) -> Optional[str]:
    """
    Generate a universal emote reaction for any NPC based on reputation and emote type.
    Works for both AI-enhanced and regular NPCs.
    
    Args:
        npc_id: NPC ID
        emote_verb: Emote verb (e.g., "wave", "nod", "smile")
        game: Game state dictionary
        username: Player username
    
    Returns:
        str or None: NPC emote reaction, or None if no reaction
    """
    if npc_id not in NPCS:
        return None
    
    npc = NPCS[npc_id]
    npc_name = npc.name
    
    # Get reputation
    reputation = game.get("reputation", {}).get(npc_id, 0)
    
    # Determine reputation level
    if reputation >= 20:
        rep_level = "beloved"
    elif reputation >= 10:
        rep_level = "friendly"
    elif reputation >= 0:
        rep_level = "neutral"
    elif reputation >= -10:
        rep_level = "unfriendly"
    else:
        rep_level = "hostile"
    
    # Get personality traits
    personality = npc.personality.lower()
    is_gruff = "gruff" in personality or "grumpy" in personality
    is_kind = "kind" in personality or "warm" in personality
    
    # Generate reaction based on emote and reputation
    if emote_verb == "wave":
        if rep_level == "beloved":
            friend_or_name = username if username else "friend"
            pronoun = npc.pronoun if hasattr(npc, 'pronoun') else 'their'
            if is_kind:
                return f"[CYAN]{npc_name} waves back enthusiastically, a wide smile on {pronoun} face. 'Hello, {friend_or_name}!'[/CYAN]"
            else:
                return f"[CYAN]{npc_name} waves back warmly. 'Good to see you, {friend_or_name}!'[/CYAN]"
        elif rep_level == "friendly":
            return f"[CYAN]{npc_name} waves back with a smile.[/CYAN]"
        elif rep_level == "neutral":
            return f"[CYAN]{npc_name} gives you a brief wave in return.[/CYAN]"
        elif rep_level == "unfriendly":
            return f"[CYAN]{npc_name} gives you a half-hearted wave, looking slightly uncomfortable.[/CYAN]"
        else:
            return f"[CYAN]{npc_name} ignores your wave, looking away.[/CYAN]"
    
    elif emote_verb == "nod":
        if rep_level == "beloved":
            return f"[CYAN]{npc_name} nods back warmly, {npc.pronoun if hasattr(npc, 'pronoun') else 'their'} eyes showing genuine respect.[/CYAN]"
        elif rep_level == "friendly":
            return f"[CYAN]{npc_name} nods back with a smile.[/CYAN]"
        elif rep_level == "neutral":
            if is_gruff:
                return f"[CYAN]{npc_name} gives you a gruff nod in return.[/CYAN]"
            else:
                return f"[CYAN]{npc_name} nods back politely.[/CYAN]"
        elif rep_level == "unfriendly":
            return f"[CYAN]{npc_name} gives you a curt, reluctant nod.[/CYAN]"
        else:
            return f"[CYAN]{npc_name} barely acknowledges your nod, {npc.pronoun if hasattr(npc, 'pronoun') else 'their'} expression remaining cold.[/CYAN]"
    
    elif emote_verb == "smile":
        if rep_level == "beloved":
            friend_or_name = username if username else "friend"
            pronoun = npc.pronoun if hasattr(npc, 'pronoun') else 'their'
            return f"[CYAN]{npc_name} smiles back warmly, {pronoun} whole face lighting up. 'Always good to see you, {friend_or_name}!'[/CYAN]"
        elif rep_level == "friendly":
            return f"[CYAN]{npc_name} smiles back cheerfully.[/CYAN]"
        elif rep_level == "neutral":
            return f"[CYAN]{npc_name} returns your smile with a polite one of {npc.pronoun if hasattr(npc, 'pronoun') else 'their'} own.[/CYAN]"
        elif rep_level == "unfriendly":
            return f"[CYAN]{npc_name} gives you a strained smile, clearly forcing it.[/CYAN]"
        else:
            return f"[CYAN]{npc_name} doesn't return your smile, {npc.pronoun if hasattr(npc, 'pronoun') else 'their'} expression remaining neutral.[/CYAN]"
    
    elif emote_verb == "bow":
        if rep_level == "beloved":
            return f"[CYAN]{npc_name} returns your bow with a deep, respectful one, showing great respect for you.[/CYAN]"
        elif rep_level == "friendly":
            return f"[CYAN]{npc_name} bows back gracefully.[/CYAN]"
        elif rep_level == "neutral":
            return f"[CYAN]{npc_name} gives you a polite bow in return.[/CYAN]"
        elif rep_level == "unfriendly":
            return f"[CYAN]{npc_name} gives you a perfunctory, shallow bow.[/CYAN]"
        else:
            return f"[CYAN]{npc_name} barely acknowledges your bow, giving you only the slightest nod.[/CYAN]"
    
    else:
        # Generic reaction for other emotes
        if rep_level == "beloved":
            return f"[CYAN]{npc_name} responds in kind, clearly pleased to interact with you.[/CYAN]"
        elif rep_level == "friendly":
            return f"[CYAN]{npc_name} responds positively to your gesture.[/CYAN]"
        elif rep_level == "neutral":
            return f"[CYAN]{npc_name} acknowledges your gesture.[/CYAN]"
        elif rep_level == "unfriendly":
            return f"[CYAN]{npc_name} gives a minimal response to your gesture.[/CYAN]"
        else:
            return f"[CYAN]{npc_name} barely reacts to your gesture.[/CYAN]"

