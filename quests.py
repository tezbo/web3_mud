"""
Quest system for Tiny Web MUD.

This module implements a flexible, event-driven quest system that supports:
- Quest templates (global definitions)
- Quest instances (per-player state)
- Event-driven progression (quests react to player actions)
- Multiple quest sources (NPCs, noticeboards)
- Timed quests, rewards, and reputation integration

Design:
- Templates define quest structure, objectives, and rewards
- Instances track per-player progress through quest stages
- Events trigger objective completion checks
- Rewards are applied on quest completion (currency, reputation, items)
"""

from typing import Dict, List, Optional, TypedDict, Any
from dataclasses import dataclass
from collections import defaultdict


# --- Quest Template Model ---

@dataclass
class QuestTemplate:
    """Defines a quest template (global definition)."""
    id: str
    name: str
    description: str  # High-level flavor description
    giver_id: str  # NPC id or pseudo-id like "noticeboard:main_village_square"
    difficulty: str  # "Easy", "Moderate", "Hard", "Epic"
    category: str  # "Errand", "Delivery", "Investigation", etc.
    timed: bool
    time_limit_minutes: Optional[int]  # In in-game minutes, if timed
    actors: List[str]  # NPC ids, factions, or pseudo-actors
    stages: List[Dict]  # List of stage dicts
    rewards: Dict  # Rewards dict with currency, reputation, items
    offer_sources: List[Dict]  # How quest is offered (NPC dialogue, noticeboard, etc.)
    failure_reputation: Optional[Dict] = None  # Optional reputation penalty on failure


# Global quest template registry
QUEST_TEMPLATES: Dict[str, QuestTemplate] = {}


def get_quest_template(quest_id: str) -> Optional[QuestTemplate]:
    """Get a quest template by ID."""
    return QUEST_TEMPLATES.get(quest_id)


def register_quest_template(template: QuestTemplate):
    """Register a quest template."""
    QUEST_TEMPLATES[template.id] = template


# --- Quest Event Model ---

class QuestEvent(TypedDict, total=False):
    """Represents a game event that quests can react to."""
    type: str  # "enter_room", "talk_to_npc", "say_to_npc", "take_item", "give_item", "drop_item"
    room_id: str
    npc_id: str
    item_id: str
    text: str
    username: str


# --- Quest Instance Helpers ---

def start_quest(game: Dict, username: str, quest_id: str, source: str) -> str:
    """
    Start a quest for a player.
    
    Args:
        game: Game state dict
        username: Player username
        quest_id: Quest template ID
        source: Source of quest offer (e.g., "npc:mara")
    
    Returns:
        str: Player-facing message
    """
    template = get_quest_template(quest_id)
    if not template:
        return f"Error: Quest '{quest_id}' not found."
    
    # Initialize quests dict if needed
    if "quests" not in game:
        game["quests"] = {}
    
    # Check if already active
    if quest_id in game["quests"]:
        instance = game["quests"][quest_id]
        if instance.get("status") == "active":
            return f"You are already working on '{template.name}'."
    
    # Get current game time
    from game_engine import GAME_TIME
    current_tick = GAME_TIME.get("tick", 0)
    current_minutes = GAME_TIME.get("minutes", 0)
    
    # Calculate expiration time if timed
    expires_at_tick = None
    expires_at_minutes = None
    if template.timed and template.time_limit_minutes:
        expires_at_minutes = current_minutes + template.time_limit_minutes
        # Convert minutes to ticks (assuming 1 tick = 1 minute)
        expires_at_tick = current_tick + template.time_limit_minutes
    
    # Create quest instance
    instance = {
        "id": quest_id,
        "template_id": quest_id,
        "status": "active",
        "giver_id": template.giver_id,
        "started_at_tick": current_tick,
        "started_at_minutes": current_minutes,
        "expires_at_tick": expires_at_tick,
        "expires_at_minutes": expires_at_minutes,
        "completed_at_tick": None,
        "current_stage_index": 0,
        "objectives_state": {},  # Track progress per objective
        "notes": [f"Quest started: {template.name}"],
        "difficulty": template.difficulty,
    }
    
    # Add initial note about first objective
    if template.stages:
        first_stage = template.stages[0]
        instance["notes"].append(f"Objective: {first_stage.get('description', 'Begin your quest.')}")
    
    game["quests"][quest_id] = instance
    
    # Clear pending offer
    game["pending_quest_offer"] = None
    
    # Special handling for Lost Package quest - spawn the package in the tavern
    if quest_id == "lost_package":
        from game_engine import ROOM_STATE
        # Add the lost package to the tavern room
        tavern_room_id = "tavern"
        if tavern_room_id not in ROOM_STATE:
            ROOM_STATE[tavern_room_id] = {"items": []}
        if "items" not in ROOM_STATE[tavern_room_id]:
            ROOM_STATE[tavern_room_id]["items"] = []
        # Only add if it doesn't already exist
        if "lost_package" not in ROOM_STATE[tavern_room_id]["items"]:
            ROOM_STATE[tavern_room_id]["items"].append("lost_package")
    
    return f"You accept the quest: {template.name}.\n{template.description}"


