#!/usr/bin/env python3
"""
Greymarket Full Retrofit: All 11 rooms in parallel
"""
import os
import sys
import json
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to import path if needed
# sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')
load_dotenv()

from agents.wordsmith import WordsmithAgent
from agents.lore_keeper import LoreKeeperAgent

async def retrofit_room(room_file: Path, index: int):
    """Retrofit a single room"""
    
    with open(room_file) as f:
        room_data = json.load(f)
    
    room_name = room_data.get('name', 'Unknown')
    old_desc = room_data.get('description', '')
    
    print(f"[{index}] 🚀 Starting: {room_name}", flush=True)
    
    wordsmith = WordsmithAgent()
    lore_keeper = LoreKeeperAgent()
    
    loop = asyncio.get_event_loop()
    
    # Get Shadowfen context
    shadowfen_context = await loop.run_in_executor(
        None,
        lore_keeper.generate,
        f"'{room_name}' in Greymarket (Shadowfen hub). What would this look like? "
        f"3-4 sentences about Shadowfen version (stilts, salvaged materials, mist, survival).",
        {}
    )
    
    # Rewrite description
    new_desc = await loop.run_in_executor(
        None,
        wordsmith.generate,
        f"Rewrite for Greymarket/Shadowfen:\n\nRoom: {room_name}\n"
        f"Old: {old_desc}\n\nContext: {shadowfen_context}\n\n"
        f"Requirements: 3-5 sentences, 3+ sensory details, Shadowfen aesthetic (mist/decay/survival), "
        f"materials (salvaged wood, mire-leather, rust, stilts). Output ONLY the description.",
        {"model": "gpt-4o"}
    )
    
    # Generate ambient messages
    ambient_msgs = await loop.run_in_executor(
        None,
        wordsmith.write_ambient_messages,
        f"{room_name} in Shadowfen Grey market",
        5
    )
    
    # Parse ambient messages
    ambient_list = [msg.strip() for msg in ambient_msgs.split('\n') if msg.strip() and not msg.startswith('#')]
    ambient_list = [msg.lstrip('0123456789.-) ') for msg in ambient_list]
    amb_final = [msg for msg in ambient_list if len(msg) > 10][:5]
    
    # Update room data
    room_data['description'] = new_desc.strip()
    room_data['ambient_messages'] = amb_final
    if 'metadata' not in room_data:
        room_data['metadata'] = {}
    room_data['metadata']['realm'] = 'Shadowfen'
    room_data['metadata']['location'] = 'Greymarket'
    room_data['metadata']['retrofitted'] = True
    
    # Save
    output_dir = Path('world/rooms/retrofitted')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / room_file.name
    
    with open(output_file, 'w') as f:
        json.dump(room_data, f, indent=2)
    
    print(f"[{index}] ✅ Completed: {room_name} ({len(amb_final)} ambient msgs)", flush=True)
    
    return {'room': room_name, 'file': room_file.name, 'desc_length': len(new_desc), 'ambient_count': len(amb_final)}


async def main():
    rooms_dir = Path('world/rooms')
    room_files = [f for f in rooms_dir.glob('*.json') if f.is_file()]
    
    print("="*70)
    print(f"🎯 GREYMARKET FULL RETROFIT: {len(room_files)} ROOMS IN PARALLEL")
    print("="*70)
    print()
    
    start_time = time.time()
    
    # Process all rooms in parallel
    results = await asyncio.gather(*[
        retrofit_room(room_file, i+1) 
        for i, room_file in enumerate(room_files)
    ])
    
    elapsed = time.time() - start_time
    
    print()
    print("="*70)
    print("✅ ALL ROOMS RETROFITTED")
    print("="*70)
    print(f"\nCompleted {len(results)} rooms in {elapsed:.1f}s")
    print(f"Average: {elapsed/len(results):.1f}s per room")
    print()
    print("📋 SUMMARY:")
    for r in results:
        print(f"  ✓ {r['room']} ({r['desc_length']} chars, {r['ambient_count']} ambient msgs)")
    print()
    print(f"📁 Output: world/rooms/retrofitted/")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
