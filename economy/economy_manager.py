"""
Economy manager for Tiny Web MUD.

Coordinates currency, pricing, and transactions.
"""

from typing import Tuple

from economy.currency import (
    get_currency, add_currency, remove_currency, has_enough_currency, format_currency,
    currency_to_copper, copper_to_currency,
    get_gold, add_gold, remove_gold, has_enough_gold, format_gold  # Legacy compatibility
)
from economy.price_table import get_base_price
from economy.merchant_profiles import calculate_final_price
from economy.loot_tables import search_room, loot_npc


def initialize_player_currency(game, starting_currency=None):
    """
    Initialize player's currency if not already set.
    
    Args:
        game: Game state dictionary
        starting_currency: Optional starting currency dict (uses default if None)
    """
    if "currency" not in game:
        from economy.currency import STARTING_GOLD, STARTING_SILVER, STARTING_COPPER
        if starting_currency is None:
            starting_currency = {
                "gold": STARTING_GOLD,
                "silver": STARTING_SILVER,
                "copper": STARTING_COPPER
            }
        game["currency"] = starting_currency


def initialize_player_gold(game, starting_amount=None):
    """
    Legacy: Initialize player's gold (converted to new currency system).
    
    Args:
        game: Game state dictionary
        starting_amount: Optional starting gold (uses default if None)
    """
    if "currency" not in game:
        from economy.currency import copper_to_currency, COPPER_PER_GOLD, STARTING_GOLD
        if starting_amount is None:
            starting_amount = STARTING_GOLD
        # Convert gold to copper, then to currency
        copper = int(starting_amount * COPPER_PER_GOLD)
        game["currency"] = copper_to_currency(copper)


def get_item_price(item_key: str, npc_id: str, game: dict) -> int:
    """
    Get the final price for an item from a merchant.
    
    Args:
        item_key: Item identifier
        npc_id: Merchant NPC identifier
        game: Game state (for reputation lookup)
    
    Returns:
        int: Final price in copper coins
    """
    base_price = get_base_price(item_key)
    if base_price == 0:
        return 0
    
    reputation = game.get("reputation", {}).get(npc_id, 0)
    return calculate_final_price(base_price, npc_id, reputation)


def process_purchase_with_gold(game: dict, item_key: str, quantity: int, 
                              npc_id: str, npc_name: str) -> Tuple[bool, str, int]:
    """
    Process a purchase using currency (gold, silver, copper).
    
    Args:
        game: Game state dictionary
        item_key: Item to purchase
        quantity: Quantity to purchase
        npc_id: Merchant NPC identifier
        npc_name: Merchant NPC name (for messages)
    
    Returns:
        Tuple of (success, message, price_per_item_in_copper)
    """
    # Get price in copper coins
    price_per_item_copper = get_item_price(item_key, npc_id, game)
    if price_per_item_copper == 0:
        return False, f"{npc_name} doesn't sell that item.", 0
    
    total_price_copper = price_per_item_copper * quantity
    price_currency = copper_to_currency(total_price_copper)
    
    # Check if player has enough currency
    current_currency = get_currency(game)
    if not has_enough_currency(game, price_currency):
        current_formatted = format_currency(current_currency)
        price_formatted = format_currency(price_currency)
        item_name = item_key.replace('_', ' ')
        plural = 's' if quantity > 1 else ''
        return False, f"You can't afford that. {npc_name} wants {price_formatted} for {quantity} {item_name}{plural} (you have {current_formatted}).", 0
    
    # Remove currency
    success, new_currency = remove_currency(game, price_currency)
    if not success:
        return False, "Error processing payment.", 0
    
    price_formatted = format_currency(price_currency)
    item_name = item_key.replace('_', ' ')
    plural = 's' if quantity > 1 else ''
    return True, f"You buy {quantity} {item_name}{plural} for {price_formatted}.", price_per_item_copper


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
            # Legacy: Add gold (converted to new currency system)
            add_gold(game, amount)
            messages.append(f"You find {format_gold(amount)}!")
        elif item_key in ["gold_coin", "silver_coin", "copper_coin"]:
            # Add currency coins directly
            currency_map = {
                "gold_coin": {"gold": 1, "silver": 0, "copper": 0},
                "silver_coin": {"gold": 0, "silver": 1, "copper": 0},
                "copper_coin": {"gold": 0, "silver": 0, "copper": 1},
            }
            currency_to_add = {k: v * amount for k, v in currency_map[item_key].items()}
            add_currency(game, currency_to_add)
            coin_name = item_key.replace("_", " ")
            if amount == 1:
                messages.append(f"You find a {coin_name}!")
            else:
                messages.append(f"You find {amount} {coin_name}s!")
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
            # Legacy: Add gold (converted to new currency system)
            add_gold(game, amount)
            messages.append(f"You find {format_gold(amount)}!")
        elif item_key in ["gold_coin", "silver_coin", "copper_coin"]:
            # Add currency coins directly
            currency_map = {
                "gold_coin": {"gold": 1, "silver": 0, "copper": 0},
                "silver_coin": {"gold": 0, "silver": 1, "copper": 0},
                "copper_coin": {"gold": 0, "silver": 0, "copper": 1},
            }
            currency_to_add = {k: v * amount for k, v in currency_map[item_key].items()}
            add_currency(game, currency_to_add)
            coin_name = item_key.replace("_", " ")
            if amount == 1:
                messages.append(f"You find a {coin_name}!")
            else:
                messages.append(f"You find {amount} {coin_name}s!")
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

