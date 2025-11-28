"""
Event bus for real-time game events.

Provides pub/sub system for:
- Room broadcasts (NPC actions, ambiance, player messages)
- Player-specific events (quest updates, private messages)
- Global events (world time changes, weather updates)
"""

import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from core.redis_manager import get_pubsub_connection, get_cache_connection

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event bus for publishing and subscribing to game events.
    
    Uses Redis pub/sub for cross-instance event distribution.
    """
    
    def __init__(self):
        self._redis = get_pubsub_connection()
        self._cache = get_cache_connection()
        self._subscriptions: Dict[str, List[Callable]] = {}
        
    def publish(self, event_type: str, data: Dict[str, Any], 
                room_id: Optional[str] = None, 
                username: Optional[str] = None,
                channel: Optional[str] = None) -> bool:
        """
        Publish an event.
        
        Args:
            event_type: Type of event (e.g., "npc_action", "player_move")
            data: Event data
            room_id: Room to broadcast to (creates room:room_id channel)
            username: User to send to (creates user:username channel)
            channel: Custom channel name (overrides room_id/username)
            
        Returns:
            True if published successfully
        """
        if self._redis is None:
            # Redis unavailable, skip publishing
            # TODO: Implement local fallback if needed, but for now just silence errors
            # logger.debug(f"Redis unavailable, skipping event publish: {event_type}")
            return False
            
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            event_json = json.dumps(event)
            
            # Determine channels to publish to
            channels = []
            if channel:
                channels.append(channel)
            elif room_id:
                channels.append(f"room:{room_id}")
            elif username:
                channels.append(f"user:{username}")
            else:
                # Global event
                channels.append("global")
            
            # Publish to all relevant channels
            for chan in channels:
                self._redis.publish(chan, event_json)
                logger.debug(f"Published event {event_type} to {chan}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing event {event_type}: {e}")
            return False
    
    def publish_room(self, room_id: str, event_type: str, data: Dict[str, Any]) -> bool:
        """Publish event to all players in a room."""
        return self.publish(event_type, data, room_id=room_id)
    
    def publish_user(self, username: str, event_type: str, data: Dict[str, Any]) -> bool:
        """Publish event to specific user."""
        return self.publish(event_type, data, username=username)
    
    def publish_global(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Publish global event."""
        return self.publish(event_type, data)
    
    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to a channel (local callback only - for in-process subscriptions).
        
        Note: For cross-instance subscriptions, use Redis pub/sub directly.
        This is mainly for local event handling.
        
        Args:
            channel: Channel name (e.g., "room:town_square", "user:player1")
            callback: Function to call with event data
        """
        if channel not in self._subscriptions:
            self._subscriptions[channel] = []
        self._subscriptions[channel].append(callback)
    
    def emit_local(self, channel: str, event: Dict[str, Any]) -> None:
        """
        Emit event to local subscribers only (in-process).
        
        Args:
            channel: Channel name
            event: Event data
        """
        if channel in self._subscriptions:
            for callback in self._subscriptions[channel]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {channel}: {e}")


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Event type constants
class EventTypes:
    """Event type constants."""
    
    # Player events
    PLAYER_MOVE = "player_move"
    PLAYER_MESSAGE = "player_message"
    PLAYER_EMOTE = "player_emote"
    PLAYER_COMMAND = "player_command"
    PLAYER_COMMAND_RESPONSE = "player_command_response"
    
    # NPC events
    NPC_ACTION = "npc_action"
    NPC_MESSAGE = "npc_message"
    NPC_MOVE = "npc_move"
    
    # Room events
    AMBIANCE = "ambiance"
    WEATHER_CHANGE = "weather_change"
    
    # Quest events
    QUEST_UPDATE = "quest_update"
    QUEST_OFFER = "quest_offer"
    QUEST_COMPLETE = "quest_complete"
    
    # System events
    WORLD_TIME_UPDATE = "world_time_update"
    SYSTEM_MESSAGE = "system_message"

