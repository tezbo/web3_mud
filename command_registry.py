"""
command_registry.py

Command registry and dispatcher system.

Provides a registry for command handlers to replace the giant if/elif chain
in handle_command. Allows commands to be extracted into separate functions/modules
while maintaining backward compatibility.
"""

from typing import Callable, Dict, List, Tuple, Optional

# Signature for command handlers
# Handlers receive: (verb, tokens, game, username, user_id, db_conn, broadcast_fn, who_fn)
# Return: (response_text, updated_game_state)
CommandHandler = Callable[
    [
        str,      # verb
        list,     # tokens (list of strings)
        dict,     # game state dict
        Optional[str],  # username
        Optional[int],  # user_id
        Optional[object],  # db_conn
        Optional[Callable],  # broadcast_fn
        Optional[Callable],  # who_fn
    ],
    Tuple[str, dict]  # (response_text, updated_game_state)
]

COMMAND_HANDLERS: Dict[str, CommandHandler] = {}
COMMAND_ALIASES: Dict[str, str] = {}


def register_command(
    verb: str,
    handler: CommandHandler,
    aliases: Optional[List[str]] = None,
):
    """
    Register a command verb and any aliases to a handler.
    
    Args:
        verb: The primary command verb (e.g., "help", "quests")
        handler: The handler function that processes this command
        aliases: Optional list of alias verbs (e.g., ["commands"] for "help")
    """
    COMMAND_HANDLERS[verb] = handler
    for alias in aliases or []:
        COMMAND_ALIASES[alias] = verb


def get_handler(verb: str) -> Optional[CommandHandler]:
    """
    Return a handler for the given verb, resolving aliases.
    
    Args:
        verb: The command verb to look up
    
    Returns:
        CommandHandler function or None if not found
    """
    base = COMMAND_ALIASES.get(verb, verb)
    return COMMAND_HANDLERS.get(base)