def complete_quest(game: Dict, username: str, quest_id: str) -> str:
    """
    Complete a quest and apply rewards.
    
    Args:
        game: Game state dict
        username: Player username
        quest_id: Quest ID to complete
    
    Returns:
        str: Completion message with rewards
    """
    if "quests" not in game:
        return "No active quests found."
    
    instance = game.get("quests", {}).get(quest_id)
    if not instance or instance.get("status") != "active":
        return "That quest is not active."
    
    template = get_quest_template(quest_id)
    if not template:
        return "Quest template not found."
    
    # Get current time
    from game_engine import GAME_TIME
    current_tick = GAME_TIME.get("tick", 0)
    current_minutes = GAME_TIME.get("minutes", 0)
    
    # Mark as completed
    instance["status"] = "completed"
    instance["completed_at_tick"] = current_tick
    
    # Calculate time bonus (if applicable)
    time_bonus = 0
    if template.timed and instance.get("expires_at_minutes"):
        time_limit = template.time_limit_minutes or 0
        elapsed = current_minutes - instance.get("started_at_minutes", current_minutes)
        if elapsed < time_limit * 0.5:  # Completed in less than half the time
            time_bonus = 1
            instance["notes"].append("Completed ahead of schedule - bonus reward!")
    
    # Move to completed_quests
    if "completed_quests" not in game:
        game["completed_quests"] = {}
    
    game["completed_quests"][quest_id] = instance.copy()
    del game["quests"][quest_id]
    
    # Apply rewards
    messages = [f"Quest completed: {template.name}!"]
    
    # Currency rewards
    if "currency" in template.rewards:
        currency_reward = template.rewards["currency"]
        amount = currency_reward.get("amount", 0)
        currency_type = currency_reward.get("currency_type", "silver")
        
        # Convert to currency dict
        currency_map = {
            "gold": {"gold": amount, "silver": 0, "copper": 0},
            "silver": {"gold": 0, "silver": amount, "copper": 0},
            "copper": {"gold": 0, "silver": 0, "copper": amount},
        }
        
        if currency_type in currency_map:
            from economy.currency import add_currency
            add_currency(game, currency_map[currency_type])
            messages.append(f"You receive {amount} {currency_type} coins.")
    
    # Reputation rewards
    if "reputation" in template.rewards:
        from game_engine import adjust_reputation
        rep_rewards = template.rewards["reputation"]
        for rep_entry in rep_rewards:
            target = rep_entry.get("target", "")
            amount = rep_entry.get("amount", 0) + time_bonus
            reason = rep_entry.get("reason", f"Completed quest: {template.name}")
            
            # Parse target (e.g., "npc:mara" or "faction:villagers")
            if target.startswith("npc:"):
                npc_id = target[4:]  # Remove "npc:" prefix
                new_rep, rep_message = adjust_reputation(game, npc_id, amount, reason)
                if rep_message:
                    messages.append(rep_message)
            # Faction reputation can be added later
    
    # Item rewards
    if "items" in template.rewards:
        item_rewards = template.rewards["items"]
        inventory = game.get("inventory", [])
        for item_reward in item_rewards:
            item_id = item_reward.get("item_id")
            quantity = item_reward.get("quantity", 1)
            is_quest_item = item_reward.get("quest_item", False)
            
            # Mark quest items in item definitions
            if is_quest_item and item_id:
                from game_engine import ITEM_DEFS
                if item_id in ITEM_DEFS:
                    # Add quest flag and make non-droppable
                    if "flags" not in ITEM_DEFS[item_id]:
                        ITEM_DEFS[item_id]["flags"] = []
                    if "quest" not in ITEM_DEFS[item_id]["flags"]:
                        ITEM_DEFS[item_id]["flags"].append("quest")
                    ITEM_DEFS[item_id]["droppable"] = False
            
            # Add items to inventory
            for _ in range(quantity):
                inventory.append(item_id)
            
            from game_engine import render_item_name
            item_name = render_item_name(item_id)
            if quantity == 1:
                messages.append(f"You receive {item_name}.")
            else:
                messages.append(f"You receive {quantity} {item_name}s.")
        
        game["inventory"] = inventory
    
    # Add completion note
    instance["notes"].append("Quest completed successfully.")
    
    return "\n".join(messages)


