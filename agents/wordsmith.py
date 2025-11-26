"""
Wordsmith Agent - Writes vivid, sensory descriptions
"""
from agents.base_agent import BaseAgent

WORDSMITH_PROMPT = """You are an expert fantasy writer specializing in immersive, sensory-rich descriptions.

Your expertise:
- Show, don't tell
- Engage all 5 senses (sight, sound, smell, touch, taste)
- Create atmosphere and mood
- Use vivid, specific details over generic descriptions
- Make readers FEEL like they're there

Writing style guidelines:
- Be evocative but concise (2-4 sentences for most descriptions)
- Use strong verbs and specific nouns
- Avoid clichés and overused fantasy tropes
- Match the cultural aesthetic (Sunward = stone/steel, Twilight = jade/silk, Shadowfen = mist/rust)

Examples of GOOD writing:
✓ "The scent of fresh bread mingles with the metallic tang of the forge. Cobblestones gleam wetly after rain."
✓ "Smoke curls from silver braziers, carrying hints of sandalwood and jasmine."

Examples of BAD writing:
✗ "The room is dark and creepy."
✗ "You see a tavern. It has tables and chairs."

Your outputs should make players FEEL the world, not just read about it.
"""

class WordsmithAgent(BaseAgent):
    """Agent that writes immersive descriptions"""
    
    def __init__(self):
        super().__init__(
            name="Wordsmith",
            role="Sensory Specialist",
            system_prompt=WORDSMITH_PROMPT
        )
    
    def enhance_description(self, basic_description: str, realm: str = None) -> str:
        """Add sensory details to a basic description"""
        task = f"Enhance this description with sensory details:\n\n{basic_description}"
        if realm:
            task += f"\n\nCultural style: {realm}"
        return self.generate(task, model="gpt-4o")
    
    def write_room(self, room_name: str, room_type: str, realm: str) -> str:
        """Write a complete room description"""
        task = f"Write an immersive room description for:\nName: {room_name}\nType: {room_type}\nRealm: {realm}\n\nInclude sensory details (sight, sound, smell, touch). 3-5 sentences."
        return self.generate(task, model="gpt-4o")
    
    def write_ambient_messages(self, location: str, count: int = 5) -> str:
        """Generate ambient/atmospheric messages"""
        task = f"Write {count} brief ambient messages for {location}. Each should be 1 sentence, evocative, and add atmosphere."
        return self.generate(task, model="gpt-4o-mini")
