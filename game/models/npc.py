"""
NPC Model
"""
from typing import Dict, List, Optional, Any, TYPE_CHECKING, Tuple
from game.models.entity import Entity
from game.systems.weather import WeatherStatusTracker

if TYPE_CHECKING:
    from game.models.player import Player
    from game.models.item import Item

class NPC(Entity):
    def __init__(self, oid: str, name: str, description: str = ""):
        super().__init__(oid, name)
        self.description = description
        self.title: str = ""
        self.personality: str = ""
        self.home_room_oid: Optional[str] = None
        self.use_ai: bool = False
        self.reactions: Dict[str, List[str]] = {}
        self.traits: Dict[str, float] = {}
        self.pronoun: str = "they"
        self.faction: str = "neutral"
        self.attackable: bool = False
        
        # Weather Status (Phase 2)
        self.weather_status = WeatherStatusTracker()
        self.weather_reactions: Dict[Tuple[str, str], str] = {}  # (weather_type, intensity) -> message
        
        # Merchant data
        self.merchant_inventory: Dict[str, int] = {}  # item_id -> stock

    def load_from_dict(self, data: Dict[str, Any]):
        """Hydrate NPC from static data definition."""
        self.name = data.get("name", self.name)
        self.title = data.get("title", "")
        self.description = data.get("description", "")
        self.personality = data.get("personality", "")
        self.home_room_oid = data.get("home")
        self.use_ai = data.get("use_ai", False)
        self.attackable = data.get("attackable", False)
        self.reactions = data.get("reactions", {})
        self.traits = data.get("traits", {})
        self.pronoun = data.get("pronoun", "they")
        
        # Load weather reactions (Phase 2)
        weather_reactions = data.get("weather_reactions", {})
        for key_str, message in weather_reactions.items():
            # Parse "rain_heavy" -> ("rain", "heavy")
            parts = key_str.split("_", 1)
            if len(parts) == 2:
                wtype, intensity = parts
                self.weather_reactions[(wtype, intensity)] = message
        
        stats = data.get("stats", {})
        if stats:
            self.stats.update(stats)
            self.faction = stats.get("faction", "neutral")

    def get_reaction(self, verb: str) -> Optional[str]:
        """Get a reaction line for a verb (nod, wave, etc)."""
        options = self.reactions.get(verb)
        if not options:
            return None
        # Simple rotation or random choice could go here
        import random
        return random.choice(options)
    
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
        
        # Generate description (same logic as Player)
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
    
    def get_weather_reaction(self, weather_state: Dict, season: str) -> Optional[str]:
        """Get NPC's reaction to current weather, if they have one."""
        if not self.weather_status.has_status():
            return None  # Only react if affected by weather
        
        wtype = weather_state.get("type", "clear")
        intensity = weather_state.get("intensity", "none")
        key = (wtype, intensity)
        
        return self.weather_reactions.get(key)
    
    def respond_to(self, player: 'Player', game_state: Dict[str, Any], db_conn=None) -> str:
        """
        Generate a response to a player.
        Uses the legacy generate_npc_line or AI client.
        """
        from game_engine import is_npc_refusing_to_talk, generate_npc_line
        
        # Check cooldown/refusal
        if is_npc_refusing_to_talk(game_state, self.oid):
            return f"{self.name} pointedly ignores you and refuses to talk."
            
        # Generate dialogue
        # Note: generate_npc_line handles both static lines and AI generation
        response = generate_npc_line(
            self.oid, 
            game_state, 
            player.username, 
            user_id=None, # TODO: Pass user_id if available in player/game_state
            db_conn=db_conn
        )
        
        return response
    def on_attacked(self, attacker: 'Entity', game_state: Dict[str, Any]) -> str:
        """
        Handle being attacked by an entity.
        """
        # Check if attackable
        if not self.attackable:
            # Check for legacy callback
            from npc import get_npc_on_attack_callback
            callback = get_npc_on_attack_callback(self.oid)
            
            if callback:
                return callback(game_state, attacker.name, self.oid)
            else:
                return f"You can't attack {self.name}."
        
        # Resolve combat round
        from game.systems.combat import CombatSystem
        combat = CombatSystem.get_instance()
        messages = combat.resolve_round(attacker, self)
        
        # Trigger AI response (e.g. fight back)
        # For now, we just return the combat log
        return "\n".join(messages)
    def die(self, source: 'Entity' = None):
        """
        Handle NPC death.
        Creates a corpse with inventory and removes NPC from room.
        """
        if not self.location:
            return
            
        # Broadcast death message
        source_name = source.name if source else "Unknown"
        self.location.broadcast(f"[RED]{self.name} has been slain by {source_name}![/RED]")
        
        # Create corpse
        from game.models.item import Corpse
        corpse = Corpse(
            oid=f"corpse_{self.oid}", 
            name=f"Corpse of {self.name}", 
            description=f"The lifeless body of {self.name}."
        )
        corpse.weight = 50.0 # Heavy
        corpse.capacity = 100.0
        
        # Transfer inventory to corpse
        # We copy the list to avoid modification issues during iteration
        for item in list(self.inventory.contents):
            self.inventory.remove(item)
            corpse.inventory.add(item)
            
        # Add corpse to room
        self.location.items.append(corpse)
        
        # Remove NPC from room
        if self.oid in self.location.npcs:
            self.location.npcs.remove(self.oid)
    def receive_item(self, giver: 'Entity', item_obj: 'Item', game_state: Dict[str, Any]) -> str:
        """
        Handle receiving an item from an entity.
        """
        from game_engine import render_item_name
        import quests
        
        item_name = item_obj.get_display_name()
        item_id = item_obj.oid
        
        # Add to NPC inventory (if we want them to hold it)
        # self.inventory.append(item_obj)
        
        # Trigger quest event
        event = quests.QuestEvent(
            type="give_item",
            room_id=self.home_room_oid or "unknown", # Best guess for location
            npc_id=self.oid,
            item_id=item_id,
            username=giver.username
        )
        
        # Handle quest result
        quest_response = quests.handle_quest_event(game_state, event)
        
        if quest_response:
            return f"You give the {item_name} to {self.name}. {quest_response}"
        else:
            return f"You give the {item_name} to {self.name}. {self.pronoun.capitalize()} accepts it with a nod."
