"""
Currency system for Tiny Web MUD.

Handles gold currency and conversion.
"""

# Starting gold amount (configurable)
STARTING_GOLD = 50


def get_gold(game):
    """Get player's current gold amount."""
    return game.get("gold", STARTING_GOLD)


def add_gold(game, amount):
    """Add gold to player's account. Returns new total."""
    current = get_gold(game)
    new_total = max(0, current + amount)  # Prevent negative gold
    game["gold"] = new_total
    return new_total


def remove_gold(game, amount):
    """
    Remove gold from player's account.
    Returns (success, new_total) where success is True if enough gold.
    """
    current = get_gold(game)
    if current < amount:
        return False, current
    new_total = current - amount
    game["gold"] = new_total
    return True, new_total


def has_enough_gold(game, amount):
    """Check if player has enough gold."""
    return get_gold(game) >= amount


def format_gold(amount):
    """Format gold amount as a string."""
    if amount == 1:
        return "1 gold"
    return f"{amount} gold"

