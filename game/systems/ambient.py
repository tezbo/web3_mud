"""
Ambient Message System
Handles periodic sensory messages in rooms to enhance immersion.
"""
import random
from typing import Dict, List, Optional

class AmbientSystem:
    def __init__(self):
        self.last_tick: int = 0
        # Check every 30 seconds (assuming 1 tick = 1 second roughly, or adjust based on game speed)
        # In this engine, ticks are often faster. Let's say check every 100 ticks.
        self.check_interval: int = 100 
        self.chance_to_trigger: float = 0.3 # 30% chance when checked

    def tick(self, game_state: Dict, current_tick: int):
        """
        Called every game tick. Checks if ambient messages should be played.
        """
        if current_tick - self.last_tick < self.check_interval:
            return

        self.last_tick = current_tick
        
        # Get active rooms (rooms with players)
        # This requires a way to find rooms with players. 
        # For now, we'll iterate active rooms in WorldManager if possible, 
        # or rely on a passed list of active room IDs.
        
        from game.world.manager import WorldManager
        from game_engine import broadcast_to_room, get_time_of_day
        
        wm = WorldManager.get_instance()
        
        # Optimization: In a real MMO, we'd only check rooms with players.
        # For this scale, iterating active loaded rooms is fine.
        for room_id, room in wm.active_rooms.items():
            # Skip if no players (if we can check that)
            # if not room.players: continue 
            
            if not room.ambient_messages:
                continue
                
            if random.random() < self.chance_to_trigger:
                message = random.choice(room.ambient_messages)
                
                # Format with time/weather context if needed (future)
                
                # Broadcast
                broadcast_to_room(room_id, f"\n[Ambient] {message}\n")
