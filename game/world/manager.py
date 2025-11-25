"""
World Manager
Handles the lifecycle of game objects (loading, caching, saving).
"""
from typing import Dict, Optional
from game.models.room import Room
from game.models.entity import Entity
from game.world.data import WORLD
from game.state import ROOM_STATE, NPC_STATE

class WorldManager:
    _instance = None
    
    def __init__(self):
        self.active_rooms: Dict[str, Room] = {}
        self.active_npcs: Dict[str, Entity] = {}

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def get_room(self, room_id: str) -> Optional[Room]:
        """
        Get a Room object. 
        If it exists in memory, return it.
        If not, load it from data, hydrate it, and return it.
        """
        if room_id in self.active_rooms:
            return self.active_rooms[room_id]

        # Load from static data
        room_data = WORLD.get(room_id)
        if not room_data:
            return None

        # Create new Room object
        room = Room(
            oid=room_id,
            name=room_data.get("name", "Unknown Room"),
            description=room_data.get("description", "")
        )

        # Hydrate dynamic state (items dropped on floor, etc)
        # Hydrate dynamic state (items dropped on floor, etc)
        if room_id in ROOM_STATE:
            saved_state = ROOM_STATE[room_id]
            item_ids = saved_state.get("items", [])
            room.items = []
            for item_id in item_ids:
                item = self.get_item(item_id)
                if item:
                    room.items.append(item)
            
        # Hydrate static properties
        room.descriptions_by_time = room_data.get("descriptions_by_time", {})
        room.outdoor = room_data.get("outdoor", False)
        room.ambient_messages = room_data.get("ambient_messages", [])
        
        # Hydrate NPCs (initial placement)
        # Note: This is a simplification. In a real system, we'd check NPC_STATE for current location.
        # For now, we'll load the static definition of who belongs here.
        room.npcs = room_data.get("npcs", [])
        
        # Check NPC_STATE to see if any NPCs have moved here or left
        # This overrides the static definition
        from game.state import NPC_STATE
        current_npcs = []
        # First add static NPCs if they haven't moved
        for npc_id in room.npcs:
            if npc_id not in NPC_STATE or NPC_STATE[npc_id].get("room") == room_id:
                current_npcs.append(npc_id)
        
        # Then add any NPCs that have moved here
        for npc_id, state in NPC_STATE.items():
            if state.get("room") == room_id and npc_id not in current_npcs:
                current_npcs.append(npc_id)
                
        room.npcs = current_npcs

        # Setup exits
        for direction, target_id in room_data.get("exits", {}).items():
            room.add_exit(direction, target_id)

        # Cache it
        self.active_rooms[room_id] = room
        return room

    def get_npc(self, npc_id: str) -> Optional[Entity]:
        """
        Lazy load an NPC.
        """
        if npc_id in self.active_npcs:
            return self.active_npcs[npc_id]

        # Load from static definitions
        from npc import NPCS as NPC_DEFS
        npc_data = NPC_DEFS.get(npc_id)
        
        if not npc_data:
            return None

        # Create new NPC object
        # Note: npc_data is an NPC object from the old system, we need to adapt it
        # or read the raw dict if available. The old system has NPCS as a dict of Objects.
        
        from game.models.npc import NPC
        npc = NPC(oid=npc_id, name=npc_data.name, description=npc_data.description)
        
        # Hydrate from the old object attributes
        npc.title = npc_data.title
        npc.personality = npc_data.personality
        npc.home_room_oid = npc_data.home
        npc.use_ai = npc_data.use_ai
        npc.reactions = npc_data.reactions
        npc.traits = npc_data.traits
        npc.pronoun = npc_data.pronoun
        npc.stats.update(npc_data.stats)

        # Hydrate dynamic state from NPC_STATE
        if npc_id in NPC_STATE:
            state = NPC_STATE[npc_id]
            npc.stats["hp"] = state.get("hp", npc.stats["max_hp"])
            # Set location if known
            room_id = state.get("room")
            if room_id:
                room = self.get_room(room_id)
                if room:
                    room.add_content(npc)

        self.active_npcs[npc_id] = npc
        return npc

    def get_item(self, item_id: str) -> Optional[Entity]:
        """
        Create an Item object from its ID.
        Items are currently transient (re-created on load), but could be cached if unique.
        """
        from game_engine import get_item_def
        from game.models.item import Item, Weapon, Armor, Container, Consumable
        
        item_def = get_item_def(item_id)
        if not item_def:
            return None
            
        item_type = item_def.get("type", "misc")
        
        # Factory logic
        if item_type == "weapon":
            item = Weapon(item_id, item_def.get("name", item_id))
        elif item_type == "armor":
            item = Armor(item_id, item_def.get("name", item_id))
        elif item_type == "container":
            item = Container(item_id, item_def.get("name", item_id))
        elif item_type in ["food", "potion", "consumable"]:
            item = Consumable(item_id, item_def.get("name", item_id))
        else:
            item = Item(item_id, item_def.get("name", item_id))
            
        item.load_from_def(item_def)
        return item

    def tick_room(self, room_id: str):
        """Tick a specific room (update items, etc)."""
        room = self.get_room(room_id)
        if room:
            room.tick()

    def get_player(self, username: str) -> Optional[Entity]:
        """
        Get a Player object.
        This is a bit different as players are loaded from DB/Redis usually.
        For now, we'll assume the legacy dict is passed in or loaded elsewhere.
        """
        # This is a placeholder for the full player loading logic
        # In the full refactor, this would talk to the StateManager
        pass
