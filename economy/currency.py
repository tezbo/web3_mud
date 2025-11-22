"""
Currency system for Tiny Web MUD.

Handles gold, silver, and copper coins with conversion.
10 copper coins = 1 silver coin
50 silver coins = 1 gold coin
"""

from collections import defaultdict
from typing import Tuple, Dict

# Starting currency (configurable)
STARTING_GOLD = 0
STARTING_SILVER = 2
STARTING_COPPER = 5

# Conversion rates
COPPER_PER_SILVER = 10
SILVER_PER_GOLD = 50
COPPER_PER_GOLD = COPPER_PER_SILVER * SILVER_PER_GOLD  # 500


def get_currency(game) -> Dict[str, int]:
    """
    Get player's current currency as a dict.
    
    Returns:
        dict: {"gold": int, "silver": int, "copper": int}
    """
    currency = game.get("currency", {})
    return {
        "gold": currency.get("gold", STARTING_GOLD),
        "silver": currency.get("silver", STARTING_SILVER),
        "copper": currency.get("copper", STARTING_COPPER),
    }


def normalize_currency(currency: Dict[str, int]) -> Dict[str, int]:
    """
    Normalize currency by converting excess coins to higher denominations.
    
    Args:
        currency: Dict with gold, silver, copper keys
    
    Returns:
        dict: Normalized currency dict
    """
    gold = currency.get("gold", 0)
    silver = currency.get("silver", 0)
    copper = currency.get("copper", 0)
    
    # Convert excess copper to silver
    if copper >= COPPER_PER_SILVER:
        silver += copper // COPPER_PER_SILVER
        copper = copper % COPPER_PER_SILVER
    
    # Convert excess silver to gold
    if silver >= SILVER_PER_GOLD:
        gold += silver // SILVER_PER_GOLD
        silver = silver % SILVER_PER_GOLD
    
    return {"gold": gold, "silver": silver, "copper": copper}


def currency_to_copper(currency: Dict[str, int]) -> int:
    """Convert currency to total copper coins."""
    gold = currency.get("gold", 0)
    silver = currency.get("silver", 0)
    copper = currency.get("copper", 0)
    return gold * COPPER_PER_GOLD + silver * COPPER_PER_SILVER + copper


def copper_to_currency(total_copper: int) -> Dict[str, int]:
    """Convert total copper coins to normalized currency dict."""
    gold = total_copper // COPPER_PER_GOLD
    remainder = total_copper % COPPER_PER_GOLD
    silver = remainder // COPPER_PER_SILVER
    copper = remainder % COPPER_PER_SILVER
    return {"gold": gold, "silver": silver, "copper": copper}


def set_currency(game, currency: Dict[str, int]):
    """Set player's currency (normalized)."""
    normalized = normalize_currency(currency)
    game["currency"] = normalized


def add_currency(game, currency: Dict[str, int]):
    """
    Add currency to player's account.
    
    Args:
        game: Game state dict
        currency: Dict with gold, silver, copper keys
    
    Returns:
        dict: New normalized currency
    """
    current = get_currency(game)
    new_currency = {
        "gold": current["gold"] + currency.get("gold", 0),
        "silver": current["silver"] + currency.get("silver", 0),
        "copper": current["copper"] + currency.get("copper", 0),
    }
    normalized = normalize_currency(new_currency)
    set_currency(game, normalized)
    return normalized


def remove_currency(game, currency: Dict[str, int]) -> Tuple[bool, Dict[str, int]]:
    """
    Remove currency from player's account.
    
    Args:
        game: Game state dict
        currency: Dict with gold, silver, copper keys to remove
    
    Returns:
        Tuple of (success, new_currency) where success is True if enough currency
    """
    current = get_currency(game)
    current_copper = currency_to_copper(current)
    needed_copper = currency_to_copper(currency)
    
    if current_copper < needed_copper:
        return False, current
    
    new_copper = current_copper - needed_copper
    new_currency = copper_to_currency(new_copper)
    set_currency(game, new_currency)
    return True, new_currency


def has_enough_currency(game, currency: Dict[str, int]) -> bool:
    """
    Check if player has enough currency (with conversion).
    
    Args:
        game: Game state dict
        currency: Dict with gold, silver, copper keys
    
    Returns:
        bool: True if player has enough currency
    """
    current = get_currency(game)
    current_copper = currency_to_copper(current)
    needed_copper = currency_to_copper(currency)
    return current_copper >= needed_copper


def format_currency(currency: Dict[str, int] = None, total_copper: int = None) -> str:
    """
    Format currency as a human-readable string.
    
    Args:
        currency: Optional currency dict
        total_copper: Optional total copper coins (will be converted)
    
    Returns:
        str: Formatted currency string (e.g., "1 gold, 2 silver, 5 copper")
    """
    if total_copper is not None:
        currency = copper_to_currency(total_copper)
    elif currency is None:
        return "no currency"
    
    currency = normalize_currency(currency)
    parts = []
    
    if currency.get("gold", 0) > 0:
        gold = currency["gold"]
        parts.append(f"{gold} gold coin{'s' if gold != 1 else ''}")
    
    if currency.get("silver", 0) > 0:
        silver = currency["silver"]
        parts.append(f"{silver} silver coin{'s' if silver != 1 else ''}")
    
    if currency.get("copper", 0) > 0:
        copper = currency["copper"]
        parts.append(f"{copper} copper coin{'s' if copper != 1 else ''}")
    
    if not parts:
        return "no currency"
    
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"


# Legacy compatibility functions (convert gold amount to new currency system)
def get_gold(game):
    """Legacy: Get total currency value in gold (for backward compatibility)."""
    currency = get_currency(game)
    total_copper = currency_to_copper(currency)
    return total_copper / COPPER_PER_GOLD


def add_gold(game, amount):
    """Legacy: Add gold amount (converted to new currency system)."""
    copper_to_add = int(amount * COPPER_PER_GOLD)
    add_currency(game, copper_to_currency(copper_to_add))
    return get_gold(game)


def remove_gold(game, amount):
    """Legacy: Remove gold amount (converted to new currency system)."""
    copper_to_remove = int(amount * COPPER_PER_GOLD)
    success, _ = remove_currency(game, copper_to_currency(copper_to_remove))
    return success, get_gold(game)


def has_enough_gold(game, amount):
    """Legacy: Check if player has enough gold (converted to new currency system)."""
    copper_needed = int(amount * COPPER_PER_GOLD)
    return has_enough_currency(game, copper_to_currency(copper_needed))


def format_gold(amount):
    """Legacy: Format gold amount (converted to new currency system)."""
    copper = int(amount * COPPER_PER_GOLD)
    return format_currency(total_copper=copper)
