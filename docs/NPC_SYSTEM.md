# NPC_SYSTEM.md
### How the NPC system works in Aethermoor

This document explains how NPCs (non-player characters) are defined, tracked and controlled in the current `web3_mud` / Aethermoor codebase.

It focuses on how **templates**, **dynamic state**, and **AI behaviour** fit together.


Not all NPCs are AI-enhanced:

- Some NPCs use **scripted dialogue and behaviours only**.  
- Others are **AI-enhanced**, calling out to OpenAI via `ai_client.py` using the configured API key.  
- Both types share the same template/state model; the difference is in how their responses and decisions are generated.

When you add or modify NPCs, you should decide explicitly whether each one is AI-enhanced or purely scripted, and ensure they inherit or call the correct helper functions to enable the right behaviour.


---

## 1. NPC templates and definitions

### 1.1 Where NPC templates live today

At the moment, NPC templates are primarily defined in Python:

- `npc.py`

You will typically see a structure like:

```python
NPCS = {
    "innkeeper": {
        "name": "Mara",
        "title": "Innkeeper of the Rusty Tankard",
        "realm": "sunward",
        "description": "...",
        "personality": { ... },
        "dialogue": { ... },
        "use_ai": True,
        # etc.
    },
    # more NPCs...
}
```

Key points:

- `NPCS` is a dictionary of template data.  
- These templates describe what an NPC **is like** (appearance, personality, default lines, stats).  
- They do *not* track where an NPC currently is or what it is doing – that is dynamic state.

In the future, these templates may move into JSON (e.g. `world/npcs/*.json`), but for now they are Python dicts.

---

## 2. NPC dynamic state (`game/state.py`)

NPC runtime state lives in global structures in `game/state.py`, such as:

- `NPC_STATE` – current room, HP, stance, flags, etc.  
- `NPC_ACTIONS_STATE` – queued actions for NPCs (e.g. walk here, say this, emote).  
- `NPC_LAST_ACTION_TIME` (or similar) – used to avoid spamming actions every tick.

These structures answer questions like:

- “Where is this NPC right now?”  
- “Is this NPC alive, wounded, hostile?”  
- “What is this NPC about to do?”  

The engine and NPC systems use this state to decide behaviour each tick and in response to player actions.

---

## 3. NPC entities and helper functions

Most NPC-related behaviour is implemented in:

- `npc.py` – template handling, basic logic, sometimes helper functions for reactions.  
- `npc_actions.py` – scheduling and processing queued NPC actions.  
- `game/state.py` – state structures and possibly state helper functions.

Common patterns:

- **Matching an NPC in a room**:

  ```python
  match_npc_in_room(room_id, partial_name)
  ```

  – used when a player targets “guard” or “innkeeper” in the current room.

- **Getting a reaction**:

  ```python
  get_npc_reaction(player, npc, message_context)
  ```

  – used when a player talks to or otherwise interacts with an NPC.

- **Enqueuing actions**:

  ```python
  schedule_npc_action(npc_id, action_type, payload)
  ```

  – an action might be “move to room X”, “say line Y”, “emote”, etc.

- **Processing NPC actions**:

  ```python
  process_npc_actions()
  ```

  – usually called on a regular tick to actually execute scheduled actions.

Depending on the current refactor state, some of these may be standalone functions, part of a small manager, or candidates to move into a `game/systems/npc_system.py` module.

---

## 4. AI-enhanced NPC dialogue (`ai_client.py`)

Some NPCs use LLM-backed dialogue instead of (or in addition to) fixed lines.

Key file:

- `ai_client.py`

Typical flow:

1. The engine or NPC system determines that an NPC should respond (e.g. the player says something).  
2. It gathers **context**:
   - NPC template (name, role, personality, realm).  
   - Room context (where they are, current weather/time if relevant).  
   - Recent player messages or actions.  
3. It builds a prompt and calls into `ai_client.py`.  
4. The AI model returns a line or set of lines.  
5. The engine sends that text back to the player and possibly broadcasts it to others in the room.

Important for agents:

- Prompts must keep NPCs **in-character** and **within lore** (Three Realms, Threadsinging, the Sundering, technology level).  
- Avoid modern references or out-of-world knowledge unless explicitly intended.

---

## 5. NPC movement and behaviour over time

NPC behaviour that unfolds over time is usually implemented via:

- `NPC_ACTIONS_STATE` – queued actions.  
- `NPC_ROUTE_POSITIONS` (if present) – track progress along a path.  
- A tick-based processor – e.g. `process_npc_actions()` called periodically.

Typical behaviours:

- Patrol routes (an NPC walking a fixed loop of rooms).  
- Idle chatter (occasionally saying or emoting something).  
- Reacting to weather/time (going indoors when it rains, closing shop at night).  
- Quest-related behaviour (moving to a location, waiting for the player).

These behaviours often interact with:

- **World time** (`game/time.py`).  
- **Weather** (`game/weather/`).  
- **Quests** (quest state in `game/state.py` or `game/quests/`).

---

## 6. Interaction with the engine

When a player interacts with an NPC (e.g. `talk innkeeper`, `attack guard`):

1. The engine identifies the target NPC using something like `match_npc_in_room`.  
2. It loads the NPC template from `NPCS` and current state from `NPC_STATE`.  
3. It chooses the appropriate behaviour:
   - Dialogue via fixed lines.  
   - AI dialogue via `ai_client.py`.  
   - Combat via a combat system.  
   - Quest-related logic.  
4. It may enqueue future NPC actions (e.g. NPC walks away later, triggers a reaction on a timer).  
5. It sends the immediate response text to the player and any broadcasts to others in the room.

---

## 7. Future direction for NPCs

The desired direction for NPC architecture is:

- **Templates in JSON**:
  - Move NPC templates from `npc.py` into something like `world/npcs/*.json`.  
  - Keep Python for behaviour logic only.

- **Dedicated NPC system module**:
  - Introduce `game/systems/npc_system.py` to:
    - Manage NPC state and actions.  
    - Provide a clean API for movement, spawning, and reactions.

- **Entity classes**:
  - Add an `NPC` class under `game/models/npc.py` that combines:
    - Template data.  
    - Dynamic state from `NPC_STATE`.  
    - Behaviour helpers.

- **State abstraction**:
  - Access NPC state via a `StateStore`-style abstraction to support Redis in future.

When writing new NPC-related code now:

- Prefer adding helper functions or small modules rather than more logic in `game_engine.py`.  
- Keep AI prompts and behaviours consistent with Aethermoor’s lore and each NPC’s defined personality.  
- Design with the eventual `NPCSystem` / `NPC` model in mind (so the refactor will be easier, not harder).
