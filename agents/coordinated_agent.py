"""
Enhanced Agent Base with Context Loading and Coordination
"""
import os
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI
from pathlib import Path

class CoordinatedAgent:
    """
    Enhanced base class for agents with shared context and coordination.
    """
    
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Load shared context
        self.project_context = self._load_project_context()
        self.current_state = self._load_current_state()
        
    def _load_project_context(self) -> str:
        """Load PROJECT_CONTEXT.md for shared knowledge"""
        context_path = Path(__file__).parent / "context" / "PROJECT_CONTEXT.md"
        try:
            with open(context_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "Project context not found. Operating with limited knowledge."
    
    def _load_current_state(self) -> Dict[str, Any]:
        """Load current_state.json for latest project state"""
        state_path = Path(__file__).parent / "context" / "current_state.json"
        try:
            with open(state_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _get_enhanced_system_prompt(self, additional_context: Optional[str] = None) -> str:
        """Build system prompt with project context"""
        prompt = f"""# AGENT IDENTITY
You are {self.name}, a specialized AI agent working on the Aethermoor MUD project.
Your role: {self.role}

# PROJECT CONTEXT
{self.project_context}

# YOUR SPECIALIZED EXPERTISE
{self.system_prompt}

# COORDINATION PROTOCOL
1. Always reference the project context above
2. Check current state for latest updates
3. Your outputs will be reviewed by Antigravity (lead AI)
4. Flag conflicts or uncertainties for escalation
5. Validate your work against lore and quality standards

# CURRENT PROJECT STATE
{json.dumps(self.current_state, indent=2)}
"""
        
        if additional_context:
            prompt += f"\n\n# ADDITIONAL CONTEXT\n{additional_context}"
        
        return prompt
    
    def generate(self, 
                 task: str, 
                 context: Optional[Dict[str, Any]] = None,
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.7,
                 coordinate_with: Optional[List[str]] = None) -> str:
        """
        Generate a response with full project context.
        
        Args:
            task: The specific task/question
            context: Additional context for this specific task
            model: OpenAI model to use
            temperature: Creativity level
            coordinate_with: List of other agents to reference (optional)
            
        Returns:
            Generated response
        """
        # Build additional context
        additional = ""
        if context:
            additional += "\n\n# TASK-SPECIFIC CONTEXT\n"
            for key, value in context.items():
                additional += f"{key}: {value}\n"
        
        if coordinate_with:
            additional += "\n\n# COORDINATE WITH THESE AGENTS\n"
            for agent in coordinate_with:
                additional += f"- {agent}\n"
            additional += "Check their outputs in /agents/outputs/ before proceeding."
        
        # Get full system prompt
        system_content = self._get_enhanced_system_prompt(additional)
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": task}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def save_output(self, content: str, filename: str, output_type: str = "drafts") -> str:
        """
        Save agent output to appropriate directory.
        
        Args:
            content: Content to save
            filename: Filename (without path)
            output_type: "planning", "drafts", or "completed"
            
        Returns:
            Path where file was saved
        """
        output_dir = Path(__file__).parent / "outputs" / output_type / self.name.lower().replace(" ", "_")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        with open(output_path, 'w') as f:
            f.write(content)
        
        return str(output_path)
    
    def load_other_agent_output(self, agent_name: str, filename: str, output_type: str = "completed") -> Optional[str]:
        """Load another agent's output for coordination"""
        agent_dir = Path(__file__).parent / "outputs" / output_type / agent_name.lower().replace(" ", "_")
        file_path = agent_dir / filename
        
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def __repr__(self):
        return f"<{self.name} ({self.role}) - Context Aware>"
