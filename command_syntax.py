"""
Command syntax helpers - shows possible arguments and options for commands.
"""

# Command syntax definitions
COMMAND_SYNTAX = {
    "goto": {
        "description": "Admin command: Teleport to a player or NPC",
        "usage": "goto <player_name|npc_name>",
        "examples": ["goto lofty", "goto herbalist", "goto mara"],
        "admin_only": True,
    },
    "stat": {
        "description": "Admin command: View detailed stats of an object",
        "usage": "stat <target>",
        "examples": ["stat me", "stat herbalist", "stat sword"],
        "admin_only": True,
    },
    "set": {
        "description": "Admin command: Set properties on objects",
        "usage": "set <target> <property> <value>",
        "examples": ["set me teleport_entrance_message \"appears in a flash of light\"", "set me location town_square"],
        "admin_only": True,
    },
    "look": {
        "description": "Look at your surroundings or examine something",
        "usage": "look [<target>]",
        "examples": ["look", "look me", "look herbalist", "look sword"],
        "aliases": ["l", "examine"],
    },
    "go": {
        "description": "Move in a direction",
        "usage": "go <direction>",
        "examples": ["go north", "go east", "go south"],
        "aliases": ["n", "s", "e", "w", "north", "south", "east", "west"],
    },
    "take": {
        "description": "Pick up an item from the room",
        "usage": "take <item> | take all",
        "examples": ["take sword", "take all"],
    },
    "drop": {
        "description": "Drop an item from your inventory",
        "usage": "drop <item> | drop all",
        "examples": ["drop sword", "drop all"],
    },
    "inventory": {
        "description": "View your inventory",
        "usage": "inventory",
        "examples": ["inventory", "inv", "i"],
        "aliases": ["inv", "i"],
    },
    "say": {
        "description": "Speak to everyone in the room",
        "usage": "say <message>",
        "examples": ["say Hello everyone!", "say How are you?"],
    },
    "tell": {
        "description": "Send a private message to another player",
        "usage": "tell <player> <message>",
        "examples": ["tell mara Hello!", "tell tezbo How are you?"],
    },
    "talk": {
        "description": "Talk to an NPC",
        "usage": "talk <npc_name>",
        "examples": ["talk herbalist", "talk mara"],
    },
    "attack": {
        "description": "Attack an NPC",
        "usage": "attack <npc_name>",
        "examples": ["attack goblin"],
        "aliases": ["hit", "strike"],
    },
    "quests": {
        "description": "View your quest log",
        "usage": "quests [detail <number>]",
        "examples": ["quests", "quests detail 1"],
        "aliases": ["questlog"],
    },
    "accept": {
        "description": "Accept a pending quest offer",
        "usage": "accept quest",
        "examples": ["accept quest"],
    },
    "decline": {
        "description": "Decline a pending quest offer",
        "usage": "decline quest",
        "examples": ["decline quest"],
    },
    "buy": {
        "description": "Buy an item from a merchant",
        "usage": "buy <item> [from <merchant>]",
        "examples": ["buy bread", "buy stew from mara"],
    },
    "list": {
        "description": "List items for sale from merchants in the room",
        "usage": "list",
        "examples": ["list"],
    },
    "time": {
        "description": "Check the current in-game time",
        "usage": "time",
        "examples": ["time"],
    },
    "weather": {
        "description": "Check the current weather",
        "usage": "weather",
        "examples": ["weather"],
    },
    "who": {
        "description": "List players currently online",
        "usage": "who",
        "examples": ["who"],
    },
    "help": {
        "description": "Show help and available commands",
        "usage": "help",
        "examples": ["help", "?"],
        "aliases": ["?"],
    },
}


def get_command_syntax(command_name):
    """
    Get syntax information for a command.
    
    Args:
        command_name: The command name (e.g., "goto", "look")
    
    Returns:
        dict or None: Syntax information dict, or None if command not found
    """
    return COMMAND_SYNTAX.get(command_name.lower())


def format_syntax_hint(command_name):
    """
    Format a syntax hint string for a command.
    
    Args:
        command_name: The command name
    
    Returns:
        str: Formatted hint string, or empty string if command not found
    """
    syntax = get_command_syntax(command_name)
    if not syntax:
        return ""
    
    hint_parts = []
    hint_parts.append(f"<span style='color: #60a5fa;'>Usage:</span> <span style='color: #ccc;'>{syntax['usage']}</span>")
    
    if syntax.get("examples"):
        examples = ", ".join([f"'{ex}'" for ex in syntax["examples"][:3]])  # Show first 3 examples
        hint_parts.append(f"<span style='color: #60a5fa;'>Examples:</span> <span style='color: #ccc;'>{examples}</span>")
    
    return " | ".join(hint_parts)


def get_suggestions_for_prefix(prefix):
    """
    Get command suggestions for a prefix (for autocomplete/hinting).
    
    Args:
        prefix: The prefix to match against
    
    Returns:
        list: List of matching command names
    """
    prefix_lower = prefix.lower()
    matches = []
    
    for cmd_name, syntax in COMMAND_SYNTAX.items():
        if cmd_name.startswith(prefix_lower):
            matches.append(cmd_name)
        # Also check aliases
        for alias in syntax.get("aliases", []):
            if alias.startswith(prefix_lower):
                matches.append(cmd_name)
    
    return sorted(set(matches))

