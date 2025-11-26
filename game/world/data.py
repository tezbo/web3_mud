"""
World Data Module
Loads and provides access to the static world definition.
"""
import sys
import json
from pathlib import Path

# Directory that stores per‑realm JSON files
_REALM_DATA_DIR = Path(__file__).parent / "realm_data"

def _ensure_realm_dir() -> None:
    """Create the realm_data directory and placeholder JSON files if they are missing."""
    _REALM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for realm in ["shadowfen", "sunward", "twilight"]:
        file_path = _REALM_DATA_DIR / f"{realm}.json"
        if not file_path.exists():
            file_path.write_text("{}", encoding="utf-8")

def _load_realm_file(path: Path) -> dict:
    """Load a single realm JSON file, returning an empty dict on error.
    The file should contain a mapping of room_oid -> room_data.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"WARNING: Could not load realm file {path}: {e}", file=sys.stderr)
        return {}

def load_world_from_json() -> dict:
    """Load all realm JSON files and merge them into a single dict.
    The resulting dict uses the room OID as the key, regardless of realm.
    """
    world: dict = {}
    for realm_file in _REALM_DATA_DIR.glob("*.json"):
        realm_data = _load_realm_file(realm_file)
        world.update(realm_data)
    return world

def register_room_in_realm(
    oid: str,
    name: str,
    description: str,
    exits: dict,
    realm: str = "shadowfen",
    outdoor: bool = False,
) -> None:
    """Add or update a room entry in the appropriate realm JSON file.
    The function writes the updated dict back to disk so that subsequent loads
    will include the new room.
    """
    _ensure_realm_dir()
    realm_file = _REALM_DATA_DIR / f"{realm.lower()}.json"
    data = _load_realm_file(realm_file)
    data[oid] = {
        "type": "Room",
        "name": name,
        "description": description,
        "exits": exits,
        "outdoor": outdoor,
    }
    try:
        with open(realm_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: Failed to write room to {realm_file}: {e}", file=sys.stderr)

# Ensure the directory and base files exist at import time
_ensure_realm_dir()

try:
    WORLD = load_world_from_json()
except Exception as e:
    print(f"ERROR: Failed to load world data: {e}", file=sys.stderr)
    WORLD = {}
