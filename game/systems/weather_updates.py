"""
Automatic background weather status updates for players and NPCs.

This module handles periodic weather status updates independent of player commands,
ensuring that weather effects accumulate over time just like time itself moves forward.
"""
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


def update_all_weather_statuses(
    get_active_games_fn: Callable[[], Dict[str, Dict[str, Any]]],
    get_active_sessions_fn: Callable[[], Dict[str, Dict[str, Any]]],
    save_game_fn: Callable[[Dict[str, Any]], None],
    get_npc_state_fn: Callable[[], Dict[str, Dict[str, Any]]] = None,
) -> None:
    """
    Update weather status for all active players and NPCs.
    This is called periodically by the background event system.
    
    Args:
        get_active_games_fn: Function that returns {username: game_state} dict
        get_active_sessions_fn: Function that returns {username: session_info} dict
        save_game_fn: Function to save a game state (takes game dict)
        get_npc_state_fn: Optional function to get NPC_STATE dict
    """
    try:
        from game.systems.atmospheric_manager import get_atmospheric_manager
        from game.models.player import Player
        from game.world.manager import WorldManager
        from game_engine import NPC_STATE
        
        atmos = get_atmospheric_manager()
        
        # Update all active players
        active_games = get_active_games_fn()
        active_sessions = get_active_sessions_fn()
        
        updated_players = 0
        for username, game in active_games.items():
            # Only update players with active sessions
            if username not in active_sessions:
                continue
                
            try:
                # Create Player object from game state
                player_obj = Player(username or "adventurer")
                player_obj.load_from_state(game)
                
                # Update weather status
                if player_obj.location:
                    # Force first update if last_update_tick is 0
                    if player_obj.weather_status.last_update_tick == 0:
                        player_obj.weather_status.last_update_tick = -1
                    
                    player_obj.update_weather_status(atmos)
                    
                    # Sync weather status back to game state
                    game["weather_status"] = player_obj.weather_status.to_dict()
                    
                    # Save the game state (this is a lightweight operation)
                    save_game_fn(game)
                    updated_players += 1
                    
            except Exception as e:
                logger.warning(f"Error updating weather for player {username}: {e}", exc_info=True)
        
        # Update all NPCs
        updated_npcs = 0
        wm = WorldManager.get_instance()
        
        # Use provided NPC state function or fall back to global NPC_STATE
        npc_state = get_npc_state_fn() if get_npc_state_fn else NPC_STATE
        
        for npc_id in npc_state.keys():
            try:
                npc = wm.get_npc(npc_id)
                if npc and hasattr(npc, 'update_weather_status'):
                    # Ensure NPC has location set
                    if not npc.location and npc_id in npc_state:
                        room_id = npc_state[npc_id].get("room")
                        if room_id:
                            room = wm.get_room(room_id)
                            if room:
                                npc.location = room
                    
                    # Update weather status
                    if npc.location:
                        # Force first update if last_update_tick is 0
                        if npc.weather_status.last_update_tick == 0:
                            npc.weather_status.last_update_tick = -1
                        
                        npc.update_weather_status(atmos)
                        
                        # Sync weather_status back to NPC_STATE
                        if npc_id in npc_state:
                            if "weather_status" not in npc_state[npc_id]:
                                npc_state[npc_id]["weather_status"] = {}
                            npc_state[npc_id]["weather_status"] = npc.weather_status.to_dict()
                            
                        updated_npcs += 1
                        
            except Exception as e:
                logger.warning(f"Error updating weather for NPC {npc_id}: {e}", exc_info=True)
        
        if updated_players > 0 or updated_npcs > 0:
            logger.debug(f"Updated weather status for {updated_players} players and {updated_npcs} NPCs")
            
    except Exception as e:
        logger.error(f"Error in update_all_weather_statuses: {e}", exc_info=True)

