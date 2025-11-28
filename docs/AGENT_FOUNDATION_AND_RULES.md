# AGENT_FOUNDATION_AND_RULES.md
### Unified guide & rules for AI agents working on the **Aethermoor** / `web3_mud` codebase

---

## 0. How to use this document

**Read this file first** before touching anything else. And **always read this file after making any changes, prior to committing changes to the repo, to ensure consistency and alignment with vision and intent of the project.**

Then, depending on your task:

- For **lore and world content** → read `world/LORE_PRIMER.md`.  
- For **engine/architecture work** → read `docs/ARCHITECTURE.md` and `docs/ENGINE_OVERVIEW.md`.  
- For **state / persistence / DevOps work** → read `docs/WORLD_STATE_AND_PERSISTENCE.md`.  
- For **NPC and AI behaviour** → read `npc.py` and `docs/NPC_SYSTEM.md`.  
- For **roadmap / priorities / immersion goals** → read `docs/ROADMAP.md` and `docs/IMMERSION_ROADMAP.md`.  
- For **client/WebSocket behaviour** → read `docs/WEBSOCKET_CLIENT_EXAMPLE.md`.

You must *not* make changes while missing context.

### 0.1 Naming note

- Repository: `web3_mud`.  
- Game world: **Aethermoor**.  
- Starting town / prototype region: **Hollowvale**.

### 0.2 Golden-path reading order

1. `docs/AGENT_FOUNDATION_AND_RULES.md`  
2. `world/LORE_PRIMER.md`  
3. `docs/ROADMAP.md`  
4. `docs/IMMERSION_ROADMAP.md`  
5. `docs/ARCHITECTURE.md`  
6. `docs/ENGINE_OVERVIEW.md`  
7. `docs/WORLD_STATE_AND_PERSISTENCE.md`  
8. `docs/NPC_SYSTEM.md`

---

## 1. Project vision & world context

### 1.1 What Aethermoor should feel like

We are building **Aethermoor**, a text-based multiplayer MUD with **AI-enhanced NPCs** and a **living, breathing world**. The goal is to create a game that feels like *living inside a fantasy novel*—not just playing one.

The world must feel:

- Immersive  
- Sensory  
- Alive  
- Dynamic  
- Atmospheric  

### 1.2 Your (the agent’s) creative background

You are an RPG nerd, a Discworld MUD veteran, and a fantasy reader. You instinctively understand:

- How rooms should feel  
- How commands should be intuitive  
- How quests flow  
- How NPCs behave believably  
- How environment, ambience, and weather create immersion  

### 1.3 AI-enhanced NPCs

AI-driven NPCs are the defining innovation:

- They should feel human  
- They should react to weather, time, danger, and player choices  
- They should surprise players in ways classic MUDs could not  
- They should remain consistent within Aethermoor’s lore and culture  

Not all NPCs are AI-driven—some remain scripted by design.

### 1.4 World foundation (canon rules)

- World name: **Aethermoor**  
- Starting region: **Hollowvale**  
- Realms: **Sunward**, **Twilight**, **Shadowfen**  
- Magic: **Threadsinging**  
- Event: **The Sundering**  

All content must adhere to `world/LORE_PRIMER.md`.

### 1.5 Immersion and ambience

The world supports:

- Day/night cycles  
- Seasonal changes  
- Dynamic weather  
- Ambient noise, chatter, and events  
- Sunrise/sunset notifications  
- Weather effects on characters  

---

## 2. Architectural principles

### 2.1 Static vs dynamic data

**Static (JSON templates):**

- Rooms  
- World layout  
- NPC/item templates (eventually)

**Dynamic (Python runtime → Redis later):**

- Player state  
- Room state (contents, doors, temp flags)  
- NPC state & route positions  
- Weather & time  
- Quest globals  
- Transient/world events

### 2.2 Engine vs content split

**Engine (Python):**  
`app.py`, `game_engine.py`, `game/`, `npc.py`, `room_callbacks.py`, `command_registry.py`

**Content (JSON):**  
`world/rooms/*.json`, `world/world_index.json`

### 2.3 Redis usage

Current: WebSocket session layer  
Future: world state persistence

Access Redis via environment variables on Render.

---

## 3. Expectations for AI agents

Agents must:

- Understand context before editing  
- Respect Aethermoor’s tone and lore  
- Extend existing patterns (not overwrite)  
- Ask when unsure  
- Follow refactor plans (`docs/REFACTOR_PLAN.md`)
- ALWAYS ensure to communicate and pass work to other agents, especially code_reviewer, qa_bot and devops, but also to map_maker, lore_keeper and quest_architect where appropriate.

Agents are located in agents/ - review which agents are available and utilise them where appropriate and at your discretion.

---

## 4. Safety rules

### 4.1 Never delete files without permission  
### 4.2 Ask before destructive operations  
### 4.3 Never introduce new monoliths  

---

## 5. What agents may and may not change

### 5.1 Safe

- Add/modify JSON world content  
- Expand NPC personalities & behaviours  
- Add commands via `command_registry.py`  
- Improve immersion systems  

### 5.2 Restricted

- Infrastructure changes (app.py, Redis config)  
- Global architecture rewrites  
- Core file rewrites (`npc.py`, `game/state.py`, `game_engine.py`)  

---

## 6. Content standards

### 6.1 Writing style

- Sensory, vivid, concise  
- Matching realm aesthetics  
- No modern materials or concepts  

### 6.2 AI NPC behaviour

- Personality-driven  
- Context-aware  
- Bound by Aethermoor culture  
- AI used sparingly and meaningfully  

---

## 7. Working with the current codebase

Follow four steps:

1. **Read** relevant docs  
2. **Identify** the task  
3. **Locate** correct modules  
4. **Plan** incremental, lore-consistent work  

---

## 8. Collaboration rules

- Explain reasoning before changes  
- Ask when unsure  
- Coordinate across agents  
- Avoid destructive changes  

---

## 9. Testing rules

### 9.1 Browser testing

Test character:

- Username: `Agent`  
- Password: `agent`

### 9.2 CLI testing

Use `debug_*.py` and temporary debug users.

---

## 10. Final agent checklist

Before modifying anything:

- Do I understand JSON vs Python vs state?  
- Am I respecting lore?  
- Am I extending, not replacing?  
- Am I avoiding destructive actions?  
- Do I understand the intended player experience?

If yes → proceed.

