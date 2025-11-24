"""
WebSocket connection manager.

Provides clean, maintainable WebSocket handling with:
- Connection lifecycle management
- Room subscriptions
- Event broadcasting
- Reconnection handling
- Clear separation of concerns
"""

import json
import logging
import asyncio
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime
from collections import defaultdict
from core.redis_manager import get_pubsub_connection
from core.event_bus import get_event_bus, EventTypes

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """
    Represents a single WebSocket connection.
    
    Clean, simple interface for managing a player's connection.
    """
    
    def __init__(self, websocket, username: str):
        """
        Initialize connection.
        
        Args:
            websocket: The WebSocket object (from Flask or ASGI)
            username: Player's username
        """
        self.websocket = websocket
        self.username = username
        self.connected = True
        self.room_id: Optional[str] = None
        self.subscribed_channels: Set[str] = set()
        self.last_activity = datetime.utcnow()
        
    async def send(self, message: Dict[str, Any]) -> bool:
        """
        Send a message to the client.
        
        Args:
            message: Message dict (will be JSON encoded)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            message_json = json.dumps(message)
            await self.websocket.send(message_json)
            self.last_activity = datetime.utcnow()
            return True
        except Exception as e:
            logger.error(f"Error sending message to {self.username}: {e}")
            self.connected = False
            return False
    
    async def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message from the client.
        
        Returns:
            Message dict or None if connection closed
        """
        if not self.connected:
            return None
        
        try:
            message_text = await self.websocket.receive()
            if message_text is None:
                self.connected = False
                return None
            
            message = json.loads(message_text)
            self.last_activity = datetime.utcnow()
            return message
        except Exception as e:
            logger.debug(f"Error receiving message from {self.username}: {e}")
            self.connected = False
            return None
    
    def subscribe_room(self, room_id: str) -> None:
        """Subscribe to room events."""
        self.room_id = room_id
        channel = f"room:{room_id}"
        self.subscribed_channels.add(channel)
        logger.info(f"{self.username} subscribed to {channel}")
    
    def subscribe_user(self) -> None:
        """Subscribe to user-specific events."""
        channel = f"user:{self.username}"
        self.subscribed_channels.add(channel)
        logger.info(f"{self.username} subscribed to {channel}")
    
    def unsubscribe_all(self) -> None:
        """Unsubscribe from all channels."""
        self.subscribed_channels.clear()
        self.room_id = None


class WebSocketManager:
    """
    Manages all WebSocket connections.
    
    Clean, maintainable manager with clear responsibilities:
    - Track active connections
    - Handle room subscriptions
    - Broadcast events to rooms/users
    - Manage connection lifecycle
    """
    
    def __init__(self):
        """Initialize manager."""
        self._connections: Dict[str, WebSocketConnection] = {}  # username -> connection
        self._room_connections: Dict[str, Set[str]] = defaultdict(set)  # room_id -> set of usernames
        self._event_bus = get_event_bus()
        self._redis = get_pubsub_connection()
        self._pubsub = None
        
    async def connect(self, websocket, username: str) -> WebSocketConnection:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket object
            username: Player username
            
        Returns:
            WebSocketConnection instance
        """
        # Close existing connection if any
        if username in self._connections:
            old_conn = self._connections[username]
            await self.disconnect(old_conn)
        
        # Create new connection
        conn = WebSocketConnection(websocket, username)
        self._connections[username] = conn
        
        # Subscribe to user-specific events
        conn.subscribe_user()
        
        logger.info(f"WebSocket connected: {username}")
        
        # Start listening for events
        asyncio.create_task(self._listen_for_events(conn))
        
        return conn
    
    async def disconnect(self, connection: WebSocketConnection) -> None:
        """
        Disconnect a WebSocket connection.
        
        Args:
            connection: Connection to disconnect
        """
        username = connection.username
        room_id = connection.room_id
        
        # Remove from room
        if room_id:
            self._room_connections[room_id].discard(username)
            if not self._room_connections[room_id]:
                del self._room_connections[room_id]
        
        # Remove connection
        if username in self._connections:
            del self._connections[username]
        
        connection.connected = False
        connection.unsubscribe_all()
        
        logger.info(f"WebSocket disconnected: {username}")
    
    async def set_room(self, connection: WebSocketConnection, room_id: str) -> None:
        """
        Set the room for a connection (auto-subscribes to room events).
        
        Args:
            connection: Connection
            room_id: Room ID to join
        """
        old_room = connection.room_id
        
        # Leave old room
        if old_room:
            self._room_connections[old_room].discard(connection.username)
        
        # Join new room
        connection.subscribe_room(room_id)
        self._room_connections[room_id].add(connection.username)
        
        logger.info(f"{connection.username} moved to room: {room_id}")
    
    async def send_to_user(self, username: str, message: Dict[str, Any]) -> bool:
        """
        Send message to specific user.
        
        Args:
            username: Target username
            message: Message dict
            
        Returns:
            True if sent, False if user not connected
        """
        if username not in self._connections:
            return False
        
        conn = self._connections[username]
        return await conn.send(message)
    
    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any], 
                                exclude_username: Optional[str] = None) -> int:
        """
        Broadcast message to all users in a room.
        
        Args:
            room_id: Room ID
            message: Message dict
            exclude_username: Username to exclude from broadcast
            
        Returns:
            Number of users who received the message
        """
        if room_id not in self._room_connections:
            return 0
        
        count = 0
        usernames = list(self._room_connections[room_id])
        
        for username in usernames:
            if username == exclude_username:
                continue
            
            if username in self._connections:
                conn = self._connections[username]
                if await conn.send(message):
                    count += 1
        
        return count
    
    async def _listen_for_events(self, connection: WebSocketConnection) -> None:
        """
        Listen for events for a connection (runs in background).
        
        Args:
            connection: Connection to listen for
        """
        try:
            # Subscribe to Redis pub/sub channels
            pubsub = self._redis.pubsub()
            
            for channel in connection.subscribed_channels:
                pubsub.subscribe(channel)
            
            # Listen for messages
            async for message in pubsub.listen():
                if not connection.connected:
                    break
                
                if message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        # Send to connection
                        await connection.send({
                            "type": "event",
                            "event": event
                        })
                    except Exception as e:
                        logger.error(f"Error processing event for {connection.username}: {e}")
            
            # Clean up
            pubsub.unsubscribe()
            pubsub.close()
            
        except Exception as e:
            logger.error(f"Error in event listener for {connection.username}: {e}")
        finally:
            await self.disconnect(connection)
    
    def get_connection(self, username: str) -> Optional[WebSocketConnection]:
        """Get connection for username."""
        return self._connections.get(username)
    
    def is_connected(self, username: str) -> bool:
        """Check if user is connected."""
        return username in self._connections
    
    def get_room_users(self, room_id: str) -> Set[str]:
        """Get set of usernames in a room."""
        return self._room_connections.get(room_id, set()).copy()


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager

