# Aethermoor MUD – Immersion-First Roadmap

> This document focuses on **player experience and narrative feel**. It is the immersion design companion to `docs/ROADMAP.md` and assumes the lore defined in `docs/LORE_PRIMER.md`.

The examples often use **Hollowvale**, the starting town in Aethermoor, as the primary reference region.

---

## 0. What this document is (and is not)

This document **is**:

- A guide to how Aethermoor should **feel** to play.  
- A roadmap for **world ambience, NPC behaviour, combat feel and AI integration**.  
- A reference for writers, designers and AI agents working on immersion systems.

This document is **not**:

- A full lore bible – see `docs/LORE_PRIMER.md`.  
- The full feature roadmap – see `docs/ROADMAP.md`.  
- A Web3 or mobile strategy document – those concepts live in `docs/ROADMAP.md`.

When in doubt:

- Use this doc to answer **“how should this feel?”**  
- Use `docs/ROADMAP.md` to answer **“what are we building next?”**  
- Use `docs/LORE_PRIMER.md` to answer **“what is canon?”**

---

## 1. A Vision from a Discworld Veteran & AI Enthusiast

> *"The measure of a great MUD isn't in its systems — it's in the moment when a player forgets they're typing commands and feels like they're actually there."*

You (the designer/agent) are:

- A long-time MUD player (Discworld especially).  
- Someone who reads fantasy and can **see, smell and hear** the world in your head.  
- Deeply familiar with what makes text worlds **addictive, intuitive and consistent**.  
- Comfortable with AI and excited about what **AI-enhanced NPCs** can do that classic MUDs never could.

Aethermoor should let players:

- Smell the rain on stone in Hollowvale’s square.  
- Hear gossip drift out of Mara’s inn door.  
- Feel reluctant to log off because “just one more conversation” might change everything.

---

## 2. The Current State: What Exists vs the Immersion Gap

### ✅ Solid Foundation

You already have the bones of something special:

- **Object-oriented architecture** – refactors towards models and systems make immersive systems possible.  
- **AI-enhanced NPCs** – NPCs that can already surprise players.  
- **Living world systems** – time of day, weather, basic ambience.  
- **Modern infrastructure** – WebSocket, Redis, proper state management.  
- **Combat & death stubs** – fundamentals that can be made far more expressive.

### ❌ The Immersion Gap

As a Discworld veteran looking at the current experience:

1. **The world doesn’t breathe yet**
   - Rooms are functional, but not richly evocative.  
   - Sensory details (smells, sounds, textures) are sparse.  
   - NPCs exist, but don’t truly **live** or relate to each other.  
   - Objects are props, not treasures with history.

2. **Combat exists (or will exist) but doesn’t thrill**
   - Without choices and flavour, it becomes “roll until something dies”.  
   - Weapons and enemies feel generic rather than memorable.  
   - Fights don’t yet create “remember when…” stories.

3. **NPCs are smart, but not yet memorable**
   - They respond, but have shallow goals/desires.  
   - They remember facts more than they **care** about outcomes.  
   - They rarely interact with each other in front of the player.

4. **Quests are mechanical instead of engaging**
   - Fetch/kill/visit without enough context or stakes.  
   - Few moral choices, consequences or long-running arcs.  
   - NPCs rarely reference quest progress organically in conversation.

This roadmap closes that gap.

---

## 3. The Immersion-First Philosophy

Every feature should be judged against these questions:

1. **Does it make players feel something?**  
   Wonder, fear, joy, curiosity, accomplishment.

2. **Does it create stories players will tell?**  
   “You won’t believe what happened when I…”, not just “I gained +5 STR.”

3. **Does it make the world feel alive?**  
   Things happen that aren’t centred on the player; NPCs have lives.

4. **Does it reward engagement over grinding?**  
   Curiosity and attention should be more rewarding than repetition.

Implementation choices should favour **story and texture** over raw efficiency whenever reasonable.

