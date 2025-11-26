#!/usr/bin/env python3
"""
Simple test to verify agents work with timeout handling
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')
load_dotenv()

from agents.lore_keeper import LoreKeeperAgent

def main():
    print("🧪 Testing Lore Keeper Agent...")
    print("=" * 60)
    
    try:
        # Initialize agent
        agent = LoreKeeperAgent()
        print("✓ Agent initialized")
        
        # Test simple task with timeout
        print("\nGenerating 5 Sunward names...")
        result = agent.generate_names("Sunward", count=5)
        
        print("\n📋 Result:")
        print(result)
        print("\n" + "=" * 60)
        print("✓ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
