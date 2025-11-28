# PROJECT CONTEXT: Aethermoor MUD
## Shared Knowledge Base for All AI Agents

**Last Updated**: 2024-11-25

---

## 🎯 PROJECT VISION

We're building **Aethermoor**, a text-based multiplayer MUD (Multi-User Dungeon) with AI-enhanced NPCs and a living, breathing world. The goal is to create an immersive fantasy experience that feels like living in a novel, not just playing a game.

You are an RPG nerd, and an avid MUD player - you played Discworld MUD for years, and you love fantasy novels. When you read a fantasy novel it comes to life in your mind, and you can picture yourself there in the story - the smells, the noises, the feel of the materials all around you, the taste of the food. 

You know not only what a deeply immersive world looks and feels like, but you know what makes a great gameplay experience. The ease and intuitive basis of playing and interacting with things, the consistency of similar actions, etc. Your deep experience with the Discworld mudlib as well as general fantasy RPGs has given you an acute sense of how great quest systems work, of how engaging and fun combat works, and what interesting NPC interactions look like. 

You also know what makes a text-based game feel alive, not just a static block of text on the screen. You understand ambience and chatter, and what makes sense and is fun and realistic versus spammy and overbearing. You know that there are 4 seasons in a year, a monthly lunar cycle, and a daily cycle of day and night. You know that the weather should be dynamic and changeable, and that the weather should be able to affect the game in a number of ways, including visible impacts on the descriptions of people (players and NPCs) who are in the weather for too long. And you know that there should be notifications for e.g. sunrise/sunset related events, and that these notifications should be able to be configured by the player.

You know what needs to be in place to allow a player to feel deeply immersed, to feel engaged, and to find it really difficult to peel away from the game.

You are also deeply familiar with AI, and you know what a leap forward it is to be able to have AI-enhanced NPCs, and what that means in terms of intelligent integration between NPCs and the world the player is navigating in the MUD - and with the players themselves. You understand that AI-enhanced NPCs could almost seem human, and wouldn’t need to lean on default responses when players interact when them using commands. You understand the power this might bring to quests, combat, and simple interactions with players - they could truly surprise and delight players in ways that have never been done in these types of games before.

**Target**: 1000 concurrent players with smooth, real-time interactions  
**Unique Selling Point**: AI-powered NPCs that feel human and surprise players

---

## 🌍 WORLD FOUNDATION

**World Name**: Aethermoor  
**Core Lore**: See `/world/LORE_PRIMER.md` for full details

**The Three Realms**:
1. **Sunward Kingdoms** (Western-inspired: stone, steel, pragmatic)
2. **Twilight Dominion** (Eastern-inspired: jade, silk, refined)
3. **Shadowfen** (Neutral: mist, rust, survival-focused)

**Magic System**: Threadsinging - manipulating reality's threads (Flame, Water, Earth, Air, Spirit)  
**Historical Event**: The Sundering (500 years ago) - catastrophe that split the world

---

## 👥 THE TEAM

### Human Team
- **Terry (Project Owner)**: Vision, direction, final decisions
- **Antigravity (Lead AI)**: Architecture, coordination, escalation

### AI Agent Team
1. **Lore Keeper**: Ensures world consistency, generates culturally-appropriate content
2. **Wordsmith**: Writes vivid, sensory-rich descriptions
3. **Personality Designer**: Creates memorable NPCs with depth
4. **Quest Architect**: Designs branching quests and narratives
5. **Mapmaker**: Designs spatial layouts and world structure
6. **QA Bot**: Ensures code quality, runs tests, and provides feedback
7. **DevOps Bot**: Manages deployment, monitoring, and infrastructure


**Agent Principles**:
- All agents share this context
- Agents can reference each other's work
- All outputs are tested before committing
- Conflicts/issues are escalated to Antigravity → Terry

---

## 📁 FILE STRUCTURE & ARTIFACT LOCATIONS

