# WORLD_STATE_AND_PERSISTENCE.md
### Templates, runtime state, and persistence in Aethermoor

This document explains how Aethermoor represents the game world, where state lives, and how it is saved and restored.

---

## 1. Pieces of the world model

There are three main pieces to the world model:

1. **Static templates** – JSON-defined blueprint data.  
2. **Runtime entities** – Python model instances (Player, Room, Item, etc.).  
3. **Shared dynamic state** – global structures in `game/state.py`.

Understanding how these fit together is critical for making safe changes.

---

## 2. Static templates (JSON)

Static templates define what the world *can* be, not what it *currently is*.

### 2.1 Location

- `world/world_index.json` – high-level index/metadata about areas and rooms.  
- `world/rooms/*.json` – per-room JSON definitions.

Loaded by:

- `world_loader.py` → which builds in-memory structures.  
- `game/world/data.py` → which typically exposes `WORLD`, a mapping of room IDs to template dicts.

### 2.2 What templates contain

Room templates generally include:

- Room ID, title/name.  
- Short and long descriptions.  
- Realm / region / area tags (e.g. Sunward, Twilight, Shadowfen).  
- Exits and which room IDs they point to.  
- Basic flags: `outdoors`, difficulty level, special tags.  
- Optional metadata for callbacks (e.g. scripted behaviour keys).

Key rules:

- Templates are **read-only at runtime**.  
- Templates do **not** contain executable logic – only data.  
- If you need behaviour, put it in Python (e.g. `room_callbacks.py`) and reference it via template metadata if needed.

---

## 3. Runtime entities (models)

Runtime entities are Python objects that encapsulate the current state and behaviour of specific things in the game.

Common models:

- `Player` – from `game/models/player.py`.  
- `Item` / container models – from `game/models/item.py`.  
- `Room` – from `game/models/room.py` (or equivalent).

### 3.1 How models relate to templates and state

Typically:

- A **Room** model:
  - Knows its `room_id`.  
  - Pulls static data from the JSON template (via `WORLD[room_id]` or a helper/registry).  
  - Looks up dynamic information in `ROOM_STATE[room_id]` (items present, flags) and/or other state structures.  
  - Provides helper methods such as `describe()`, `get_entrance_message()`, etc.

- A **Player** model:
  - Knows its `player_id` and current `room_id`.  
  - Holds an `InventorySystem` instance for items carried.  
  - Contains stats, health, etc., sometimes mirrored or complemented by global state.

- An **Item** model:
  - May be a simple object or a container that uses `InventorySystem`.  
  - Can compute `total_weight` and answer questions like “can this item fit here?”.

The models are the main way the engine and systems **reason about** entities, but they are not the only holders of state. They must stay in sync with the shared dynamic state in `game/state.py`.

---

## 4. Shared dynamic state (`game/state.py`)

`game/state.py` is the *authoritative* location for shared world state, especially things that multiple systems need to see or change.

Examples include:

- `ROOM_STATE` – items on the ground, per-room flags, temporary markers.  
- `NPC_STATE` – NPC health, positions, moods, timers.  
- `NPC_ACTIONS_STATE` – queued NPC behaviours (move here, speak there).  
- `GAME_TIME`, `WORLD_CLOCK` – current day, time of day, etc.  
- `WEATHER_STATE` – current weather per region/realm.  
- `EXIT_STATES` – whether certain doors/exits are locked, blocked, or altered.  
- `QUEST_GLOBAL_STATE`, `QUEST_SPECIFIC_ITEMS` – quest progress.

Important:

- The state here is **process-local** for now – each running game server keeps its own copy in memory.  
- Many systems, including models, should treat these structures as the source of truth when multiple actors can modify the same thing.

---

## 5. Persistence (saving & loading)

Persistence currently happens via a JSON snapshot file:

- `mud_state.json`

### 5.1 Saving

On shutdown (or at certain checkpoints):

1. Relevant structures from `game/state.py` are gathered.  
2. They are serialised into JSON and written to `mud_state.json`.  
3. This represents the *current world* at the moment of shutdown.

This means:

- NPC positions, room contents, quest state, time/weather, etc. can all be restored.

### 5.2 Loading

On startup:

1. Static templates are loaded from `world/world_index.json` and `world/rooms/*.json` into `WORLD`.  
2. A default dynamic state is initialised in `game/state.py`.  
3. If `mud_state.json` exists:
   - Its contents are read and used to update `game/state.py`.  
   - This merges the saved state back in so the world continues from where it stopped.

If the save file is missing or invalid, the game will start from a “fresh” world using only the static templates and default state.

---

## 6. Redis and future state management

### 6.1 Current situation

At present:

- Redis is mainly used as a backend for Socket.IO (network-level rooms, message queues).  
- Game state itself is still only in process memory (`game/state.py`).

### 6.2 Planned direction

The long-term plan is:

1. Introduce a `StateStore` abstraction in something like `game/state_store.py` that provides methods such as:

   ```python
   class StateStore:
       def get_room_state(self, room_id): ...
       def set_room_state(self, room_id, state): ...
       def get_npc_state(self, npc_id): ...
       def set_npc_state(self, npc_id, state): ...
       # etc.
   ```

2. Initially implement `StateStore` using the existing globals in `game/state.py`.  
3. Later, add a Redis-backed implementation that stores state in Redis keys/hashes/sets while keeping the same interface.


### 6.3 Render deployment and DevOps responsibilities

The current live environment for Aethermoor is hosted on **Render**:

- **Application service (websocket + HTTP app):**  
  - Render dashboard URL: `https://dashboard.render.com/web/srv-d4gn2sf5r7bs73bcbqfg`  
  - Entry-point process uses `app.py` inside this repository.

- **Redis instance (shared infrastructure backend):**  
  - Render dashboard URL: `https://dashboard.render.com/r/red-d4i0m6fdiees73brqu00`  
  - Used today by Socket.IO for message queues and rooms.  
  - Future state-store implementations may use this instance as the backing store for world state.

**DevOps agent responsibilities:**

- Never hard-code Redis credentials or connection strings in the repo – always use environment variables configured via the Render dashboard.  
- Use the Render dashboard to:
  - Inspect logs for the application service and Redis instance.  
  - Monitor health, restarts, and resource usage.  
  - Trigger manual deploys/restarts if required (after code changes are merged).  
- When adding new persistence or state features:
  - Design them to work locally (using in-process `game/state.py`).  
  - Provide a clear path to using the Render Redis instance via a `StateStore` abstraction, without baking Render-specific details into game logic modules.


**For AI agents and contributors:**

- When adding new features that need shared state, strongly prefer to:
  - Add a helper function in `game/state.py`, or  
  - Use (or extend) the future `StateStore` abstraction,

rather than directly manipulating global dicts all over the codebase.

---

## 7. Practical guidelines for contributors

When working with world data:

1. **Do not modify JSON templates at runtime.**  
2. **Do not put logic in JSON.** JSON is data-only; behaviour goes in Python.  
3. **Use models where they exist** (Player, Room, Item) instead of ad-hoc dicts.  
4. **Treat `game/state.py` as the shared truth** for anything that multiple systems may touch.  
5. **Do not change the save format (`mud_state.json`) without an explicit migration plan and owner approval.**  
6. **When in doubt, ask** – especially before altering persistence or state structures.