---

## Phase I – Make the World Breathe (2–3 weeks)

> *Transform static rooms into living places.*

### 1.1 Sensory Room Descriptions 🌅

**Priority:** Critical · **Impact:** Transformative

**Current:**  
“You are in the town square.”

**Target:**  
“The town square bustles with activity. The scent of fresh bread wafts from Mara’s inn, mixing with the metallic tang of the blacksmith’s forge. Cobblestones, worn smooth by centuries of footsteps, gleam wetly after the morning rain. A weathered fountain burbles in the centre, its stone basin green with moss.”

**Implementation sketch:**

```python
class Room:
    def __init__(self, ...):
        self.base_description = ""  # core description
        self.sensory_details = {
            "sight": [],
            "sound": [],
            "smell": [],
            "touch": [],
            "taste": [],
        }
        self.atmosphere_overrides = {
            # e.g. ("night", "clear"): {...}, ("day", "rain"): {...}
        }

    def get_full_description(self, game_time, weather_state):
        # Combine base description, sensory details and any overrides
        ...
```

**Action items:**

- Add sensory fields to `Room` and/or room JSON templates.  
- Implement `get_full_description()` to blend base + sensory + time/weather variants.  
- Add small variants for morning/noon/evening/night and for key weather states.  
- **AI integration:** Use an AI helper to propose sensory details from existing base descriptions, then store them as data (not prompts) for repeatable output.

---

### 1.2 Objects with Stories 📿

**Priority:** High · **Impact:** High

**Goal:** Every item should reward curiosity.

**Example:**

```
> look sword
A rusty longsword, its blade pitted with age.

> examine sword closely
Along the hilt, you notice faded engravings:
"Forged in the Third Age for Captain Aldric Stormwind.
May it serve you as it served him — faithfully to the end."
The rust tells a story of long abandonment. How did it end up here,
in this forgotten cellar?
```

**Implementation sketch:**

```python
class Item:
    def __init__(self, ...):
        self.description = ""
        self.detailed_description = ""
        self.history = ""            # lore snippet
        self.previous_owners = []    # in-world story, not necessarily tracked mechanically
        self.creation_date = None    # game-time creation
        self.condition = 100         # affects value/performance
```

**Action items:**

- Add `examine closely <item>` (or similar) to surface detailed descriptions.  
- Extend item models to support detailed lore/history text.  
- Consider condition/aging (rust, wear) where it adds flavour.  
- **AI integration:** Generate first-draft item backstories, then store them as canonical text.

---

### 1.3 NPC Relationships & Social Dynamics 💑

**Priority:** Critical · **Impact:** Transformative

NPCs should form a **social web**, not exist as isolated nodes.

**Example:**

```
> talk to mara
Mara glances toward the door nervously. "Have you seen Grimble lately?
He owes me for last week's ale, and I haven't seen hide nor hair of him..."

> talk to grimble
Grimble shifts uncomfortably. "Mara's been asking about me, hasn't she?
Look, I'll pay her back when my luck turns. Tell her I'm good for it!"
```

**Implementation sketch:**

```python
class NPC:
    def __init__(self, ...):
        self.relationships = {
            # npc_id: relationship data
            "mara": {
                "affection": 10,
                "respect": 5,
                "trust": -2,
                "history": "Owes her for a shipment of ale.",
                "current_status": "owes_money",
            },
        }
        self.gossip_knowledge = []  # things they know about others
        self.secrets = []           # guarded information
```>

**Action items:**

- Define a simple relationship schema (affection/respect/trust/status).  
- Seed initial relationships between key Hollowvale NPCs.  
- Have NPCs occasionally mention others in conversation (via templates or AI).  
- Include relevant relationship/gossip snippets in AI prompts so dialogue feels interconnected.

---

## Phase II – Make Combat Memorable (≈ 2 weeks)

> *From dice rolls to war stories.*

### 2.1 Tactical Combat with Choices ⚔️