def fail_quest(game: Dict, username: str, quest_id: str, reason: str) -> str:
    """
    Fail a quest and apply failure penalties.
    
    Args:
        game: Game state dict
        username: Player username
        quest_id: Quest ID to fail
        reason: Reason for failure
    
    Returns:
        str: Failure message
    """
    if "quests" not in game:
        return "No active quests found."
    
    instance = game.get("quests", {}).get(quest_id)
    if not instance or instance.get("status") != "active":
        return "That quest is not active."
    
    template = get_quest_template(quest_id)
    if not template:
        return "Quest template not found."
    
    # Get current time
    from game_engine import GAME_TIME
    current_tick = GAME_TIME.get("tick", 0)
    
    # Mark as failed
    instance["status"] = "failed"
    instance["completed_at_tick"] = current_tick
    instance["notes"].append(f"Quest failed: {reason}")
    
    # Move to completed_quests
    if "completed_quests" not in game:
        game["completed_quests"] = {}
    
    game["completed_quests"][quest_id] = instance.copy()
    del game["quests"][quest_id]
    
    # Apply failure reputation penalty if defined
    if template.failure_reputation:
        from game_engine import adjust_reputation
        for rep_entry in template.failure_reputation:
            target = rep_entry.get("target", "")
            amount = rep_entry.get("amount", 0)
            reason_text = rep_entry.get("reason", f"Failed quest: {template.name}")
            
            if target.startswith("npc:"):
                npc_id = target[4:]
                adjust_reputation(game, npc_id, amount, reason_text)
    
    return f"Quest failed: {template.name}.\n{reason}"


def get_active_quests(game: Dict) -> List[Dict]:
    """Get list of active quest instances."""
    return [
        instance for instance in game.get("quests", {}).values()
        if instance.get("status") == "active"
    ]


def get_completed_quests(game: Dict) -> List[Dict]:
    """Get list of completed quest instances."""
    return list(game.get("completed_quests", {}).values())


# --- Event-Driven Quest Progression ---

