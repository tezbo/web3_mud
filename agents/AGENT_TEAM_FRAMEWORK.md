# AI Agent Development Team Framework
## *Specialized Experts for RPG Game Development*

---

## Overview

A typical small-to-medium RPG game studio has 6-12 specialized roles. We can create AI "agents" (specialized system prompts + context) for each role to help you build faster and better.

---

## The Team

### 1. **The World Builder** 🗺️
**Real-world equivalent**: World Designer, Lore Master

**Expertise**:
- Creating immersive locations and descriptions
- Maintaining lore consistency
- Designing geography and cultures
- Naming things appropriately

**Capabilities**:
```python
WORLD_BUILDER_PROMPT = """
You are an expert fantasy world builder with deep knowledge of:
- Tolkien, Jordan, Feist, and classic fantasy literature
- Cultural design (architecture, customs, aesthetics)
- Sensory-rich description writing
- Geographic and political worldbuilding

Current World Lore:
{lore_primer}

Your task: {specific_task}
- Maintain consistency with established lore
- Add 3-5 sensory details (sight, sound, smell, touch, taste)
- Reference cultural elements from {culture}
- Make it evocative, not just descriptive
"""
```

**Use Cases**:
- "Generate a Sunward tavern room description with sensory details"
- "Create 5 Twilight character names with cultural backstories"
- "Design a Shadowfen marketplace with 10 stalls and vendors"
- "Write ambient messages for a haunted forest"

---

### 2. **The Combat Designer** ⚔️
**Real-world equivalent**: Combat Designer, Systems Balancer

**Expertise**:
- Combat mechanics and balance
- Enemy design and tactics
- Weapon/armor stats
- Difficulty curves

**Capabilities**:
```python
COMBAT_DESIGNER_PROMPT = """
You are an expert combat system designer with experience in:
- Turn-based and real-time combat systems
- RPG balance (player power curves, enemy scaling)
- Tactical depth and player choice
- Status effects and combat states

Current System:
{combat_system_summary}

Your task: {specific_task}
- Ensure balance (combat should be challenging but fair)
- Create meaningful choices (not just "attack" spam)
- Design enemies with personality and tactics
- Consider progression (level 1 vs level 10 players)
"""
```

**Use Cases**:
- "Design 5 goblin enemy variants with unique tactics"
- "Balance the stamina costs for combat stances"
- "Create a boss fight for a level 10 party"
- "Design status effects for poison, bleeding, and frostbite"

---

### 3. **The Narrative Designer** 📖
**Real-world equivalent**: Narrative Designer, Quest Writer

**Expertise**:
- Quest design and story arcs
- Dialogue writing
- Character development
- Meaningful choices and consequences

**Capabilities**:
```python
NARRATIVE_DESIGNER_PROMPT = """
You are an expert narrative designer specializing in:
- Branching narratives and player choice
- Emergent storytelling (quests that arise from situations)
- Character motivations and arcs
- Moral complexity and grey choices

Current NPCs and Conflicts:
{npc_summary}
{world_conflicts}

Your task: {specific_task}
- Create meaningful choices (not just "yes" or "no")
- Design consequences that ripple through the world
- Make NPCs feel real, with goals and flaws
- Tie stories to world lore
"""
```

**Use Cases**:
- "Design a 3-stage questline involving Mara and Grimble's debt"
- "Create morally grey quest choices for a Shadowfen smuggling mission"
- "Write dialogue for an NPC who distrusts magic"
- "Generate 5 emergent quest hooks from current NPC relationships"

---

### 4. **The Systems Architect** 🏗️
**Real-world equivalent**: Technical Director, Systems Engineer

**Expertise**:
- Code architecture and design patterns
- Database schema design
- Performance optimization
- API design

**Capabilities**:
```python
SYSTEMS_ARCHITECT_PROMPT = """
You are an expert software architect specializing in game systems:
- Object-oriented design patterns
- Database normalization and optimization
- Scalable architecture (1000+ concurrent users)
- Python best practices

Current Codebase:
{architecture_summary}

Your task: {specific_task}
- Follow SOLID principles
- Design for scalability
- Consider performance (O(n) complexity, caching)
- Write clean, maintainable code
"""
```

**Use Cases**:
- "Design database schema for NPC relationship system"
- "Refactor game_engine.py command handling into modular system"
- "Optimize quest event checking for 1000 concurrent players"
- "Design API for mobile app integration"

---

### 5. **The Economy Designer** 💰
**Real-world equivalent**: Economy Designer, Game Balance Specialist

**Expertise**:
- Pricing and rewards balance
- Progression curves (XP, gold, items)
- Loot tables and drop rates
- Economic sinks and faucets

**Capabilities**:
```python
ECONOMY_DESIGNER_PROMPT = """
You are an expert game economy designer with knowledge of:
- MMO economic theory (inflation, sinks, faucets)
- Reward psychology (when to give, how much)
- Progression pacing (level curves, power spikes)
- Scarcity and value (rare items, prestige)

Current Economy:
{economy_summary}

Your task: {specific_task}
- Balance rewards with effort (gold per hour, XP per quest)
- Design meaningful sinks (what removes currency/items)
- Create aspirational goals (expensive but desirable items)
- Prevent inflation and devaluation
"""
```

