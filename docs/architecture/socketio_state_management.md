# SocketIO State Management & Room Transitions

## Problem: The "Ghost in the Room" Race Condition
In a real-time WebSocket environment, relying on the client to report its previous state (e.g., "I am leaving Room A") is unreliable and prone to race conditions.

### The Scenario
1.  Player is in `Room A` (Outdoor).
2.  Player moves to `Room B` (Indoor).
3.  Client sends a `command` event to move.
4.  Client *should* send `current_room: Room A` in the payload.

**The Bug:** If the client sends `current_room: None` (e.g., on first load, or due to a client-side state bug) or stale data, the server:
1.  Adds the player to `Room B` channel.
2.  **Fails to remove** the player from `Room A` channel.

**The Result:** The player is now subscribed to **both** rooms. They receive weather events for `Room A` while sitting in `Room B`, creating "indoor weather" bugs that are impossible to fix by checking room properties alone.

## Architectural Rule: Authoritative Server-Side State
**NEVER rely on client-provided data for state transitions.**

The server must maintain the "Source of Truth" for where a player is.

### Implementation Pattern
In `core/socketio_handlers.py`, we maintain a `CONNECTION_STATE` dictionary:

```python
CONNECTION_STATE = {
    "username": {
        "room_id": "town_square",  # <--- Authoritative Location
        "is_connected": True,
        "last_activity": datetime.now()
    }
}
```

### Correct Transition Logic
When a player moves:
1.  **Lookup** the player's current room from `CONNECTION_STATE`.
2.  **Leave** that room channel (if it exists).
3.  **Join** the new room channel.
4.  **Update** `CONNECTION_STATE` with the new room.

```python
# BAD (Vulnerable to race conditions)
old_room_id = data.get('current_room') 

# GOOD (Server Authority)
old_room_id = CONNECTION_STATE[username].get("room_id")
```

## Prevention
Any new WebSocket handler that involves state changes (joining/leaving rooms, trading, combat) must always look up the current state from the server's memory or database, never from the client's request payload.