def handle_quest_event(game: Dict, event: QuestEvent):
    """
    Process a game event and update quest progress.
    
    Called from game_engine whenever something notable happens.
    Updates active quests based on event type and objectives.
    
    Args:
        game: Game state dict
        event: QuestEvent dict with type and relevant data
    """
    active_quests = get_active_quests(game)
    if not active_quests:
        return
    
    for instance in active_quests:
        quest_id = instance["id"]
        template = get_quest_template(quest_id)
        if not template:
            continue
        
        current_stage_index = instance.get("current_stage_index", 0)
        if current_stage_index >= len(template.stages):
            continue
        
        current_stage = template.stages[current_stage_index]
        objectives = current_stage.get("objectives", [])
        
        # Check each objective to see if event satisfies it
        objectives_completed = instance.get("objectives_state", {}).copy()
        if current_stage_index not in objectives_completed:
            objectives_completed[current_stage_index] = {}
        
        stage_completed = True
        for objective in objectives:
            obj_id = objective.get("id", "")
            obj_type = objective.get("type", "")
            
            # Check if objective is already completed
            if objectives_completed[current_stage_index].get(obj_id, False):
                continue
            
            # Check if event satisfies objective
            satisfied = False
            
            if obj_type == "go_to_room":
                if event.get("type") == "enter_room":
                    required_room = objective.get("room_id", "")
                    if event.get("room_id") == required_room:
                        satisfied = True
            
            elif obj_type == "talk_to_npc":
                if event.get("type") == "talk_to_npc":
                    required_npc = objective.get("npc_id", "")
                    if event.get("npc_id") == required_npc:
                        satisfied = True
            
            elif obj_type == "say_to_npc":
                if event.get("type") == "say_to_npc":
                    required_npc = objective.get("npc_id", "")
                    keywords = objective.get("keywords", [])
                    text = event.get("text", "").lower()
                    
                    if event.get("npc_id") == required_npc:
                        # Check if text contains any keyword
                        if keywords:
                            if any(keyword.lower() in text for keyword in keywords):
                                satisfied = True
                        else:
                            satisfied = True  # Just talking to them is enough
            
            elif obj_type == "obtain_item":
                if event.get("type") == "take_item":
                    required_item = objective.get("item_id", "")
                    if event.get("item_id") == required_item:
                        satisfied = True
                # Also check if item is already in inventory
                elif event.get("type") == "enter_room":
                    required_item = objective.get("item_id", "")
                    inventory = game.get("inventory", [])
                    if required_item in inventory:
                        satisfied = True
            
            elif obj_type == "deliver_item":
                if event.get("type") == "give_item" or event.get("type") == "talk_to_npc":
                    required_item = objective.get("item_id", "")
                    required_npc = objective.get("npc_id", None)
                    required_room = objective.get("room_id", None)
                    
                    # Check if player has item
                    inventory = game.get("inventory", [])
                    has_item = required_item in inventory
                    
                    # Check NPC requirement
                    if required_npc:
                        if event.get("npc_id") != required_npc:
                            has_item = False
                    
                    # Check room requirement
                    if required_room:
                        if event.get("room_id") != required_room:
                            has_item = False
                    
                    if has_item and (required_npc or required_room):
                        satisfied = True
            
            # Mark objective as completed
            if satisfied:
                objectives_completed[current_stage_index][obj_id] = True
                instance["notes"].append(f"Completed: {objective.get('description', obj_type)}")
            
            # Check if objective is still incomplete
            if not objectives_completed[current_stage_index].get(obj_id, False):
                stage_completed = False
        
        # Update objectives state
        instance["objectives_state"] = objectives_completed
        
        # If all objectives in current stage are completed
        if stage_completed:
            instance["notes"].append(f"Stage completed: {current_stage.get('description', 'Objective completed')}")
            
            # Advance to next stage
            if current_stage_index + 1 < len(template.stages):
                instance["current_stage_index"] = current_stage_index + 1
                next_stage = template.stages[current_stage_index + 1]
                instance["notes"].append(f"New objective: {next_stage.get('description', 'Continue your quest.')}")
            else:
                # All stages complete - complete the quest
                complete_quest(game, event.get("username", "adventurer"), quest_id)


def tick_quests(game: Dict, current_tick: int):
    """
    Handle time-based quest updates (timers, expiration).
    
    Called periodically to check for expired quests.
    
    Args:
        game: Game state dict
        current_tick: Current game tick
    """
    active_quests = get_active_quests(game)
    if not active_quests:
        return
    
    for instance in active_quests:
        quest_id = instance["id"]
        expires_at_tick = instance.get("expires_at_tick")
        
        if expires_at_tick and current_tick >= expires_at_tick:
            # Quest expired
            username = "adventurer"  # Default, should be passed in context
            fail_quest(game, username, quest_id, "You ran out of time.")


# --- Quest Offering System ---

def offer_quest_to_player(game: Dict, username: str, quest_id: str, source: str) -> str:
    """
    Store a pending quest offer.
    
    Args:
        game: Game state dict
        username: Player username
        quest_id: Quest template ID
        source: Source of offer (e.g., "npc:mara")
    
    Returns:
        str: Descriptive message about the quest
    """
    template = get_quest_template(quest_id)
    if not template:
        return "Quest not found."
    
    from game_engine import GAME_TIME
    current_tick = GAME_TIME.get("tick", 0)
    
    game["pending_quest_offer"] = {
        "quest_id": quest_id,
        "source": source,
        "offered_at_tick": current_tick,
    }
    
    # Build offer message
    message_parts = [template.description]
    
    if template.timed:
        time_limit = template.time_limit_minutes or 0
        message_parts.append(f"\nThis quest must be completed within {time_limit} minutes.")
    
    message_parts.append(f"\n(Type 'accept quest' to take it on or 'decline quest' to turn it down.)")
    
    return "\n".join(message_parts)


