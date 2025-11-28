"""
QA Bot Agent - Automated Testing and Verification.
"""
import sys
import time
import requests
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

sys.path.append(str(Path(__file__).parents[1]))  # Add project root to path
from agents.agent_framework import AutonomousAgent

class QABotAgent(AutonomousAgent):
    """
    Agent responsible for running automated tests against the running game server.
    """
    def __init__(self) -> None:
        super().__init__(
            name="QA Bot",
            role="Quality Assurance",
            capabilities=["qa", "test", "verify"]
        )
        self.base_url: str = "http://127.0.0.1:5000"
        self.session = requests.Session()

    def run_loop(self) -> None:
        """
        Monitor for 'qa_ready' tasks or run periodic health checks.
        """
        self.log("Starting QA Bot loop...")
        sleep_duration: int = 5
        while True:
            if self.check_workforce_status() == 'paused':
                time.sleep(sleep_duration)
                continue
            task = self.find_qa_task()
            if task:
                self.run_verification_suite(task)
            else:
                time.sleep(sleep_duration)

    def find_qa_task(self) -> None:
        """
        Placeholder: look for tasks in 'qa_ready' state.
        """
        return None

    # --- Helper Methods ---

    def _send_command(self, cmd: str, expected_text: str = None) -> Dict:
        """Send a command to the game server."""
        resp = self.session.post(f"{self.base_url}/command", json={"command": cmd})
        data = resp.json()
        
        if expected_text:
            response_text = data.get("response", "")
            log_text = "".join(data.get("log", []))
            full_text = response_text + log_text
            if expected_text.lower() not in full_text.lower():
                self.log(f"⚠️ Warning: Expected '{expected_text}' not found.")
                
        return data

    def _create_character(self, username: str) -> bool:
        """Helper to create a new character with default stats."""
        try:
            self.log(f"Creating character: {username}")
            # Welcome screen
            resp = self.session.get(f"{self.base_url}/welcome")
            if resp.status_code != 200:
                self.log(f"❌ Server not reachable. Status: {resp.status_code}")
                return False

            # Start New
            resp = self.session.post(f"{self.base_url}/welcome_command", json={"command": "N"})
            data = resp.json()
            if data.get("redirect"):
                redirect_url = data["redirect"]
                if redirect_url.startswith("/"):
                    redirect_url = f"{self.base_url}{redirect_url}"
                self.session.get(redirect_url)
            else:
                self.log("❌ Failed to start new character (no redirect)")
                return False
                
            # Onboarding flow
            password = "password123"
            self._send_command(username)
            self._send_command(password)
            self._send_command("human")
            self._send_command("nonbinary")
            self._send_command("str 2, agi 2, wis 2, wil 2, luck 2")
            data = self._send_command("scarred_past")
            
            if data.get("onboarding") is False:
                self.log("✅ Character created successfully")
                return True
            
            self.log("❌ Onboarding did not complete")
            return False
        except Exception as e:
            self.log(f"❌ Character creation failed: {e}")
            return False

    # --- Test Suites ---

    def run_smoke_test(self) -> bool:
        """
        Run a basic smoke test: Welcome -> New Character -> Onboarding -> Look -> Move.
        """
        self.log("🧪 Starting Smoke Test...")
        results: List[str] = []
        feedback: List[str] = []
        
        try:
            username: str = f"qa_smoke_{int(time.time())}"
            if not self._create_character(username):
                results.append("Onboarding: FAIL")
                return False
            
            results.append("Onboarding: PASS")

            # Test Look
            self.log("Sending 'look' command")
            data = self._send_command("look")
            description: str = "".join(data.get("log", []))
            
            if "[WEATHER]" in description or "Exits:" in description or "You see" in description:
                self.log("✅ Room description detected")
                results.append("Look: PASS")
            else:
                self.log("❌ Room description missing/malformed")
                results.append("Look: FAIL")

            # Test Help
            data = self._send_command("help")
            if "Available commands" in "".join(data.get("log", [])):
                self.log("✅ Help command successful")
                results.append("Command: PASS")
            else:
                self.log("❌ Help command failed")
                results.append("Command: FAIL")

            self.log(f"🏁 Smoke Test Complete. Results: {results}")
            self.generate_feedback(results, feedback)
            return all("PASS" in r for r in results)

        except Exception as e:
            self.log(f"❌ Smoke Test Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_inventory_test(self) -> bool:
        """
        Run a specific test for the new Inventory System.
        Flow: Login -> Look -> Take Item -> Check Inventory -> Drop Item -> Check Room.
        """
        self.log("🎒 Starting Inventory System Test...")
        results: List[str] = []
        
        try:
            # 1. Login/Create Character
            username: str = f"inv_tester_{int(time.time())}"
            if not self._create_character(username):
                return False
                
            # 2. Look at room
            self.log("Looking at room...")
            data = self._send_command("look")
            
            # 3. Try to take an item (assuming 'sword' or similar might exist, or fail gracefully)
            # For a robust test, we should spawn an item or use a debug command.
            # Since we don't have that yet, we'll try to get a common item.
            target_item = "sword" 
            
            self.log(f"Attempting to take '{target_item}'...")
            data = self._send_command(f"get {target_item}")
            response = data.get("response", "") + "".join(data.get("log", []))
            
            if "You pick up" in response:
                self.log(f"✅ Successfully picked up {target_item}")
                results.append("Take: PASS")
            elif "don't see that" in response:
                self.log(f"⚠️ Could not find {target_item}. Skipping take test.")
                results.append("Take: SKIPPED")
            else:
                self.log(f"❌ Failed to take item: {response}")
                results.append("Take: FAIL")
                
            # 4. Check Inventory
            self.log("Checking inventory...")
            data = self._send_command("inventory")
            response = data.get("response", "") + "".join(data.get("log", []))
            
            if "You are carrying:" in response:
                self.log("✅ Inventory command working")
                if target_item in response and "Take: PASS" in results:
                    self.log(f"✅ Item {target_item} confirmed in inventory")
                    results.append("Inventory Check: PASS")
            else:
                self.log(f"❌ Inventory command failed: {response}")
                results.append("Inventory Check: FAIL")
                
            # 5. Drop Item
            if "Take: PASS" in results:
                self.log(f"Dropping {target_item}...")
                data = self._send_command(f"drop {target_item}")
                response = data.get("response", "") + "".join(data.get("log", []))
                
                if "You drop" in response:
                    self.log(f"✅ Successfully dropped {target_item}")
                    results.append("Drop: PASS")
                else:
                    self.log(f"❌ Failed to drop item: {response}")
                    results.append("Drop: FAIL")

            self.log(f"🏁 Inventory Test Complete. Results: {results}")
            return all("PASS" in r or "SKIPPED" in r for r in results)

        except Exception as e:
            self.log(f"❌ Inventory Test Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_regression_suite(self) -> bool:
        """
        Run the full pytest suite and analyze results with AI.
        """
        self.log("🧪 Starting Regression Suite...")
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "tests/"], capture_output=True, text=True)
            output: str = result.stdout + result.stderr
            analysis: dict = self._analyze_test_results_with_ai(output)
            self.log(f"\n🤖 QA Bot Regression Analysis 🤖")
            self.log("=================================")
            self.log(f"Status: {analysis.get('status', 'UNKNOWN')}")
            self.log(f"Summary: {analysis.get('summary', 'No summary')}")
            if analysis.get('failures'):
                self.log("\nFailures:")
                for fail in analysis['failures']:
                    self.log(f"- {fail}")
            return result.returncode == 0
        except Exception as e:
            self.log(f"❌ Regression Suite Error: {e}")
            return False

    def _analyze_test_results_with_ai(self, test_output: str) -> dict:
        """Use AI to analyze pytest output."""
        prompt = f"""
        Analyze these pytest results.
        Identify any regressions or failures.
        OUTPUT:
        {test_output[-4000:]}
        """
        system_prompt = "You are an expert QA Engineer. Analyze test output and return JSON: { 'status': 'PASS'|'FAIL', 'summary': str, 'failures': [str] }"
        return self.think(prompt, system_prompt, response_format={"type": "json_object"})

    def generate_feedback(self, results: List[str], specific_feedback: List[str]) -> None:
        """Generate UX/Gameplay feedback using AI."""
        prompt = f"""
        Generate a QA report based on these smoke test results.
        Results: {results}
        Specific Feedback: {specific_feedback}
        """
        system_prompt = "You are a QA Bot for a MUD game. Provide constructive feedback on gameplay and immersion based on test results."
        feedback: str = self.think(prompt, system_prompt)
        self.log("\n🤖 QA Bot Feedback Report (AI Generated) 🤖")
        self.log("==========================================")
        self.log(feedback)
        self.log("==========================================\n")

if __name__ == "__main__":
    agent = QABotAgent()
    print("1. Running Regression Suite (Unit Tests)...")
    agent.run_regression_suite()
    print("\n2. Running Smoke Test (Gameplay)...")
    agent.run_smoke_test()
    print("\n3. Running Inventory Test (New Feature)...")
    agent.run_inventory_test()