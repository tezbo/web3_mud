#!/usr/bin/env python3
"""
Generate a web of relationships between NPCs using the Social Architect Agent.
"""
import sys
import json
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to import path if needed
# sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')
load_dotenv()

from agents.social_architect import SocialArchitectAgent
# from agents.dashboard import update_agent_status  # Removed: using local definition

# Temporary: Copy update_agent_status logic since it's not easily importable from dashboard.py 
# (dashboard.py is a script, not a module structure we can easily import from without refactoring)
STATUS_FILE = Path('agents/agent_status.json')
def update_status(agent_name, task, status, progress=None):
    try:
        if STATUS_FILE.exists():
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {}
        
        data[agent_name] = {
            "task": task,
            "status": status,
            "timestamp": time.time(),
            "progress": progress
        }
        
        with open(STATUS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

async def process_npc(npc_file, all_npcs, index, total):
    name = npc_file.stem
    update_status("Social Architect", f"Connecting {name}", "WORKING", f"{index}/{total}")
    
    # Load target NPC
    with open(npc_file, 'r') as f:
        npc_data = json.load(f)
        
    # Skip if already has relationships (unless forced, but for now skip)
    if "relationships" in npc_data and npc_data["relationships"]:
        return
        
    agent = SocialArchitectAgent()
    
    # Generate relationships
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            agent.generate_relationships, 
            npc_data, 
            all_npcs, 
            npc_data.get('realm', 'Shadowfen')
        )
        
        # Debug: Print raw response if it fails
        if not response or not response.strip():
            print(f"⚠️ Empty response for {name}")
            return

        from agents.utils import clean_json_output
        try:
            result = json.loads(clean_json_output(response))
        except json.JSONDecodeError:
            print(f"⚠️ Raw response for {name}: {response[:100]}...")
            raise

        relationships = result.get("relationships", [])
        
        # Update NPC data
        npc_data["relationships"] = relationships
        
        # Save back to file
        with open(npc_file, 'w') as f:
            json.dump(npc_data, f, indent=2)
            
        print(f"✅ Connected {name} with {len(relationships)} others.")
        
    except Exception as e:
        print(f"❌ Error connecting {name}: {e}")
        update_status("Social Architect", f"Error {name}", "ERROR")

async def main():
    npc_dir = Path('world/npcs/retrofitted')
    if not npc_dir.exists():
        print(f"❌ Directory not found: {npc_dir}")
        return
        
    npc_files = list(npc_dir.glob('*.json'))
    if not npc_files:
        print("❌ No NPCs found to connect.")
        return
        
    print(f"🕸️  Weaving relationships for {len(npc_files)} NPCs...")
    
    # Load all NPCs into memory for context
    all_npcs = []
    for p in npc_files:
        with open(p, 'r') as f:
            all_npcs.append(json.load(f))
            
    # Process in batches
    batch_size = 3
    for i in range(0, len(npc_files), batch_size):
        batch = npc_files[i:i+batch_size]
        tasks = [process_npc(p, all_npcs, i+j+1, len(npc_files)) for j, p in enumerate(batch)]
        await asyncio.gather(*tasks)
        
    update_status("Social Architect", "Web Complete", "DONE")
    print("\n✨ Relationship Web Complete!")

if __name__ == "__main__":
    asyncio.run(main())
