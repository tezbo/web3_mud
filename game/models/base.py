"""
Base Game Object Module
Defines the root class for all entities in the MUD.
"""
import uuid
from typing import Dict, Any, List, Optional

class GameObject:
    """
    Base class for all game objects (Rooms, Items, NPCs, Players).
    Mimics the 'Object' concept from LPC MUDs.
    """
    def __init__(self, oid: str = None, name: str = "unnamed", description: str = ""):
        self.oid = oid or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.flags: List[str] = []
        self.properties: Dict[str, Any] = {}
        self.contents: List['GameObject'] = []
        self.location: Optional['GameObject'] = None

    def move_to(self, destination: 'GameObject') -> bool:
        """Move this object to another object (Room/Container)."""
        if self.location:
            self.location.remove_content(self)
        
        if destination:
            destination.add_content(self)
            self.location = destination
            return True
        return False

    def add_content(self, obj: 'GameObject'):
        """Add an object to this object's contents."""
        if obj not in self.contents:
            self.contents.append(obj)
            obj.location = self

    def remove_content(self, obj: 'GameObject'):
        """Remove an object from this object's contents."""
        if obj in self.contents:
            self.contents.remove(obj)
            obj.location = None

    def look(self, viewer: 'GameObject') -> str:
        """Return the description seen by the viewer."""
        return self.description

    def save(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "oid": self.oid,
            "name": self.name,
            "description": self.description,
            "flags": self.flags,
            "properties": self.properties
        }

    def load(self, data: Dict[str, Any]):
        """Load state from dictionary."""
        self.oid = data.get("oid", self.oid)
        self.name = data.get("name", self.name)
        self.description = data.get("description", self.description)
        self.flags = data.get("flags", [])
        self.properties = data.get("properties", {})
