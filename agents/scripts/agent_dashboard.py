#!/usr/bin/env python3
"""
Agent Dashboard
Shows live status of AI agents working in parallel.
"""
import sys
import time
import json
import os
from pathlib import Path

# Add project root to import path
sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')

STATUS_FILE = Path('agents/agent_status.json')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_status():
    if not STATUS_FILE.exists():
        return {}
    try:
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def print_dashboard():
    while True:
        status_data = load_status()
        clear_screen()
        
        print("\n🤖 AETHERMOOR AGENT TEAM DASHBOARD")
        print("=" * 60)
        print(f"{'AGENT':<25} | {'STATUS':<10} | {'TASK':<30}")
        print("-" * 60)
        
        if not status_data:
            print("Waiting for agents to report...")
        
        for agent, info in status_data.items():
            status = info.get('status', 'UNKNOWN')
            task = info.get('task', '')
            progress = info.get('progress', '')
            
            # Colorize status (if terminal supports it, otherwise plain)
            status_display = status
            if status == "WORKING":
                status_display = f"⚡ {status}"
            elif status == "DONE":
                status_display = f"✅ {status}"
            elif status == "ERROR":
                status_display = f"❌ {status}"
            elif status == "IDLE":
                status_display = f"💤 {status}"
                
            task_display = f"{task} {f'({progress})' if progress else ''}"
            
            print(f"{agent:<25} | {status_display:<10} | {task_display:<30}")
            
        print("-" * 60)
        print("Press Ctrl+C to exit")
        time.sleep(1)

if __name__ == "__main__":
    try:
        print_dashboard()
    except KeyboardInterrupt:
        print("\nDashboard closed.")
