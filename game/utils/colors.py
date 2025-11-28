"""
Color markup utilities for web client.
Replaces ANSI codes with HTML-friendly tags.
"""

def room(text: str) -> str:
    """Wrap text in room color tag."""
    return f"[ROOM_DESCRIPTIONS]{text}[/ROOM_DESCRIPTIONS]"

def item(text: str) -> str:
    """Wrap text in item color tag."""
    return f"[ITEM]{text}[/ITEM]"

def npc(text: str) -> str:
    """Wrap text in npc color tag."""
    return f"[NPC]{text}[/NPC]"

def error(text: str) -> str:
    """Wrap text in error color tag."""
    return f"[ERROR]{text}[/ERROR]"

def system(text: str) -> str:
    """Wrap text in system color tag."""
    return f"[SYSTEM]{text}[/SYSTEM]"

def player(text: str) -> str:
    """Wrap text in player color tag."""
    return f"[PLAYER]{text}[/PLAYER]"

def speech(text: str) -> str:
    """Wrap text in speech color tag."""
    return f"[SAY]{text}[/SAY]"

def exit_name(text: str) -> str:
    """Wrap text in exit color tag."""
    return f"[EXITS]{text}[/EXITS]"
