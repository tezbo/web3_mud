# Agent Coordination System - Overview

## How Agents Work Together

This document explains how the AI agent team coordinates, plans, creates artifacts, and integrates their work into the project.

---

## Directory Structure

```
agents/
├── context/                        # Shared knowledge
│   ├── PROJECT_CONTEXT.md         # Team bible (read first!)
│   ├── current_state.json         # Latest project state
│   └── next_priorities.md         # Upcoming work queue
│
├── outputs/                        # All agent work products
│   ├── planning/                  # Planning documents
│   │   ├── EXAMPLE_world_map_planning.md
│   │   └── [agent creates planning docs here]
│   │
│   ├── drafts/                    # Work in progress
│   │   ├── lore_keeper/          # Organized by agent
│   │   ├── wordsmith/
│   │   ├── personality_designer/
│   │   ├── quest_architect/
│   │   └── mapmaker/
│   │
│   └── completed/                 # Validated, ready for integration
│       ├── lore_keeper/
│       ├── wordsmith/
│       ├── personality_designer/
│       ├── quest_architect/
│       └── mapmaker/
│
└── [agent python files]
```

---

## Agent Workflow (Step-by-Step)

### 1. ASSIGNMENT
- Antigravity (or Terry) assigns a task to an agent
- Example: "Mapmaker: Design a Sunward city with 15 rooms"

### 2. RESEARCH
Agent reads:
- `/agents/context/PROJECT_CONTEXT.md` (always)
- `/agents/context/current_state.json` (latest state)
- `/world/LORE_PRIMER.md` (world lore)
- Relevant specialized docs (e.g., `/world/materials/`)

### 3. PLANNING
Agent creates a planning document in `/agents/outputs/planning/`:
- Research findings
- Proposed approach
- Coordination needs (which agents to work with)
- Artifact outputs (what files will be created)
- Validation tests
- Questions for review

**Example**: `/agents/outputs/planning/sunward_city_thornhaven.md`

### 4. COORDINATION
Agent checks other agents' outputs:
- Read `/agents/outputs/completed/[other_agent]/` for existing work
- Note dependencies or conflicts
- Plan integration points

### 5. CREATION
Agent creates drafts in `/agents/outputs/drafts/[agent_name]/`:
- Multiple iterations
- Self-review against quality standards
- Reference materials and lore

**Example**: `/agents/outputs/drafts/mapmaker/thornhaven_map.md`

### 6. VALIDATION
Agent runs tests:
- Lore consistency check
- Quality standards (see PROJECT_CONTEXT.md)
- Integration compatibility

### 7. COMPLETION
If validated, agent:
- Moves artifact to `/agents/outputs/completed/[agent_name]/`
- Creates summary document
- Notifies Antigravity for review

### 8. INTEGRATION
Antigravity:
- Reviews completed work
- Integrates into main project structure
- Updates `/agents/context/current_state.json`
- Creates git commit with agent attribution

---

## Example: Creating a New City

**Task**: "Create Thornhaven, capital of Sunward Kingdoms"

### Mapmaker's Role
1. **Planning**: Creates `thornhaven_city_plan.md`
   - 15 rooms layout
   - Districts: Market, Noble Quarter, Temple District
   - Navigation flow with central hub
   
2. **Drafts**: Creates room JSON templates
   - `/agents/outputs/drafts/mapmaker/thornhaven_rooms/`
   - Files: `market_square.json`, `throne_room.json`, etc.
   
3. **Completed**: After validation
   - Moves to `/agents/outputs/completed/mapmaker/thornhaven/`

### Wordsmith's Role
1. **Coordination**: Reads Mapmaker's layout
2. **Planning**: Creates `thornhaven_descriptions_plan.md`
3. **Drafts**: Writes sensory-rich descriptions for each room
4. **Completed**: Enhanced room descriptions with Sunward cultural flavor

### Personality Designer's Role
1. **Coordination**: Reads both Map and Wordsmith outputs
2. **Planning**: Plans 8 NPCs for the city
3. **Drafts**: Creates NPC profiles (goals, fears, secrets, relationships)
4. **Completed**: 8 fully-realized NPCs placed appropriately

### Quest Architect's Role
1. **Coordination**: Reviews all previous work
2. **Planning**: Designs 3 quests utilizing the city and NPCs
3. **Drafts**: Quest documents with multiple solutions
4. **Completed**: Integrated questlines

### Lore Keeper's Role (Throughout)
- Reviews all outputs for consistency
- Flags anachronisms or lore conflicts
- Approves cultural appropriateness

---

## Artifact Types & Storage

### Planning Documents
- **Location**: `/agents/outputs/planning/`
- **Format**: Markdown
- **Purpose**: Communicate intent, get approval
- **Example**: `sunward_expansion_plan.md`

### World Data
- **Location**: `/world/` (after integration)
- **Subfolders**:
  - `/world/maps/` - Map artifacts
  - `/world/materials/` - Material definitions
  - `/world/rooms/` - Room JSON files
  - `/world/npcs/` - NPC JSON files
  
### Content Templates
- **Location**: `/agents/outputs/drafts/[agent]/templates/`
- **Format**: JSON or Markdown
- **Purpose**: Reusable structures
- **Example**: `sunward_room_template.json`

### Reference Lists
- **Location**: `/world/materials/`, `/world/references/`
- **Format**: Markdown or JSON
- **Purpose**: Shared vocabulary
- **Examples**:
  - `MATERIALS_REFERENCE.md` (metals, textiles, wood, stone)
  - `name_database.json` (used names to avoid duplicates)
  - `cultural_glossary.md` (Sunward/Twilight/Shadowfen terms)

---

## Coordination Mechanisms

### 1. Shared Context Files
All agents load:
- `PROJECT_CONTEXT.md` - Mission, standards, team roles
- `current_state.json` - Latest project state
- Material/lore references

### 2. Inter-Agent References
Agents can read each other's outputs:
```python
# Wordsmith reading Mapmaker's work
mapmaker_output = agent.load_other_agent_output(
    agent_name="mapmaker",
    filename="thornhaven_layout.md",
    output_type="completed"
)
```

### 3. Planning Documents
Agents declare dependencies:
```markdown
## Dependencies
- **Mapmaker**: Need city layout before writing descriptions
- **Lore Keeper**: Review for cultural accuracy
```

### 4. Escalation Protocol
Agents flag issues to Antigravity:
- Conflicts between agents
- Lore uncertainties
- Quality concerns
- Technical blockers

---

## Git Integration (Future)

Agents will be able to:
1. Create feature branches (`feature/agent-mapmaker-thornhaven`)
2. Commit their work with attribution
3. Create pull requests for review
4. Run tests before committing

**Current**: Antigravity handles git integration manually  
**Future**: Automated with agent git permissions

---

## Testing Framework

Each agent has validation tests (see `PROJECT_CONTEXT.md`):

- **Lore Keeper**: Cultural consistency, no anachronisms
- **Wordsmith**: 3+ sensory details, appropriate length
- **Personality Designer**: NPCs have goal/fear/secret
- **Quest Architect**: 2+ solutions, consequences defined
- **Mapmaker**: Logical navigation, central hubs

Tests run before moving artifacts from `drafts/` to `completed/`.

---

## Summary: The Agent Lifecycle

```
Assignment → Research → Planning → Coordination → Creation → Validation → Completion → Integration
     ↓           ↓          ↓            ↓             ↓            ↓            ↓            ↓
  Antigravity  Read docs  Draft plan  Check others  Build drafts  Run tests   Mark done   Git commit
```

**Key Principle**: **Transparency & Traceability**  
Every agent action is documented, reviewable, and integrated systematically.
