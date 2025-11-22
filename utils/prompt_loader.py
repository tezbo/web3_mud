"""
Shared prompt loader utility.

Loads prompt templates from the prompts/ directory and formats them with provided values.
"""

import os


def load_prompt(filename, fallback_text="", **kwargs):
    """
    Load a prompt template from the prompts directory and format it with provided values.
    
    Args:
        filename: Name of the prompt file (e.g., "npc_dialogue_system.txt")
        fallback_text: Text to return if file is missing or unreadable
        **kwargs: Values to interpolate into the template using str.format()
    
    Returns:
        str: Formatted prompt text, or fallback_text if file cannot be loaded
    """
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", filename)
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read().strip()
            if template and kwargs:
                return template.format(**kwargs)
            return template if template else fallback_text
    except (FileNotFoundError, IOError, KeyError, ValueError) as e:
        # File missing, unreadable, or formatting error - use fallback
        if fallback_text:
            # Format fallback text if kwargs provided
            try:
                return fallback_text.format(**kwargs) if kwargs else fallback_text
            except (KeyError, ValueError):
                return fallback_text
        return fallback_text

