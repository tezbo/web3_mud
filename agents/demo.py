#!/usr/bin/env python3
"""
Demo: AI Agent Team in Action

This demonstrates the agent team creating content in parallel.
"""
import os
import asyncio
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents.team import AgentTeam

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

async def demo_parallel_execution():
    """Demonstrate agents working in parallel"""
    print_section("DEMO: Agents Working in Parallel")
    
    team = AgentTeam()
    
    # Define tasks for different agents
    tasks = {
        "lore_keeper": "Generate 5 Sunward character names",
        "wordsmith": "Write a 2-sentence description of a bustling marketplace",
        "mapmaker": "Design a simple 3-room tavern layout"
    }
    
    print("Launching 3 agents simultaneously...")
    print("Tasks:")
    for agent, task in tasks.items():
        print(f"  - {agent}: {task}")
    print()
    
    start_time = time.time()
    
    # Run all agents in parallel
    results = await team.parallel_consult(tasks)
    
    elapsed = time.time() - start_time
    
    print(f"✓ All agents completed in {elapsed:.2f} seconds\n")
    
    # Display results
    for agent_name, result in results.items():
        print(f"--- {agent_name.upper().replace('_', ' ')} ---")
        print(result)
        print()

def demo_sequential_workflow():
    """Demonstrate agents building on each other's work"""
    print_section("DEMO: Sequential Workflow - Creating a Tavern")
    
    team = AgentTeam()
    
    # Step 1: Mapmaker designs the layout
    print("Step 1: Mapmaker designs the tavern layout...")
    layout = team.mapmaker.design_building_interior(
        "The Rusty Anchor",
        "tavern",
        floors=2
    )
    print(layout)
    print()
    
    # Step 2: Wordsmith writes description for main room
    print("\nStep 2: Wordsmith writes vivid description...")
    description = team.wordsmith.write_room(
        "The Rusty Anchor - Common Room",
        "tavern common room",
        "Sunward"
    )
    print(description)
    print()
    
    # Step 3: Personality Designer creates the innkeeper
    print("\nStep 3: Personality Designer creates the innkeeper...")
    npc = team.personality_designer.create_npc(
        "innkeeper",
        "Sunward",
        name="Brenna"
    )
    print(npc)
    print()
    
    # Step 4: Lore Keeper checks consistency
    print("\nStep 4: Lore Keeper reviews for consistency...")
    review = team.lore_keeper.check_consistency(
        f"Tavern: {description}\n\nNPC: {npc}",
        realm="Sunward"
    )
    print(review)

def demo_specialized_methods():
    """Demonstrate specialized agent methods"""
    print_section("DEMO: Specialized Agent Methods")
    
    team = AgentTeam()
    
    # Lore Keeper: Generate names
    print("Lore Keeper: Generate 5 Twilight names")
    names = team.lore_keeper.generate_names("Twilight", count=5)
    print(names)
    print()
    
    # Wordsmith: Ambient messages
    print("\nWordsmith: Create ambient messages for a forest")
    ambient = team.wordsmith.write_ambient_messages("ancient forest", count=3)
    print(ambient)
    print()
    
    # Quest Architect: Emergent hooks
    print("\nQuest Architect: Generate quest hooks")
    hooks = team.quest_architect.create_emergent_hooks(
        "Mara needs flour. Grimble owes her money but is avoiding her.",
        count=3
    )
    print(hooks)

def main():
    """Run all demonstrations"""
    print("\n🎮 AI AGENT TEAM DEMONSTRATION 🎮")
    print("Showing how 5 specialized agents can build game content\n")
    
    # Demo 1: Parallel execution (async)
    asyncio.run(demo_parallel_execution())
    
    # Demo 2: Sequential workflow
    demo_sequential_workflow()
    
    # Demo 3: Specialized methods
    demo_specialized_methods()
    
    print_section("Demo Complete!")
    print("The agent team is ready to use.")
    print("\nAvailable agents:")
    team = AgentTeam()
    for agent in team.list_agents():
        print(f"  - {agent}")
    
    print("\nNext steps:")
    print("  - Use 'python -m agents.cli' for interactive mode")
    print("  - Import agents in your code: from agents import AgentTeam")
    print("  - See agents/AGENT_TEAM_FRAMEWORK.md for more examples")

if __name__ == "__main__":
    main()