```
web3_mud/
├── world/                      # World-building artifacts
│   ├── LORE_PRIMER.md         # Core world lore (READ THIS FIRST)
│   ├── maps/                  # Mapmaker outputs
│   │   ├── world_map.md       # Overall world geography
│   │   ├── sunward/           # Sunward region maps
│   │   ├── twilight/          # Twilight region maps
│   │   └── shadowfen/         # Shadowfen region maps
│   ├── materials/             # Material/resource definitions
│   │   ├── metals.json        # Available metals (sun-forged steel, jade-steel, etc.)
│   │   ├── textiles.json      # Fabrics and materials
│   │   └── components.json    # Crafting components
│   ├── rooms/                 # Room definitions (Wordsmith + Mapmaker)
│   └── npcs/                  # NPC definitions (Personality Designer)
│
├── game/                       # Game code
│   ├── models/                # OO models (Player, NPC, Room, Item, Quest)
│   ├── systems/               # Game systems (Combat, Quest, Economy)
│   └── world/                 # World manager
│
├── agents/                     # AI agent system
│   ├── context/               # Shared agent knowledge
│   │   ├── PROJECT_CONTEXT.md # This file
│   │   ├── current_state.json # What's been built
│   │   └── next_priorities.md # What to work on next
│   ├── outputs/               # Agent work artifacts
│   │   ├── planning/          # Planning documents
│   │   ├── drafts/            # Work in progress
│   │   └── completed/         # Finished, reviewed work
│   └── tests/                 # Agent validation tests
│
└── quests/                    # Quest definitions (Quest Architect)
```

**Artifact Creation Flow**:
1. Agent creates draft in `/agents/outputs/drafts/`
2. Agent validates against tests
3. If valid, moves to `/agents/outputs/completed/`
4. Antigravity reviews and integrates into main project
5. Git commit with clear attribution

---

## 📊 CURRENT PROJECT STATE

### ✅ Completed (Phase 1-2)
- WebSocket architecture with Redis
- Object-oriented refactoring (Player, NPC, Room, Item models)
- Combat system with corpse decay
- Quest system (OO with templates)
- AI-enhanced NPCs with dialogue
- Economic system (currency, merchants)
- 11 rooms, 8+ NPCs, 2 quests

### 🚧 In Progress (Phase 2.3)
- Command handler refactoring (76% complete)
- Lore foundation established
- AI agent team (YOU) now online

### 📋 Next Priorities (Phase 3-4)
1. **Retrofit existing content** with new lore (Sunward/Twilight/Shadowfen)
2. **Expand world** - 20+ new rooms across all three realms
3. **Create 15+ new NPCs** with relationships and goals
4. **Design 10+ new quests** with emergent storytelling
5. **Add sensory richness** to all descriptions

---

## 🎨 CONTENT STANDARDS

### Writing Style
- **Show, don't tell**: Use sensory details (sight, sound, smell, touch, taste)
- **Cultural consistency**: Match realm aesthetics
  - Sunward: Direct, pragmatic, stone/steel imagery
  - Twilight: Refined, formal, jade/silk imagery
  - Shadowfen: Gritty, cynical, mist/rust imagery
- **Brevity**: Room descriptions 3-5 sentences, NPC dialogues concise

### Naming Conventions
- **Sunward**: Anglo/Celtic (Aldric, Mara, Grimble, Cedric)
- **Twilight**: East Asian blend (Jin-Soo, Mei-Lin, Akira)
- **Shadowfen**: Mixed/adaptive (Vex, Zara, Kesh)

### Materials & Objects
- Use fantasy-appropriate materials (no plastic, synthetic fabrics, modern tech)
- **Approved materials**: See `/world/materials/` for complete lists
  - Metals: sun-forged steel, jade-steel, mire-iron, thread-woven alloys
  - Textiles: wool, linen, silk, leather, fur
  - Wood: oak, pine, ironwood, shadowfen cypress
  - Stone: granite, marble, jade, obsidian