def accept_pending_quest(game: Dict, username: str) -> str:
    """Accept a pending quest offer."""
    pending = game.get("pending_quest_offer")
    if not pending:
        return "You don't have any quest offers to accept right now."
    
    quest_id = pending.get("quest_id")
    if not quest_id:
        return "Invalid quest offer."
    
    # Start the quest
    return start_quest(game, username, quest_id, pending.get("source", ""))


def decline_pending_quest(game: Dict, username: str) -> str:
    """Decline a pending quest offer."""
    pending = game.get("pending_quest_offer")
    if not pending:
        return "You don't have any quest offers to decline right now."
    
    template = get_quest_template(pending.get("quest_id", ""))
    quest_name = template.name if template else "the quest"
    
    # Clear pending offer
    game["pending_quest_offer"] = None
    
    return f"You decline {quest_name}. Perhaps another time."


def maybe_offer_npc_quest(game: Dict, username: str, npc_id: str, player_text: str, current_tick: int) -> Optional[str]:
    """
    Check if NPC should offer a quest based on player dialogue.
    
    Args:
        game: Game state dict
        username: Player username
        npc_id: NPC ID
        player_text: Player's spoken text
        current_tick: Current game tick
    
    Returns:
        Optional[str]: Extra flavor text if quest is offered, None otherwise
    """
    # Check all quest templates for NPC-based offers
    for quest_id, template in QUEST_TEMPLATES.items():
        # Skip if player already has this quest (active or completed)
        if quest_id in game.get("quests", {}):
            continue
        if quest_id in game.get("completed_quests", {}):
            continue
        
        # Check if this quest has an NPC offer source for this NPC
        for offer_source in template.offer_sources:
            if offer_source.get("type") == "npc_dialogue":
                source_npc_id = offer_source.get("npc_id", "")
                if source_npc_id == npc_id:
                    # Check trigger conditions
                    trigger = offer_source.get("trigger", {})
                    trigger_kind = trigger.get("kind", "")
                    
                    if trigger_kind == "say_contains":
                        keywords = trigger.get("keywords", [])
                        text_lower = player_text.lower()
                        
                        # Check if player text contains any keyword
                        if keywords and any(keyword.lower() in text_lower for keyword in keywords):
                            # Offer the quest
                            offer_quest_to_player(game, username, quest_id, f"npc:{npc_id}")
                            return offer_source.get("offer_text", "")
    
    return None


# --- Quest Display/UI ---

def render_quest_list(game: Dict) -> str:
    """
    Render a list of active quests.
    
    Returns:
        str: Formatted quest list
    """
    active_quests = get_active_quests(game)
    completed_count = len(get_completed_quests(game))
    
    if not active_quests:
        if completed_count > 0:
            return f"You have no active quests.\n(You have completed {completed_count} quest{'s' if completed_count != 1 else ''}.)"
        return "You have no active quests."
    
    lines = ["Your current quests:\n"]
    lines.append("#  Name             Diff.   Status         Time Left    Current Objective")
    
    from game_engine import GAME_TIME
    current_tick = GAME_TIME.get("tick", 0)
    current_minutes = GAME_TIME.get("minutes", 0)
    
    for idx, instance in enumerate(active_quests, 1):
        quest_id = instance["id"]
        template = get_quest_template(quest_id)
        if not template:
            continue
        
        name = template.name[:15].ljust(15)
        difficulty = template.difficulty[:7].ljust(7)
        
        # Determine status and time left
        status = "Active"
        time_left = ""
        
        if template.timed and instance.get("expires_at_minutes"):
            expires_at = instance.get("expires_at_minutes", 0)
            remaining_minutes = max(0, expires_at - current_minutes)
            
            if remaining_minutes <= 0:
                status = "Expired"
            elif remaining_minutes <= 5:
                status = "Urgent"
                time_left = f"{int(remaining_minutes)} min"
            else:
                status = "Timed"
                time_left = f"{int(remaining_minutes)} min"
        else:
            time_left = "-"
        
        status = status[:13].ljust(13)
        time_left = time_left[:11].ljust(11)
        
        # Get current objective
        stage_index = instance.get("current_stage_index", 0)
        current_obj = "Continue your quest."
        if stage_index < len(template.stages):
            current_stage = template.stages[stage_index]
            current_obj = current_stage.get("description", "Continue your quest.")
            # Truncate if too long
            if len(current_obj) > 30:
                current_obj = current_obj[:27] + "..."
        
        lines.append(f"{idx}  {name} {difficulty} {status} {time_left} {current_obj}")
    
    lines.append(f"\n(Type 'quests detail <number>' to see more about a quest.)")
    
    if completed_count > 0:
        lines.append(f"\n(You have completed {completed_count} quest{'s' if completed_count != 1 else ''}.)")
    
    return "\n".join(lines)


