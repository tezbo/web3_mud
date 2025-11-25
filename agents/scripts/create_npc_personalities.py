#!/usr/bin/env python3
"""
Create or update NPC personality data for all existing NPCs using the Personality Designer and Lore Keeper agents.
UPDATED: More robust JSON parsing and status reporting for visibility.
"""
import os
import sys
import json
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to import path
sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')
load_dotenv()

from agents.personality_designer import PersonalityDesignerAgent
from agents.lore_keeper import LoreKeeperAgent
from agents.utils import clean_json_output

OUTPUT_DIR = Path('world/npcs/retrofitted')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATUS_FILE = Path('agents/agent_status.json')

def update_agent_status(agent_name, task, status, progress=None):
    """Update the shared status file for the dashboard."""
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
        pass # Don't crash on status update

async def enrich_npc(npc_path: Path, total_count: int, index: int):
    # Load base NPC data
    with open(npc_path) as f:
        npc = json.load(f)
    name = npc.get('name', npc_path.stem)
    realm = npc.get('realm', 'Shadowfen')
    
    # Update Status
    update_agent_status("Personality Designer", f"Designing {name}", "WORKING", f"{index}/{total_count}")
    
    # Initialize agents
    personality = PersonalityDesignerAgent()
    lore = LoreKeeperAgent()

    # 1. Generate personality traits
    prompt = (
        f"Create a detailed personality profile for an NPC named '{name}' in the {realm} realm. "
        "Provide the following fields exactly as JSON (no extra text):\n"
        "{\n"
        "  \"goal\": string,\n"
        "  \"fear\": string,\n"
        "  \"secret\": string,\n"
        "  \"speech_pattern\": string,\n"
        "  \"relationships\": [string]  // brief hints of who they know or owe\n"
        "}\n"
        "Make the tone appropriate for the realm (Sunward = pragmatic, Twilight = formal, Shadowfen = gritty)."
    )
    
    personality_raw = await asyncio.get_event_loop().run_in_executor(
        None, personality.generate, prompt, {"model": "gpt-4o-mini"}
    )
    
    try:
        traits = json.loads(clean_json_output(personality_raw))
        if not isinstance(traits, dict):
            raise ValueError("Output is not a JSON object")
        required_keys = ["goal", "fear", "secret", "speech_pattern", "relationships"]
        missing = [k for k in required_keys if k not in traits]
        if missing:
            raise ValueError(f"Missing keys: {missing}")
    except Exception as e:
        print(f"⚠️ Failed to parse Personality output for {name}: {e}")
        update_agent_status("Personality Designer", f"Failed {name}", "ERROR")
        traits = {}

    # 2. Validate with Lore Keeper
    update_agent_status("Lore Keeper", f"Validating {name}", "WORKING")
    
    validation_prompt = (
        f"Check the following personality traits for consistency with {realm} culture. "
        f"Return a JSON object with the corrected traits. Do not include any conversational text, ONLY the JSON.\n"
        f"Traits: {json.dumps(traits)}"
    )
    
    validated_raw = await asyncio.get_event_loop().run_in_executor(
        None, lore.generate, validation_prompt, {"model": "gpt-4o-mini"}
    )
    
    try:
        validated_traits = json.loads(clean_json_output(validated_raw))
    except Exception as e:
        print(f"⚠️ Lore validation parse error for {name}: {e}")
        validated_traits = traits

    # 3. Merge into NPC data
    npc.update({
        "personality": validated_traits,
        "metadata": {"retrofitted": True, "realm": realm}
    })

    # 4. Write to retrofitted folder
    out_path = OUTPUT_DIR / npc_path.name
    with open(out_path, 'w') as f:
        json.dump(npc, f, indent=2)
        
    print(f"✅ Saved enriched NPC: {name}")
    return npc_path.name

async def main():
    npc_dir = Path('world/npcs')
    npc_files = [p for p in npc_dir.glob('*.json') if p.is_file()]
    
    if not npc_files:
        print("❌ No NPC JSON files found in world/npcs")
        return 1
        
    print(f"Found {len(npc_files)} NPC files. Starting parallel enrichment...\n")
    
    # Reset status
    update_agent_status("Personality Designer", "Idle", "IDLE")
    update_agent_status("Lore Keeper", "Idle", "IDLE")
    
    # Run in parallel batches of 3 to avoid rate limits but keep speed
    batch_size = 3
    for i in range(0, len(npc_files), batch_size):
        batch = npc_files[i:i+batch_size]
        tasks = [enrich_npc(p, len(npc_files), i+j+1) for j, p in enumerate(batch)]
        await asyncio.gather(*tasks)
        
    update_agent_status("Personality Designer", "Complete", "DONE")
    update_agent_status("Lore Keeper", "Complete", "DONE")
    print("\nAll NPCs processed.")
    return 0

if __name__ == "__main__":
    asyncio.run(main())
