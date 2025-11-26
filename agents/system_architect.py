import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[1]))  # Add project root to path
from dotenv import load_dotenv
from agents.agent_framework import AutonomousAgent

load_dotenv()

class SystemArchitectAgent(AutonomousAgent):
    """
    Agent responsible for system architecture, refactoring, and core implementation.
    """
    
    def __init__(self):
        super().__init__(
            name="System Architect",
            role="Lead Developer & Architect",
            capabilities=["refactor", "audit", "implement", "design"]
        )
        
    def execute_task(self, task):
        """
        Execute a development task.
        """
        self.log(f"🏗️ System Architect starting task: {task['title']}")
        
        # 1. Analyze the Request
        analysis = self.think(
            f"I need to execute this task: {task['title']}\nDescription: {task.get('description', '')}\n\nHow should I approach this?",
            system_prompt="You are a System Architect. Plan the implementation steps."
        )
        self.log(f"🤔 Analysis: {analysis}")
        
        # 2. Perform the work (This is where we'd have specific logic for different task types)
        # For now, we'll implement the specific logic for the OO Audit here or make it generic
        
        if "audit" in task['title'].lower():
            self.perform_audit()
        elif "implement" in task['title'].lower() or "restore" in task['title'].lower():
            self.implement_feature(task)
        else:
            self.log("⚠️ Generic task execution not fully implemented yet.")

    def implement_feature(self, task):
        """
        Implement a feature based on the task description.
        """
        self.log(f"🛠️ Implementing feature: {task['title']}")
        
        # 1. Plan the implementation
        plan = self.think(
            f"Plan the implementation for: {task['title']}\nDescription: {task.get('description', '')}\n\nReturn a JSON list of files to create/edit with their content.",
            system_prompt="You are a System Architect. Output JSON: { 'files': [ { 'path': str, 'content': str, 'description': str } ] }",
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
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w') as f:
                f.write(content)
                
        self.log(f"✅ Implementation of {task['title']} complete.")

if __name__ == "__main__":
    agent = SystemArchitectAgent()
    # Simulate task
    agent.execute_task({"id": "story-1.1", "title": "Complete OO Transition Audit", "description": "Audit root files"})