**Priority:** Critical · **Impact:** High

Combat should offer meaningful decisions, not just “attack until dead”.

**Example choices:**

```
The goblin circles you warily, dagger glinting.

Your options:
[aggressive] Strike hard (high damage, costs stamina, exposes you)
[defensive] Block and counter (lower damage, safer)
[tactical] Aim for the wounded leg (chance to knock down)
[special] Power attack (costs 15 stamina, +50% damage)
```

**Implementation sketch:**

```python
class CombatState:
    def __init__(self):
        self.round_number = 0
        self.combatants = {
            "player": {
                "stance": "neutral",
                "stamina": 50,
                "status_effects": [],
                "position": "standing",
            },
            # enemies...
        }

    def get_available_actions(self, combatant):
        actions = ["basic_attack"]
        if combatant.stamina >= 15:
            actions.append("power_attack")
        if combatant.has_skill("disarm"):
            actions.append("disarm")
        # context-specific actions based on enemy state...
        return actions
```

**Action items:**

- Add stamina and stances to the combat system.  
- Introduce a small set of status effects (bleeding, stunned, poisoned).  
- Make a simple but expressive action menu each round (even if entered as text commands).  
- **AI integration:** Use AI to generate **narrative wrappers** around deterministic outcomes (“Your blade catches the light as it arcs toward…”).

---

### 2.2 Memorable Enemies 👹

**Priority:** High · **Impact:** High

Enemies should feel like individuals with **style**.

**Implementation sketch:**

```python
class EnemyArchetype:
    def __init__(self, ...):
        self.combat_personality = "cautious"  # or aggressive/tactical
        self.signature_moves = []             # unique abilities
        self.combat_dialogue = []            # taunts, warnings, last words
        self.story_item_template = None      # unique loot with lore
```

**Action items:**

- Define archetypes (goblin scout / goblin veteran / goblin shaman, etc.).  
- Give each archetype a couple of signature moves and a handful of combat lines.  
- Attach **story-linked loot** to some enemies so encounters feel narrative, not generic.  
- **AI integration:** Use AI once to propose personality, moves and lines per archetype; store results as static data.

---

## Phase III – Make NPCs Unforgettable (2–3 weeks)

> *From responders to characters.*

### 3.1 NPC Goals & Agency 🎯

**Priority:** Critical · **Impact:** Transformative

NPCs shouldn’t just wait for commands – they should **want** things.

**Implementation sketch:**

```python
class NPCGoals:
    def __init__(self):
        self.current_goal = {
            "type": "collect_debt",   # find_person, recover_item, revenge, etc.
            "target": "grimble",
            "urgency": 8,            # 1–10
            "mood_impact": -5,
            "deadline": None,
            "consequences": "will_get_angry",
        }
        self.mood = "frustrated"
        self.will_initiate_conversation = True
```

**Action items:**

- Attach simple goal structures to key NPCs.  
- Let goals influence mood and dialogue tone.  
- Allow NPCs to **bring up their problems** unprompted when urgency is high.  
- **AI integration:** Include goal + mood in system prompts so responses feel motivated (“You’re worried about Grimble’s debt and feeling short-tempered.”).

---

### 3.2 Emergent Quests & Dynamic Storytelling 📖

**Priority:** High · **Impact:** Transformative

Quests should **emerge** from NPC situations, not just from “quest board” style triggers.

**Concept:**

- Mara’s flour shipment is late → she complains to you.  
- You see Grimble drunk in the tavern → he begs you to help him fix it.  
- Whether you help, ignore or exploit them shapes relationships and follow-on quests.

**Implementation sketch:**

```python
class DynamicQuest:
    def __init__(self, ...):
        self.trigger_conditions = {...}      # world + NPC states
        self.discovery_method = "conversation"
        self.possible_solutions = []         # multiple paths
        self.involved_npcs = {}
        self.moral_axes = ["pragmatic", "kind", "selfish"]

    def progress_check(self, player_actions):
        # Evaluate whether actions advance the quest, even if the player never typed 'accept'
        ...
```

