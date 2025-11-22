"""
Economy system for Tiny Web MUD.

This package handles currency, pricing, merchants, and loot.
"""

from economy.currency import (
    get_gold,
    add_gold,
    remove_gold,
    has_enough_gold,
    format_gold,
    STARTING_GOLD,
)
from economy.price_table import get_base_price, item_exists
from economy.merchant_profiles import (
    get_merchant_personality,
    get_price_multiplier,
    get_reputation_price_modifier,
    calculate_final_price,
)
from economy.loot_tables import search_room, loot_npc
from economy.economy_manager import (
    initialize_player_gold,
    get_item_price,
    process_purchase_with_gold,
    handle_search_command,
    handle_loot_npc_command,
)

__all__ = [
    "get_gold",
    "add_gold",
    "remove_gold",
    "has_enough_gold",
    "format_gold",
    "STARTING_GOLD",
    "get_base_price",
    "item_exists",
    "get_merchant_personality",
    "get_price_multiplier",
    "get_reputation_price_modifier",
    "calculate_final_price",
    "search_room",
    "loot_npc",
    "initialize_player_gold",
    "get_item_price",
    "process_purchase_with_gold",
    "handle_search_command",
    "handle_loot_npc_command",
]

