"""
Merchant personality profiles for Tiny Web MUD.

Merchants have different personality types that affect pricing.
"""

import random
from typing import Literal

MerchantPersonality = Literal["greedy", "fair", "generous", "random"]


# Personality multipliers for base prices
PERSONALITY_MULTIPLIERS = {
    "greedy": 1.3,      # 30% markup
    "fair": 1.0,        # Normal prices
    "generous": 0.85,   # 15% discount
    "random": None,     # Random between 0.8 and 1.3
}


# Merchant personality assignments
MERCHANT_PERSONALITIES = {
    "innkeeper": "fair",      # Mara is fair
    "blacksmith": "greedy",   # Blacksmith charges premium
    "herbalist": "generous",  # Herbalist is kind
    "wandering_trader": "random",  # Trader varies
}


def get_merchant_personality(npc_id: str) -> MerchantPersonality:
    """
    Get personality type for a merchant NPC.
    
    Args:
        npc_id: NPC identifier
    
    Returns:
        str: Personality type ("greedy", "fair", "generous", or "random")
    """
    return MERCHANT_PERSONALITIES.get(npc_id, "fair")


def get_price_multiplier(npc_id: str) -> float:
    """
    Get price multiplier for a merchant based on their personality.
    
    Args:
        npc_id: NPC identifier
    
    Returns:
        float: Price multiplier (e.g., 1.3 for greedy, 0.85 for generous)
    """
    personality = get_merchant_personality(npc_id)
    
    if personality == "random":
        # Random between 0.8 and 1.3
        return round(random.uniform(0.8, 1.3), 2)
    
    multiplier = PERSONALITY_MULTIPLIERS.get(personality, 1.0)
    return multiplier


def get_reputation_price_modifier(reputation: int) -> float:
    """
    Get price modifier based on player reputation with merchant.
    
    Args:
        reputation: Reputation score with the merchant
    
    Returns:
        float: Price modifier (1.0 = normal, <1.0 = discount, >1.0 = markup)
    """
    if reputation >= 50:
        # Very high rep: 20-40% discount
        return 0.7  # 30% discount
    elif reputation >= 25:
        # High rep: 10-20% discount
        return 0.85  # 15% discount
    elif reputation >= 10:
        # Moderate rep: slight discount
        return 0.95  # 5% discount
    elif reputation >= 0:
        # Neutral to slightly positive
        return 1.0  # Normal price
    elif reputation >= -10:
        # Slightly negative
        return 1.1  # 10% markup
    elif reputation >= -25:
        # Negative
        return 1.2  # 20% markup
    else:
        # Very low rep: 30-50% markup
        return 1.4  # 40% markup


def calculate_final_price(base_price: int, npc_id: str, reputation: int) -> int:
    """
    Calculate final price with all modifiers applied.
    
    Args:
        base_price: Base price from price table
        npc_id: Merchant NPC identifier
        reputation: Player reputation with merchant
    
    Returns:
        int: Final price in gold (rounded)
    """
    # Apply personality multiplier
    personality_mult = get_price_multiplier(npc_id)
    
    # Apply reputation modifier
    rep_mod = get_reputation_price_modifier(reputation)
    
    # Calculate final price
    final = base_price * personality_mult * rep_mod
    
    # Round to nearest integer, minimum 1
    return max(1, int(round(final)))

