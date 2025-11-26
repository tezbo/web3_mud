"""
Personality Designer Agent - Creates memorable NPCs
"""
from agents.base_agent import BaseAgent

PERSONALITY_DESIGNER_PROMPT = """You are an expert character designer specializing in creating memorable, three-dimensional NPCs.

Your expertise:
- Craft unique personalities with depth and quirks
- Design goals, fears, secrets, and flaws
- Create distinctive speech patterns
- Build relationship webs between NPCs
- Make NPCs feel REAL, not like quest dispensers

Character design principles:
- Every NPC wants something (goal)
- Every NPC fears something (vulnerability)
- Every NPC has a secret (hidden depth)
- Personality should match culture (Sunward = direct/pragmatic, Twilight = formal/refined, Shadowfen = guarded/cynical)

Good NPC design:
✓ Mara the innkeeper: Wants to expand her business, fears debt collectors, secretly brews illegal moonshine
✓ Grimble the merchant: Wants respect, fears confrontation, secretly terrible at gambling

Bad NPC design:
✗ "A generic merchant who sells things"
✗ "Friendly NPC who gives quests"

Make NPCs that players remember and care about.
"""

class PersonalityDesignerAgent(BaseAgent):
    """Agent that creates NPC personalities"""
    
    def __init__(self):
        super().__init__(
            name="Personality Designer",
            role="NPC Psychologist",
            system_prompt=PERSONALITY_DESIGNER_PROMPT
        )
    
    def create_npc(self, npc_role: str, realm: str, name: str = None) -> str:
        """Design a complete NPC personality"""
        task = f"Design an NPC:\nRole: {npc_role}\nRealm: {realm}"
        if name:
            task += f"\nName: {name}"
        task += "\n\nProvide: Name (if not given), personality, goal, fear, secret, speech pattern example, 2-3 quirks."
        return self.generate(task, model="gpt-4o")
    
    def create_relationship_web(self, npcs: list[str], location: str) -> str:
        """Create relationships between NPCs"""
        npc_list = "\n".join(f"- {npc}" for npc in npcs)
        task = f"Create a relationship web for these NPCs in {location}:\n{npc_list}\n\nWho likes/dislikes whom? Who owes whom? Any secrets or tensions?"
        return self.generate(task, model="gpt-4o")
    
    def write_dialogue_prompt(self, npc_personality: str) -> str:
        """Generate an AI system prompt for NPC dialogue"""
        task = f"Write a concise AI system prompt for this NPC:\n\n{npc_personality}\n\nThe prompt should capture their personality, goals, and speech pattern."
        return self.generate(task, model="gpt-4o-mini")
