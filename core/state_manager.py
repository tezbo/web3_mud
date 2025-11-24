"""
Unified state manager for game state.

Provides single source of truth with:
- Redis cache for hot data (fast access)
- Database for persistence (cold data)
- Automatic sync between cache and database
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from core.redis_manager import (
    get_cache_connection,
    CacheKeys,
    get_cached_state,
    set_cached_state,
    delete_cached_state,
)
from core.event_bus import get_event_bus, EventTypes

logger = logging.getLogger(__name__)


class GameStateManager:
    """
    Manages game state with Redis cache + database persistence.
    
    Strategy:
    - Hot data: Redis (player state, room state)
    - Cold data: Database (persistence, history)
    - Sync: Periodic writes from Redis to database
    """
    
    def __init__(self, db_get_fn=None, db_save_fn=None):
        """
        Initialize state manager.
        
        Args:
            db_get_fn: Function to get game state from database (username) -> dict
            db_save_fn: Function to save game state to database (game_state) -> None
        """
        try:
            self._cache = get_cache_connection()
        except Exception as e:
            logger.warning(f"Could not connect to Redis cache: {e}. StateManager will use database only.")
            self._cache = None
        self._db_get = db_get_fn
        self._db_save = db_save_fn
        try:
            self._event_bus = get_event_bus()
        except Exception as e:
            logger.warning(f"Could not initialize event bus: {e}. Events will be disabled.")
            self._event_bus = None
    
    def get_player_state(self, username: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get player's game state.
        
        Args:
            username: Player username
            use_cache: Whether to use cache (default True)
            
        Returns:
            Game state dict or None if not found
        """
        # Try cache first
        if use_cache:
            cached = get_cached_state(CacheKeys.player_state(username))
            if cached:
                return cached
        
        # Fall back to database
        if self._db_get:
            try:
                state = self._db_get(username)
                if state:
                    # Cache it for next time
                    set_cached_state(CacheKeys.player_state(username), state, ttl=900)
                    # Also cache location
                    if "location" in state:
                        set_cached_state(CacheKeys.player_location(username), state["location"], ttl=900)
                    return state
            except Exception as e:
                logger.error(f"Error loading player state from DB for {username}: {e}")
        
        return None
    
    def save_player_state(self, username: str, state: Dict[str, Any], 
                         sync_to_db: bool = True, use_cache: bool = True) -> bool:
        """
        Save player's game state.
        
        Args:
            username: Player username
            state: Game state dict
            sync_to_db: Whether to immediately sync to database (default True)
            use_cache: Whether to update cache (default True)
            
        Returns:
            True if successful
        """
        success = True
        
        # Update cache
        if use_cache and self._cache:
            try:
                set_cached_state(CacheKeys.player_state(username), state, ttl=900)
                # Also cache location separately for quick room queries
                if "location" in state:
                    set_cached_state(CacheKeys.player_location(username), state["location"], ttl=900)
                    # Update room player set
                    self._update_room_players(state["location"], username)
            except Exception as e:
                logger.error(f"Error caching player state for {username}: {e}")
                success = False
        
        # Sync to database
        if sync_to_db and self._db_save:
            try:
                # Pass username and state to db_save function
                self._db_save(username, state)
            except Exception as e:
                logger.error(f"Error saving player state to DB for {username}: {e}")
                # Don't fail entirely if DB save fails (cache is still updated)
                # This allows graceful degradation
        
        # Emit state changed event
        if self._event_bus:
            try:
                self._event_bus.publish_user(
                    username,
                    EventTypes.SYSTEM_MESSAGE,
                    {"message_type": "state_update"}
                )
            except Exception as e:
                logger.debug(f"Error emitting state update event: {e}")
        
        return success
    
    def get_room_state(self, room_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get room state (items, NPCs, etc.).
        
        Args:
            room_id: Room ID
            use_cache: Whether to use cache
            
        Returns:
            Room state dict (defaults to empty dict if not found)
        """
        if use_cache:
            cached = get_cached_state(CacheKeys.room_state(room_id))
            if cached:
                return cached
        
        # Fall back to default room state
        # TODO: Load from database or WORLD definition if needed
        return {}
    
    def save_room_state(self, room_id: str, state: Dict[str, Any], 
                       use_cache: bool = True) -> bool:
        """
        Save room state.
        
        Args:
            room_id: Room ID
            state: Room state dict
            use_cache: Whether to update cache
            
        Returns:
            True if successful
        """
        if use_cache:
            try:
                set_cached_state(CacheKeys.room_state(room_id), state, ttl=3600)  # 1 hour TTL
                return True
            except Exception as e:
                logger.error(f"Error caching room state for {room_id}: {e}")
                return False
        return True
    
    def get_room_players(self, room_id: str) -> List[str]:
        """
        Get list of player usernames in a room.
        
        Args:
            room_id: Room ID
            
        Returns:
            List of usernames
        """
        if not self._cache:
            return []
        try:
            players = self._cache.smembers(CacheKeys.room_players(room_id))
            return list(players) if players else []
        except Exception as e:
            logger.error(f"Error getting room players for {room_id}: {e}")
            return []
    
    def _update_room_players(self, room_id: str, username: str) -> None:
        """
        Update room player set (internal helper).
        
        Args:
            room_id: Room ID
            username: Player username
        """
        try:
            key = CacheKeys.room_players(room_id)
            # Add player to room set
            self._cache.sadd(key, username)
            # Set expiry on the set (expires if no players for 1 hour)
            self._cache.expire(key, 3600)
        except Exception as e:
            logger.debug(f"Error updating room players: {e}")
    
    def remove_player_from_room(self, room_id: str, username: str) -> None:
        """
        Remove player from room player set.
        
        Args:
            room_id: Room ID
            username: Player username
        """
        try:
            key = CacheKeys.room_players(room_id)
            self._cache.srem(key, username)
        except Exception as e:
            logger.debug(f"Error removing player from room: {e}")
    
    def move_player(self, username: str, old_room_id: str, new_room_id: str) -> bool:
        """
        Move player between rooms (updates both location and room sets).
        
        Args:
            username: Player username
            old_room_id: Previous room
            new_room_id: New room
            
        Returns:
            True if successful
        """
        try:
            # Update player state location
            state = self.get_player_state(username)
            if state:
                state["location"] = new_room_id
                self.save_player_state(username, state, sync_to_db=False)  # Batch DB writes
            
            # Update room player sets
            if old_room_id:
                self.remove_player_from_room(old_room_id, username)
            self._update_room_players(new_room_id, username)
            
            # Emit move event
            self._event_bus.publish_room(
                new_room_id,
                EventTypes.PLAYER_MOVE,
                {
                    "username": username,
                    "from_room": old_room_id,
                    "to_room": new_room_id,
                }
            )
            
            return True
        except Exception as e:
            logger.error(f"Error moving player {username}: {e}")
            return False
    
    def invalidate_cache(self, username: str) -> None:
        """
        Invalidate cached state for a player.
        
        Args:
            username: Player username
        """
        try:
            delete_cached_state(CacheKeys.player_state(username))
            delete_cached_state(CacheKeys.player_location(username))
            delete_cached_state(CacheKeys.player_session(username))
        except Exception as e:
            logger.debug(f"Error invalidating cache for {username}: {e}")


# Global state manager instance
_state_manager: Optional[GameStateManager] = None


def get_state_manager(db_get_fn=None, db_save_fn=None) -> GameStateManager:
    """
    Get global state manager instance.
    
    Args:
        db_get_fn: Function to get from database
        db_save_fn: Function to save to database
        
    Returns:
        GameStateManager instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = GameStateManager(db_get_fn=db_get_fn, db_save_fn=db_save_fn)
    return _state_manager

