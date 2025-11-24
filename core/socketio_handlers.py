"""
Flask-SocketIO event handlers.

Clean, maintainable WebSocket handlers that integrate with:
- Game engine (command processing)
- Event bus (real-time events)
- State manager (player state)
"""

import logging
from flask import session
from flask_socketio import emit, join_room, leave_room
from core.event_bus import get_event_bus, EventTypes
from core.state_manager import get_state_manager

logger = logging.getLogger(__name__)


def register_socketio_handlers(socketio, get_game_fn, handle_command_fn, save_game_fn):
    """
    Register all SocketIO event handlers.
    
    Clean, maintainable registration function.
    
    Args:
        socketio: SocketIO instance
        get_game_fn: Function to get game state (username) -> game dict
        handle_command_fn: Function to handle commands (command, game, username, ...) -> (response, game)
        save_game_fn: Function to save game state (game) -> None
    """
    
    @socketio.on('connect')
    def handle_connect(auth):
        """
        Handle WebSocket connection.
        
        Clean connection handler:
        1. Verify authentication
        2. Join user-specific room
        3. Join player's current room
        4. Send welcome message
        """
        username = session.get('username')
        user_id = session.get('user_id')
        
        if not username or not user_id:
            logger.warning(f"WebSocket connection attempt without authentication")
            return False  # Reject connection
        
        logger.info(f"WebSocket connected: {username}")
        
        # Join user-specific room (for direct messages)
        join_room(f"user:{username}")
        
        # Get player's current room and join it
        game = get_game_fn()
        if game:
            room_id = game.get('location')
            if room_id:
                join_room(f"room:{room_id}")
                logger.info(f"{username} joined room: {room_id}")
        
        # Send welcome message
        emit('connected', {
            'message': 'WebSocket connected',
            'username': username
        })
        
        return True
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection."""
        username = session.get('username')
        if username:
            logger.info(f"WebSocket disconnected: {username}")
            
            # Leave all rooms (automatic, but explicit for clarity)
            leave_room(f"user:{username}")
            
            # Get room from state and leave it
            game = get_game_fn()
            if game:
                room_id = game.get('location')
                if room_id:
                    leave_room(f"room:{room_id}")
    
    @socketio.on('command')
    def handle_command(data):
        """
        Handle game command.
        
        Clean command handler:
        1. Extract command
        2. Process via game engine
        3. Save game state
        4. Emit response
        5. Broadcast room events if needed
        
        Args:
            data: Dict with 'command' key
        """
        username = session.get('username')
        user_id = session.get('user_id')
        
        if not username or not user_id:
            emit('error', {'message': 'Not authenticated'})
            return
        
        command = data.get('command', '').strip()
        request_id = data.get('id')  # Optional request ID for response matching
        
        if not command:
            emit('error', {
                'message': 'Empty command',
                'id': request_id
            })
            return
        
        try:
            # Get game state
            game = get_game_fn()
            if not game:
                emit('error', {
                    'message': 'No game state found',
                    'id': request_id
                })
                return
            
            # Create broadcast function for room messages
            def broadcast_fn(room_id, text):
                """Broadcast message to room via SocketIO."""
                socketio.emit('room_message', {
                    'room_id': room_id,
                    'message': text,
                    'message_type': 'system'
                }, room=f"room:{room_id}")
            
            # Get database connection for AI token tracking
            from app import get_db
            conn = get_db()
            
            try:
                # Process command via game engine
                from app import list_active_players
                response, game = handle_command_fn(
                    command,
                    game,
                    username=username,
                    user_id=user_id,
                    db_conn=conn,
                    broadcast_fn=broadcast_fn,
                    who_fn=list_active_players,
                )
                
                # Save game state
                save_game_fn(game)
                
                # Emit command response
                emit('command_response', {
                    'command': command,
                    'response': response,
                    'id': request_id
                })
                
                # Handle room changes (if player moved)
                new_room_id = game.get('location')
                old_room_id = data.get('current_room')
                
                if new_room_id and new_room_id != old_room_id:
                    # Player moved to new room
                    if old_room_id:
                        leave_room(f"room:{old_room_id}")
                    join_room(f"room:{new_room_id}")
                    
                    emit('room_changed', {
                        'old_room': old_room_id,
                        'new_room': new_room_id
                    })
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error handling command '{command}' for {username}: {e}", exc_info=True)
            emit('error', {
                'message': f'Error processing command: {str(e)}',
                'id': request_id
            })
    
    @socketio.on('ping')
    def handle_ping(data):
        """Handle ping (keep-alive)."""
        emit('pong', {'timestamp': data.get('timestamp')})
    
    logger.info("SocketIO handlers registered")

