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
from agents.wordsmith import WordsmithAgent

class AutonomousWordsmith(AutonomousAgent):
    def __init__(self):
        super().__init__("Wordsmith", "Writer", ["Description", "Write", "Lore"])
        self.agent = WordsmithAgent()
        
    def execute_task(self, task):
        self.log(f"✍️ Starting writing task: {task['title']}")
        
        location_name = task['title'].replace("Write ", "").replace(" Descriptions", "")
        output_dir = Path("agents/outputs/shadowfen")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log(f"📜 Drafting description for {location_name}...")
        desc = self.agent.write_room(location_name, "Location", "Shadowfen")
        
        filename = f"desc_{location_name.lower().replace(' ', '_')}.txt"
        with open(output_dir / filename, "w") as f:
            f.write(desc)
            
        self.log(f"✨ Description saved to {filename}")
        
        self.log(f"💬 Generating ambient messages...")
        ambient = self.agent.write_ambient_messages(location_name, 3)
        with open(output_dir / filename, "a") as f:
            f.write("\n\nAmbient Messages:\n" + ambient)
            
        time.sleep(2)

if __name__ == "__main__":
    agent = AutonomousWordsmith()
    agent.run_loop()
