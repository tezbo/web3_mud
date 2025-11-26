import sys
import os
import time
import json
import random
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv()

from agents.agent_framework import AutonomousAgent
from agents.quest_architect import QuestArchitectAgent

class AutonomousQuestArchitect(AutonomousAgent):
    def __init__(self):
        super().__init__("Quest Architect", "Game Designer", ["Quest", "Story", "Narrative"])
        self.agent = QuestArchitectAgent()
        
    def execute_task(self, task):
        self.log(f"🔮 Starting quest design: {task['title']}")
        
        quest_name = task['title'].replace("Design ", "").replace(" Quest", "")
        output_dir = Path("agents/outputs/shadowfen")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log(f"🧠 Designing quest structure for {quest_name}...")
        # Infer hook from title
        hook = f"A quest about {quest_name} in Shadowfen."
        design = self.agent.design_quest(hook)
        
        filename = f"quest_{quest_name.lower().replace(' ', '_')}.txt"
        with open(output_dir / filename, "w") as f:
            f.write(design)
            
        self.log(f"✨ Quest design saved to {filename}")
        time.sleep(2)

if __name__ == "__main__":
    agent = AutonomousQuestArchitect()
    agent.run_loop()
