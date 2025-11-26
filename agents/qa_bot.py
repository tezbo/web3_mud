"""
QA Bot Agent - Automated Testing and Verification.
"""
import sys
import time
import requests
import re
import subprocess
from pathlib import Path
from typing import List, Dict

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
        self.base_url: str = "http://127.0.0.1:5004"
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

    def run_smoke_test(self) -> bool:
        """
        Run a basic smoke test: Welcome -> New Character -> Onboarding -> Look -> Move.
        """
        self.log("🧪 Starting Smoke Test...")
        results: List[str] = []
        feedback: List[str] = []
        try:
            self.log("Accessing Welcome Screen...")
            resp = self.session.get(f"{self.base_url}/welcome")
            if resp.status_code != 200:
                self.log(f"❌ Server not reachable. Status: {resp.status_code}")
                return False
            self.log(f"✅ Welcome Screen Loaded. Cookies: {self.session.cookies.get_dict()}")

            self.log("Sending 'N' to start new character...")
            resp = self.session.post(f"{self.base_url}/welcome_command", json={"command": "N"})
            data = resp.json()
            if data.get("redirect"):
                redirect_url = data["redirect"]
                if redirect_url.startswith("/"):
                    redirect_url = f"{self.base_url}{redirect_url}"
                self.log(f"Following redirect to: {redirect_url}")
                resp = self.session.get(redirect_url)
                self.log(f"✅ Onboarding Started. Cookies: {self.session.cookies.get_dict()}")
            else:
                self.log("❌ Failed to start new character (no redirect)")
                return False

            def send_command(cmd: str, expected_text: str = None) -> Dict:
                resp = self.session.post(f"{self.base_url}/command", json={"command": cmd})
                data = resp.json()
                response_text: str = data.get("response", "")
                log_text: str = "".join(data.get("log", []))
                full_text: str = response_text + log_text
                if expected_text and expected_text.lower() not in full_text.lower():
                    self.log(f"⚠️ Warning: Expected '{expected_text}' not found.")
                return data

            username: str = f"qa_bot_{int(time.time())}"
            password: str = "password123"

            self.log(f"Sending Username: {username}")
            data = send_command(username)
            self.log("Sending Password")
            data = send_command(password)
            self.log("Selecting Race (human)")
            data = send_command("human")
            self.log("Selecting Gender (nonbinary)")
            data = send_command("nonbinary")
            self.log("Allocating Stats")
            data = send_command("str 2, agi 2, wis 2, wil 2, luck 2")
            self.log("Selecting Backstory (scarred_past)")
            data = send_command("scarred_past")

            if data.get("onboarding") is False:
                self.log(f"✅ Onboarding Complete. Cookies: {self.session.cookies.get_dict()}")
                results.append("Onboarding: PASS")
            else:
                self.log("❌ Onboarding Failed (Still in progress)")
                feedback.append("UX: Onboarding process is incomplete.")
                self.log(f"DEBUG: Last response data: {data}")
                results.append("Onboarding: FAIL")
                return False

            self.log("Sending 'look' command")
            data = send_command("look")
            description: str = "".join(data.get("log", []))
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

            data = send_command("help")
            if "Available commands" in "".join(data.get("log", [])):
                self.log("✅ Command Execution Successful")
                results.append("Command: PASS")
            else:
                self.log("❌ Command Execution Failed")
                results.append("Command: FAIL")

            self.log(f"🏁 Smoke Test Complete. Results: {results}")
            self.generate_feedback(results, feedback)
            return all("PASS" in r for r in results)

        except Exception as e:
            self.log(f"❌ Smoke Test Error: {e}")
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
    agent.run_smoke_test()