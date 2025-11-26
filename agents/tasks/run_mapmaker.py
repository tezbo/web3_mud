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
from agents.mapmaker import MapmakerAgent

class AutonomousMapmaker(AutonomousAgent):
    def __init__(self):
        super().__init__("Mapmaker", "Level Designer", ["Map", "Layout", "Design"])
        self.agent = MapmakerAgent()
        
    def execute_task(self, task):
        self.log(f"🏗️ Starting generation for: {task['title']}")
        
        # Extract parameters from task description or title
        # For now, we'll infer based on keywords or use defaults
        area_name = task['title'].replace("Design ", "").replace(" Layout", "")
        
        output_dir = Path("agents/outputs/shadowfen")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log(f"🧠 Generating layout for {area_name}...")
        result = self.agent.design_area(area_name, "District", 6, "Shadowfen")
        
        filename = f"map_{area_name.lower().replace(' ', '_')}.txt"
        with open(output_dir / filename, "w") as f:
            f.write(result)
            
        self.log(f"✨ Layout saved to {filename}")
        time.sleep(2) # Simulate work

if __name__ == "__main__":
    agent = AutonomousMapmaker()
    agent.run_loop()