def render_quest_detail(game: Dict, index_or_id: str) -> str:
    """
    Render detailed information about a specific quest.
    
    Args:
        game: Game state dict
        index_or_id: Quest index (from list) or quest_id string
    
    Returns:
        str: Detailed quest information
    """
    active_quests = get_active_quests(game)
    
    # Try to resolve index_or_id to a quest instance
    instance = None
    
    # Check if it's a numeric index
    try:
        index = int(index_or_id)
        if 1 <= index <= len(active_quests):
            instance = active_quests[index - 1]
    except ValueError:
        # Not a number, try as quest_id
        if index_or_id in game.get("quests", {}):
            instance = game["quests"][index_or_id]
        elif index_or_id in game.get("completed_quests", {}):
            instance = game["completed_quests"][index_or_id]
    
    if not instance:
        return f"Quest '{index_or_id}' not found. Type 'quests' to see your active quests."
    
    template = get_quest_template(instance["id"])
    if not template:
        return "Quest template not found."
    
    lines = [f"=== {template.name} ==="]
    lines.append(f"Difficulty: {template.difficulty}")
    lines.append(f"Category: {template.category}")
    lines.append(f"Status: {instance.get('status', 'Unknown').title()}")
    
    # Giver info
    giver_id = template.giver_id
    if giver_id.startswith("npc:"):
        npc_id = giver_id[4:]
        from npc import NPCS
        npc = NPCS.get(npc_id)
        if npc:
            lines.append(f"Given by: {npc.name}")
    else:
        lines.append(f"Source: {giver_id}")
    
    # Time info
    from game_engine import GAME_TIME
    current_tick = GAME_TIME.get("tick", 0)
    current_minutes = GAME_TIME.get("minutes", 0)
    
    started_minutes = instance.get("started_at_minutes", 0)
    elapsed_minutes = current_minutes - started_minutes
    
    lines.append(f"Started: {elapsed_minutes} minutes ago")
    
    if template.timed and instance.get("expires_at_minutes"):
        expires_at = instance.get("expires_at_minutes", 0)
        remaining_minutes = max(0, expires_at - current_minutes)
        if remaining_minutes > 0:
            lines.append(f"Time remaining: {int(remaining_minutes)} minutes")
        else:
            lines.append(f"Time remaining: EXPIRED")
    
    if instance.get("completed_at_tick"):
        completed_minutes = instance.get("completed_at_minutes", 0)
        total_time = completed_minutes - started_minutes
        lines.append(f"Completed in: {total_time} minutes")
    
    # Notes/progress log
    notes = instance.get("notes", [])
    if notes:
        lines.append("\nProgress:")
        for note in notes[-5:]:  # Show last 5 notes
            lines.append(f"  - {note}")
    
    # Current objective
    stage_index = instance.get("current_stage_index", 0)
    if stage_index < len(template.stages):
        current_stage = template.stages[stage_index]
        lines.append(f"\nCurrent Objective:")
        lines.append(f"  {current_stage.get('description', 'Continue your quest.')}")
    
    # Rewards preview
    if template.rewards:
        lines.append("\nRewards:")
        if "currency" in template.rewards:
            curr = template.rewards["currency"]
            lines.append(f"  - {curr.get('amount', 0)} {curr.get('currency_type', 'coins')}")
        if "reputation" in template.rewards:
            lines.append(f"  - Reputation improvements")
        if "items" in template.rewards:
            items = template.rewards["items"]
            from game_engine import render_item_name
            for item_reward in items:
                item_id = item_reward.get("item_id")
                quantity = item_reward.get("quantity", 1)
                item_name = render_item_name(item_id) if item_id else "item"
                lines.append(f"  - {quantity} {item_name}")
    
    return "\n".join(lines)