**Action items:**

- Allow quest “state” to update when the player naturally acts, even before an explicit “start”.  
- Have NPCs talk about evolving situations rather than presenting rigid quest menus.  
- Track multiple valid resolutions, with relationship consequences instead of only “completed/failed”.  
- **AI integration:** Use AI to draft branching quest beats from NPC conflicts, then encode results structurally.

---

## Phase IV – Make the World Reactive (1–2 weeks)

> *Your choices echo.*

### 4.1 Persistent Consequences 🌊

**Priority:** High · **Impact:** High

Important actions should ripple through NPCs, locations and prices.

**Implementation sketch:**

```python
class ConsequenceLog:
    def __init__(self):
        self.player_actions = []       # chronological log
        self.faction_standings = {}    # per-player or global
        self.world_state_changes = []  # e.g. flags, phase changes

    def record_action(self, player_id, action_type, details):
        # Store and maybe trigger follow-on effects
        ...

    def trigger_consequences(self, action):
        # Adjust NPC relationships, prices, room descriptions, etc.
        ...
```

**Examples:**

- Help Mara aggressively → Grimble raises prices and spreads rumours.  
- Steal from a shop → guards remember; certain NPCs refuse to trade.  
- Solve disputes peacefully → different factions trust you more.

**Action items:**

- Define which player actions are “consequence-worthy” events.  
- Log them in a consistent structure.  
- Apply simple, visible world changes (dialogue variants, prices, description tweaks).  
- **AI integration:** Include recent notable actions in NPC prompts so they can reference them naturally.

---

## Phase V – The AI Revolution (Ongoing)

> *What no classic MUD has done before.*

### 5.1 NPCs That Surprise You 🎭

**Priority:** Critical · **Impact:** Game‑changing

NPCs should sometimes feel like they are controlled by another player.

**Key ideas:**

- **Proactive NPCs:** They approach you when something matters to them.  
- **Improvisation:** They can change topic to what *they* care about.  
- **Initiative:** They react to your reputation and recent deeds without being asked.

**Prompt flavour sketch:**

```text
You are {npc_name}. The player just {player_action}.

You CAN:
- Bring up your own goals or worries
- Change the subject to something important to you
- Reveal information if the player has earned your trust
- Propose trades, deals or favours unprompted
- React emotionally (excitement, fear, suspicion)

Recent events you care about: {recent_events}
Your current goal: {goal}
Your mood: {mood}
```

**Action items:**

- Give certain NPCs a chance each tick to “take initiative” if the player is present.  
- Allow AI responses to *start* conversations, not only answer them.  
- Implement overheard NPC‑to‑NPC exchanges that the player can witness.  
- Carefully cap frequency so this feels alive, not spammy.

---

### 5.2 Dynamic but Grounded Content Generation 🪄

**Priority:** Medium · **Impact:** Replayability

Use AI to generate **fresh but cached** flavour where it helps most:

- Ambient lines per room that rotate over time.  
- Additional item examination lore.  
- Personalities for generic townsfolk.

**Implementation sketch:**

```python
def generate_with_ai_fallback(prompt, cache_key, ttl=7200):
    cached = redis.get(cache_key)
    if cached:
        return cached

    try:
        result = call_openai(prompt)
        redis.setex(cache_key, ttl, result)
        return result
    except Exception:
        return FALLBACK_DEFAULT
```

**Principles:**

- Generate once, **cache aggressively**.  
- Store anything that becomes canon in your own DB, not just Redis.  
- Never block critical gameplay on AI availability.

---

## 6. Quick Wins (High Impact, Low Effort)

These can be slotted into any sprint:

1. **Sensory details template**  
   - Add 3–5 sensory details for each existing room.  
   - Use AI as a helper to propose text; commit the chosen text as data.

