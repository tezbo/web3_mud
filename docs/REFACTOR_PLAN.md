# Refactor Plan: Decommissioning game_engine.py

**Objective:** Completely dismantle the legacy `game_engine.py` monolith and migrate all functionality to the new modular architecture (`core/`, `game/systems/`, `game/models/`).

**Status:** In Progress
**Target Architecture:** Hybrid Object-Oriented (Logic) + JSON (Data)

---

### Phase 1: Inventory & Items (COMPLETE)
- [x] **Goal:** Move inventory logic out of `game_engine.py` into `game/systems/inventory.py`.
- [x] **Tasks:**
    - [x] Create `game/systems/inventory.py` (or `inventory_system.py`).
    - [x] Implement `InventorySystem` class with weight/capacity logic.
    - [x] Update `Item` model to use `InventorySystem` (for containers).
    - [x] Update `Player` model to use `InventorySystem`.
    - [x] Update `Room` model to use `InventorySystem` (for room contents).
    - [x] Refactor `game_engine.py` to use these new models for inventory commands.
    - [x] **Verification:**
        - [x] Unit tests for `InventorySystem`.
        - [x] Integration tests for `Player` and `Room`.
        - [x] Manual/Agent verification of `inventory`, `take`, `drop` commands.

## Phase 2: Combat System
**Goal:** Encapsulate combat logic in a dedicated system.
*   [ ] Create `game/systems/combat.py` (or enhance existing).
*   [ ] Move combat functions:
    *   `calculate_damage`
    *   `resolve_attack`
    *   `handle_death`
    *   `get_weapon_stats`
*   [ ] Implement `CombatSystem` class to manage state.

## Phase 3: NPC System
**Goal:** Move NPC AI and behavior to a dedicated manager.
*   [ ] Create `game/systems/npc_system.py`.
*   [ ] Move NPC functions:
    *   `process_npc_movements`
    *   `get_npc_reaction`
    *   `spawn_npc`
*   [ ] Ensure NPCs use the `AtmosphericManager` for weather reactions.

## Phase 4: Player Management
**Goal:** Centralize player state and persistence.
*   [ ] Enhance `game/models/player.py`.
*   [ ] Move player functions:
    *   `create_character`
    *   `save_player`
    *   `load_player`
    *   `update_stats`
    *   `calculate_level`

## Phase 5: Command Processing
**Goal:** Create a robust Command Pattern parser.
*   [ ] Create `core/command_parser.py`.
*   [ ] Extract the massive `handle_command` function.
*   [ ] Create individual Command classes (e.g., `LookCommand`, `MoveCommand`, `GetCommand`).
*   [ ] Register commands in a `CommandRegistry`.

## Phase 6: World & Navigation
**Goal:** Finalize world loading and movement logic.
*   [ ] Ensure `game/world/` handles all map loading.
*   [ ] Move navigation logic (`move_player`, `get_exits`) to `game/systems/navigation.py`.

## Phase 7: Final Cleanup
**Goal:** Delete the monolith.
*   [ ] Verify `game_engine.py` is empty or only contains re-exports.
*   [ ] Update `app.py` to import directly from new modules.
*   [ ] Delete `game_engine.py`.

---

# Work Log

## 2025-11-27: Phase 1 - Inventory & Items

### 1. Inventory System Implementation
**Intent:** Create a robust, reusable inventory system that handles weight, capacity, and nesting.
**Rationale:** The legacy `game_engine.py` had ad-hoc functions for weight calculation. We needed a proper Object-Oriented system that supports containers-in-containers (like Discworld) and centralized logic.
**Action:**
*   Created `game/systems/inventory.py`: Moved item definitions and utility functions (pluralization, matching) from `game_engine.py`.
*   Created `game/systems/inventory_system.py`: Implemented the `InventorySystem` class with recursive weight calculation and circular dependency checks.
*   Created `tests/test_inventory.py`: Verified the system with unit tests.

### 2. Model Integration
**Intent:** Update Game Objects (`Item`, `Player`) to use the new `InventorySystem`.
**Rationale:** Models were using simple lists (`[]`) for inventory, which lacked validation (weight limits) and logic.
**Action:**
*   Refactored `game/models/item.py`:
    *   `Item` now has an optional `inventory` attribute.
    *   `Container` now uses `InventorySystem` instead of a list.
    *   `total_weight` property now recursively calculates weight.
*   Refactored `game/models/player.py`:
    *   Replaced `self.inventory = []` with `self.inventory = InventorySystem()`.
    *   Updated `take_item`, `drop_item`, `give_item` to use the new system.
*   Created `tests/test_item_model.py` and `tests/test_player_inventory.py`: Verified integration.

### 3. Legacy Compatibility
**Intent:** Ensure existing code in `game_engine.py` still works during the transition.
**Rationale:** We can't break the running game while refactoring.
**Action:**
*   Updated `game_engine.py` to import item definitions and functions from `game/systems/inventory.py` instead of defining them locally.


### Session 2 (Current)
- **Architecture:** Solidified "Modern LPC" approach (Python composition + JSON data).
- **Refactor:**
    - Created `game/systems/inventory_system.py` with recursive weight and capacity checks.
    - Integrated `InventorySystem` into `Item`, `Player`, and `Room` models.
    - Added `__iter__` to `InventorySystem` to support legacy iteration in `game_engine.py`.
    - **Movement Messages:** Refactored entrance/exit messages to be Room-owned behavior:
        - Added `get_entrance_message()` and `get_exit_message()` methods to `Room` class.
        - Updated `Player.move()` to use Room methods instead of global `get_entrance_exit_message()`.
        - Messages are now customizable per-room via JSON (architecture alignment).
- **Fixes:**
    - Resolved 500 Error during onboarding (transient port conflict).
    - Fixed `inventory` command crash by making `InventorySystem` iterable.
    - Fixed `NameError: name 'get_entrance_exit_message' is not defined` by moving logic to Room objects.
    - Fixed `NameError: name 'OPPOSITE_DIRECTION' is not defined` by adding import to Player model.
    - Cleaned up duplicate `* 2.py` files in `agents/` and `ai/`.
- **Verification:**
    - All unit tests passed.
    - `debug_repro.py` confirmed full onboarding and inventory flow works.
    - `debug_movement.py` confirmed movement and entrance/exit broadcasts work correctly.

