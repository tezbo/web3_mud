"""
Agent Team Manager - Orchestrates collaboration between agents
"""
import asyncio
from typing import List, Dict, Any
from agents.lore_keeper import LoreKeeperAgent
from agents.wordsmith import WordsmithAgent
from agents.personality_designer import PersonalityDesignerAgent
from agents.quest_architect import QuestArchitectAgent
from agents.mapmaker import MapmakerAgent
from agents.system_agent import SystemAgent

class AgentTeam:
    """Manages the team of AI agents"""
    
    def __init__(self):
        self.lore_keeper = LoreKeeperAgent()
        self.wordsmith = WordsmithAgent()
        self.personality_designer = PersonalityDesignerAgent()
        self.quest_architect = QuestArchitectAgent()
        self.mapmaker = MapmakerAgent()
        self.system_agent = SystemAgent()
        
    def get_agent(self, agent_name: str):
        """Get agent by name"""
        agents = {
            "lore_keeper": self.lore_keeper,
            "wordsmith": self.wordsmith,
            "personality_designer": self.personality_designer,
            "quest_architect": self.quest_architect,
            "mapmaker": self.mapmaker,
            "system_agent": self.system_agent
        }
        return agents.get(agent_name)
    
    def consult(self, agent_name: str, task: str, **kwargs) -> str:
        """Get advice from a specific agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return f"Error: Unknown agent '{agent_name}'"
        return agent.generate(task, **kwargs)
    
    async def parallel_consult(self, tasks: Dict[str, str]) -> Dict[str, str]:
        """
        Consult multiple agents in parallel.
        
        Args:
            tasks: Dict mapping agent_name to task string
            
        Returns:
            Dict mapping agent_name to response
        """
        async def run_agent(agent_name: str, task: str):
            agent = self.get_agent(agent_name)
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                agent.generate, 
                task
            )
            return agent_name, result
        
        # Run all agents in parallel
        results = await asyncio.gather(
            *[run_agent(name, task) for name, task in tasks.items()]
        )
        
        return {name: result for name, result in results}
    
    def list_agents(self) -> List[str]:
        """List all available agents"""
        return ["lore_keeper", "wordsmith", "personality_designer", "quest_architect", "mapmaker", "system_agent"]
