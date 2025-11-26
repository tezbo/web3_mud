#!/usr/bin/env python3
"""
Janitor Agent
Analyzes the codebase and suggests cleanup actions.
"""
import os
import sys
from pathlib import Path

# Add project root to import path if needed
# sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')

def analyze_structure():
    root = Path('.')
    
    # Files to ignore
    ignore = {'.git', 'venv', '__pycache__', 'node_modules', '.DS_Store', 'discworld_example'}
    
    # Categories
    test_scripts = []
    docs = []
    agents = []
    core = []
    world = []
    
    print("🧹 JANITOR AGENT: Analyzing folder structure...\n")
    
    for item in root.iterdir():
        if item.name in ignore:
            continue
            
        if item.is_file():
            if item.name.startswith('test_') or item.name.startswith('verify_') or item.name.endswith('_test.py'):
                test_scripts.append(item.name)
            elif item.suffix == '.md':
                docs.append(item.name)
            elif item.suffix == '.py':
                core.append(item.name)
    
    print(f"Found {len(test_scripts)} test scripts in root (should be in tests/ or scripts/)")
    print(f"Found {len(docs)} markdown files in root (should be in docs/)")
    
    print("\n📋 PROPOSED CLEANUP PLAN:")
    print("1. Create 'tests/' directory and move test scripts there")
    print("2. Create 'docs/' directory and move documentation there (except README.md)")
    print("3. Create 'scripts/' directory for utility scripts")
    
    print("\nFiles to move to tests/:")
    for f in test_scripts[:5]: print(f"  - {f}")
    if len(test_scripts) > 5: print(f"  ...and {len(test_scripts)-5} more")
    
    print("\nFiles to move to docs/:")
    for f in docs:
        if f != 'README.md':
            print(f"  - {f}")

if __name__ == "__main__":
    analyze_structure()
