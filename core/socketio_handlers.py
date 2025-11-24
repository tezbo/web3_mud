"""
Flask-SocketIO event handlers.

Clean, maintainable WebSocket handlers that integrate with:
- Game engine (command processing)
- Event bus (real-time events)
- State manager (player state)
"""

import logging
from datetime import datetime, timedelta
from flask import session
from flask_socketio import emit, join_room, leave_room
from core.event_bus import get_event_bus, EventTypes
from core.state_manager import get_state_manager

logger = logging.getLogger(__name__)

# Track connection state and last activity for idle timeout
# Format: {username: {"last_activity": datetime, "is_connected": bool, "was_connected": bool}}
CONNECTION_STATE = {}


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
        4. Check if reconnect and broadcast to room
        5. Send welcome message
        """
        username = session.get('username')
        user_id = session.get('user_id')
        
        if not username or not user_id:
            logger.warning(f"WebSocket connection attempt without authentication")
            return False  # Reject connection
        
        logger.info(f"WebSocket connected: {username}")
        
        # Check if this is a reconnect (was previously connected)
        is_reconnect = False
        if username in CONNECTION_STATE:
            was_connected = CONNECTION_STATE[username].get("was_connected", False)
            is_reconnect = was_connected
        
        # Update connection state
        CONNECTION_STATE[username] = {
            "last_activity": datetime.now(),
            "is_connected": True,
            "was_connected": True,
            "room_id": room_id  # Track current room for notifications
        }
        
        # Join user-specific room (for direct messages)
        join_room(f"user:{username}")
        
        # Get player's current room and join it
        game = get_game_fn()
        room_id = None
        if game:
            room_id = game.get('location')
            if room_id:
                join_room(f"room:{room_id}")
                logger.info(f"{username} joined room: {room_id}")
        
        # If reconnect, broadcast to room
        if is_reconnect and room_id:
            reconnect_msg = f"{username} springs to life."
            socketio.emit('room_message', {
                'room_id': room_id,
                'message': reconnect_msg,
                'message_type': 'system'
            }, room=f"room:{room_id}")
            logger.info(f"Broadcasted reconnect message for {username} in {room_id}")
        
        # Send welcome message
        emit('connected', {
            'message': 'WebSocket connected',
            'username': username,
            'is_reconnect': is_reconnect
        })
        
        return True
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection."""
        username = session.get('username')
        if username:
            logger.info(f"WebSocket disconnected: {username}")
            
            # Get room from state before leaving
            game = get_game_fn()
            room_id = None
            if game:
                room_id = game.get('location')
            
            # Broadcast disconnect message to room
            if room_id:
                disconnect_msg = f"{username} slowly turns to stone."
                socketio.emit('room_message', {
                    'room_id': room_id,
                    'message': disconnect_msg,
                    'message_type': 'system'
                }, room=f"room:{room_id}")
                logger.info(f"Broadcasted disconnect message for {username} in {room_id}")
            
            # Update connection state
            if username in CONNECTION_STATE:
                CONNECTION_STATE[username]["is_connected"] = False
                # Keep was_connected=True so we know it's a reconnect next time
            
            # Leave all rooms (automatic, but explicit for clarity)
            leave_room(f"user:{username}")
            
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
                # Check for idle timeout BEFORE updating (check previous activity)
                if username in CONNECTION_STATE:
                    last_activity = CONNECTION_STATE[username].get("last_activity")
                    if last_activity:
                        idle_time = datetime.now() - last_activity
                        if idle_time > timedelta(minutes=15):
                            # Auto-logout due to idle timeout
                            room_id = game.get('location')
                            if room_id:
                                logout_msg = f"{username} has been logged out automatically for being idle too long."
                                socketio.emit('room_message', {
                                    'room_id': room_id,
                                    'message': logout_msg,
                                    'message_type': 'system'
                                }, room=f"room:{room_id}")
                            
                            # Save game state before logout
                            save_game_fn(game)
                            
                            # Disconnect the user
                            emit('error', {
                                'message': 'You have been logged out due to inactivity (15 minutes).',
                                'id': request_id
                            })
                            
                            # Update connection state
                            CONNECTION_STATE[username]["is_connected"] = False
                            
                            return
                
                # Update last activity time (after checking, so next check uses this time)
                if username in CONNECTION_STATE:
                    CONNECTION_STATE[username]["last_activity"] = datetime.now()
                else:
                    CONNECTION_STATE[username] = {
                        "last_activity": datetime.now(),
                        "is_connected": True,
                        "was_connected": True
                    }
                
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
                    
                    # Update room_id in connection state
                    if username in CONNECTION_STATE:
                        CONNECTION_STATE[username]["room_id"] = new_room_id
                    
                    # Check if user wants system notifications
                    notify_settings = game.get("notify", {})
                    show_notification = notify_settings.get("system", False)
                    
                    emit('room_changed', {
                        'old_room': old_room_id,
                        'new_room': new_room_id,
                        'show_notification': show_notification
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
    
    def start_idle_timeout_checker(socketio, get_game_fn, save_game_fn):
        """
        Start background task to check for idle users and auto-logout.
        
        Args:
            socketio: Flask-SocketIO instance
            get_game_fn: Function to get game state
            save_game_fn: Function to save game state
        """
        def idle_check_task():
            """Background task to check for idle users."""
            logger.info("Idle timeout checker started")
            
            while True:
                try:
                    current_time = datetime.now()
                    idle_users = []
                    
                    # Check all users in CONNECTION_STATE
                    for username, state in list(CONNECTION_STATE.items()):
                        if not state.get("is_connected", False):
                            continue  # Skip users who are already disconnected
                        
                        last_activity = state.get("last_activity")
                        if last_activity:
                            idle_time = current_time - last_activity
                            if idle_time > timedelta(minutes=15):
                                idle_users.append(username)
                    
                    # Auto-logout idle users
                    for username in idle_users:
                        try:
                            state = CONNECTION_STATE.get(username, {})
                            room_id = state.get("room_id")
                            
                            if room_id:
                                logout_msg = f"{username} has been logged out automatically for being idle too long."
                                socketio.emit('room_message', {
                                    'room_id': room_id,
                                    'message': logout_msg,
                                    'message_type': 'system'
                                }, room=f"room:{room_id}")
                                logger.info(f"Auto-logged out {username} for inactivity")
                            
                            # Try to save game state (may fail if no session, but that's ok)
                            try:
                                # We can't call get_game_fn() in background task without session
                                # Game state will be saved on next command attempt
                                pass
                            except Exception:
                                pass
                            
                            # Send logout message to user
                            socketio.emit('error', {
                                'message': 'You have been logged out due to inactivity (15 minutes). Please refresh the page.'
                            }, room=f"user:{username}")
                            
                            # Update connection state (next command will be rejected)
                            CONNECTION_STATE[username]["is_connected"] = False
                            
                        except Exception as e:
                            logger.error(f"Error auto-logging out {username}: {e}", exc_info=True)
                    
                    # Sleep for 1 minute before next check
                    socketio.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Error in idle timeout checker: {e}", exc_info=True)
                    socketio.sleep(60)  # Wait 1 minute on error
        
        # Start the background task
        socketio.start_background_task(idle_check_task)
        logger.info("Idle timeout checker started")
    
    # Start idle timeout checker
    start_idle_timeout_checker(socketio, get_game_fn, save_game_fn)
    
    logger.info("SocketIO handlers registered")

