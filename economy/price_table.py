"""
Base price table for items in Tiny Web MUD.

All prices are in copper coins. These are base prices before merchant multipliers
and reputation modifiers are applied.

Note: 1 gold = 500 copper, 1 silver = 10 copper
"""

# Prices in copper coins
BASE_PRICES = {
    # Food & Drink
    "stew": 1000,  # 2 gold
    "bowl_of_stew": 1000,  # 2 gold
    "ale": 500,  # 1 gold
    "tankard_of_ale": 500,  # 1 gold
    "bread": 500,  # 1 gold
    "loaf_of_bread": 500,  # 1 gold
    "piece_of_bread": 500,  # 1 gold
    
    # Tools & Equipment
    "iron_hammer": 7500,  # 15 gold
    "wooden_tankard": 500,  # 1 gold
    "cracked_spyglass": 12500,  # 25 gold
    
    # Materials
    "lump_of_ore": 2500,  # 5 gold
    "loose_stone": 500,  # 1 gold
    
    # Misc
    "weathered_signpost": 1500,  # 3 gold
    "copper_coin": 0,  # Legacy item, not sold
}


def get_base_price(item_key):
    """
    Get base price for an item.
    
    Args:
        item_key: Item identifier string
    
    Returns:
        int: Base price in copper coins, or 0 if item not found
    """
    return BASE_PRICES.get(item_key, 0)


def item_exists(item_key):
    """Check if item exists in price table."""
    return item_key in BASE_PRICES

