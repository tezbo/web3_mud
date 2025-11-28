# Aethermoor / web3_mud Architecture & Master Plan

**Status:** Active Development
**Architecture Pattern:** Hybrid Object-Oriented (Logic) + JSON (Data)
**Legacy Status:** Migrating from Monolithic (`game_engine.py`) to Modular (`core/`, `game/`)

---

## 1. Core Philosophy
We are building a scalable, maintainable MUD engine that combines the best of classic Object-Oriented MUD design (like Discworld/LPC) with modern software engineering practices.

### The Separation of Logic and Data
*   **Behavior (.py):** Defines *how* things work.
    *   `Room` class: Handles looking, entering, exiting.
    *   `NPC` class: Handles combat, dialogue, movement.
    *   `WeatherSystem`: Handles atmospheric changes.
*   **Content (.json):** Defines *what* exists.
    *   `world/map.json`: Contains room descriptions, exit links, and static items.
    *   `data/items.json`: Defines sword stats, potion effects, etc.

### Object-Oriented Structure
*   **Game Entities:** All physical things inherit from a base `GameObject` (or similar interface).
*   **Systems:** Global mechanics are managed by dedicated Systems (e.g., `AtmosphericManager`, `CombatSystem`).

---

## 2. Architectural Alignment: The "Modern LPC" Approach
We are building a modern, Pythonic interpretation of the classic LPC (LPMud) architecture used by Discworld.

| Feature | Discworld (LPC) | Web3 MUD (Python) | Philosophy |
| :--- | :--- | :--- | :--- |
| **The "Driver"** | C Program (Networking, I/O) | `core/` (SocketIO, Event Bus) | Handles low-level machinery. Agnostic to game rules. |
| **The "Mudlib"** | LPC Code (`/std/room.c`) | `game/` (`models/room.py`) | Defines the game rules, logic, and entity behaviors. |
| **Objects** | Persistent LPC Objects | Persistent Python Objects | The world is a collection of "living" objects in memory. |
| **Code Reuse** | Deep Inheritance (`inherit "/std/room"`) | **Composition** (`self.weather = WeatherSystem()`) | Python favors "Has-A" over "Is-A" for flexibility. |
| **Content** | Hardcoded in `.c` files | **JSON Data** (`world/map.json`) | Separates *Logic* from *Data* for scalability and AI generation. |

### Key Principles
1.  **The "Object" Philosophy:** Just like in LPC, our world is made of persistent objects (`Room`, `Item`, `NPC`) that react to events.
2.  **Driver vs. Lib Separation:** We strictly separate the engine (`core/`) from the game implementation (`game/`).
3.  **Composition over Inheritance:** We use Python's strength (composition) to build complex entities without the "diamond of death" inheritance problems of old LPC MUDs.

---

## 3. Directory Structure

### `core/` (Infrastructure)
Foundational machinery that runs the simulation. Agnostic to specific game lore.
*   `event_bus.py`: Central event dispatching.
*   `state_manager.py`: Manages game state persistence.
*   `socketio_handlers.py`: Real-time networking logic.
*   `redis_manager.py`: Caching and pub/sub.

### `game/` (Implementation)
The specific implementation of the Aethermoor MUD (starting region: Hollowvale).
*   **`models/`**: OO Classes for game entities.
    *   `player.py`, `room.py`, `npc.py`, `item.py`.
*   **`systems/`**: Game mechanics and logic.
    *   `atmospheric_manager.py`: Time, Weather, Seasons.
    *   `combat.py`: Attack resolution.
    *   `quest_manager.py`: Quest tracking.
*   **`world/`**: JSON content and loaders.

### `agents/` (AI Ecosystem)
Autonomous agents that help build and maintain the game.
*   `devops.py`: Monitors deployment health.
*   `mapmaker.py`: Generates room layouts.
*   `lore_keeper.py`: Ensures narrative consistency.

### `app.py` (Entry Point)
The Flask web server and SocketIO entry point. Connects the web frontend to the `core` machinery.

### `game_engine.py` (DEPRECATED)
**Legacy Monolith.** Contains old logic for items, combat, and commands.
**Action:** actively being refactored and dismantled. Do not add new code here.

---

## 3. Refactor Roadmap: Decommissioning `game_engine.py`

**Objective:** Completely dismantle `game_engine.py` and migrate functionality to `core/` and `game/`.

### Phase 1: Inventory & Items (High Priority)
**Goal:** Centralize all item management logic.
*   [ ] Create `game/systems/inventory.py`.
*   [ ] Move item utility functions (`get_item_def`, `calculate_weight`, etc.) from `game_engine.py`.

### Phase 2: Combat System
**Goal:** Encapsulate combat logic.
*   [ ] Enhance `game/systems/combat.py`.
*   [ ] Move damage calculation and attack resolution from `game_engine.py`.

### Phase 3: NPC System
**Goal:** Move NPC AI and behavior.
*   [ ] Create `game/systems/npc_system.py`.
*   [ ] Move `process_npc_movements` and reaction logic.

### Phase 4: Player Management
**Goal:** Centralize player state.
*   [ ] Enhance `game/models/player.py` with creation/saving logic.

### Phase 5: Command Processing
**Goal:** Create a robust Command Pattern parser.
*   [ ] Create `core/command_parser.py`.
*   [ ] Extract `handle_command` from `game_engine.py`.

### Phase 6: Final Cleanup
**Goal:** Delete the monolith.
*   [ ] Update `app.py` imports.
*   [ ] Delete `game_engine.py`.

---

## 4. Current Progress
*   ✅ **Atmospheric Systems:** Fully refactored into `game/systems/atmospheric_manager.py`.
*   ✅ **Networking:** Moved to `core/socketio_handlers.py`.
*   ✅ **App Entry:** `app.py` reconstructed and modernized.
*   ✅ **Architecture:** Hybrid OO/JSON pattern established.