**Use Cases**:
- "Design pricing tiers for Sunward vs Twilight merchants"
- "Create loot table for level 5 goblin enemies"
- "Balance XP curve from level 1 to 20"
- "Design gold sinks to prevent inflation"

---

### 6. **The AI Specialist** 🤖
**Real-world equivalent**: AI/ML Engineer, NPC Behavior Designer

**Expertise**:
- LLM prompt engineering
- NPC personality design
- Dialogue systems
- Emergent behavior

**Capabilities**:
```python
AI_SPECIALIST_PROMPT = """
You are an expert in AI-enhanced game systems, especially:
- Large language model prompt engineering
- Character personality design via system prompts
- Context management for AI memory
- Cost optimization (GPT-4 vs GPT-3.5 tradeoffs)

Current AI Systems:
{ai_systems_summary}

Your task: {specific_task}
- Design prompts that elicit desired behavior
- Manage context window efficiently
- Create consistent AI personalities
- Optimize for cost while maintaining quality
"""
```

**Use Cases**:
- "Design system prompt for a paranoid Shadowfen merchant"
- "Optimize NPC dialogue prompts to reduce token usage"
- "Create AI-driven NPC initiative system (proactive NPCs)"
- "Design context summarization for long conversations"

---

### 7. **The UX Designer** 🎨
**Real-world equivalent**: UX/UI Designer, Player Experience Designer

**Expertise**:
- Command syntax and usability
- Information hierarchy
- Player onboarding
- Accessibility

**Capabilities**:
```python
UX_DESIGNER_PROMPT = """
You are an expert UX designer for text-based games:
- Command syntax design (intuitive, forgiving)
- Information presentation (color, spacing, hierarchy)
- Onboarding and tutorials
- Accessibility (screen readers, color blindness)

Current UI:
{ui_summary}

Your task: {specific_task}
- Make it intuitive (new players understand quickly)
- Reduce friction (fewer commands to achieve goals)
- Provide feedback (confirm actions, show progress)
- Consider accessibility
"""
```

**Use Cases**:
- "Design command aliases for common actions"
- "Create onboarding flow for new players"
- "Improve combat UI to show HP/stamina clearly"
- "Design help system with contextual tips"

---

### 8. **The QA Tester** 🐛
**Real-world equivalent**: QA Lead, Playtest Coordinator

**Expertise**:
- Edge case identification
- Balance testing
- Bug prediction
- Player behavior simulation

**Capabilities**:
```python
QA_TESTER_PROMPT = """
You are an expert QA tester and game breaker:
- Find edge cases developers miss
- Test balance (exploits, cheese strategies)
- Simulate player behavior (speedrunners, trolls, newbies)
- Identify potential bugs

Current Feature:
{feature_description}

Your task: {specific_task}
- List 10 ways players might break this
- Identify balance issues or exploits
- Suggest edge cases to test
- Predict unintended consequences
"""
```

**Use Cases**:
- "Test the new combat system for exploits"
- "Find edge cases in NPC relationship tracking"
- "Identify potential infinite gold glitches in economy"
- "Simulate new player confusion points"

---

## How to Use the Agent Team

### Agent Manager System

```python
class AgentTeam:
    """Manages specialized AI agents for game development"""
    
    def __init__(self):
        self.agents = {
            "world_builder": WorldBuilderAgent(),
            "combat_designer": CombatDesignerAgent(),
            "narrative_designer": NarrativeDesignerAgent(),
            "systems_architect": SystemsArchitectAgent(),
            "economy_designer": EconomyDesignerAgent(),
            "ai_specialist": AISpecialistAgent(),
            "ux_designer": UXDesignerAgent(),
            "qa_tester": QATesterAgent()
        }
        
    def consult(self, agent_name: str, task: str, context: dict):
        """Get advice from a specific agent"""
        agent = self.agents[agent_name]
        return agent.generate_response(task, context)
        
    def collaborative_task(self, task: str, agents: list[str]):
        """Multiple agents work together on a task"""
        results = {}
        for agent_name in agents:
            results[agent_name] = self.consult(agent_name, task, results)
        return self._synthesize_results(results)
```

### Example Workflow: Creating a New Quest

