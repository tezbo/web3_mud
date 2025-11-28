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
                                     process_ambiance_fn=None,
                                     process_weather_ambiance_fn=None,
                                     process_decay_fn=None,
                                     update_weather_fn=None,
                                     get_active_games_fn=None):
    """
    Start background task that generates NPC actions and ambiance events.
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
                    process_ambiance_fn,
                    process_weather_ambiance_fn,
                    process_decay_fn,
                    get_active_games_fn
                )
                
                # Update weather status for all players and NPCs (every cycle)
                if update_weather_fn:
                    try:
                        update_weather_fn()
                    except Exception as e:
                        logger.error(f"Error updating weather statuses: {e}", exc_info=True)
                
                # Sleep for 5 seconds before next check
                socketio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in background event generator: {e}", exc_info=True)
                socketio.sleep(10)  # Wait longer on error
    
    # Start the background task
    socketio.start_background_task(background_task)
    logger.info("Background event generator started")


def _generate_events_once(socketio, get_game_setting_fn, get_all_rooms_fn,
                          process_ambiance_fn, process_weather_ambiance_fn=None, process_decay_fn=None, get_active_games_fn=None):
    """Generate events for all active rooms (called periodically)."""
    if not get_all_rooms_fn:
        return
    
    # Get all room IDs
    room_ids = get_all_rooms_fn()
    if not room_ids:
        return
    
    current_time = datetime.now()
    
    # Get configuration settings
    npc_interval_min = 30.0
    npc_interval_max = 60.0
    ambiance_interval_min = 120.0
    ambiance_interval_max = 240.0
    weather_ambiance_interval_min = 120.0  # Weather messages every 2-4 minutes
    weather_ambiance_interval_max = 240.0
    
    if get_game_setting_fn:
        try:
            npc_interval_min = float(get_game_setting_fn("npc_action_interval_min", "30"))
            npc_interval_max = float(get_game_setting_fn("npc_action_interval_max", "60"))
            ambiance_interval_min = float(get_game_setting_fn("ambiance_interval_min", "120"))
            ambiance_interval_max = float(get_game_setting_fn("ambiance_interval_max", "240"))
            weather_ambiance_interval_min = float(get_game_setting_fn("weather_ambiance_interval_min", "120"))
            weather_ambiance_interval_max = float(get_game_setting_fn("weather_ambiance_interval_max", "240"))
        except (ValueError, TypeError):
            pass
    
    # Check each room for events
    # First, get list of rooms with active players from ACTIVE_GAMES (simplest method)
    rooms_with_players = set()
    try:
        # Use provided function if available
        if get_active_games_fn:
            active_games = get_active_games_fn()
            for username, game in active_games.items():
                location = game.get("location")
                if location:
                    rooms_with_players.add(location)
        else:
            # Fallback: Import here to avoid circular import issues
            import sys
            # Try 'app' first, then '__main__'
            app_module = sys.modules.get('app')
            if not app_module or not hasattr(app_module, 'ACTIVE_GAMES'):
                app_module = sys.modules.get('__main__')
                
            if app_module and hasattr(app_module, 'ACTIVE_GAMES'):
                ACTIVE_GAMES = app_module.ACTIVE_GAMES
                for username, game in ACTIVE_GAMES.items():
                    location = game.get("location")
                    if location:
                        rooms_with_players.add(location)
        
        logger.debug(f"[BACKGROUND EVENTS] Found {len(rooms_with_players)} rooms with active players: {list(rooms_with_players)}")
    except Exception as e:
        logger.warning(f"Could not get rooms with players from ACTIVE_GAMES: {e}")
    
    for room_id in room_ids:
        try:
            # Get or initialize room event times (stored in Redis or memory)
            room_key = f"room:{room_id}:last_events"
            room_events = {}
            try:
                room_events = get_cached_state(room_key, {})
            except Exception as e:
                logger.debug(f"Could not get cached state for {room_key}: {e}, using memory fallback")
                room_events = {}

            # If Redis returned empty (or failed), try memory fallback
            if not room_events:
                if not hasattr(_generate_events_once, '_room_events_cache'):
                    _generate_events_once._room_events_cache = {}
                room_events = _generate_events_once._room_events_cache.get(room_key, {})
            
            # Check if room is outdoor BEFORE initializing timers
            from game_engine import WORLD
            room_def_precheck = WORLD.get(room_id, {})
            outdoor_val = room_def_precheck.get("outdoor", False)
            # Robust boolean conversion matching WorldManager
            is_room_outdoor = str(outdoor_val).lower() in ['true', '1', 'yes'] if isinstance(outdoor_val, str) else bool(outdoor_val)
            
            if not room_events:
                # Initialize room events - only set weather timer for outdoor rooms
                room_events = {
                    "last_npc_action_time": current_time.isoformat(),
                    "last_ambiance_time": current_time.isoformat(),
                    "last_npc_weather_reaction_time": (current_time - timedelta(seconds=45)).isoformat(),
                }
                
                # Only initialize weather timer for outdoor rooms
                if is_room_outdoor:
                    past_weather_time = current_time - timedelta(seconds=int(weather_ambiance_interval_max))
                    room_events["last_weather_ambiance_time"] = past_weather_time.isoformat()
                # Indoor rooms: do not initialize weather ambiance timer at all
            
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
                if not set_cached_state(room_key, room_events, ttl=3600):
                    logger.debug(f"Redis set failed for {room_key}, using memory fallback")
                    if not hasattr(_generate_events_once, '_room_events_cache'):
                        _generate_events_once._room_events_cache = {}
                    _generate_events_once._room_events_cache[room_key] = room_events
                last_npc_time = current_time
                
            elapsed_npc_seconds = (current_time - last_npc_time).total_seconds()
            
            # Only trigger if enough time has passed (using random interval between min and max)
            # This ensures events happen at varied intervals, not exactly at min interval
            trigger_interval = random.uniform(npc_interval_min, npc_interval_max)
            
            if elapsed_npc_seconds >= trigger_interval:
                # Get NPCs in the room
                from game_engine import NPC_STATE, WORLD, WEATHER_STATE
                from game.world.manager import WorldManager
                
                # Find NPCs in this room
                room_npc_ids = [npc_id for npc_id, state in NPC_STATE.items() 
                               if state.get("room") == room_id and state.get("alive", True)]
                
                if room_npc_ids:
                    wm = WorldManager.get_instance()
                    possible_actions = {}
                    
                    for npc_id in room_npc_ids:
                        try:
                            npc = wm.get_npc(npc_id)
                            if npc:
                                # Get idle action from NPC object
                                action = npc.get_idle_action(room_id, WEATHER_STATE)
                                if action:
                                    possible_actions[npc_id] = action
                        except Exception as e:
                            logger.warning(f"Error getting idle action for NPC {npc_id}: {e}")
                    
                    if possible_actions:
                        # Choose one random NPC action
                        npc_id, action_data = random.choice(list(possible_actions.items()))
                        
                        # Get NPC name
                        npc = wm.get_npc(npc_id)
                        npc_name = npc.name if npc else "Someone"
                        
                        if isinstance(action_data, dict):
                            action = action_data.get("action", "")
                            vocal = action_data.get("vocal", "")
                            # Format: [NPC]Action[/NPC]\n[NPC]Name says: "Vocal"[/NPC]
                            action_text = f"[NPC]{action}[/NPC]\n[SAY]{npc_name} says: \"{vocal}\"[/SAY]"
                        else:
                            action_text = f"[NPC]{action_data}[/NPC]"
                        
                        # Emit directly via SocketIO to room
                        socketio.emit('room_message', {
                            'room_id': room_id,
                            'message': action_text,
                            'message_type': 'npc'
                        }, room=f"room:{room_id}")
                        
                        logger.debug(f"Emitted NPC action to room {room_id} after {elapsed_npc_seconds:.1f}s (interval: {trigger_interval:.1f}s): {action[:50]}...")
                        
                        # Update last NPC action time to NOW (not future time)
                        room_events["last_npc_action_time"] = current_time.isoformat()
                        if not set_cached_state(room_key, room_events, ttl=3600):
                            if not hasattr(_generate_events_once, '_room_events_cache'):
                                _generate_events_once._room_events_cache = {}
                            _generate_events_once._room_events_cache[room_key] = room_events
            
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
                if not set_cached_state(room_key, room_events, ttl=3600):
                    if not hasattr(_generate_events_once, '_room_events_cache'):
                        _generate_events_once._room_events_cache = {}
                    _generate_events_once._room_events_cache[room_key] = room_events
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
                    
                    # Ensure it's formatted correctly - Client prefers no tags for ambiance
                    # if not ambiance_msg.startswith('[AMBIANCE]'):
                    #     ambiance_msg = f"[AMBIANCE]{ambiance_msg}[/AMBIANCE]"
                    
                    # Emit directly via SocketIO to room
                    socketio.emit('room_message', {
                        'room_id': room_id,
                        'message': ambiance_msg,
                        'message_type': 'ambiance'
                    }, room=f"room:{room_id}")
                    
                    logger.debug(f"Emitted ambiance to room {room_id} after {elapsed_ambiance_seconds:.1f}s (interval: {trigger_interval:.1f}s): {ambiance_msg[:50]}...")
                    
                    # Update last ambiance time to NOW (not future time)
                    room_events["last_ambiance_time"] = current_time.isoformat()
                    if not set_cached_state(room_key, room_events, ttl=3600):
                        if not hasattr(_generate_events_once, '_room_events_cache'):
                            _generate_events_once._room_events_cache = {}
                        _generate_events_once._room_events_cache[room_key] = room_events
            
            # Check for weather ambiance (separate from general ambiance, more frequent)
            # Only process weather ambiance for outdoor rooms
            # Use the outdoor check we already did earlier (is_room_outdoor)
            from game_engine import WEATHER_STATE
            is_outdoor = is_room_outdoor  # Use the check we already did earlier
            
            # CRITICAL: Skip ALL weather ambiance processing for indoor rooms
            # This must happen BEFORE any weather ambiance processing
            if not is_outdoor:
                # Room is indoor - completely skip weather ambiance processing
                # Clear any existing weather ambiance timer to prevent stale triggers
                if "last_weather_ambiance_time" in room_events:
                    logger.info(f"[INDOOR_ROOM] Clearing weather ambiance timer for indoor room: {room_id}")
                    del room_events["last_weather_ambiance_time"]
                if "next_weather_ambiance_interval_seconds" in room_events:
                    del room_events["next_weather_ambiance_interval_seconds"]
                # Save the cleaned state
                if not set_cached_state(room_key, room_events, ttl=3600):
                    if not hasattr(_generate_events_once, '_room_events_cache'):
                        _generate_events_once._room_events_cache = {}
                    _generate_events_once._room_events_cache[room_key] = room_events
                # Do not process weather ambiance for indoor rooms - skip entirely
                logger.debug(f"[INDOOR_ROOM] Skipping weather ambiance processing for indoor room: {room_id}")
            elif is_outdoor and process_weather_ambiance_fn:
                # Room is outdoor and function is available - check timer
                last_weather_ambiance_time_str = room_events.get("last_weather_ambiance_time")
                if last_weather_ambiance_time_str:
                    try:
                        last_weather_ambiance_time = datetime.fromisoformat(last_weather_ambiance_time_str)
                    except (ValueError, TypeError):
                        last_weather_ambiance_time = None
                else:
                    last_weather_ambiance_time = None
                
                # If no last time recorded, initialize to past time to allow immediate trigger
                if last_weather_ambiance_time is None:
                    # Set to past time so first message appears immediately (after first interval)
                    past_time = current_time - timedelta(seconds=int(weather_ambiance_interval_max))
                    room_events["last_weather_ambiance_time"] = past_time.isoformat()
                    if not set_cached_state(room_key, room_events, ttl=3600):
                        if not hasattr(_generate_events_once, '_room_events_cache'):
                            _generate_events_once._room_events_cache = {}
                        _generate_events_once._room_events_cache[room_key] = room_events
                    last_weather_ambiance_time = past_time
                
                elapsed_weather_ambiance_seconds = (current_time - last_weather_ambiance_time).total_seconds()
                
                # Use stored trigger interval or calculate a new one only when triggering
                # Store the required interval so we don't recalculate every check
                stored_interval = room_events.get("next_weather_ambiance_interval_seconds")
                if stored_interval is None:
                    # First time - calculate and store the interval
                    stored_interval = random.uniform(weather_ambiance_interval_min, weather_ambiance_interval_max)
                    room_events["next_weather_ambiance_interval_seconds"] = stored_interval
                
                # Only trigger if enough time has passed (using stored interval)
                if elapsed_weather_ambiance_seconds >= stored_interval:
                    # Create a minimal game state for weather ambiance processing
                    sample_game = {"location": room_id}
                    
                    # Process weather ambiance - it returns a list of messages
                    try:
                        weather_msgs = process_weather_ambiance_fn(sample_game, broadcast_fn=None)
                        
                        if weather_msgs and len(weather_msgs) > 0:
                            # Get the first message (usually there's just one)
                            weather_msg = weather_msgs[0] if isinstance(weather_msgs, list) else weather_msgs
                            
                            # Final safety check: verify room is still outdoor before emitting
                            # (double-check in case something changed)
                            room_def_check = WORLD.get(room_id, {})
                            room_is_outdoor_check = room_def_check.get("outdoor", False)
                            
                            if room_is_outdoor_check:
                                # Wrap weather message in [WEATHER] tags for coloring
                                weather_text = f"[WEATHER]{weather_msg}[/WEATHER]"
                                
                                # Emit directly via SocketIO to room
                                socketio.emit('room_message', {
                                    'room_id': room_id,
                                    'message': weather_text,
                                    'message_type': 'weather'
                                }, room=f"room:{room_id}")
                                
                                logger.info(f"Emitted weather ambiance to room {room_id} after {elapsed_weather_ambiance_seconds:.1f}s")
                            else:
                                # Room is indoor - don't emit but log for debugging
                                logger.warning(f"[BLOCKED] Skipping weather message for indoor room {room_id}: {weather_msg[:50]}...")
                        
                        # Update last weather ambiance time to NOW and calculate next interval
                        room_events["last_weather_ambiance_time"] = current_time.isoformat()
                        room_events["next_weather_ambiance_interval_seconds"] = random.uniform(weather_ambiance_interval_min, weather_ambiance_interval_max)
                        
                        if not set_cached_state(room_key, room_events, ttl=3600):
                            if not hasattr(_generate_events_once, '_room_events_cache'):
                                _generate_events_once._room_events_cache = {}
                            _generate_events_once._room_events_cache[room_key] = room_events
                    except Exception as e:
                        logger.error(f"Error processing weather ambiance for room {room_id}: {e}", exc_info=True)
                    except Exception as e:
                        logger.error(f"Error processing weather ambiance for room {room_id}: {e}", exc_info=True)
            
            # Check for NPC weather reactions (separate from regular NPC actions)
            if is_outdoor:
                last_npc_weather_reaction_time_str = room_events.get("last_npc_weather_reaction_time")
                if last_npc_weather_reaction_time_str:
                    try:
                        last_npc_weather_reaction_time = datetime.fromisoformat(last_npc_weather_reaction_time_str)
                    except (ValueError, TypeError):
                        last_npc_weather_reaction_time = None
                else:
                    last_npc_weather_reaction_time = None
                
                # Initialize to past time if needed
                if last_npc_weather_reaction_time is None:
                    past_time = current_time - timedelta(seconds=45)  # Initialize to allow first reaction
                    room_events["last_npc_weather_reaction_time"] = past_time.isoformat()
                    if not set_cached_state(room_key, room_events, ttl=3600):
                        if not hasattr(_generate_events_once, '_room_events_cache'):
                            _generate_events_once._room_events_cache = {}
                        _generate_events_once._room_events_cache[room_key] = room_events
                    last_npc_weather_reaction_time = past_time
                
                elapsed_npc_weather_seconds = (current_time - last_npc_weather_reaction_time).total_seconds()
                
                # Check for significant weather and NPCs with weather reactions
                weather_type = WEATHER_STATE.get("type", "clear")
                weather_intensity = WEATHER_STATE.get("intensity", "none")
                
                # Only trigger if enough time has passed (30-60 seconds)
                # Relaxed check: Allow clear weather if NPCs have reactions for it
                if elapsed_npc_weather_seconds >= random.uniform(30.0, 60.0):
                    
                    # Get NPCs in room and check for weather reactions
                    from game_engine import NPC_STATE, get_season, get_time_of_day
                    from game.world.manager import WorldManager
                    
                    npc_ids = [npc_id for npc_id, state in NPC_STATE.items() 
                               if state.get("room") == room_id and state.get("alive", True)]
                    
                    if npc_ids:
                        season = get_season()
                        time_of_day = get_time_of_day()
                        wm = WorldManager.get_instance()
                        random.shuffle(npc_ids)
                        
                        # Try each NPC until we find one with a weather reaction
                        for npc_id in npc_ids:
                            try:
                                npc = wm.get_npc(npc_id)
                                if npc:
                                    reaction = npc.get_weather_reaction(WEATHER_STATE, season, time_of_day)
                                    
                                    if npc and hasattr(npc, 'get_weather_reaction'):
                                        # Update NPC weather status first
                                        from game.systems.atmospheric_manager import get_atmospheric_manager
                                        atmos = get_atmospheric_manager()
                                        if npc.location:
                                            npc.update_weather_status(atmos)
                                        
                                        reaction_data = npc.get_weather_reaction(WEATHER_STATE, season, time_of_day)
                                        if reaction_data:
                                            # Handle both new dict format and legacy string format
                                            if isinstance(reaction_data, dict):
                                                action = reaction_data.get("action", "")
                                                vocal = reaction_data.get("vocal", "")
                                                npc_name = npc.name
                                                
                                                # Format: [NPC]Action[/NPC]\n[NPC]Name says: "Vocal"[/NPC]
                                                # We wrap each line individually because the client regex might not support newlines
                                                reaction_text = f"[NPC]{action}[/NPC]\n[SAY]{npc_name} says: \"{vocal}\"[/SAY]"
                                            else:
                                                # Legacy string format fallback
                                                reaction_text = f"[NPC]{reaction_data}[/NPC]"
                                            
                                            # Emit to room
                                            socketio.emit('room_message', {
                                                'room_id': room_id,
                                                'message': reaction_text,
                                                'message_type': 'npc_weather_reaction'
                                            }, room=f"room:{room_id}")
                                            
                                            # Update timer
                                            room_events["last_npc_weather_reaction_time"] = current_time.isoformat()
                                            if not set_cached_state(room_key, room_events, ttl=3600):
                                                if not hasattr(_generate_events_once, '_room_events_cache'):
                                                    _generate_events_once._room_events_cache = {}
                                                _generate_events_once._room_events_cache[room_key] = room_events
                                            break  # Only one reaction per cycle
                            except Exception as e:
                                logger.warning(f"Error getting weather reaction for NPC {npc_id}: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"Error generating events for room {room_id}: {e}", exc_info=True)
