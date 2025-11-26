#!/usr/bin/env python3
"""
Multi-Agent Parallel Execution Demo
Shows agents working concurrently on different tasks
"""
import os
import sys
import time
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')
load_dotenv()

from agents.lore_keeper import LoreKeeperAgent
from agents.wordsmith import WordsmithAgent
from agents.mapmaker import MapmakerAgent

async def run_agent_async(agent, task_name, task):
    """Run an agent task asynchronously"""
    print(f"🚀 Starting: {task_name}", flush=True)
    start = time.time()
    
    # Run in executor to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, agent.generate, task)
    
    elapsed = time.time() - start
    print(f"✓ Completed: {task_name} ({elapsed:.1f}s)", flush=True)
    return task_name, result, elapsed

async def main():
    print("=" * 70)
    print("🎯 MULTI-AGENT PARALLEL EXECUTION TEST")
    print("=" * 70)
    
    # Initialize agents
    print("\n[1/3] Initializing agents...", flush=True)
    lore_keeper = LoreKeeperAgent()
    wordsmith = WordsmithAgent()
    mapmaker = MapmakerAgent()
    print("✓ 3 agents ready\n", flush=True)
    
    # Define tasks
    print("[2/3] Launching tasks in parallel...", flush=True)
    tasks = {
        "Lore Keeper": (lore_keeper, "Generate 5 Twilight character names"),
        "Wordsmith": (wordsmith, "Write a 2-sentence description of a misty swamp at dawn"),
        "Mapmaker": (mapmaker, "Design a simple 3-room dungeon layout with ASCII map")
    }
    
    # Run all in parallel
    start_time = time.time()
    
    results = await asyncio.gather(*[
        run_agent_async(agent, name, task) 
        for name, (agent, task) in tasks.items()
    ])
    
    total_time = time.time() - start_time
    
    # Display results
    print(f"\n[3/3] All agents completed in {total_time:.1f}s total")
    print("=" * 70)
    
    for task_name, result, elapsed in results:
        print(f"\n📋 {task_name} ({elapsed:.1f}s):")
        print("-" * 70)
        print(result)
        print()
    
    print("=" * 70)
    print("✅ SUCCESS: Multi-agent parallel execution working!")
    print(f"Sequential would have taken: ~{sum(r[2] for r in results):.1f}s")
    print(f"Parallel completion: {total_time:.1f}s")
    print(f"Speedup: {sum(r[2] for r in results) / total_time:.1f}x")

if __name__ == "__main__":
    asyncio.run(main())
