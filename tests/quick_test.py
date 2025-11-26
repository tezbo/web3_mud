#!/usr/bin/env python3
"""Quick test - does basic agent work?"""
import os
from dotenv import load_dotenv
load_dotenv()

from agents.base_agent import BaseAgent
from agents.lore_keeper import LORE_KEEPER_PROMPT

# Use simple base agent, not coordinated one
agent = BaseAgent("Lore Keeper", "Quick Test", LORE_KEEPER_PROMPT)

print("Testing Lore Keeper...")
result = agent.generate("Generate 5 Sunward character names", model="gpt-4o-mini")
print(result)