2. **NPC mood system**  
   - Add a simple `mood` field to NPCs that shifts based on recent events.  
   - Include mood in AI prompts so dialogue varies even with the same player.

3. **“Previously…” callback**  
   - When chatting with an NPC, include the last few interactions in the prompt.  
   - NPCs reference past conversations occasionally (“As I told you yesterday…”).

4. **Combat flavour text**  
   - Add a small library of flavour strings per weapon type and stance.  
   - Bind them to deterministic results: the maths stay the same; the story feels richer.

5. **Relationship-aware shops**  
   - Tie merchant prices and tone to a basic reputation score.  
   - High rep: “For you, friend, a small discount.”  
   - Low rep: “You’ll pay extra after the trouble you caused.”

---

## 7. Technical Infrastructure Notes (Immersion-Relevant)

Some systems need light scaffolding to support immersion features:

### 7.1 Suggested Schema Extensions

```sql
-- NPC Relationships
CREATE TABLE npc_relationships (
    npc_id_1 TEXT,
    npc_id_2 TEXT,
    affection INTEGER,
    respect INTEGER,
    history TEXT,
    last_interaction TIMESTAMP
);

-- Dynamic Quests
CREATE TABLE dynamic_quests (
    quest_id TEXT PRIMARY KEY,
    trigger_npc TEXT,
    involved_npcs JSONB,
    current_state TEXT,
    player_choices JSONB,
    created_at TIMESTAMP
);

-- World State Events
CREATE TABLE world_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT,
    affected_rooms JSONB,
    affected_npcs JSONB,
    effects JSONB,
    expires_at TIMESTAMP
);
```

These tables are optional but illustrate the **shape** of data needed for relationships, emergent quests and world events.

### 7.2 AI Cost & Caching

```python
TIER_COSTS = {
    "critical": "gpt-4-turbo",   # NPC initiative, quest gen
    "standard": "gpt-4o-mini",   # Normal dialogue
    "cache": "gpt-3.5-turbo",    # Ambient descriptions
    "fallback": "templates",     # If AI fails
}
```

- Use higher-cost models only where they materially impact experience.  
- Cache aggressively, especially for ambient text and lore that can be reused.  
- Always have template-based fallbacks for AI downtime.

---

## 8. Success Metrics (Immersion)

To know if immersion is improving, track:

1. **Session depth**
   - Commands per session.  
   - Unique rooms visited.  
   - NPCs interacted with.  
   - Items examined (not just picked up).

2. **Conversation quality**
   - Percentage of NPC conversations that go beyond three exchanges.  
   - Frequency of players typing freeform text versus only command words.  
   - Changes in NPC reputation per session.

3. **Exploration behaviour**
   - How often players examine items closely.  
   - How often they return to the same NPC multiple times.  
   - Number of times players follow up on hints or gossip.

4. **Story engagement**
   - Percentage of quests discovered through conversation rather than explicit listing.  
   - Distribution of different quest resolutions chosen (not just “optimal” path).  
   - Frequency of players revisiting earlier quest locations/NPCs.

5. **The “holy shit” metric**
   - Screenshots or logs of surprising NPC interactions.  
   - Player messages about unexpected moments.  
   - Organic sharing of stories (“You have to meet Mara after…”) among testers.

---

## 9. Lore & Other Documents

- For **worldbuilding, realms, Threadsinging and the Sundering**, see `docs/LORE_PRIMER.md`.  
- For **feature sequencing, Web3 experiments and mobile client plans**, see `docs/ROADMAP.md`.  
- For **architecture, state and persistence design**, see:
  - `docs/ARCHITECTURE.md`  
  - `docs/ENGINE_OVERVIEW.md`  
  - `docs/WORLD_STATE_AND_PERSISTENCE.md`

Treat this document as the **experience north star**: when choosing between two implementations, prefer the one that better serves immersion, story and the feeling of a living world.
