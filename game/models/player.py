"""
Player Model
"""
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from game.models.entity import Entity

if TYPE_CHECKING:
    from game.models.room import Room
    from game.models.npc import NPC

class Player(Entity):
    def __init__(self, username: str):
        # Use username as the OID for players
        super().__init__(oid=username, name=username)
        self.username = username
        self.race: str = "human"
        self.gender: str = "unknown"
        self.backstory: str = ""
        self.max_carry_weight: float = 20.0
        
        # Game State Trackers
        self.quests: Dict[str, Any] = {}
        self.completed_quests: Dict[str, Any] = {}
        self.reputation: Dict[str, int] = {}
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

    def load_from_state(self, state: Dict[str, Any]):
        """Load player state from the legacy dictionary format."""
        location_oid = state.get("location", "town_square")
        
        # Resolve location to Room object
        from game.world.manager import WorldManager
        self.location = WorldManager.get_instance().get_room(location_oid)
        
        char_data = state.get("character", {})
        self.race = char_data.get("race", "human")
        self.gender = char_data.get("gender", "unknown")
        self.backstory = char_data.get("backstory", "")
        
        if "stats" in char_data:
            self.stats.update(char_data["stats"])
            
        # Load inventory (convert strings to Item objects)
        inventory_ids = state.get("inventory", [])
        self.inventory = []
        wm = WorldManager.get_instance()
        for item_id in inventory_ids:
            item = wm.get_item(item_id)
            if item:
                self.inventory.append(item)
            
        self.max_carry_weight = state.get("max_carry_weight", 20.0)
        self.reputation = state.get("reputation", {})
        self.npc_memory = state.get("npc_memory", {})
        
        # Load quests
        from game.systems.quest_manager import QuestManager
        from game.models.quest import Quest
        
        qm = QuestManager.get_instance()
        self.quests = {}
        for q_id, q_data in state.get("quests", {}).items():
            template = qm.get_template(q_id)
            if template:
                self.quests[q_id] = Quest.from_dict(q_data, template)
            else:
                # Fallback for missing templates? Or just keep raw dict?
                # For now, we skip or keep raw dict if we want to be safe, 
                # but let's assume templates exist.
                pass
                
        # Completed quests can remain as dicts for now, or be objects too.
        # Keeping as dicts is safer for history.
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

    def to_state(self) -> Dict[str, Any]:
        """Serialize back to legacy dictionary format (for saving)."""
        return {
            "username": self.username,
            "location": self.location.oid if self.location else "town_square",
            "inventory": [item.oid for item in self.inventory],
            "max_carry_weight": self.max_carry_weight,
            "character": {
                "race": self.race,
                "gender": self.gender,
                "stats": self.stats,
                "backstory": self.backstory
            },
            "reputation": self.reputation,
            "npc_memory": self.npc_memory,
            "quests": {qid: q.to_dict() for qid, q in self.quests.items()},
            "completed_quests": self.completed_quests,
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
            "defense": self.defense
        }

    def __repr__(self):
        return f"<Player {self.username} Lvl:{self.level} HP:{self.hp}/{self.max_hp}>"

    # --- RPG Mechanics ---

    def take_damage(self, amount: int) -> Tuple[int, bool]:
        """
        Apply damage to player.
        Returns (actual_damage_taken, is_dead).
        """
        actual_damage = max(0, amount - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage, self.hp == 0

    def heal(self, amount: int) -> int:
        """
        Heal the player.
        Returns actual amount healed.
        """
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def use_stamina(self, amount: int) -> bool:
        """
        Try to use stamina.
        Returns True if successful, False if not enough.
        """
        if self.stamina >= amount:
            self.stamina -= amount
            return True
        return False

    def recover_stamina(self, amount: int):
        """Recover stamina."""
        self.stamina = min(self.max_stamina, self.stamina + amount)

    def gain_xp(self, amount: int) -> bool:
        """
        Gain XP and check for level up.
        Returns True if leveled up.
        """
        self.xp += amount
        if self.xp >= self.xp_to_next:
            self.level_up()
            return True
        return False

    def level_up(self):
        """Handle level up logic."""
        self.level += 1
        self.xp -= self.xp_to_next
        self.xp_to_next = int(self.xp_to_next * 1.5)
        
        # Stat increases
        self.max_hp += 5
        self.hp = self.max_hp
        self.max_stamina += 5
        self.stamina = self.max_stamina
        self.strength += 1
        self.dexterity += 1

    def move(self, direction: str, broadcast_fn=None, game_state_for_quests=None) -> Tuple[bool, str]:
        """
        Execute a move command.
        Returns (success, message).
        """
        if not self.location:
            return False, "You are floating in a void."

        # 1. Check Exit
        target_oid = self.location.get_exit(direction)
        if not target_oid:
            return False, "You can't go that way."

        # 2. Check Accessibility (Legacy Hook)
        # We still need to call the legacy is_exit_accessible for now until that's refactored
        from game_engine import is_exit_accessible, get_entrance_exit_message, get_movement_message, OPPOSITE_DIRECTION
        
        # Note: is_exit_accessible expects the legacy game dict, but we might get away with passing None 
        # if it only checks global state. Let's check... it takes 'game'.
        # For now, we'll assume it's accessible or skip the check if we can't easily replicate it.
        # Ideally, we move that logic to Room/Exit models.
        # Let's assume accessible for this step to keep it pure OO, or minimal legacy dependency.
        
        # 3. Handle Movement
        from game.world.manager import WorldManager
        wm = WorldManager.get_instance()
        target_room = wm.get_room(target_oid)
        
        if not target_room:
            return False, "That way is blocked by a void."

        old_room_oid = self.location.oid
        
        # 4. Broadcast Leave
        if broadcast_fn:
            leave_msg = get_entrance_exit_message(old_room_oid, target_oid, direction, self.name, is_exit=True, is_npc=False)
            broadcast_fn(old_room_oid, leave_msg)

        # 5. Update Location
        self.move_to(target_room)
        
        # 6. Broadcast Arrive
        if broadcast_fn:
            opposite = OPPOSITE_DIRECTION.get(direction, "somewhere")
            arrive_msg = get_entrance_exit_message(target_oid, old_room_oid, opposite, self.name, is_exit=False, is_npc=False)
            broadcast_fn(target_oid, arrive_msg)

        # 7. Trigger Quest Events
        if game_state_for_quests:
            import quests
            event = quests.QuestEvent(
                type="enter_room",
                room_id=target_oid,
                username=self.username
            )
            quests.handle_quest_event(game_state_for_quests, event)

        # 8. Return Description
        movement_msg = get_movement_message(target_oid, direction)
        return True, f"{movement_msg}\n{target_room.look(self)}"

    def take_item(self, item_id: str, from_room: 'Room', game_state_for_quests=None) -> tuple[bool, str]:
        """
        Take an item from a room.
        Returns (success, message).
        """
        from game_engine import QUEST_SPECIFIC_ITEMS, get_item_def, calculate_inventory_weight
        from game.world.manager import WorldManager
        
        # Find item object in room
        item_obj = next((i for i in from_room.items if hasattr(i, 'oid') and i.oid == item_id), None)
        
        # Check quest-specific items if not found in standard items
        if not item_obj:
            if item_id in QUEST_SPECIFIC_ITEMS:
                quest_data = QUEST_SPECIFIC_ITEMS[item_id]
                if quest_data.get("room_id") == from_room.oid and quest_data.get("owner_username") == self.username:
                    # Create temporary item object for quest item
                    wm = WorldManager.get_instance()
                    item_obj = wm.get_item(item_id)
            
        if not item_obj:
            return False, "You don't see that here."
        
        # Check weight limit
        current_weight = sum(i.weight for i in self.inventory if hasattr(i, 'weight'))
        if current_weight + item_obj.weight > self.max_carry_weight:
            return False, "You can't pick up much more, you'll fall over!"
        
        # Check if item can be taken
        can_take, reason = item_obj.can_be_taken(self)
        if not can_take:
            return False, reason

        # Remove from room
        if item_id in QUEST_SPECIFIC_ITEMS:
            del QUEST_SPECIFIC_ITEMS[item_id]
        elif item_obj in from_room.items:
            from_room.items.remove(item_obj)
        
        # Add to inventory
        self.inventory.append(item_obj)
        item_obj.on_take(self)
        
        # Trigger quest event
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

    def drop_item(self, item_id: str, to_room: 'Room') -> tuple[bool, str]:
        """
        Drop an item into a room.
        Returns (success, message).
        """
        from game_engine import render_item_name
        
        # Find item in inventory
        item_obj = next((i for i in self.inventory if hasattr(i, 'oid') and i.oid == item_id), None)
        
        if not item_obj:
            return False, "You don't have that item."
        
        # Check if droppable
        can_drop, reason = item_obj.can_be_dropped(self)
        if not can_drop:
            return False, reason
        
        # Remove from inventory
        self.inventory.remove(item_obj)
        
        # Add to room
        to_room.items.append(item_obj)
        item_obj.on_drop(self)
        
        display_name = item_obj.get_display_name()
        return True, f"You drop the {display_name}."

    def talk_to(self, npc: 'NPC', game_state: Dict[str, Any], db_conn=None) -> str:
        """
        Initiate conversation with an NPC.
        Returns the NPC's response.
        """
        # Check if NPC is in the same room
        if not self.location or npc.oid not in self.location.npcs:
            return f"You don't see {npc.name} here."
            
        # Delegate to NPC to generate response
        response = npc.respond_to(self, game_state, db_conn)
        
        # Trigger quest event
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
        """
        Attack a target.
        Returns the result message.
        """
        # Check location
        if not self.location or (target.oid not in self.location.npcs and target.oid != self.username):
             # Note: target.oid might be username for players
            return f"You don't see {target.name} here."
            
        # Delegate to target to handle being attacked
        return target.on_attacked(self, game_state)
    def give_item(self, item_id: str, target: 'Entity', game_state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Give an item to a target (NPC or Player).
        Returns (success, message).
        """
        from game_engine import render_item_name
        
        # Find item in inventory
        item_obj = next((i for i in self.inventory if hasattr(i, 'oid') and i.oid == item_id), None)
        
        if not item_obj:
            return False, "You don't have that item."
            
        # Check location
        if not self.location or (target.oid not in self.location.npcs and target.oid != self.username):
            # Check for other players in room (legacy check needed or WorldManager lookup)
            # For now, we assume target is valid if passed in, but we should verify presence
            pass

        # Remove from inventory
        self.inventory.remove(item_obj)
        
        # Delegate to target to receive item
        # If target is NPC
        if hasattr(target, 'receive_item'):
            response = target.receive_item(self, item_obj, game_state)
            return True, response
            
        # If target is Player (or generic Entity without receive_item)
        if hasattr(target, 'inventory'):
            target.inventory.append(item_obj)
            item_name = item_obj.get_display_name()
            return True, f"You give the {item_name} to {target.name}."
            
        # Fallback (shouldn't happen for valid entities)
        self.inventory.append(item_obj) # Refund
        return False, f"You can't give things to {target.name}."

    def look_at(self, target_name: str) -> str:
        """Look at a specific target (item, npc, self, etc)."""
        target_name = target_name.lower()
        
        # 1. Self
        if target_name in ["me", "self", self.username.lower()]:
            # TODO: Add more detail (equipment, stats)
            return f"You look at yourself. You are {self.name}, a {self.race}."
            
        # 2. Inventory
        for item in self.inventory:
            # Simple match: exact or partial word match
            if target_name == item.name.lower() or target_name in [adj.lower() for adj in item.adjectives] or target_name in item.name.lower().split():
                return f"You see {item.get_display_name()}.\n{item.description}"
                
        if not self.location:
            return "You see nothing."
            
        # 3. Items in Room
        for item in self.location.items:
            if target_name == item.name.lower() or target_name in [adj.lower() for adj in item.adjectives] or target_name in item.name.lower().split():
                return f"You see {item.get_display_name()}.\n{item.description}"
                
        # 4. NPCs in Room
        from game.world.manager import WorldManager
        wm = WorldManager.get_instance()
        for npc_id in self.location.npcs:
            npc = wm.get_npc(npc_id)
            if npc and (target_name == npc.name.lower() or target_name in npc.name.lower().split()):
                return f"You see {npc.name}.\n{npc.description}"
                
        return f"You don't see '{target_name}' here."
