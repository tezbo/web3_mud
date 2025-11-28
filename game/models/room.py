"""
Room Model
"""
from typing import List, Optional, Dict, Any
from game.models.base import GameObject
from game.systems.inventory_system import InventorySystem

class Room(GameObject):
    def __init__(self, oid: str, name: str, description: str):
        super().__init__(oid, name, description)
        self.exits: dict[str, str] = {}  # direction -> room_oid
        
        # Inventory System (Room contents)
        # Rooms have infinite capacity effectively, but we track weight for realism if needed
        self.inventory = InventorySystem(self, max_weight=float('inf'), max_items=1000)
        # Legacy attribute for backward compatibility
        self.items: List[Any] = self.inventory.contents
        
        self.descriptions_by_time: Dict[str, str] = {}
        self.outdoor: bool = False
        
        # Dynamic contents (loaded at runtime)
        self.npcs: List[str] = [] # List of NPC IDs
        self.players: List[str] = [] # List of Player Usernames
        self.ambient_messages: List[str] = [] # List of ambient sensory messages

    def add_exit(self, direction: str, target_room_oid: str):
        self.exits[direction] = target_room_oid

    def get_exit(self, direction: str) -> Optional[str]:
        return self.exits.get(direction)

    def broadcast(self, message: str, exclude_oid: Optional[str] = None):
        """Send a message to all players in the room."""
        # Use the global broadcast function from app/game_engine
        # We need to import it or have it injected. For now, we'll import the helper wrapper.
        from game_engine import broadcast_to_room
        
        # broadcast_to_room handles the socket/redis logic
        broadcast_to_room(self.oid, message, exclude_user_id=exclude_oid)

    def look(self, viewer: 'GameObject') -> str:
        """
        Return the full room description including exits, items, and entities.
        Replaces game_engine.describe_location.
        """
        lines = []
        
        # 1. Base Description (Time/Weather aware) - no room name for immersion
        desc = self._get_base_description_text()
        
        # DEBUG: Log room state
        if self.oid == "tavern":
            import logging
            
        lines.append(desc)
        
        # 3. Weather/Time Line (dark yellow) - for outdoor rooms only
        # CRITICAL: Only show weather line for truly outdoor rooms
        # Use explicit boolean check to ensure no false positives
        if self.outdoor is True:
            weather_line = self._get_weather_time_line()
            if weather_line:
                lines.append(f"[WEATHER_DESC]{weather_line}[/WEATHER_DESC]")
        # Safety: explicitly do nothing for indoor rooms
        else:
            # Room is indoor - do not show any weather line
            pass
        
        # 4. Exits (configurable color, default dark green)
        exits = list(self.exits.keys())
        count = len(exits)
        
        if count == 0:
            exit_text = "There are no obvious exits."
        elif count == 1:
            exit_text = f"There is one obvious exit: {exits[0]}."
        else:
            from game_engine import number_to_words
            count_str = number_to_words(count)
            # Join with commas and 'and'
            if count == 2:
                exits_list = f"{exits[0]} and {exits[1]}"
            else:
                exits_list = ", ".join(exits[:-1]) + f" and {exits[-1]}"
            exit_text = f"There are {count_str} obvious exits: {exits_list}."
            
        lines.append(f"[EXITS]{exit_text}[/EXITS]")
        
        # 5. Items
        items_text = self._get_items_description(viewer)
        if items_text:
            lines.append(items_text)
        
        # 6. Entities (NPCs + Players)
        entities_text = self._get_entities_description(viewer)
        if entities_text:
            lines.append(entities_text)
        
        return "\n".join(lines)

    def _get_base_description_text(self) -> str:
        """Get the room description based on time of day and weather."""
        from game.systems.atmospheric_manager import get_atmospheric_manager
        
        atmos = get_atmospheric_manager()
        
        # Get time-aware description if available
        # For now, use base description (time-specific descriptions per room can be added later)
        desc = self.description
        
        if self.outdoor is True:
            desc = atmos.apply_weather_to_description(desc)
            
        return desc
    
    def _get_weather_time_line(self) -> str:
        """Get the combined weather and time description for outdoor rooms ONLY."""
        # CRITICAL: Only return weather line if room is explicitly outdoor
        # Use strict boolean check - must be exactly True
        if self.outdoor is not True:
            # Room is indoor - return empty string (no weather line)
            return ""
        from game.systems.atmospheric_manager import get_atmospheric_manager
        # Always pass is_outdoor=True since we've already verified the room is outdoor
        return get_atmospheric_manager().get_combined_description(is_outdoor=True)

    def _get_items_description(self, viewer: 'GameObject') -> str:
        """Get description of items in the room."""
        from game_engine import render_item_name, QUEST_SPECIFIC_ITEMS
        
        # Start with standard room items (objects)
        visible_items = []
        # Start with standard room items (objects)
        visible_items = []
        for item in self.inventory.contents:
            if hasattr(item, 'oid'):
                visible_items.append(item.oid)
            else:
                visible_items.append(item) # Fallback for strings
        
        # Add quest specific items for this viewer
        if hasattr(viewer, 'username'):
            username = viewer.username
            for item_id, data in QUEST_SPECIFIC_ITEMS.items():
                if data.get("room_id") == self.oid and data.get("owner_username") == username:
                    if item_id not in visible_items:
                        visible_items.append(item_id)

        if not visible_items:
            return "You don't see anything notable lying around."
            
        # Use item objects if available for better names/descriptions
        item_names = []
        for item_id in visible_items:
            # Try to find object in self.inventory.contents
            found_obj = next((i for i in self.inventory.contents if hasattr(i, 'oid') and i.oid == item_id), None)
            if found_obj:
                item_names.append(found_obj.get_display_name())
            else:
                item_names.append(render_item_name(item_id))
                
        return "You can see: " + ", ".join(item_names) + "."

    def _get_entities_description(self, viewer: 'GameObject') -> str:
        """Get description of NPCs and Players."""
        from game.world.manager import WorldManager
        wm = WorldManager.get_instance()
        
        present_names = []
        
        # NPCs
        for npc_id in self.npcs:
            npc = wm.get_npc(npc_id)
            if npc:
                present_names.append(npc.name)
                
        # Players (TODO: Connect to live session list)
        # For now, we'll rely on the game_engine to inject this or read from shared state
        # This is a temporary limitation during refactor
        
        if not present_names:
            return ""
            
        return "Also here: " + ", ".join(present_names)

    def get_entrance_message(self, actor_name: str, direction: str, is_npc: bool = False) -> str:
        """
        Get the message displayed when someone enters the room.
        
        Args:
            actor_name: Name of the entity entering
            direction: Direction they came FROM
            is_npc: Whether the entity is an NPC
        """
        # TODO: Load custom messages from room data/JSON
        # For now, use standard default
        
        if is_npc:
            return f"{actor_name} arrives from the {direction}."
        else:
            return f"[CYAN]{actor_name} arrives from the {direction}.[/CYAN]"

    def get_exit_message(self, actor_name: str, direction: str, is_npc: bool = False) -> str:
        """
        Get the message displayed when someone leaves the room.
        
        Args:
            actor_name: Name of the entity leaving
            direction: Direction they are going TO
            is_npc: Whether the entity is an NPC
        """
        # TODO: Load custom messages from room data/JSON
        
        if is_npc:
            return f"{actor_name} leaves {direction}."
        else:
            return f"[CYAN]{actor_name} leaves {direction}.[/CYAN]"

    def tick(self):
        """Called periodically to update room state (items, etc)."""
        # Update items
        items_to_remove = []
        for item in self.inventory.contents:
            if hasattr(item, 'tick'):
                item.tick()
                if getattr(item, 'destroyed', False):
                    items_to_remove.append(item)
        
        # Remove destroyed items
        for item in items_to_remove:
            self.inventory.remove(item)
            # Optional: Broadcast message about item crumbling to dust
            self.broadcast(f"{item.name} crumbles into dust.")
