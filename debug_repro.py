import requests
import sys
import time

BASE_URL = "http://127.0.0.1:5001"

def send_command(session, cmd):
    print(f"Sending command: {cmd}")
    resp = session.post(f"{BASE_URL}/command", json={"command": cmd})
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print("Response Text (Error):")
        print(resp.text[:1000])
        return None
    try:
        return resp.json()
    except:
        print("Failed to decode JSON")
        print(resp.text[:1000])
        return None

def debug_full_flow():
    session = requests.Session()
    username = f"debug_{int(time.time())}" # e.g. debug_1764195128 (16 chars)
    
    print(f"--- Starting Flow for {username} ---")
    
    # 1. Welcome
    session.get(f"{BASE_URL}/welcome")
    
    # 2. Start New
    resp = session.post(f"{BASE_URL}/welcome_command", json={"command": "N"})
    data = resp.json()
    if data.get("redirect"):
        url = f"{BASE_URL}{data['redirect']}"
        session.get(url)
    
    # 3. Onboarding
    # Username
    data = send_command(session, username)
    if not data: return
    print(f"Response: {data.get('response')}")
    
    # Password
    data = send_command(session, "password123")
    if not data: return
    print(f"Response: {data.get('response')}")
    
    # Race
    data = send_command(session, "human")
    if not data: return
    print(f"Response: {data.get('response')}")
    
    # Gender
    data = send_command(session, "nonbinary")
    if not data: return
    print(f"Response: {data.get('response')}")
    
    # Stats
    data = send_command(session, "str 2, agi 2, wis 2, wil 2, luck 2")
    if not data: return
    print(f"Response: {data.get('response')}")
    
    # Backstory
    data = send_command(session, "scarred_past")
    if not data: return
    print(f"Response: {data.get('response')}")
    
    if data.get("onboarding") is False:
        print("✅ Onboarding Complete!")
        
        # 4. Look
        data = send_command(session, "look")
        print(f"Look Log: {data.get('log')}")
        
        # 5. Inventory
        data = send_command(session, "inventory")
        print(f"Inventory Log: {data.get('log')}")

if __name__ == "__main__":
    debug_full_flow()