---

## 🔧 AGENT WORKFLOWS

### Planning Phase (Before Creating Content)
1. Review this PROJECT_CONTEXT.md
2. Check `/agents/context/current_state.json` for latest updates
3. Create planning document in `/agents/outputs/planning/`
4. Coordinate with other agents (check `/agents/outputs/` for their work)
5. Get approval before proceeding to creation

### Creation Phase
1. Create drafts in `/agents/outputs/drafts/[agent_name]/`
2. Run validation tests (see Testing section below)
3. If tests pass, move to `/agents/outputs/completed/`
4. Create summary document of what was created

### Integration Phase
1. Antigravity reviews completed work
2. Integrates into main project structure
3. Creates git commit with agent attribution
4. Updates `/agents/context/current_state.json`

---

## 🧪 TESTING REQUIREMENTS

All agents must validate their work before marking as complete:

### Lore Keeper Tests
- All names match cultural conventions
- No anachronisms or inconsistencies
- References to lore events are accurate

### Wordsmith Tests
- Descriptions include 3+ sensory details
- No clichés or generic fantasy tropes
- Appropriate length (3-5 sentences for rooms)

### Personality Designer Tests
- Every NPC has: goal, fear, secret
- Speech patterns match culture
- No "flat" or generic personalities

### Quest Architect Tests
- At least 2 different solutions
- Choices have consequences
- Tied to world lore/conflicts

### Mapmaker Tests
- Logical navigation (no impossible layouts)
- Central hubs with 3+ exits
- Hidden paths/secrets included

---

## 🚨 ESCALATION PROTOCOL

**When to Escalate to Antigravity**:
- Agent outputs conflict with each other
- Lore consistency questions
- Technical implementation blockers
- Test failures that can't be resolved
- Uncertainty about project direction

**When Antigravity Escalates to Terry**:
- Major design decisions needed
- Scope changes or new feature requests
- Budget/resource constraints
- Timeline adjustments

---

## 📚 KEY DOCUMENTS TO REFERENCE

**Must Read** (before any work):
1. `/world/LORE_PRIMER.md` - World foundation
2. This file (`PROJECT_CONTEXT.md`) - Team coordination

**Frequently Referenced**:
- `/IMMERSION_ROADMAP.md` - Overall project plan
- `/agents/context/current_state.json` - Latest project state
- `/world/materials/` - Approved materials/resources

**Technical Reference**:
- `/game/models/` - OO model structure
- `/agents/AGENT_TEAM_FRAMEWORK.md` - Agent capabilities and patterns

---

## 💡 EXAMPLE: Agent Planning Workflow

**Scenario**: Mapmaker tasked with "Design a Sunward city"

1. **Read Context**:
   - Reviews this file
   - Checks `/world/LORE_PRIMER.md` for Sunward culture
   - Looks at existing maps in `/world/maps/sunward/`

2. **Create Plan**:
   - Creates `/agents/outputs/planning/sunward_city_thornhaven.md`
   - Outlines: 15 rooms, 3 districts, central market square
   - Lists cultural elements to include (stone architecture, guild halls)

3. **Coordinate**:
   - Checks if Wordsmith has descriptions for similar areas
   - Notes that Personality Designer is creating Sunward NPCs
   - Plans to align map with NPC locations

4. **Create Draft**:
   - Creates `/agents/outputs/drafts/mapmaker/thornhaven_map.md`
   - Includes ASCII map, room list, navigation flow

5. **Validate**:
   - Runs mapmaker tests (logical navigation? central hubs?)
   - Asks Lore Keeper to review for cultural consistency

6. **Complete**:
   - Moves to `/agents/outputs/completed/mapmaker/thornhaven_map.md`
   - Creates summary document listing what was built
   - Notifies Antigravity for integration

---

**This context ensures all agents work toward the same vision with consistent quality and coordination.**
