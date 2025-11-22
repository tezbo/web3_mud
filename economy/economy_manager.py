"""
Economy manager for Tiny Web MUD.

Coordinates currency, pricing, and transactions.
"""

from typing import Tuple

from economy.currency import get_gold, add_gold, remove_gold, has_enough_gold, format_gold
from economy.price_table import get_base_price
from economy.merchant_profiles import calculate_final_price
from economy.loot_tables import search_room, loot_npc


def initialize_player_gold(game, starting_amount=None):
    """
    Initialize player's gold if not already set.
    
    Args:
        game: Game state dictionary
        starting_amount: Optional starting gold (uses default if None)
    """
    if "gold" not in game:
        from economy.currency import STARTING_GOLD
        game["gold"] = starting_amount if starting_amount is not None else STARTING_GOLD


def get_item_price(item_key: str, npc_id: str, game: dict) -> int:
    """
    Get the final price for an item from a merchant.
    
    Args:
        item_key: Item identifier
        npc_id: Merchant NPC identifier
        game: Game state (for reputation lookup)
    
    Returns:
        int: Final price in gold
    """
    base_price = get_base_price(item_key)
    if base_price == 0:
        return 0
    
    reputation = game.get("reputation", {}).get(npc_id, 0)
    return calculate_final_price(base_price, npc_id, reputation)


def process_purchase_with_gold(game: dict, item_key: str, quantity: int, 
                              npc_id: str, npc_name: str) -> Tuple[bool, str, int]:
    """
    Process a purchase using gold currency.
    
    Args:
        game: Game state dictionary
        item_key: Item to purchase
        quantity: Quantity to purchase
        npc_id: Merchant NPC identifier
        npc_name: Merchant NPC name (for messages)
    
    Returns:
        Tuple of (success, message, price_per_item)
    """
    # Get price
    price_per_item = get_item_price(item_key, npc_id, game)
    if price_per_item == 0:
        return False, f"{npc_name} doesn't sell that item.", 0
    
    total_price = price_per_item * quantity
    
    # Check if player has enough gold
    if not has_enough_gold(game, total_price):
        current_gold = get_gold(game)
        return False, f"You can't afford that. {npc_name} wants {format_gold(total_price)} for {quantity} {item_key.replace('_', ' ')}{'s' if quantity > 1 else ''} (you have {format_gold(current_gold)}).", 0
    
    # Remove gold
    success, new_total = remove_gold(game, total_price)
    if not success:
        return False, "Error processing payment.", 0
    
    return True, f"You buy {quantity} {item_key.replace('_', ' ')}{'s' if quantity > 1 else ''} for {format_gold(total_price)}.", price_per_item


def handle_search_command(game: dict, room_id: str) -> str:
    """
    Handle search/scavenge/loot command for a room.
    
    Args:
        game: Game state dictionary
        room_id: Current room identifier
    
    Returns:
        str: Response message
    """
    # Get highest reputation in area (for bonus)
    reputation = game.get("reputation", {})
    max_rep = max(reputation.values()) if reputation else 0
    
    # Search room
    found = search_room(room_id, max_rep)
    
    if not found:
        return "You search carefully but find nothing of value."
    
    # Process found items
    messages = []
    for item_key, amount in found:
        if item_key == "gold":
            # Add gold directly
            add_gold(game, amount)
            messages.append(f"You find {format_gold(amount)}!")
        else:
            # Add item to inventory
            inventory = game.get("inventory", [])
            for _ in range(amount):
                inventory.append(item_key)
            game["inventory"] = inventory
            item_name = item_key.replace("_", " ")
            if amount == 1:
                messages.append(f"You find a {item_name}!")
            else:
                messages.append(f"You find {amount} {item_name}s!")
    
    return "\n".join(messages)


def handle_loot_npc_command(game: dict, npc_id: str) -> str:
    """
    Handle looting an NPC.
    
    Args:
        game: Game state dictionary
        npc_id: NPC identifier
    
    Returns:
        str: Response message
    """
    reputation = game.get("reputation", {}).get(npc_id, 0)
    found = loot_npc(npc_id, reputation)
    
    if not found:
        return "You find nothing of value."
    
    # Process found items
    messages = []
    for item_key, amount in found:
        if item_key == "gold":
            add_gold(game, amount)
            messages.append(f"You find {format_gold(amount)}!")
        else:
            inventory = game.get("inventory", [])
            for _ in range(amount):
                inventory.append(item_key)
            game["inventory"] = inventory
            item_name = item_key.replace("_", " ")
            if amount == 1:
                messages.append(f"You find a {item_name}!")
            else:
                messages.append(f"You find {amount} {item_name}s!")
    
    return "\n".join(messages)