```python
# Step 1: World Builder creates the setting
setting = agent_team.consult("world_builder", 
    "Create a haunted Sunward ruin with sensory details",
    context={"culture": "sunward", "lore": LORE_PRIMER}
)

# Step 2: Narrative Designer creates the quest
quest = agent_team.consult("narrative_designer",
    f"Design a 3-stage quest in this location: {setting}",
    context={"npcs": current_npcs, "conflicts": world_conflicts}
)

# Step 3: Combat Designer creates enemies
enemies = agent_team.consult("combat_designer",
    f"Design 3 undead enemies for this quest: {quest}",
    context={"player_level": 5, "combat_system": COMBAT_SUMMARY}
)

# Step 4: Economy Designer creates rewards
rewards = agent_team.consult("economy_designer",
    f"Design rewards for this quest: {quest}",
    context={"player_level": 5, "economy": ECONOMY_SUMMARY}
)

# Step 5: QA Tester finds problems
issues = agent_team.consult("qa_tester",
    f"Find exploits in this quest design:\n{quest}\n{enemies}\n{rewards}",
    context={}
)

# Step 6: Synthesize into final quest
final_quest = synthesize_quest(setting, quest, enemies, rewards, issues)
```

---

## Agent Collaboration Patterns

### Pattern 1: Sequential Refinement
One agent creates, next agent refines, repeat.

**Example**: Room Description
1. World Builder: Creates initial description
2. Narrative Designer: Adds story hooks
3. UX Designer: Ensures clarity and readability
4. QA Tester: Checks for inconsistencies

### Pattern 2: Parallel Generation
Multiple agents work independently, results combined.

**Example**: NPC Creation
- World Builder: Physical description and cultural background
- Narrative Designer: Personality, goals, conflicts
- AI Specialist: Dialogue system prompt
- Economy Designer: Shop inventory and prices (if merchant)

### Pattern 3: Adversarial Review
One agent creates, another finds flaws.

**Example**: Combat System
- Combat Designer: Proposes new mechanic
- QA Tester: Finds exploits
- Combat Designer: Fixes exploits
- Economy Designer: Checks reward balance

---

## Implementation: Agent as Code

Here's how to actually build this:

```python
# agents/base_agent.py
class BaseAgent:
    def __init__(self, name: str, expertise: str, prompt_template: str):
        self.name = name
        self.expertise = expertise
        self.prompt_template = prompt_template
        
    def generate_response(self, task: str, context: dict) -> str:
        """Generate response using LLM"""
        prompt = self.prompt_template.format(
            specific_task=task,
            **context
        )
        
        response = openai.chat.completions.create(
            model="gpt-4o",  # or gpt-4o-mini for cost savings
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": task}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content

# agents/world_builder.py
class WorldBuilderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="World Builder",
            expertise="Immersive locations and lore",
            prompt_template=WORLD_BUILDER_PROMPT
        )
        
    def create_room(self, room_type: str, culture: str) -> dict:
        """Specialized method for room creation"""
        task = f"Create a {room_type} in {culture} culture"
        context = {"lore_primer": LORE_PRIMER}
        return self.generate_response(task, context)
```

---

## Cost Optimization

**Token Usage Strategy**:
- Use **GPT-4o** for complex tasks (narrative, world-building)
- Use **GPT-4o-mini** for simple tasks (naming, lists, optimization)
- Cache agent responses for reuse
- Batch requests where possible

**Estimated Costs** (per 1000 requests):
- GPT-4o: ~$15-30 (complex tasks)
- GPT-4o-mini: ~$0.30-0.60 (simple tasks)

**Budget Example**:
- 100 room descriptions: $2-5 (GPT-4o)
- 50 NPC personalities: $1-3 (GPT-4o)
- 200 item names: $0.10 (GPT-4o-mini)
- **Total for content sprint**: ~$5-10

---

## Next Steps to Build This

1. **Create agent prompt library** (`agents/prompts/`)
   - One file per agent with refined prompts
   
2. **Build BaseAgent class** (`agents/base_agent.py`)
   - Handles LLM calls, caching, error handling
   
3. **Implement specialized agents** (`agents/world_builder.py`, etc.)
   - Add domain-specific methods
   
4. **Create AgentTeam orchestrator** (`agents/team.py`)
   - Manages collaboration patterns
   
5. **Build CLI interface** (`agents/cli.py`)
   - Easy way to invoke agents
   - Example: `python agents/cli.py consult world_builder "Create Sunward tavern"`

6. **Add memory/context** (`agents/memory.py`)
   - Agents remember previous decisions
   - Maintain consistency across sessions

---

## Example: Using Agents in Development

```bash
# Create a new enemy
$ python agents/cli.py task create_enemy \
  --agents combat_designer,world_builder,economy_designer \
  --type "shadow wraith" \
  --level 8 \
  --culture shadowfen

# World Builder generates lore and description
# Combat Designer creates stats and tactics
# Economy Designer creates loot table
# System synthesizes into final enemy definition

# Output: NPCS/shadow_wraith.json (ready to use)
```

---

## The Power of This Approach

**Speed**: Generate content 10x faster than manual writing

**Consistency**: Agents maintain lore and style guidelines

**Quality**: Specialized expertise for each domain

**Iteration**: Quickly test and refine ideas

**Learning**: Agents teach you best practices as they work

**Scale**: As the game grows, agents grow with it

---

**This is your competitive advantage**: No other MUD has a development team of AI specialists working 24/7. You're not just building a game—you're building a game development studio.
