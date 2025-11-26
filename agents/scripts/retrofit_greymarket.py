#!/usr/bin/env python3
"""
Greymarket Retrofit: Transform existing rooms into Shadowfen aesthetic
Uses Wordsmith + Lore Keeper agents in parallel
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')
load_dotenv()

from agents.wordsmith import WordsmithAgent
from agents.lore_keeper import LoreKeeperAgent

async def retrofit_room(room_file: Path):
    """Retrofit a single room to Shadowfen lore"""
    
    # Load existing room
    with open(room_file) as f:
        room_data = json.load(f)
    
    room_name = room_data.get('name', 'Unknown')
    old_desc = room_data.get('description', '')
    
    print(f"\n{'='*70}")
    print(f"🔧 RETROFITTING: {room_name}")
    print(f"{'='*70}")
    print(f"Original: {old_desc[:100]}...")
    
    # Initialize agents
    wordsmith = WordsmithAgent()
    lore_keeper = LoreKeeperAgent()
    
    # Task 1: Lore Keeper reviews what type of building fits Shadowfen
    print("\n[1/3] Lore Keeper: Determining Shadowfen equivalent...")
    shadowfen_context = await asyncio.get_event_loop().run_in_executor(
        None,
        lore_keeper.generate,
        f"This room is '{room_name}' in Greymarket (Shadowfen hub). "
        f"What would this type of building look like in Shadowfen culture? "
        f"Consider: stilted buildings, salvaged materials, mist, pragmatic survival focus. "
        f"Give 3-4 sentences about the Shadowfen version of this location.",
        {}
    )
    print(f"✓ Context: {shadowfen_context[:150]}...")
    
    # Task 2: Wordsmith rewrites description with sensory details
    print("\n[2/3] Wordsmith: Rewriting description...")
    new_desc = await asyncio.get_event_loop().run_in_executor(
        None,
        wordsmith.generate,
        f"Rewrite this room description for Greymarket in the Shadowfen:\n\n"
        f"Room: {room_name}\n"
        f"Old description: {old_desc}\n\n"
        f"Shadowfen context: {shadowfen_context}\n\n"
        f"Requirements:\n"
        f"- 3-5 sentences\n"
        f"- Include 3+ sensory details (sight, sound, smell, touch)\n"
        f"- Shadowfen aesthetic: mist, decay, survival, pragmatism\n"
        f"- Materials: salvaged wood, mire-leather, rust, stilts\n"
        f"- Make it atmospheric and immersive\n\n"
        f"Output ONLY the new description, nothing else.",
        {"model": "gpt-4o"}
    )
    print(f"✓ New description created")
    
    # Task 3: Generate ambient messages
    print("\n[3/3] Wordsmith: Creating ambient messages...")
    ambient_msgs = await asyncio.get_event_loop().run_in_executor(
        None,
        wordsmith.write_ambient_messages,
        f"{room_name} in Shadowfen Greymarket",
        5
    )
    
    # Parse ambient messages (should be a list)
    ambient_list = [msg.strip() for msg in ambient_msgs.split('\n') if msg.strip() and not msg.startswith('#')]
    ambient_list = [msg.lstrip('0123456789.-) ') for msg in ambient_list]  # Remove numbering
    amb_final = [msg for msg in ambient_list if len(msg) > 10][:5]  # Take first 5 valid ones
    
    print(f"✓ {len(amb_final)} ambient messages created")
    
    # Update room data
    room_data['description'] = new_desc.strip()
    if 'ambient_messages' not in room_data:
        room_data['ambient_messages'] = []
    room_data['ambient_messages'] = amb_final
    
    # Add metadata
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
    
    print(f"\n✅ SAVED: {output_file}")
    print(f"\n📋 NEW DESCRIPTION:")
    print(f"{new_desc}")
    print(f"\n🌫️ AMBIENT MESSAGES:")
    for i, msg in enumerate(amb_final, 1):
        print(f"  {i}. {msg}")
    
    return room_data


async def main():
    """Retrofit first room as proof of concept"""
    
    print("🎯 GREYMARKET RETROFIT - PROOF OF CONCEPT")
    print("Testing with 1 room, then scaling to all 11\n")
    
    # Start with town square (central location)
    room_file = Path('world/rooms/town_square.json')
    
    if not room_file.exists():
        print(f"❌ Room file not found: {room_file}")
        return 1
    
    result = await retrofit_room(room_file)
    
    print("\n" + "="*70)
    print("✅ PROOF OF CONCEPT COMPLETE")
    print("="*70)
    print("\nNext: Run this script on all 11 rooms in parallel")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
