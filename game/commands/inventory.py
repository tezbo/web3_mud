"""
Inventory Commands

Handles commands related to inventory management:
- inventory (i, inv): List items, optionally sorted
- take (get): Pick up items
- drop: Drop items
- bury: Permanently remove items
"""

from typing import Tuple, Dict, Any, List, Optional
from game.models.player import Player
from game.world.manager import WorldManager
from game.utils import colors
from game.state import (
    QUEST_SPECIFIC_ITEMS,
    BURIED_ITEMS,
    ROOM_STATE,
    GAME_TIME
)
from game.utils.text import number_to_words
from game.systems.inventory import (
    render_item_name,
    match_item_name_in_collection,
    is_item_buryable,
    get_item_def,
    pluralize_item_name
)

def handle_inventory_command(
    verb: str,
    tokens: List[str],
    game: Dict[str, Any],
    username: str,
    user_id: Optional[str] = None,
    db_conn: Optional[Any] = None,
    broadcast_fn: Optional[Any] = None,
    who_fn: Optional[Any] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Handle 'inventory' command.
    Usage: inventory [sort <name|weight|type>]
    """
    # Bridge to OO System
    player = Player(username or "adventurer")
    player.load_from_state(game)
    
    response_parts = []
    
    # Check for sort argument
    sort_by = None
    if len(tokens) >= 3 and tokens[1] == "sort":
        sort_by = tokens[2].lower()
    
    # Show items
    if player.inventory:
        items = list(player.inventory)
        
        # Apply sorting
        if sort_by == "name":
            items.sort(key=lambda x: x.get_display_name())
            response_parts.append(f"[Sorted by name]")
        elif sort_by == "weight":
            items.sort(key=lambda x: x.total_weight, reverse=True)
            response_parts.append(f"[Sorted by weight]")
        elif sort_by == "type":
            items.sort(key=lambda x: (x.item_type, x.get_display_name()))
            response_parts.append(f"[Sorted by type]")
            
        # Group items by name (if not sorting by weight/unique properties that split groups)
        # For now, we'll keep the grouping logic but apply it to the sorted list
        # Note: Grouping might undo sorting visuals if we group non-adjacent items, 
        # but usually we group identical items which should sort together anyway.
        
        from collections import Counter
        item_names = [item.get_display_name() for item in items]
        counts = Counter(item_names)
        
        # Re-construct list preserving sort order but collapsing duplicates
        seen = set()
        grouped_items = []
        
        for item in items:
            name = item.get_display_name()
            if name in seen:
                continue
            seen.add(name)
            
            count = counts[name]
            if count > 1:
                plural_name = pluralize_item_name(name, count)
                count_str = number_to_words(count)
                grouped_items.append(f"{count_str} {plural_name}")
            else:
                # Use singular form with article
                if name.lower().startswith(('a', 'e', 'i', 'o', 'u')):
                    grouped_items.append(f"an {name}")
                else:
                    grouped_items.append(f"a {name}")
        
        if len(grouped_items) == 1:
            response_parts.append(f"You are carrying {grouped_items[0]}.")
        elif len(grouped_items) == 2:
            response_parts.append(f"You are carrying {grouped_items[0]} and {grouped_items[1]}.")
        else:
            response_parts.append("You are carrying: " + ", ".join(grouped_items[:-1]) + f", and {grouped_items[-1]}.")
            
    else:
        response_parts.append("You are not carrying anything.")
    
    # Show currency in wallet
    from economy.currency import get_currency, format_currency
    currency = get_currency(game)
    currency_str = format_currency(currency)
    
    # Only show wallet if player has currency
    if currency_str != "no currency":
        response_parts.append(f"Wallet: You have {currency_str}.")
    
    return "\n".join(response_parts), game


def handle_take_command(
    verb: str,
    tokens: List[str],
    game: Dict[str, Any],
    username: str,
    user_id: Optional[str] = None,
    db_conn: Optional[Any] = None,
    broadcast_fn: Optional[Any] = None,
    who_fn: Optional[Any] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Handle 'take' command."""
    if len(tokens) < 2:
        return "Take what?", game

    item_input = " ".join(tokens[1:]).lower()
    loc_id = game.get("location", "town_square")
    
    wm = WorldManager.get_instance()
    room = wm.get_room(loc_id)
    player = Player(username or "adventurer")
    player.load_from_state(game)
    
    response = ""
    
    if not room:
        response = "You reach for something that isn't really there."
    elif item_input in ["all", "everything"]:
        # Take all items
        items_to_take = list(room.items) # Copy list as we'll modify it
        taken_names = []
        full = False
        
        for item in items_to_take:
            success, msg = player.take_item(item.oid, room, game_state_for_quests=game)
            if success:
                taken_names.append(item.get_display_name())
            elif "fall over" in msg: # Weight limit
                full = True
                break
        
        if taken_names:
            if len(taken_names) == 1:
                response = f"You pick up the {taken_names[0]}."
            else:
                response = f"You pick up: {', '.join(taken_names)}."
            
            if full:
                response += "\nYou can't carry any more."
        else:
            if full:
                response = "You can't carry any more."
            else:
                response = "There's nothing here to pick up."
    else:
        # Take specific item
        target_oid = None
        
        # 1. Check standard items in room
        for item in room.items:
            # Exact match or partial match
            if item_input == item.name.lower() or item_input in [adj.lower() for adj in item.adjectives] or item_input in item.name.lower().split():
                target_oid = item.oid
                break
        
        # 2. Check quest items (legacy)
        if not target_oid:
            for item_id, quest_item_data in QUEST_SPECIFIC_ITEMS.items():
                if quest_item_data.get("room_id") == loc_id and quest_item_data.get("owner_username") == username:
                    # Check name match (need item def)
                    item_def = get_item_def(item_id)
                    name = item_def.get("name", "").lower()
                    if item_input in name:
                        target_oid = item_id
                        break
        
        if target_oid:
            success, msg = player.take_item(target_oid, room, game_state_for_quests=game)
            response = msg
        else:
            response = f"You don't see '{item_input}' here."
    
    # Sync inventory back
    game["inventory"] = [i.oid for i in player.inventory]
    return response, game


def handle_drop_command(
    verb: str,
    tokens: List[str],
    game: Dict[str, Any],
    username: str,
    user_id: Optional[str] = None,
    db_conn: Optional[Any] = None,
    broadcast_fn: Optional[Any] = None,
    who_fn: Optional[Any] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Handle 'drop' command."""
    if len(tokens) < 2:
        return "Drop what?", game

    item_input = " ".join(tokens[1:]).lower()
    loc_id = game.get("location", "town_square")
    
    wm = WorldManager.get_instance()
    room = wm.get_room(loc_id)
    player = Player(username or "adventurer")
    player.load_from_state(game)
    
    response = ""
    
    if not room:
        response = "You feel disoriented for a moment."
    elif not player.inventory:
        response = "You're not carrying anything."
    elif item_input in ["all", "everything"]:
            # Drop all
            items_to_drop = list(player.inventory)
            dropped_names = []
            for item in items_to_drop:
                success, msg = player.drop_item(item.oid, room)
                if success:
                    dropped_names.append(item.get_display_name())
            
            if dropped_names:
                if len(dropped_names) == 1:
                    response = f"You drop the {dropped_names[0]}."
                else:
                    response = f"You drop: {', '.join(dropped_names)}."
            else:
                response = "You couldn't drop anything."
    else:
        # Find item in inventory
        target_oid = None
        for item in player.inventory:
                # Exact match or partial match
                if item_input == item.name.lower() or item_input in [adj.lower() for adj in item.adjectives] or item_input in item.name.lower().split():
                    target_oid = item.oid
                    break
        
        if target_oid:
            success, msg = player.drop_item(target_oid, room)
            response = msg
        else:
            response = f"You don't have a '{item_input}'."
            
    # Sync inventory back
    game["inventory"] = [i.oid for i in player.inventory]
    return response, game


def handle_bury_command(
    verb: str,
    tokens: List[str],
    game: Dict[str, Any],
    username: str,
    user_id: Optional[str] = None,
    db_conn: Optional[Any] = None,
    broadcast_fn: Optional[Any] = None,
    who_fn: Optional[Any] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Handle 'bury' command."""
    if len(tokens) < 2:
        return "Bury what?", game

    item_input = " ".join(tokens[1:]).lower()
    loc_id = game.get("location", "town_square")
    inventory = game.get("inventory", [])
    
    wm = WorldManager.get_instance()
    
    if not wm.get_room(loc_id): # Access via WORLD dict check in legacy code, here via manager
         # Fallback to legacy check if needed, but manager is safer
         pass

    # Legacy logic used ROOM_STATE directly, we should respect that for consistency
    # or use Room object if possible. For bury, it modifies ROOM_STATE["items"] directly
    # which is the persistence layer.
    
    # We'll stick to the legacy implementation logic for now to ensure compatibility
    # with how items are stored (strings in lists).
    
    if loc_id not in ROOM_STATE and loc_id in wm.rooms:
         ROOM_STATE[loc_id] = {"items": []}
    
    if loc_id not in ROOM_STATE:
        return "You feel disoriented for a moment.", game

    room_state = ROOM_STATE.setdefault(loc_id, {"items": []})
    room_items = room_state["items"]
    
    response = ""
    
    if item_input in ["all", "everything"]:
        # Bury all buryable items in the room
        buried_items = []
        non_buryable_items = []
        current_tick = GAME_TIME.get("tick", 0)
        current_minutes = GAME_TIME.get("minutes", 0)
        
        # Initialize buried items tracking for this room if needed
        if loc_id not in BURIED_ITEMS:
            BURIED_ITEMS[loc_id] = []
        
        # Check each item in the room
        for item_id in room_items[:]:  # Use slice to iterate over copy
            can_bury, reason = is_item_buryable(item_id)
            if can_bury:
                buried_items.append(item_id)
                room_items.remove(item_id)
                # Add to buried items with timestamp
                BURIED_ITEMS[loc_id].append({
                    "item_id": item_id,
                    "buried_at_tick": current_tick,
                    "buried_at_minutes": current_minutes,
                })
            else:
                non_buryable_items.append(item_id)
        
        room_state["items"] = room_items
        
        # Build response
        if buried_items:
            item_names = [render_item_name(item_id) for item_id in buried_items]
            if len(buried_items) == 1:
                response = f"You dig a small hole and bury the {item_names[0]}, covering it with earth. You can recover it within a day."
            else:
                response = f"You dig a hole and bury {len(buried_items)} items, covering them with earth. You can recover them within a day.\nBuried: {', '.join(item_names)}."
            
            if non_buryable_items:
                non_buryable_names = [render_item_name(item_id) for item_id in non_buryable_items]
                response += f"\n(You cannot bury: {', '.join(non_buryable_names)}.)"
            
            # Broadcast to room if other players are present
            if broadcast_fn is not None:
                actor_name = username or "Someone"
                if len(buried_items) == 1:
                    broadcast_message = f"{actor_name} digs a hole and buries something in the ground."
                else:
                    broadcast_message = f"{actor_name} digs a hole and buries several items in the ground."
                broadcast_fn(loc_id, broadcast_message)
        else:
            if non_buryable_items:
                non_buryable_names = [render_item_name(item_id) for item_id in non_buryable_items]
                response = f"There's nothing buryable here. ({', '.join(non_buryable_names)} cannot be buried.)"
            else:
                response = "There's nothing here to bury."
    else:
        # Bury a specific item - try inventory first, then room
        matched_item = None
        source = None
        
        # Check inventory
        matched_item = match_item_name_in_collection(item_input, inventory)
        if matched_item:
            source = "inventory"
        else:
            # Check room
            matched_item = match_item_name_in_collection(item_input, room_items)
            if matched_item:
                source = "room"
        
        if not matched_item:
            response = f"You don't see a '{item_input}' here to bury."
        else:
            # Check if item is buryable
            can_bury, reason = is_item_buryable(matched_item)
            
            if not can_bury:
                response = reason
            else:
                # Remove from source
                if source == "inventory":
                    inventory.remove(matched_item)
                    game["inventory"] = inventory
                else:
                    room_items.remove(matched_item)
                    room_state["items"] = room_items
                
                # Add to buried items
                current_tick = GAME_TIME.get("tick", 0)
                current_minutes = GAME_TIME.get("minutes", 0)
                
                if loc_id not in BURIED_ITEMS:
                    BURIED_ITEMS[loc_id] = []
                    
                BURIED_ITEMS[loc_id].append({
                    "item_id": matched_item,
                    "buried_at_tick": current_tick,
                    "buried_at_minutes": current_minutes,
                })
                
                item_name = render_item_name(matched_item)
                response = f"You dig a small hole and bury the {item_name}, covering it with earth. You can recover it within a day."
                
                # Broadcast
                if broadcast_fn is not None:
                    actor_name = username or "Someone"
                    broadcast_fn(loc_id, f"{actor_name} digs a hole and buries a {item_name}.")

    return response, game
