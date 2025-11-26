import json
from agents.base_agent import BaseAgent

class SocialArchitectAgent(BaseAgent):
    """
    Agent responsible for defining social structures, relationships, and factions.
    """
    
    def __init__(self):
        super().__init__(
            name="Social Architect",
            role="Sociologist & Network Theorist",
            system_prompt=(
                "You are an expert Social Architect for a living fantasy world. "
                "Your goal is to weave complex, realistic webs of relationships between characters. "
                "You understand that relationships are driven by need, history, debt, blood, and rivalry. "
                "You output strict JSON data defining these connections."
            )
        )

    def generate_relationships(self, target_npc, other_npcs, realm_context):
        """
        Generate relationships for a specific NPC given a list of potential contacts.
        """
        # Create a summary of other NPCs to save token space
        others_summary = [
            f"- {n.get('name')} ({n.get('role', 'Unknown')}): {n.get('personality', {}).get('goal', 'Unknown')}"
            for n in other_npcs if n.get('name') != target_npc.get('name')
        ]
        
        prompt = (
            f"Define social connections for '{target_npc.get('name')}' ({target_npc.get('role')}) "
            f"in the {realm_context} realm.\n\n"
            f"Target Personality: {json.dumps(target_npc.get('personality', {}))}\n\n"
            f"Potential Contacts:\n" + "\n".join(others_summary[:10]) + "\n\n"  # Limit to 10 context NPCs
            f"Task: Select 2-4 meaningful relationships from the list above. "
            f"Return a JSON object with a 'relationships' list. Each item must have:\n"
            f"- 'target': Name of the other NPC\n"
            f"- 'type': One of [Ally, Rival, Family, Employer, Employee, Debtor, Creditor, Secret]\n"
            f"- 'strength': 1-10 (1=acquaintance, 10=blood bond/mortal enemy)\n"
            f"- 'description': One sentence explaining the dynamic.\n\n"
            f"Example:\n"
            f"{{\n"
            f"  \"relationships\": [\n"
            f"    {{\"target\": \"Garrick\", \"type\": \"Rival\", \"strength\": 7, \"description\": \"Competes for the best ale supply.\"}}\n"
            f"  ]\n"
            f"}}"
        )
        
        return self.generate(prompt, {"model": "gpt-4o-mini", "response_format": {"type": "json_object"}})
