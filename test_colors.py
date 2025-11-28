import requests
import re

BASE_URL = "http://127.0.0.1:5001"

def test_color_rendering():
    """Test that color tags are properly removed/rendered in responses."""
    session = requests.Session()
    
    # Login
    session.get(f"{BASE_URL}/welcome")
    session.post(f"{BASE_URL}/welcome_command", json={"command": "Y"})
    session.post(f"{BASE_URL}/login", data={"username": "testuser", "password": "test123"})
    
    # Send look command (should have color tags in response)
    resp = session.post(f"{BASE_URL}/command", json={"command": "look"})
    
    if resp.status_code == 200:
        data = resp.json()
        log = data.get("log", [])
        
        # Check last few log entries for color tags
        print("Testing color tag rendering:")
        print("=" * 60)
        
        for entry in log[-5:]:
            # Check for raw tags (shouldn't be visible in browser)
            has_dark_yellow = "[DARK_YELLOW]" in entry
            has_dark_green = "[DARK_GREEN]" in entry
            has_exits = "[EXITS]" in entry
            
            if has_dark_yellow or has_dark_green or has_exits:
                print(f"❌ FOUND RAW TAGS (these should be processed by JavaScript):")
                print(f"   {entry[:100]}...")
            else:
                print(f"✅ No raw tags found in: {entry[:60]}...")
        
        print("=" * 60)
        print("\nNote: Color tags like [DARK_YELLOW] are correct in the API response.")
        print("They should be processed by JavaScript in the browser to show colored text.")
        print("\nTo verify colors work:")
        print("1. Open http://127.0.0.1:5001 in a browser")
        print("2. Login as a user")
        print("3. Type 'look'")
        print("4. Weather info should be DARK YELLOW")
        print("5. Exits should be DARK GREEN")
    else:
        print(f"Error: {resp.status_code}")

if __name__ == "__main__":
    test_color_rendering()
