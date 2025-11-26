"""
Room Model
"""
from typing import List, Optional, Dict, Any
from game.models.base import GameObject

class Room(GameObject):
    def __init__(self, oid: str, name: str, description: str):
        super().__init__(oid, name, description)
        self.exits: dict[str, str] = {}  # direction -> room_oid
        self.items: List[Any] = []  # List of Item objects (or strings for legacy support)
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
        lines.append(desc)
        
        # 3. Weather/Time Line (dark yellow) - for outdoor rooms only
        if self.outdoor:
            weather_line = self._get_weather_time_line()
            if weather_line:
                lines.append(f"[DARK_YELLOW]{weather_line}[/DARK_YELLOW]")
        
        # 4. Exits (dark green)
        exits_str = ", ".join(self.exits.keys()) or "none"
        lines.append(f"[DARK_GREEN]Exits: {exits_str}[/DARK_GREEN]")
        
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
        # Import helpers from game_engine (temporary bridge)
        from game_engine import get_time_of_day, apply_weather_to_description
        
        time_of_day = get_time_of_day()
        desc = self.descriptions_by_time.get(time_of_day, self.description)
        
        if self.outdoor:
            desc = apply_weather_to_description(desc, time_of_day)
            
        return desc
    
    def _get_weather_time_line(self) -> str:
        """Get the combined weather and time description for outdoor rooms."""
        from game_engine import get_combined_time_weather_description
        return get_combined_time_weather_description(is_outdoor=self.outdoor)

    def _get_items_description(self, viewer: 'GameObject') -> str:
        """Get description of items in the room."""
        from game_engine import render_item_name, QUEST_SPECIFIC_ITEMS
        
        # Start with standard room items (objects)
        visible_items = []
        for item in self.items:
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
            # Try to find object in self.items
            found_obj = next((i for i in self.items if hasattr(i, 'oid') and i.oid == item_id), None)
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

    def tick(self):
        """Called periodically to update room state (items, etc)."""
        # Update items
        items_to_remove = []
        for item in self.items:
            if hasattr(item, 'tick'):
                item.tick()
                if getattr(item, 'destroyed', False):
                    items_to_remove.append(item)
        
        # Remove destroyed items
        for item in items_to_remove:
            self.items.remove(item)
            # Optional: Broadcast message about item crumbling to dust
            self.broadcast(f"{item.name} crumbles into dust.")
