from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from game.models.entity import Entity
from game.systems.inventory_system import InventorySystem
from game.systems.weather import WeatherStatusTracker

if TYPE_CHECKING:
    from game.models.room import Room
    from game.models.npc import NPC

class Player(Entity):
    def __init__(self, username: str):
        """Initialize player with a username and default attributes."""
        super().__init__(oid=username, name=username)
        self.username: str = username
        self.race: str = "human"
        self.gender: str = "unknown"
        self.backstory: str = ""
        self.user_description: str = ""
        
        # Inventory System
        self.inventory = InventorySystem(self, max_weight=20.0, max_items=50)
        # Legacy attribute for backward compatibility if needed, but InventorySystem handles it
        self.max_carry_weight: float = 20.0
        
        # Weather Status Tracking
        self.weather_status = WeatherStatusTracker()
        
        # Game State Trackers
        self.quests: Dict[str, Any] = {}
        self.completed_quests: Dict[str, Any] = {}
        
        from game.systems.reputation import ReputationSystem
        self.reputation = ReputationSystem()
        
        self.npc_memory: Dict[str, List[Dict]] = {}
        
        # RPG Stats
        self.level: int = 1
        self.xp: int = 0
        self.xp_to_next: int = 100
        
        self.max_hp: int = 20
        self.hp: int = 20
        self.max_stamina: int = 20
        self.stamina: int = 20
        
        # Attributes
        self.strength: int = 10
        self.dexterity: int = 10
        self.intelligence: int = 10
        self.defense: int = 0
        
        # Settings
        self.color_settings: Dict[str, str] = {
            "say": "cyan",
            "emote": "white",
            "tell": "yellow",
            "exits": "darkgreen",
            "weather": "darkyellow",
            "room_descriptions": "white",
            "command": "blue",
            "error": "red",
            "success": "green",
            "npc": "orange",
            "system": "gray",
            "wallet": "lightgreen",
            "combat": "red",
            "status": "cyan"
        }

    def load_from_state(self, state: Dict[str, Any]) -> None:
        """Load player state from the legacy dictionary format."""
        # The definitions for 'location' and its attributes must be added.
        location_oid = state.get("location", "town_square")
        
        from game.world.manager import WorldManager
        self.location: Optional[Room] = WorldManager.get_instance().get_room(location_oid)
        
        char_data = state.get("character", {})
        self.race = char_data.get("race", "human")
        self.gender = char_data.get("gender", "unknown")
        self.backstory = char_data.get("backstory", "")
        self.user_description = state.get("user_description", "")
        
        if "stats" in char_data:
            self.stats.update(char_data["stats"])
        
        inventory_ids = state.get("inventory", [])
        # Clear existing inventory
        self.inventory.contents = []
        
        wm = WorldManager.get_instance()
        for item_id in inventory_ids:
            item = wm.get_item(item_id)
            if item:
                self.inventory.add(item)
        
        self.max_carry_weight = state.get("max_carry_weight", 20.0)
        self.inventory.max_weight = self.max_carry_weight
        
        # Load Reputation
        rep_data = state.get("reputation", {})
        self.reputation.initialize(rep_data)
        
        self.npc_memory = state.get("npc_memory", {})
        
        from game.systems.quest_manager import QuestManager
        from game.models.quest import Quest
        
        qm = QuestManager.get_instance()
        self.quests = {}
        for q_id, q_data in state.get("quests", {}).items():
            template = qm.get_template(q_id)
            if template:
                self.quests[q_id] = Quest.from_dict(q_data, template)
            else:
                pass
                
        self.completed_quests = state.get("completed_quests", {})
        if "color_settings" in state:
            self.color_settings.update(state["color_settings"])
        
        # Load RPG stats
        self.level = state.get("level", 1)
        self.xp = state.get("xp", 0)
        self.xp_to_next = state.get("xp_to_next", 100)
        self.hp = state.get("hp", 20)
        self.max_hp = state.get("max_hp", 20)
        self.stamina = state.get("stamina", 20)
        self.max_stamina = state.get("max_stamina", 20)
        self.strength = state.get("strength", 10)
        self.dexterity = state.get("dexterity", 10)
        self.intelligence = state.get("intelligence", 10)
        self.defense = state.get("defense", 0)
        
        # Load weather status
        if "weather_status" in state:
            self.weather_status.from_dict(state["weather_status"])

    def to_state(self) -> Dict[str, Any]:
        """Serialize player state for persistence."""
        return {
            "username": self.username,
            "race": self.race,
            "gender": self.gender,
            "backstory": self.backstory,
            "user_description": self.user_description,
            "location": self.location.oid if self.location else None,
            "max_carry_weight": self.max_carry_weight,
            "inventory": [item.oid if hasattr(item, 'oid') else str(item) for item in self.inventory.contents],
            "quests": {q_id: quest.to_dict() for q_id, quest in self.quests.items()},
            "completed_quests": self.completed_quests,
            "reputation": self.reputation.to_dict(),
            "npc_memory": self.npc_memory,
            "color_settings": self.color_settings,
            # RPG Stats
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "stamina": self.stamina,
            "max_stamina": self.max_stamina,
            "strength": self.strength,
            "dexterity": self.dexterity,
            "intelligence": self.intelligence,
            "defense": self.defense,
            # Weather Status
            "weather_status": self.weather_status.to_dict(),
            # Character Data
            "character": {
                "race": self.race,
                "gender": self.gender,
                "backstory": self.backstory,
                "stats": {
                    "strength": self.strength,
                    "dexterity": self.dexterity,
                    "intelligence": self.intelligence,
                    "defense": self.defense,
                }
            }
        }

    def __repr__(self):
        return f"<Player {self.username} Lvl:{self.level} HP:{self.hp}/{self.max_hp}>"

    def take_damage(self, amount: int) -> Tuple[int, bool]:
        """Apply damage to player. Returns (actual_damage_taken, is_dead)."""
        actual_damage = max(0, amount - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage, self.hp == 0

    def heal(self, amount: int) -> int:
        """Heal the player. Returns actual amount healed."""
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def use_stamina(self, amount: int) -> bool:
        """Try to use stamina. Returns True if successful, False if not enough."""
        if self.stamina >= amount:
            self.stamina -= amount
            return True
        return False

    def recover_stamina(self, amount: int) -> None:
        """Recover stamina."""
        self.stamina = min(self.max_stamina, self.stamina + amount)

    def gain_xp(self, amount: int) -> bool:
        """Gain XP and check for level up. Returns True if leveled up."""
        self.xp += amount
        if self.xp >= self.xp_to_next:
            self.level_up()
            return True
        return False

    def level_up(self) -> None:
        """Handle level up logic."""
        self.level += 1
        self.xp -= self.xp_to_next
        self.xp_to_next = int(self.xp_to_next * 1.5)
        self.max_hp += 5
        self.hp = self.max_hp
        self.max_stamina += 5
        self.stamina = self.max_stamina
        self.strength += 1
        self.dexterity += 1

    def move(self, direction: str, broadcast_fn=None, game_state_for_quests=None) -> Tuple[bool, str]:
        """Execute a move command. Returns (success, message)."""
        from game_engine import OPPOSITE_DIRECTION, get_movement_message
        
        if not self.location:
            return False, "You are floating in a void."

        target_oid = self.location.get_exit(direction)
        if not target_oid:
            return False, "You can't go that way."

        from game.world.manager import WorldManager
        wm = WorldManager.get_instance()
        target_room = wm.get_room(target_oid)
        
        if not target_room:
            return False, "That way is blocked by a void."

        old_room_oid = self.location.oid
        
        if broadcast_fn:
            # Use Room object to get message
            leave_msg = self.location.get_exit_message(self.name, direction, is_npc=False)
            broadcast_fn(old_room_oid, leave_msg)

        self.move_to(target_room)
        
        if broadcast_fn:
            opposite = OPPOSITE_DIRECTION.get(direction, "somewhere")
            # Use Room object to get message
            arrive_msg = target_room.get_entrance_message(self.name, opposite, is_npc=False)
            broadcast_fn(target_oid, arrive_msg)

        if game_state_for_quests:
            import quests
            event = quests.QuestEvent(
                type="enter_room",
                room_id=target_oid,
                username=self.username
            )
            quests.handle_quest_event(game_state_for_quests, event)

        movement_msg = get_movement_message(target_oid, direction)
        return True, f"{movement_msg}\n{target_room.look(self)}"

    def take_item(self, item_id: str, from_room: 'Room', game_state_for_quests=None) -> Tuple[bool, str]:
        """Take an item from a room. Returns (success, message)."""
        from game_engine import QUEST_SPECIFIC_ITEMS, get_item_def, calculate_inventory_weight
        
        item_obj = next((i for i in from_room.items if hasattr(i, 'oid') and i.oid == item_id), None)
        
        if not item_obj:
            if item_id in QUEST_SPECIFIC_ITEMS:
                quest_data = QUEST_SPECIFIC_ITEMS[item_id]
                if quest_data.get("room_id") == from_room.oid and quest_data.get("owner_username") == self.username:
                    wm = WorldManager.get_instance()
                    item_obj = wm.get_item(item_id)
        
        if not item_obj:
            return False, "You don't see that here."
        
        if not self.inventory.can_add(item_obj):
            return False, "You can't carry that much weight/items."
        
        can_take, reason = item_obj.can_be_taken(self)
        if not can_take:
            return False, reason

        if item_id in QUEST_SPECIFIC_ITEMS:
            del QUEST_SPECIFIC_ITEMS[item_id]
        elif item_obj in from_room.items:
            from_room.items.remove(item_obj)
        
        self.inventory.add(item_obj)
        item_obj.on_take(self)
        
        if game_state_for_quests:
            import quests
            event = quests.QuestEvent(
                type="take_item",
                room_id=from_room.oid,
                item_id=item_id,
                username=self.username
            )
            quests.handle_quest_event(game_state_for_quests, event)
        
        from game_engine import render_item_name
        display_name = render_item_name(item_id)
        return True, f"You pick up the {display_name}."

    def drop_item(self, item_id: str, to_room: 'Room') -> Tuple[bool, str]:
        """Drop an item into a room. Returns (success, message)."""
        from game_engine import render_item_name
        
        item_obj = next((i for i in self.inventory.contents if hasattr(i, 'oid') and i.oid == item_id), None)
        
        if not item_obj:
            return False, "You don't have that item."
        
        can_drop, reason = item_obj.can_be_dropped(self)
        if not can_drop:
            return False, reason
        
        self.inventory.remove(item_obj)
        to_room.items.append(item_obj)
        item_obj.on_drop(self)
        
        display_name = item_obj.get_display_name()
        return True, f"You drop the {display_name}."

    def talk_to(self, npc: 'NPC', game_state: Dict[str, Any], db_conn=None) -> str:
        """Initiate conversation with an NPC. Returns the NPC's response."""
        if not self.location or npc.oid not in self.location.npcs:
            return f"You don't see {npc.name} here."
        
        response = npc.respond_to(self, game_state, db_conn)
        
        import quests
        event = quests.QuestEvent(
            type="talk_to_npc",
            room_id=self.location.oid,
            npc_id=npc.oid,
            username=self.username
        )
        quests.handle_quest_event(game_state, event)
        
        return response
    
    def attack(self, target: 'Entity', game_state: Dict[str, Any]) -> str:
        """Attack a target. Returns the result message."""
        if not self.location or (target.oid not in self.location.npcs and target.oid != self.username):
            return f"You don't see {target.name} here."
        return target.on_attacked(self, game_state)
    
    def give_item(self, item_id: str, target: 'Entity', game_state: Dict[str, Any]) -> Tuple[bool, str]:
        """Give an item to a target (NPC or Player). Returns (success, message)."""
        from game_engine import render_item_name
        
        item_obj = next((i for i in self.inventory.contents if hasattr(i, 'oid') and i.oid == item_id), None)
        
        if not item_obj:
            return False, "You don't have that item."
        
        if not self.location or (target.oid not in self.location.npcs and target.oid != self.username):
            pass
        
        self.inventory.remove(item_obj)
        if hasattr(target, 'receive_item'):
            response = target.receive_item(self, item_obj, game_state)
            return True, response
        
        if hasattr(target, 'inventory'):
            # Check if target inventory is a list or InventorySystem
            if isinstance(target.inventory, list):
                target.inventory.append(item_obj)
            elif hasattr(target.inventory, 'add'):
                target.inventory.add(item_obj)
                
            item_name = item_obj.get_display_name()
            return True, f"You give the {item_name} to {target.name}."
        
        self.inventory.add(item_obj) 
        return False, f"You can't give things to {target.name}."

    def get_burden_status(self) -> str:
        """Get a description of the player's burden based on inventory weight."""
        current_weight = self.inventory.current_weight
        max_weight = self.inventory.max_weight
        
        if max_weight <= 0:
            return ""
            
        ratio = current_weight / max_weight
        
        if ratio > 0.9:
            return "He looks terribly overburdened!"
        elif ratio > 0.75:
            return "He looks like he's straining under the weight of his load."
        elif ratio > 0.5:
            return "He looks like he's carrying a heavy load."
        
        return ""
    
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
    
    def get_weather_description(self, pronoun: str = "they") -> str:
        """
        Get weather status description for this player.
        
        Args:
            pronoun: Pronoun to use ("you", "he", "she", "they")
        
        Returns:
            str: Weather description or empty string
        """
        if not self.weather_status.has_status():
            return ""
        
        wetness = self.weather_status.wetness
        cold = self.weather_status.cold
        heat = self.weather_status.heat
        
        # Find dominant condition
        max_condition = max(wetness, cold, heat)
        if max_condition == 0:
            return ""
        
        # Use proper verb conjugation based on pronoun
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
        
        # Generate description for dominant condition
        if wetness == max_condition:
            if wetness <= 2:
                if pronoun == "you":
                    return "You look a bit damp."
                return f"{pronoun.capitalize()} {verb_look} a bit damp."
            elif wetness <= 4:
                if pronoun == "you":
                    return "You can tell you have been standing in the rain for a while."
                return f"You can tell {pronoun} {verb_have} been standing in the rain for a while."
            elif wetness <= 7:
                if pronoun == "you":
                    return "You look thoroughly soaked through."
                return f"{pronoun.capitalize()} {verb_look} thoroughly soaked through."
            else:
                if pronoun == "you":
                    return "You are absolutely drenched from head to toe."
                return f"{pronoun.capitalize()} {verb_be} absolutely drenched from head to toe."
        elif cold == max_condition:
            if cold <= 2:
                if pronoun == "you":
                    return "You look a little chilled."
                return f"{pronoun.capitalize()} {verb_look} a little chilled."
            elif cold <= 4:
                if pronoun == "you":
                    return "You are shivering slightly in the cold."
                return f"{pronoun.capitalize()} {verb_be} shivering slightly in the cold."
            elif cold <= 7:
                if pronoun == "you":
                    return "You look very cold and uncomfortable."
                return f"{pronoun.capitalize()} {verb_look} very cold and uncomfortable."
            else:
                if pronoun == "you":
                    return "You are shivering violently, lips tinged blue."
                return f"{pronoun.capitalize()} {verb_be} shivering violently, lips tinged blue."
        else:  # heat
            if heat <= 2:
                if pronoun == "you":
                    return "You look a touch flushed from the heat."
                return f"{pronoun.capitalize()} {verb_look} a touch flushed from the heat."
            elif heat <= 4:
                if pronoun == "you":
                    return "A sheen of sweat glistens on your skin."
                return f"A sheen of sweat glistens on {pronoun} skin."
            elif heat <= 7:
                if pronoun == "you":
                    return "You look overheated and unsteady."
                return f"{pronoun.capitalize()} {verb_look} overheated and unsteady."
            else:
                if pronoun == "you":
                    return "You are drenched in sweat and look ready to collapse from the heat."
                return f"{pronoun.capitalize()} {verb_be} drenched in sweat and {verb_look} ready to collapse from the heat."

    def look_at(self, target_name: str) -> str:
        """Look at a specific target (item, npc, self, etc)."""
        target_name = target_name.lower()
        
        if target_name in ["me", "self", self.username.lower()]:
            # Self look
            desc = f"You look at yourself. You are {self.name}, a {self.race}."
            if self.user_description:
                desc += f"\nYou are {self.user_description}"
            
            # Add weather status (NEW - Phase 1)
            # Update weather status before displaying (ensures it's current)
            if self.location and hasattr(self, 'update_weather_status'):
                from game.systems.atmospheric_manager import get_atmospheric_manager
                atmos = get_atmospheric_manager()
                
                # Force first update if last_update_tick is 0
                if self.weather_status.last_update_tick == 0:
                    self.weather_status.last_update_tick = -1
                
                self.update_weather_status(atmos)
            
            weather_desc = self.get_weather_description(pronoun="you")
            if weather_desc:
                desc += f"\n{weather_desc}"
            
            # Add burden status (self)
            burden = self.get_burden_status()
            if burden:
                # Adjust pronouns for self
                burden = burden.replace("He looks", "You feel").replace("his load", "your load")
                desc += f"\n{burden}"
                
            # Add inventory visibility (self)
            if self.inventory.contents:
                held_items = [i for i in self.inventory.contents if getattr(i, 'is_held', False)]
                carried_items = [i for i in self.inventory.contents if not getattr(i, 'is_held', False)]
                
                from game.utils.text import format_item_list
                
                if held_items:
                    held_str = format_item_list(held_items)
                    held_str = held_str[0].upper() + held_str[1:] if held_str else ""
                    desc += f"\nYou are holding: {held_str}."
                    
                if carried_items:
                    carried_str = format_item_list(carried_items)
                    carried_str = carried_str[0].upper() + carried_str[1:] if carried_str else ""
                    desc += f"\nYou are carrying: {carried_str}."
                
            return desc
            
        for item in self.inventory.contents:
            if target_name == item.name.lower() or target_name in [adj.lower() for adj in item.adjectives] or target_name in item.name.lower().split():
                desc = item.description
                if hasattr(item, "detailed_description") and item.detailed_description:
                    desc += f"\n\n{item.detailed_description}"
                if hasattr(item, "history") and item.history:
                    desc += f"\n\nHistory: {item.history}"
                return f"You see {item.get_display_name()}.\n{desc}"
                
        if not self.location:
            return "You see nothing."
            
        # TODO: Check for other players in the room
        # Deferred to Phase 2 - needs proper user lookup system
        # from app import get_users_in_room
        # if hasattr(self.location, 'oid'):
        #     room_players = get_users_in_room(self.location.oid)
        #     for other_username in room_players:
        #         if other_username.lower() != self.username.lower() and target_name == other_username.lower():
        #             # Found another player!
        #             # Load their game state to get description
        #             from app import get_game_state
        #             other_state = get_game_state(other_username)
        #             
        #             if other_state:
        #                 char_data = other_state.get("character", {})
        #                 race = char_data.get("race", "unknown")
        #                 gender = char_data.get("gender", "nonbinary")
        #                 user_desc = other_state.get("user_description", "")
        #                 
        #                 # Determine pronoun based on gender
        #                 if gender == "male":
        #                     pronoun = "He"
        #                     is_verb = "is"
        #                     lower_pronoun = "he"
        #                 elif gender == "female":
        #                     pronoun = "She"
        #                     is_verb = "is"
        #                     lower_pronoun = "she"
        #                 else:  # nonbinary or unknown
        #                     pronoun = "They"
        #                     is_verb = "are"
        #                     lower_pronoun = "they"
        #                 
        #                 desc = f"You see {other_username}, a {race}."
        #                 if user_desc:
        #                     desc += f"\n{pronoun} {is_verb} {user_desc}"
        #                 
        #                 # Add weather status (NEW)
        #                 # Create temp Player object to check weather status
        #                 from game.models.player import Player as OtherPlayer
        #                 other_player = OtherPlayer(other_username)
        #                 other_player.load_from_state(other_state)
        #                 weather_desc = other_player.get_weather_description(pronoun=lower_pronoun)
        #                 if weather_desc and getattr(self.location, 'outdoor', False):
        #                     desc += f"\n{weather_desc}"
        #                 
        #                 return desc
            
        for item in self.location.items:
            if target_name == item.name.lower() or target_name in [adj.lower() for adj in item.adjectives] or target_name in item.name.lower().split():
                desc = item.description
                if hasattr(item, "detailed_description") and item.detailed_description:
                    desc += f"\n\n{item.detailed_description}"
                if hasattr(item, "history") and item.history:
                    desc += f"\n\nHistory: {item.history}"
                return f"You see {item.get_display_name()}.\n{desc}"
                
        from game.world.manager import WorldManager
        wm = WorldManager.get_instance()
        for npc_id in self.location.npcs:
            npc = wm.get_npc(npc_id)
            if npc and (target_name == npc.name.lower() or target_name in npc.name.lower().split()):
                desc = f"You see {npc.name}."
                if npc.description:
                    desc += f"\n{npc.description}"
                
                # Add weather status if available (Phase 2)
                # Ensure NPC has location set and weather status updated
                if not npc.location:
                    npc.location = self.location
                
                if npc.location and hasattr(npc, 'update_weather_status'):
                    from game.systems.atmospheric_manager import get_atmospheric_manager
                    atmos = get_atmospheric_manager()
                    
                    # Force first update if last_update_tick is 0
                    if npc.weather_status.last_update_tick == 0:
                        npc.weather_status.last_update_tick = -1
                    
                    npc.update_weather_status(atmos)
                    
                    # Sync back to NPC_STATE
                    from game_engine import NPC_STATE
                    if npc_id in NPC_STATE:
                        if "weather_status" not in NPC_STATE[npc_id]:
                            NPC_STATE[npc_id]["weather_status"] = {}
                        NPC_STATE[npc_id]["weather_status"] = npc.weather_status.to_dict()
                
                weather_desc = npc.get_weather_description(pronoun=npc.pronoun)
                if weather_desc:
                    desc += f"\n{weather_desc}"
                
                # Add inventory visibility
                if hasattr(npc, 'inventory') and npc.inventory.contents:
                    held_items = [i for i in npc.inventory.contents if getattr(i, 'is_held', False)]
                    carried_items = [i for i in npc.inventory.contents if not getattr(i, 'is_held', False)]
                    
                    from game.utils.text import format_item_list
                    
                    # Get correct pronoun (capitalize for sentence start)
                    pronoun = getattr(npc, 'pronoun', 'they')
                    pronoun_cap = pronoun.capitalize()
                    
                    if held_items:
                        held_str = format_item_list(held_items)
                        # Capitalize first letter
                        held_str = held_str[0].upper() + held_str[1:] if held_str else ""
                        desc += f"\n{pronoun_cap} is holding: {held_str}."
                        
                    if carried_items:
                        carried_str = format_item_list(carried_items)
                        carried_str = carried_str[0].upper() + carried_str[1:] if carried_str else ""
                        desc += f"\n{pronoun_cap} is carrying: {carried_str}."
                
                return desc
                
        return f"You don't see '{target_name}' here."