import time
import asyncio
import sys
from agents.base_agent import BaseAgent

class SleepyAgent(BaseAgent):
    def __init__(self, name):
        super().__init__(name=name, role="Sleeper", system_prompt="I sleep.")

    def sleep(self, duration):
        print(f"[{self.name}] Going to sleep for {duration}s...")
        time.sleep(duration) # Blocking sleep to test if executor handles it
        print(f"[{self.name}] Woke up!")
        return f"Slept for {duration}s"

async def run_parallel_test():
    agent1 = SleepyAgent("Sleeper 1")
    agent2 = SleepyAgent("Sleeper 2")
    
    print("Starting parallel sleep test (2 agents x 2 seconds)...")
    start_time = time.time()
    
    # Run both in parallel using run_in_executor (simulating how we call LLMs)
    loop = asyncio.get_running_loop()
    
    task1 = loop.run_in_executor(None, agent1.sleep, 2)
    task2 = loop.run_in_executor(None, agent2.sleep, 2)
    
    await asyncio.gather(task1, task2)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nTotal duration: {duration:.2f}s")
    
    if duration < 3.0:
        print("✅ SUCCESS: Agents ran in parallel!")
        return 0
    else:
        print("❌ FAILURE: Agents ran sequentially!")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(run_parallel_test()))
