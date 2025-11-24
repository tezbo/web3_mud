"""
WebSocket handler for Flask.

Clean, maintainable WebSocket endpoint handler.
Simple interface that connects the WebSocket layer to game logic.
"""

import json
import logging
from typing import Dict, Any
from core.websocket_manager import get_websocket_manager, WebSocketConnection
from core.event_bus import get_event_bus, EventTypes

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    Handles WebSocket connections and messages.
    
    Clean separation:
    - WebSocket handling (this class)
    - Game logic (game_engine.py)
    - State management (state_manager.py)
    - Events (event_bus.py)
    """
    
    def __init__(self, command_handler_fn=None):
        """
        Initialize handler.
        
        Args:
            command_handler_fn: Function to handle commands
                Signature: (command: str, username: str) -> (response: str, events: list)
        """
        self._ws_manager = get_websocket_manager()
        self._event_bus = get_event_bus()
        self._command_handler = command_handler_fn
    
    async def handle_connection(self, websocket, username: str) -> None:
        """
        Handle a new WebSocket connection.
        
        Clean, simple connection handler that:
        1. Registers connection
        2. Sends welcome message
        3. Starts message loop
        
        Args:
            websocket: WebSocket object
            username: Player username
        """
        # Register connection
        conn = await self._ws_manager.connect(websocket, username)
        
        try:
            # Send welcome message
            await conn.send({
                "type": "connected",
                "message": "WebSocket connected. Welcome!",
                "username": username
            })
            
            # Load player's room and subscribe
            # TODO: Get from state manager
            # room_id = state_manager.get_player_state(username).get("location")
            # if room_id:
            #     await self._ws_manager.set_room(conn, room_id)
            
            # Message loop
            await self._message_loop(conn)
            
        except Exception as e:
            logger.error(f"Error in WebSocket connection for {username}: {e}")
        finally:
            await self._ws_manager.disconnect(conn)
    
    async def _message_loop(self, connection: WebSocketConnection) -> None:
        """
        Handle incoming messages from client.
        
        Clean message loop:
        1. Receive message
        2. Route to appropriate handler
        3. Send response
        
        Args:
            connection: WebSocket connection
        """
        while connection.connected:
            try:
                # Receive message
                message = await connection.receive()
                if message is None:
                    break  # Connection closed
                
                # Route message
                message_type = message.get("type")
                
                if message_type == "command":
                    await self._handle_command(connection, message)
                elif message_type == "ping":
                    await self._handle_ping(connection)
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except Exception as e:
                logger.error(f"Error in message loop for {connection.username}: {e}")
                break
    
    async def _handle_command(self, connection: WebSocketConnection, message: Dict[str, Any]) -> None:
        """
        Handle a game command.
        
        Clean command handler:
        1. Extract command
        2. Call game logic
        3. Send response
        4. Broadcast events
        
        Args:
            connection: WebSocket connection
            message: Command message
        """
        command = message.get("command", "").strip()
        request_id = message.get("id")  # Optional request ID for response matching
        
        if not command:
            await connection.send({
                "type": "error",
                "message": "Empty command",
                "id": request_id
            })
            return
        
        try:
            # Call game logic handler
            if self._command_handler:
                response, events = self._command_handler(command, connection.username)
            else:
                # Fallback: just echo
                response = f"Unknown command: {command}"
                events = []
            
            # Send response
            await connection.send({
                "type": "command_response",
                "command": command,
                "response": response,
                "id": request_id,
                "events": events or []
            })
            
        except Exception as e:
            logger.error(f"Error handling command '{command}' for {connection.username}: {e}")
            await connection.send({
                "type": "error",
                "message": f"Error processing command: {str(e)}",
                "id": request_id
            })
    
    async def _handle_ping(self, connection: WebSocketConnection) -> None:
        """Handle ping message (keep-alive)."""
        await connection.send({
            "type": "pong",
            "timestamp": connection.last_activity.isoformat()
        })


# Helper function for Flask integration
async def handle_websocket_connection(websocket, username: str, command_handler_fn=None) -> None:
    """
    Flask WebSocket connection handler.
    
    Clean entry point for Flask integration.
    
    Args:
        websocket: WebSocket object from Flask
        username: Player username
        command_handler_fn: Command handler function
    """
    handler = WebSocketHandler(command_handler_fn=command_handler_fn)
    await handler.handle_connection(websocket, username)

