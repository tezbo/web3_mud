# ENGINE_OVERVIEW.md
### How the Aethermoor MUD engine works today

This document describes how the engine *currently* works in the `web3_mud` / Aethermoor project.  
It is a factual snapshot intended for both humans and AI agents.

---

## 1. High-level architecture

The engine has three main layers:

1. **Driver layer** – Flask + Socket.IO + Redis glue that handles network I/O.  
2. **Engine layer** – the orchestration logic that processes commands and coordinates systems.  
3. **Systems & models layer** – focused modules and classes implementing specific game features.

---

### 1.1 Driver layer (Flask, Socket.IO, Redis)

Key files:

- `app.py` – primary app entrypoint (websocket server, HTTP endpoints).  
- Socket.IO event handlers – receive text from clients and send responses back.  
- `core/redis_manager.py` – manages Redis connections and is used by Socket.IO for scalable message queues.

Responsibilities:

- Accept a player’s input string from the client.  
- Identify the session / player.  
- Pass that input into the engine layer for processing.  
- Send back output messages (room descriptions, chat, combat results, errors).

Game logic does *not* live here – this layer is mostly plumbing.

---

### 1.2 Engine layer (`game_engine.py`)

`game_engine.py` is currently the main orchestration module. It:

- Receives a single player input line and their session/player ID.  
- Locates the corresponding player object and room.  
- Parses the input using the command dispatch/registry.  
- Calls into appropriate systems (movement, combat, inventory, NPC interaction, etc.).  
- Writes updates into shared state in `game/state.py` and/or model instances.  
- Returns text output and broadcast events back to the driver layer.

Over time, more and more logic is being pulled out of `game_engine.py` into smaller, focused modules under `game/` and `game/systems/`. The long-term goal is to leave `game_engine.py` as a thin orchestrator only (and ultimately, to replace it entirely once the modular architecture is complete, as described in `docs/REFACTOR_PLAN.md`).

---

### 1.3 Systems & models layer (`game/`, `game/systems/`, `game/models/`)

This layer holds the *actual* implementation of game mechanics.

Typical examples:

- **World/time/weather helpers** – e.g. `game/time.py`, `game/weather/weather_system.py`.  
- **State helpers** – `game/state.py` (dynamic state globals), plus any helper functions that read/write them.  
- **Inventory system** – e.g. `game/systems/inventory_system.py` providing an `InventorySystem` class used by models.  
- **Room callbacks** – `room_callbacks.py` (scripted per-room behaviour hooks).  
- **Onboarding** – `onboarding.py` (new player experience).  
- **Command registry** – `command_registry.py` (command registration and dispatch helpers).

**Models** under `game/models/` encapsulate core game entities:

- `game/models/player.py` – `Player` class.  
- `game/models/item.py` – `Item` and container classes.  
- `game/models/room.py` (or equivalent) – `Room` class that combines static templates with dynamic state and provides helpers such as `get_entrance_message()` / `get_exit_message()`.

Models typically:

- Hold per-entity state (e.g. a player’s inventory, stats, current room).  
- Delegate shared logic (e.g. inventory operations) to systems like `InventorySystem`.  
- Provide convenience methods that hide low-level state details from the engine.

---

## 2. Static templates vs runtime entities vs shared state

The engine distinguishes between:

1. **Static templates** – world definition from JSON.  
2. **Runtime entities** – Python model instances representing specific players, rooms, items.  
3. **Shared dynamic state** – global structures in `game/state.py` that track world-wide information.

---

### 2.1 Static world templates (JSON)

Files:

- `world/world_index.json`  
- `world/rooms/*.json`

Loader:

- `world_loader.py` – parses JSON and creates in-memory templates.  
- `game/world/data.py` – usually exposes the `WORLD` mapping of room IDs to template dicts.

Static templates include:

- Room ID and name.  
- Short and long descriptions.  
- Exits and their directions.  
- Flags like `outdoors`, `realm`, `area`, etc.  
- Optional per-room metadata used by callbacks.

Templates are **immutable** at runtime – they represent the designed world, not the current state of it.

---

### 2.2 Runtime entities (models)

Models represent **specific instances** that exist during play. For example:

