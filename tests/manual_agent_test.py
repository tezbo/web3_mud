#!/usr/bin/env python3
"""
MANUAL TEST - Run this in your terminal to verify agents work
Command: python3 manual_agent_test.py
"""
import os
import sys
from dotenv import load_dotenv

# Immediate feedback
print("=" * 70, flush=True)
print("🧪 AGENT TEST STARTING", flush=True)
print("=" * 70, flush=True)

# Step 1
print("\n[1/4] Loading environment...", flush=True)
sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: No API key found", flush=True)
    sys.exit(1)
print("✓ Environment loaded", flush=True)

# Step 2
print("\n[2/4] Importing agent...", flush=True)
try:
    from agents.lore_keeper import LoreKeeperAgent
    print("✓ Agent imported successfully", flush=True)
except Exception as e:
    print(f"❌ Import failed: {e}", flush=True)
    sys.exit(1)

# Step 3
print("\n[3/4] Initializing agent...", flush=True)
try:
    agent = LoreKeeperAgent()
    print(f"✓ Agent initialized: {agent}", flush=True)
except Exception as e:
    print(f"❌ Initialization failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4
print("\n[4/4] Calling OpenAI API...", flush=True)
print("(This will take 5-15 seconds)", flush=True)

try:
    result = agent.generate_names("Sunward", count=3)
    print("\n" + "=" * 70, flush=True)
    print("✅ SUCCESS! Result:", flush=True)
    print(result, flush=True)
    print("=" * 70, flush=True)
except Exception as e:
    print(f"\n❌ API call failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
