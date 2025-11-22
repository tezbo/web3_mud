"""
Base price table for items in Tiny Web MUD.

All prices are in gold. These are base prices before merchant multipliers
and reputation modifiers are applied.
"""

BASE_PRICES = {
    # Food & Drink
    "stew": 2,
    "bowl_of_stew": 2,
    "ale": 1,
    "tankard_of_ale": 1,
    "bread": 1,
    "loaf_of_bread": 1,
    "piece_of_bread": 1,
    
    # Tools & Equipment
    "iron_hammer": 15,
    "wooden_tankard": 1,
    "cracked_spyglass": 25,
    
    # Materials
    "lump_of_ore": 5,
    "loose_stone": 1,
    
    # Misc
    "weathered_signpost": 3,
    "copper_coin": 0,  # Legacy item, not sold
}


def get_base_price(item_key):
    """
    Get base price for an item.
    
    Args:
        item_key: Item identifier string
    
    Returns:
        int: Base price in gold, or 0 if item not found
    """
    return BASE_PRICES.get(item_key, 0)


def item_exists(item_key):
    """Check if item exists in price table."""
    return item_key in BASE_PRICES