- A `Player` object for each connected player/character.  
- `Room` objects used during movement/description, derived from a JSON template plus dynamic state.  
- `Item` objects in inventories or lying in rooms.

Models often:

- Hold references into `game/state.py` (e.g. room IDs, item IDs).  
- Use systems like `InventorySystem` for nested contents and weight calculations.  
- Provide methods the engine calls to encapsulate behaviour (e.g. `Player.move_to(room_id)`).

The combination of **template + model + shared state** is what gives each room, item and character its full meaning at runtime.

---

### 2.3 Shared dynamic state (`game/state.py`)

`game/state.py` contains global data structures used by many systems. Examples include:

- `ROOM_STATE` – items present in each room, transient flags.  
- `NPC_STATE`, `NPC_ACTIONS_STATE` – NPC positions, health, queued actions.  
- `QUEST_GLOBAL_STATE`, `QUEST_SPECIFIC_ITEMS` – quest progression.  
- `GAME_TIME`, `WORLD_CLOCK`, `WEATHER_STATE` – world-level simulation.  
- `EXIT_STATES` – doors, locks, one-way paths, blocked exits, etc.

Even where models exist, these global structures are still the authoritative source of shared truth for world-wide state. Models and systems must cooperate with these structures rather than silently duplicating state.

---

## 3. Game loop and command flow

### 3.1 From client message to engine

1. Client sends a line of text over Socket.IO.  
2. Driver layer (in `app.py`) receives the event and identifies the session/player.  
3. It calls a function in `game_engine.py` (e.g. `process_user_input(session_id, text)`).

### 3.2 Within `game_engine.py`

Inside `process_user_input` (or equivalent):

1. Look up the `Player` object and their current room ID.  
2. Parse the input using the command registry/dispatch system.  
3. Call the appropriate command handler (movement, inventory, combat, socials, etc.).  
4. Use systems and models to perform the requested action.  
5. Update state in `game/state.py` and/or model instances.  
6. Build textual output for the acting player.  
7. Build broadcast messages for other players/NPCs in affected rooms (movement, combat, chatter).  
8. Return all output to the driver layer for sending to clients.

---

## 4. Time, weather, NPCs and ticks

Some systems progress over time via ticks:

- **World time / calendar** – handled in `game/time.py` and related helpers.  
- **Weather** – handled in `game/weather/` modules; may depend on realm, region, and season.  
- **NPC behaviour** – idle movement, chatter, reactions; usually scheduled via NPC state and action queues.  
- **Corpse decay / temporary entities** – cleaned up on schedule.  
- **Quest timers** – time-limited objectives or world events.

Ticks are usually scheduled via background tasks started from `app.py` and/or the engine initialisation code.

---

## 5. Redis usage

Currently:

- Redis is used primarily by Flask-Socket.IO for message queues and room membership at the network level.  
- Game state itself still lives in process memory (`game/state.py`).

Planned (see also `docs/REFACTOR_PLAN.md`):

- Introduce a `StateStore` abstraction that hides whether state comes from globals or Redis.  
- Gradually migrate world state (rooms, NPCs, players, weather, etc.) into Redis behind that abstraction.

When adding new logic that interacts heavily with shared state, prefer to call small helper functions or a `StateStore`-style API rather than writing directly into global dicts from scattered locations.

---

## 6. Long-term direction

The current engine is **functional** but evolving. The long-term direction is:

- `game_engine.py` becomes thinner and eventually is decommissioned once all subsystems live under `core/`, `game/systems/` and `game/models/`.  
- Core systems (combat, NPCs, navigation, inventory, quests) live under `game/systems/`.  
- Models (`Player`, `Room`, `Item`, `NPC`) live under `game/models/`.  
- Templates (rooms, NPCs, items) live in JSON under `world/`.  
- State is provided through a `StateStore` abstraction, backed by Redis at scale.

Any new code you write should make that future easier, not harder.


---

## 7. See also

- `docs/ARCHITECTURE.md` – high-level architecture and philosophy.  
- `docs/WORLD_STATE_AND_PERSISTENCE.md` – how world data and state fit together.  
- `docs/NPC_SYSTEM.md` – how NPCs and AI-enhanced behaviour are wired in.  
- `docs/WEBSOCKET_CLIENT_EXAMPLE.md` – example of connecting to the engine via WebSockets.
