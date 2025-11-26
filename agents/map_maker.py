import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[1]))  # Add project root to path
from dotenv import load_dotenv
from agents.agent_framework import AutonomousAgent

load_dotenv()

class MapMakerAgent(AutonomousAgent):
    """
    Agent responsible for world layout, room connections, and geography.
    """
    
    def __init__(self):
        super().__init__(
            name="Mapmaker",
            role="Level Designer",
            capabilities=["map", "room", "layout", "geography"]
        )
        
    def execute_task(self, task):
        """
        Execute a mapping/design task.
        """
        self.log(f"🗺️ Mapmaker starting task: {task['title']}")
        
        # 1. Analyze the Request
        analysis = self.think(
            f"I need to execute this task: {task['title']}\nDescription: {task.get('description', '')}\n\nHow should I approach this?",
            system_prompt="You are a Mapmaker for a text-based MUD. Plan the world layout and connections."
        )
        self.log(f"🤔 Analysis: {analysis}")
        
        # 2. Implement
        self.implement_map(task)

    def implement_map(self, task):
        """
        Generate map/room code based on the task.
        """
        self.log(f"🏗️ Building map for: {task['title']}")
        
        # 1. Plan the map
        plan = self.think(
            f"Plan the map/rooms for: {task['title']}\nDescription: {task.get('description', '')}\n\nReturn a JSON list of files to create/edit with their content. This is a Python MUD project. Use Python code for room definitions.",
            system_prompt="You are a Mapmaker. Output JSON: { 'files': [ { 'path': str, 'content': str, 'description': str } ] }",
            response_format={"type": "json_object"}
        )
        
        files = plan.get('files', [])
        self.log(f"📋 Plan involves {len(files)} files.")
        
        # 2. Apply changes
        for file in files:
            path = file['path']
            content = file['content']
            desc = file['description']
            
            self.log(f"📝 Writing {path}: {desc}")
            
            # Ensure directory exists
            if os.path.dirname(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w') as f:
                f.write(content)
                
        self.log(f"✅ Map generation for {task['title']} complete.")
        self.commit_work(task['id'], f"Implement {task['title']}")

if __name__ == "__main__":
    import os
    agent = MapMakerAgent()
    agent.run_loop()
