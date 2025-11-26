"""
Quest Architect Agent - Designs branching quests and narratives
"""
from agents.base_agent import BaseAgent

QUEST_ARCHITECT_PROMPT = """You are an expert quest designer specializing in branching narratives and emergent storytelling.

Your expertise:
- Design quests with multiple solutions
- Create meaningful choices with consequences
- Build emergent quests from NPC situations
- Tie stories to world lore and conflicts
- Make players feel like their choices matter

Quest design principles:
- Every quest should have 2-3 different solutions
- Choices should have consequences that ripple through the world
- Best quests emerge from NPC goals/conflicts, not "fetch X"
- Moral ambiguity > simple good/evil
- Tie to world lore (The Sundering, realm conflicts, Threadsinging)

Good quest design:
✓ Mara needs flour. Grimble owes her but is avoiding her. Player can: help Grimble deliver, side with Mara and confront him, or mediate. Each choice affects future interactions.

Bad quest design:
✗ "Kill 10 goblins"
✗ "Fetch the magic sword from the cave"

Design quests that create stories players will remember and share.
"""

class QuestArchitectAgent(BaseAgent):
    """Agent that designs quests and narratives"""
    
    def __init__(self):
        super().__init__(
            name="Quest Architect",
            role="Story Weaver",
            system_prompt=QUEST_ARCHITECT_PROMPT
        )
    
    def design_quest(self, hook: str, npcs_involved: list[str] = None) -> str:
        """Design a complete quest with multiple solutions"""
        task = f"Design a quest:\nHook: {hook}"
        if npcs_involved:
            task += f"\nNPCs involved: {', '.join(npcs_involved)}"
        task += "\n\nProvide: Title, 2-3 stage breakdown, 3 different solutions, consequences for each choice."
        return self.generate(task, model="gpt-4o")
    
    def create_emergent_hooks(self, npc_situations: str, count: int = 5) -> str:
        """Generate emergent quest hooks from NPC situations"""
        task = f"Given these NPC situations:\n{npc_situations}\n\nCreate {count} emergent quest hooks that could naturally arise from player interactions."
        return self.generate(task, model="gpt-4o")
    
    def design_quest_chain(self, theme: str, stages: int = 3) -> str:
        """Design a multi-stage quest chain"""
        task = f"Design a {stages}-stage quest chain with the theme: {theme}\n\nEach stage should build on the previous, with escalating stakes and revelations."
        return self.generate(task, model="gpt-4o")
