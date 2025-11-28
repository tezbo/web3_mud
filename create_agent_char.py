#!/usr/bin/env python3
"""
Create the 'Agent' test character for browser testing.
This character is used by agents to test the game in the browser.
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:5001"

def create_agent_character():
    """Create the Agent/agent test character."""
    session = requests.Session()
    
    print("Creating 'Agent' test character...")
    
    # Start character creation
    session.get(f"{BASE_URL}/welcome")
    session.post(f"{BASE_URL}/welcome_command", json={"command": "N"})
    session.get(f"{BASE_URL}/?onboarding=start")
    
    # Character creation flow
    steps = [
        ("Agent", "Username"),
        ("agent", "Password"),
        ("human", "Race"),
        ("nonbinary", "Gender"),
        ("str 2, agi 2, wis 2, wil 2, luck 2", "Stats"),
        ("scarred_past", "Backstory"),
    ]
    
    for command, description in steps:
        print(f"Setting {description}: {command}")
        resp = session.post(f"{BASE_URL}/command", json={"command": command})
        if resp.status_code != 200:
            print(f"❌ Error setting {description}: {resp.status_code}")
            sys.exit(1)
    
    # Verify character created
    resp = session.post(f"{BASE_URL}/command", json={"command": "look"})
    if resp.status_code == 200:
        data = resp.json()
        if "Agent" in str(data.get("log", [])):
            print("✅ 'Agent' character created successfully!")
            print("\nTest credentials:")
            print("  Username: Agent")
            print("  Password: agent")
            return True
        else:
            print("❌ Character creation may have failed - couldn't verify")
            return False
    else:
        print(f"❌ Verification failed: {resp.status_code}")
        return False

if __name__ == "__main__":
    create_agent_character()
