"""
Shared utilities for AI agents.
"""
import json
import re
from typing import Any, Dict

def clean_json_output(text: str) -> str:
    """
    Extract JSON from potential markdown code blocks.
    """
    text = text.strip()
    
    # Try to find JSON block with regex
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
        
    # Fallback to simple splitting
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
        
    return text

def parse_json_safely(text: str) -> Dict[str, Any]:
    """
    Parse JSON string safely, handling markdown blocks and errors.
    """
    cleaned = clean_json_output(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try finding just the first { and last } as last resort
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        raise