def render_noticeboard(game: Dict, room_id: str, current_tick: int) -> str:
    """
    Render noticeboard quest postings for a room.
    
    Args:
        game: Game state dict
        room_id: Room ID
        current_tick: Current game tick
    
    Returns:
        str: Noticeboard content
    """
    available_quests = get_noticeboard_quests_for_room(game, room_id, current_tick)
    
    if not available_quests:
        return "The noticeboard is empty. No quests are posted here right now."
    
    lines = ["=== Village Noticeboard ==="]
    lines.append("Several notices are posted here:\n")
    
    for idx, template in enumerate(available_quests, 1):
        lines.append(f"{idx}. {template.name} ({template.difficulty})")
        lines.append(f"   {template.description[:60]}...")
        if template.timed:
            lines.append(f"   Time limit: {template.time_limit_minutes} minutes")
        lines.append("")
    
    lines.append("(Type 'board <number>' to read a posting in detail.)")
    
    return "\n".join(lines)


def get_noticeboard_quests_for_room(game: Dict, room_id: str, current_tick: int) -> List[QuestTemplate]:
    """
    Get quests available via noticeboard in this room.
    
    Args:
        game: Game state dict
        room_id: Room ID
        current_tick: Current game tick
    
    Returns:
        List of QuestTemplate objects
    """
    available = []
    
    for quest_id, template in QUEST_TEMPLATES.items():
        # Skip if player already has this quest
        if quest_id in game.get("quests", {}):
            continue
        if quest_id in game.get("completed_quests", {}):
            continue
        
        # Check if this quest has a noticeboard offer source for this room
        for offer_source in template.offer_sources:
            if offer_source.get("type") == "noticeboard":
                source_room_id = offer_source.get("room_id", "")
                if source_room_id == room_id:
                    # Check post duration (simplified: always available for now)
                    available.append(template)
    
    return available


# --- Quest Initialization ---

def initialize_quests():
    """
    Initialize all quest templates.
    This should be called once at startup.
    """
    global QUEST_TEMPLATES
    
    # Lost Package quest
    lost_package_template = QuestTemplate(
        id="lost_package",
        name="Lost Package",
        description="Mara has misplaced a small package in the stock room behind her tavern. She needs someone to help her find it and bring it back.",
        giver_id="npc:innkeeper",
        difficulty="Easy",
        category="Errand",
        timed=False,
        time_limit_minutes=None,
        actors=["innkeeper"],
        stages=[
            {
                "id": "talk_to_mara",
                "description": "Talk to Mara and offer to help her find the lost package.",
                "objectives": [
                    {
                        "id": "talk_to_mara_obj",
                        "type": "talk_to_npc",
                        "npc_id": "innkeeper"
                    },
                    {
                        "id": "say_help_obj",
                        "type": "say_to_npc",
                        "npc_id": "innkeeper",
                        "keywords": ["help", "what's wrong", "can I help", "assist", "package"]
                    }
                ]
            },
            {
                "id": "find_package",
                "description": "Find the lost package in the stock room behind the tavern.",
                "objectives": [
                    {
                        "id": "go_to_stock_room",
                        "type": "go_to_room",
                        "room_id": "tavern"  # The package is in the tavern (back room could be added later)
                    },
                    {
                        "id": "obtain_package",
                        "type": "obtain_item",
                        "item_id": "lost_package"
                    }
                ]
            },
            {
                "id": "return_package",
                "description": "Return the package to Mara at the tavern.",
                "objectives": [
                    {
                        "id": "deliver_to_mara",
                        "type": "deliver_item",
                        "item_id": "lost_package",
                        "npc_id": "innkeeper",
                        "room_id": "tavern"
                    }
                ]
            }
        ],
        rewards={
            "currency": {"amount": 5, "currency_type": "silver"},
            "reputation": [
                {"target": "npc:innkeeper", "amount": 5, "reason": "Helped recover her package"}
            ],
            "items": [
                {
                    "item_id": "mara_lucky_charm",
                    "quantity": 1,
                    "quest_item": True
                }
            ]
        },
        offer_sources=[
            {
                "type": "npc_dialogue",
                "npc_id": "innkeeper",
                "trigger": {
                    "kind": "say_contains",
                    "keywords": ["help", "what's wrong", "can I help", "package", "lost"]
                },
                "offer_text": "Mara looks up, clearly relieved. 'Oh, thank goodness. I've lost a small parcel somewhere in the stock room. Could you help me find it?'"
            }
        ],
        failure_reputation=None  # No penalty for failure (player-friendly)
    )
    
    register_quest_template(lost_package_template)


def register_quest_template(template: QuestTemplate):
    """Register a quest template in the global registry."""
    QUEST_TEMPLATES[template.id] = template


# Initialize quests when module is imported
initialize_quests()

