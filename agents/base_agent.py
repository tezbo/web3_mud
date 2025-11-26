"""
Base Agent Class for AI Game Development Team
"""
import os
from typing import Dict, Any, Optional
from openai import OpenAI

class BaseAgent:
    """Base class for all specialized AI agents"""
    
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def generate(self, 
                 task: str, 
                 context: Optional[Dict[str, Any]] = None,
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.7,
                 timeout: int = 30) -> str:
        """
        Generate a response for the given task.
        
        Args:
            task: The specific task/question for the agent
            context: Additional context to inject into the prompt
            model: OpenAI model to use (gpt-4o, gpt-4o-mini)
            temperature: Creativity level (0-1)
            timeout: Timeout in seconds (default 30)
            
        Returns:
            Generated response string
        """
        # Format system prompt with context if provided
        system_content = self.system_prompt
        if context:
            try:
                system_content = system_content.format(**context)
            except KeyError as e:
                return f"Error formatting prompt: Missing key {e}"
            
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": task}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                timeout=timeout
            )
            return response.choices[0].message.content
        except TimeoutError:
            return f"Error: Request timed out after {timeout} seconds"
        except Exception as e:
            return f"Error ({type(e).__name__}): {str(e)}"
    
    def __repr__(self):
        return f"<Agent: {self.name} ({self.role})>"
