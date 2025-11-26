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
from datetime import datetime
from dotenv import load_dotenv

# Add project root to import path
sys.path.insert(0, os.getcwd())
load_dotenv()

from agents.personality_designer import PersonalityDesignerAgent
from agents.lore_keeper import LoreKeeperAgent
from agents.utils import clean_json_output

OUTPUT_DIR = Path('world/npcs/retrofitted')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATUS_FILE = Path('agent_tasks.json')

def update_agent_status(agent_name, task, status, log_message=None):
    """Update the shared status file for the dashboard."""
    try:
        if STATUS_FILE.exists():
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
        else:
            return # Should exist
        
        if agent_name not in data['agents']:
            data['agents'][agent_name] = {}
            
        agent = data['agents'][agent_name]
        agent['status'] = status.lower()
        agent['last_active'] = datetime.utcnow().isoformat() + "Z"
        
        if task:
             # Find task ID if possible, or just describe it
             pass 

        if log_message:
            if 'logs' not in agent:
                agent['logs'] = []
            timestamp = datetime.utcnow().strftime('%H:%M:%S')
            agent['logs'].append(f"[{timestamp}] {log_message}")
            # Keep last 20 logs
            if len(agent['logs']) > 20:
                agent['logs'] = agent['logs'][-20:]
        
        with open(STATUS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Status update failed: {e}")

async def enrich_npc(npc_path: Path, total_count: int, index: int):
    # Load base NPC data
    with open(npc_path) as f:
        npc = json.load(f)
    name = npc.get('name', npc_path.stem)
    realm = npc.get('realm', 'Shadowfen')
    
    # Update Status
    update_agent_status("Personality Designer", None, "working", f"Starting analysis of {name} from {realm}...")
    
    # Initialize agents
    personality = PersonalityDesignerAgent()
    lore = LoreKeeperAgent()

    # 1. Generate personality traits
    update_agent_status("Personality Designer", None, "working", f"Generating personality profile for {name}...")
    
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
        update_agent_status("Personality Designer", None, "working", f"Generated traits: Goal='{traits.get('goal')}'")
    except Exception as e:
        print(f"⚠️ Failed to parse Personality output for {name}: {e}")
        update_agent_status("Personality Designer", None, "working", f"Error parsing output for {name}: {e}")
        traits = {}

    # 2. Validate with Lore Keeper
    update_agent_status("Lore Keeper", None, "working", f"Validating {name} against {realm} lore...")
    
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
        update_agent_status("Lore Keeper", None, "working", f"Validation complete for {name}.")
    except Exception as e:
        print(f"⚠️ Lore validation parse error for {name}: {e}")
        update_agent_status("Lore Keeper", None, "working", f"Validation error for {name}: {e}")
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
