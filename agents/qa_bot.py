"""
QA Bot Agent - Automated Testing and Verification.
"""
import sys
import time
import requests
import re
import subprocess
from pathlib import Path
sys.path.append(str(Path(__file__).parents[1]))  # Add project root to path
from agents.agent_framework import AutonomousAgent

class QABotAgent(AutonomousAgent):
    """
    Agent responsible for running automated tests against the running game server.
    """
    
    def __init__(self):
        super().__init__(
            name="QA Bot",
            role="Quality Assurance",
            capabilities=["qa", "test", "verify"]
        )
        self.base_url = "http://127.0.0.1:5004"
        self.session = requests.Session()
        
    def run_loop(self):
        """
        Monitor for 'qa_ready' tasks or run periodic health checks.
        """
        self.log("Starting QA Bot loop...")
        
        while True:
            if self.check_workforce_status() == 'paused':
                time.sleep(5)
                continue
                
            # For now, we'll just look for a specific trigger file or task
            # In a real system, this would consume from a queue
            task = self.find_qa_task()
            if task:
                self.run_verification_suite(task)
            else:
                time.sleep(5)

    def find_qa_task(self):
        # Placeholder: look for tasks in 'qa_ready' state
        return None

    def run_smoke_test(self):
        """
        Run a basic smoke test: Welcome -> New Character -> Onboarding -> Look -> Move.
        """
        self.log("🧪 Starting Smoke Test...")
        results = []
        feedback = []
        
        try:
            # 1. Initialize Session via Welcome Screen
            self.log("Accessing Welcome Screen...")
            resp = self.session.get(f"{self.base_url}/welcome")
            if resp.status_code != 200:
                self.log(f"❌ Server not reachable. Status: {resp.status_code}")
                return False
            self.log(f"✅ Welcome Screen Loaded. Cookies: {self.session.cookies.get_dict()}")
            
            # 2. Start New Character ('N' command)
            self.log("Sending 'N' to start new character...")
            resp = self.session.post(f"{self.base_url}/welcome_command", json={"command": "N"})
            data = resp.json()
            
            if data.get("redirect"):
                # Follow redirect manually to initialize onboarding session
                redirect_url = data["redirect"]
                if redirect_url.startswith("/"):
                    redirect_url = f"{self.base_url}{redirect_url}"
                
                self.log(f"Following redirect to: {redirect_url}")
                resp = self.session.get(redirect_url)
                self.log(f"✅ Onboarding Started. Cookies: {self.session.cookies.get_dict()}")
            else:
                self.log("❌ Failed to start new character (no redirect)")
                return False

            # Helper to send command
            def send_command(cmd, expected_text=None):
                resp = self.session.post(f"{self.base_url}/command", json={"command": cmd})
                data = resp.json()
                response_text = data.get("response", "")
                log_text = "".join(data.get("log", []))
                full_text = response_text + log_text
                
                if expected_text and expected_text.lower() not in full_text.lower():
                    self.log(f"⚠️ Warning: Expected '{expected_text}' not found.")
                
                return data

            # 3. Onboarding Flow
            username = f"qa_bot_{int(time.time())}"
            password = "password123"
            
            # Step 1: Username
            self.log(f"Sending Username: {username}")
            data = send_command(username)
            
            # Step 2: Password
            self.log("Sending Password")
            data = send_command(password)
            
            # Step 3: Race
            self.log("Selecting Race (human)")
            data = send_command("human")
            
            # Step 4: Gender
            self.log("Selecting Gender (nonbinary)")
            data = send_command("nonbinary")
            
            # Step 5: Stats
            self.log("Allocating Stats")
            data = send_command("str 2, agi 2, wis 2, wil 2, luck 2")
            
            # Step 6: Backstory
            self.log("Selecting Backstory (scarred_past)")
            data = send_command("scarred_past")
            
            # Check completion
            if data.get("onboarding") is False:
                self.log(f"✅ Onboarding Complete. Cookies: {self.session.cookies.get_dict()}")
                results.append("Onboarding: PASS")
            else:
                self.log("❌ Onboarding Failed (Still in progress)")
                self.log(f"DEBUG: Last response data: {data}")
                results.append("Onboarding: FAIL")
                return False
                
            # 4. Look (Verify Weather & Exits)
            self.log("Sending 'look' command")
            data = send_command("look")
            description = "".join(data.get("log", []))
            
            if "[WEATHER]" in description:
                self.log("✅ Weather Line Detected")
                results.append("Weather: PASS")
            else:
                self.log("❌ Weather Line Missing")
                feedback.append("UX: Weather information is missing from the room description. It adds immersion.")
                results.append("Weather: FAIL")
                
            if "[EXITS]" in description:
                self.log("✅ Exits Formatted Detected")
                results.append("Exits: PASS")
            else:
                self.log("❌ Exits Formatting Missing")
                feedback.append("UX: Exits are not clearly formatted. Players need to know where they can go.")
                results.append("Exits: FAIL")
                
            # 5. Move
            data = send_command("help")
            if "Available commands" in "".join(data.get("log", [])):
                 self.log("✅ Command Execution Successful")
                 results.append("Command: PASS")
            else:
                 self.log("❌ Command Execution Failed")
                 results.append("Command: FAIL")

            self.log(f"🏁 Smoke Test Complete. Results: {results}")
            
            # Generate Feedback
            self.generate_feedback(results, feedback)
            
            return all("PASS" in r for r in results)
            
        except Exception as e:
            self.log(f"❌ Smoke Test Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_regression_suite(self):
        """
        Run the full pytest suite and analyze results with AI.
        """
        self.log("🧪 Starting Regression Suite...")
        try:
            # Run pytest and capture output
            result = subprocess.run([sys.executable, "-m", "pytest", "tests/"], capture_output=True, text=True)
            output = result.stdout + result.stderr
            
            # Analyze with AI
            analysis = self._analyze_test_results_with_ai(output)
            
            self.log("\n🤖 QA Bot Regression Analysis 🤖")
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

    def _analyze_test_results_with_ai(self, test_output):
        """Use AI to analyze pytest output."""
        prompt = f"""
        Analyze these pytest results.
        Identify any regressions or failures.
        
        OUTPUT:
        {test_output[-4000:]}
        """
        
        system_prompt = "You are an expert QA Engineer. Analyze test output and return JSON: { 'status': 'PASS'|'FAIL', 'summary': str, 'failures': [str] }"
        
        return self.think(prompt, system_prompt, response_format={"type": "json_object"})

    def generate_feedback(self, results, specific_feedback):
        """
        Generate UX/Gameplay feedback using AI.
        """
        prompt = f"""
        Generate a QA report based on these smoke test results.
        
        Results: {results}
        Specific Feedback: {specific_feedback}
        """
        
        system_prompt = "You are a QA Bot for a MUD game. Provide constructive feedback on gameplay and immersion based on test results."
        
        feedback = self.think(prompt, system_prompt)
        
        self.log("\n🤖 QA Bot Feedback Report (AI Generated) 🤖")
        self.log("==========================================")
        self.log(feedback)
        self.log("==========================================\n")

if __name__ == "__main__":
    agent = QABotAgent()
    # Run a single smoke test immediately for verification
    agent.run_smoke_test()
