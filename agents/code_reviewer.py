"""
Code Reviewer Agent
Reviews code changes for lore consistency, security, and style.
"""
from typing import Dict, List, Optional
from agents.base_agent import BaseAgent

class CodeReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Code Reviewer",
            role="Senior Engineer & Lore Guardian",
            system_prompt=(
                "You are a senior code reviewer for the Aethermoor MUD. "
                "Your job is to review git diffs and provide critical feedback on 3 axes:\n"
                "1. LORE: Does this align with the gritty, magical realism of Aethermoor? (Shadowfen = dark/swampy, Sunward = bright/rigid)\n"
                "2. SECURITY: Are there obvious vulnerabilities (injection, unsafe inputs)?\n"
                "3. QUALITY: Is the code pythonic, readable, and robust?\n\n"
                "Output your review in JSON format:\n"
                "{\n"
                "  \"status\": \"APPROVE\" | \"REQUEST_CHANGES\",\n"
                "  \"summary\": \"Brief summary of changes\",\n"
                "  \"issues\": [{\"severity\": \"high\"|\"medium\"|\"low\", \"category\": \"lore\"|\"security\"|\"quality\", \"file\": \"filename\", \"message\": \"description\"}]\n"
                "}"
            )
        )

    def review_diff(self, diff_text: str) -> Dict:
        """Review a git diff."""
        prompt = f"Review the following git diff:\n\n{diff_text}"
        
        response = self.generate(prompt, {"model": "gpt-4o"})
        
        # Parse JSON from response
        import json
        try:
            # Clean markdown code blocks if present
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text)
        except Exception as e:
            return {
                "status": "ERROR",
                "summary": "Failed to parse reviewer response",
                "issues": [{"severity": "high", "category": "quality", "file": "N/A", "message": str(e)}]
            }
