import requests
import sys
import time

BASE_URL = "http://127.0.0.1:5001"

def send_command(session, cmd):
    print(f"Sending command: {cmd}")
    resp = session.post(f"{BASE_URL}/command", json={"command": cmd})
    if resp.status_code != 200:
        print(f"Error: {resp.status_code}")
        print(resp.text[:500])
        return None
    return resp.json()

def debug_movement():
    session = requests.Session()
    username = f"mover_{int(time.time())}"
    
    # 1. Create Character
    print(f"Creating character {username}...")
    session.get(f"{BASE_URL}/welcome")
    session.post(f"{BASE_URL}/welcome_command", json={"command": "N"})
    session.get(f"{BASE_URL}/?onboarding=start")
    
    send_command(session, username)
    send_command(session, "password123")
    send_command(session, "human")
    send_command(session, "nonbinary")
    send_command(session, "str 2, agi 2, wis 2, wil 2, luck 2")
    data = send_command(session, "scarred_past")
    
    if data.get("onboarding") is False:
        print("✅ Onboarding Complete!")
        
        # 2. Look
        data = send_command(session, "look")
        print(f"Look: {data.get('log')[-1]}")
        
        # 3. Move North (should trigger the error if not fixed)
        print("Moving North...")
        data = send_command(session, "n")
        print(f"Move Result: {data.get('log')[-1]}")
        
        # 4. Move South (back)
        print("Moving South...")
        data = send_command(session, "s")
        print(f"Move Result: {data.get('log')[-1]}")

if __name__ == "__main__":
    debug_movement()
