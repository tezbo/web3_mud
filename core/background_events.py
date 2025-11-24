"""
Background event generator for NPC actions and ambiance.

Periodically generates NPC actions and ambiance messages and emits them
via Flask-SocketIO to all connected players in rooms.
"""

import logging
import random
from datetime import datetime, timedelta
from core.redis_manager import CacheKeys, get_cached_state, set_cached_state

logger = logging.getLogger(__name__)


def start_background_event_generator(socketio, get_game_setting_fn=None, 
                                     get_all_rooms_fn=None,
                                     get_all_npc_actions_fn=None,
                                     process_ambiance_fn=None):
    """
    Start background task that generates NPC actions and ambiance events.
    
    Uses Flask-SocketIO's background task system to periodically check
    rooms and emit events to connected players.
    
    Args:
        socketio: Flask-SocketIO instance
        get_game_setting_fn: Function to get game settings
        get_all_rooms_fn: Function to get all room IDs
        get_all_npc_actions_fn: Function to get NPC actions for a room
        process_ambiance_fn: Function to process ambiance for a room
    """
    if not socketio:
        logger.warning("SocketIO not available, background events disabled")
        return
    
    def background_task():
        """Background task loop."""
        logger.info("Background event generator task started")
        
        while True:
            try:
                _generate_events_once(
                    socketio,
                    get_game_setting_fn,
                    get_all_rooms_fn,
                    get_all_npc_actions_fn,
                    process_ambiance_fn
                )
                
                # Sleep for 5 seconds before next check
                socketio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in background event generator: {e}", exc_info=True)
                socketio.sleep(10)  # Wait longer on error
    
    # Start the background task
    socketio.start_background_task(background_task)
    logger.info("Background event generator started")


def _generate_events_once(socketio, get_game_setting_fn, get_all_rooms_fn,
                          get_all_npc_actions_fn, process_ambiance_fn):
    """Generate events for all active rooms (called periodically)."""
    if not get_all_rooms_fn:
        return
    
    # Get all room IDs
    room_ids = get_all_rooms_fn()
    if not room_ids:
        return
    
    current_time = datetime.now()
    
    # Get intervals from settings
    npc_interval_min = float((get_game_setting_fn("npc_action_interval_min", "30") or "30"))
    npc_interval_max = float((get_game_setting_fn("npc_action_interval_max", "60") or "60"))
    ambiance_interval_min = float((get_game_setting_fn("ambiance_interval_min", "120") or "120"))
    ambiance_interval_max = float((get_game_setting_fn("ambiance_interval_max", "240") or "240"))
    
    # Check each room for events
    for room_id in room_ids:
        try:
            # Check if room has active players (via Redis cache)
            from core.redis_manager import get_cache_connection
            cache = get_cache_connection()
            room_players_key = CacheKeys.room_players(room_id)
            players = cache.smembers(room_players_key)
            
            if not players or len(players) == 0:
                # Skip rooms with no active players
                continue
            
            # Get or initialize room event times (stored in Redis)
            room_key = f"room:{room_id}:last_events"
            room_events = get_cached_state(room_key, {})
            
            if not room_events:
                room_events = {
                    "last_npc_action_time": current_time.isoformat(),
                    "last_ambiance_time": current_time.isoformat(),
                }
            
            # Check for NPC actions
            last_npc_time_str = room_events.get("last_npc_action_time")
            if last_npc_time_str:
                try:
                    last_npc_time = datetime.fromisoformat(last_npc_time_str)
                except (ValueError, TypeError):
                    last_npc_time = None
            else:
                last_npc_time = None
            
            # If no last time recorded, initialize to now (don't trigger immediately)
            if last_npc_time is None:
                room_events["last_npc_action_time"] = current_time.isoformat()
                set_cached_state(room_key, room_events, ttl=3600)
                last_npc_time = current_time
                
            elapsed_npc_seconds = (current_time - last_npc_time).total_seconds()
            
            # Only trigger if enough time has passed (using random interval between min and max)
            # This ensures events happen at varied intervals, not exactly at min interval
            trigger_interval = random.uniform(npc_interval_min, npc_interval_max)
            
            if elapsed_npc_seconds >= trigger_interval and get_all_npc_actions_fn:
                npc_actions = get_all_npc_actions_fn(room_id)
                if npc_actions:
                    # Choose one random NPC action
                    npc_id, action = random.choice(list(npc_actions.items()))
                    action_text = f"[NPC]{action}[/NPC]"
                    
                    # Emit directly via SocketIO to room
                    socketio.emit('room_message', {
                        'room_id': room_id,
                        'message': action_text,
                        'message_type': 'npc'
                    }, room=f"room:{room_id}")
                    
                    logger.debug(f"Emitted NPC action to room {room_id} after {elapsed_npc_seconds:.1f}s (interval: {trigger_interval:.1f}s): {action[:50]}...")
                    
                    # Update last NPC action time to NOW (not future time)
                    room_events["last_npc_action_time"] = current_time.isoformat()
                    set_cached_state(room_key, room_events, ttl=3600)
            
            # Check for ambiance
            last_ambiance_time_str = room_events.get("last_ambiance_time")
            if last_ambiance_time_str:
                try:
                    last_ambiance_time = datetime.fromisoformat(last_ambiance_time_str)
                except (ValueError, TypeError):
                    last_ambiance_time = None
            else:
                last_ambiance_time = None
            
            # If no last time recorded, initialize to now (don't trigger immediately)
            if last_ambiance_time is None:
                room_events["last_ambiance_time"] = current_time.isoformat()
                set_cached_state(room_key, room_events, ttl=3600)
                last_ambiance_time = current_time
                
            elapsed_ambiance_seconds = (current_time - last_ambiance_time).total_seconds()
            
            # Only trigger if enough time has passed (using random interval between min and max)
            # This ensures events happen at varied intervals, not exactly at min interval
            trigger_interval = random.uniform(ambiance_interval_min, ambiance_interval_max)
            
            if elapsed_ambiance_seconds >= trigger_interval and process_ambiance_fn:
                # Create a minimal game state for ambiance processing
                sample_game = {"location": room_id}
                
                # Process ambiance - it returns a list of messages
                ambiance_msgs = process_ambiance_fn(sample_game, broadcast_fn=None)
                
                if ambiance_msgs and len(ambiance_msgs) > 0:
                    # Get the first message (usually there's just one)
                    ambiance_msg = ambiance_msgs[0] if isinstance(ambiance_msgs, list) else ambiance_msgs
                    
                    # Ensure it's formatted correctly
                    if not ambiance_msg.startswith('[AMBIANCE]'):
                        ambiance_msg = f"[AMBIANCE]{ambiance_msg}[/AMBIANCE]"
                    
                    # Emit directly via SocketIO to room
                    socketio.emit('room_message', {
                        'room_id': room_id,
                        'message': ambiance_msg,
                        'message_type': 'ambiance'
                    }, room=f"room:{room_id}")
                    
                    logger.debug(f"Emitted ambiance to room {room_id} after {elapsed_ambiance_seconds:.1f}s (interval: {trigger_interval:.1f}s): {ambiance_msg[:50]}...")
                    
                    # Update last ambiance time to NOW (not future time)
                    room_events["last_ambiance_time"] = current_time.isoformat()
                    set_cached_state(room_key, room_events, ttl=3600)
                
        except Exception as e:
            logger.error(f"Error generating events for room {room_id}: {e}", exc_info=True)
