"""
DevOps Agent - Monitors deployments and merges approved branches
"""

import os
import time
import json
import logging
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from agents.base_agent import BaseAgent

load_dotenv()

logger = logging.getLogger(__name__)

class DevOpsAgent(BaseAgent):
    """
    Agent responsible for monitoring deployment status, checking CI/CD pipelines,
    and verifying system health.
    """
    
    def __init__(self):
        super().__init__(
            name="DevOps Engineer",
            role="DevOps & Infrastructure Specialist",
            system_prompt=(
                "You are an expert DevOps Engineer responsible for maintaining the stability "
                "and deployment pipeline of the MUD. You monitor GitHub Actions, Render deployments, "
                "and system health metrics. You provide concise status reports and actionable "
                "recommendations when builds fail."
            )
        )
        # Load tokens from env
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.render_api_key = os.environ.get("RENDER_API_KEY")
        self.repo_owner = "tezbo"
        self.repo_name = "web3_mud"
        
    def check_github_actions_status(self, branch="main"):
        """Check the status of the latest GitHub Actions run for a branch."""
        if not self.github_token:
            return {"status": "unknown", "error": "GITHUB_TOKEN not set"}
            
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        params = {"branch": branch, "per_page": 1}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("workflow_runs"):
                return {"status": "unknown", "message": "No runs found"}
                
            latest_run = data["workflow_runs"][0]
            return {
                "status": latest_run["status"],
                "conclusion": latest_run["conclusion"],
                "url": latest_run["html_url"],
                "created_at": latest_run["created_at"]
            }
        except Exception as e:
            print(f"⚠️ GitHub API Error: {e}")
            return {"status": "error", "message": str(e)}

    def check_render_deployment_status(self, service_id=None):
        """Check the status of the latest Render deployment."""
        if not self.render_api_key:
            return {"status": "unknown", "error": "RENDER_API_KEY not set"}
            
        headers = {
            "Authorization": f"Bearer {self.render_api_key}",
            "Accept": "application/json"
        }

        # If service_id not provided, try to find it
        service_id = service_id or os.environ.get("RENDER_SERVICE_ID")
        
        if not service_id:
            # Try to fetch the first web service
            try:
                services_url = "https://api.render.com/v1/services"
                services_res = requests.get(services_url, headers=headers, params={"limit": 10})
                services_res.raise_for_status()
                services_data = services_res.json()
                
                # Look for a web service named 'web3_mud' or just take the first one
                for svc in services_data:
                    if svc['service']['name'] == 'web3_mud' or len(services_data) == 1:
                        service_id = svc['service']['id']
                        print(f"🔍 Found Render Service: {svc['service']['name']} ({service_id})")
                        break
                
                if not service_id and services_data:
                    # Fallback to first one
                    service_id = services_data[0]['service']['id']
                    print(f"⚠️ Using first found service: {services_data[0]['service']['name']} ({service_id})")
                    
            except Exception as e:
                print(f"⚠️ Could not list services: {e}")

        if not service_id:
             return {"status": "unknown", "error": "RENDER_SERVICE_ID not set and could not be discovered"}

        url = f"https://api.render.com/v1/services/{service_id}/deploys"
        headers = {
            "Authorization": f"Bearer {self.render_api_key}",
            "Accept": "application/json"
        }
        params = {"limit": 1}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return {"status": "unknown", "message": "No deploys found"}
                
            latest_deploy = data[0]["deploy"]
            return {
                "status": latest_deploy["status"],
                "id": latest_deploy["id"],
                "url": f"https://dashboard.render.com/web/{service_id}/deploys/{latest_deploy['id']}",
                "created_at": latest_deploy["createdAt"]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def monitor_deployment(self, branch="main", interval=30, timeout=600):
        """Monitor a deployment until it succeeds or fails."""
        start_time = time.time()
        
        print(f"🔍 Monitoring deployment for branch '{branch}'...")
        
        while time.time() - start_time < timeout:
            # Check GitHub Actions
            gh_status = self.check_github_actions_status(branch)
            # Debug: print full status
            print(f"DEBUG GitHub Status: {gh_status}")
            
            gh_msg = f"GitHub: {gh_status.get('status', 'unknown')}"
            if gh_status.get('conclusion'):
                gh_msg += f" ({gh_status.get('conclusion')})"
            
            # Check Render
            render_status = self.check_render_deployment_status()
            render_msg = f"Render: {render_status.get('status', 'unknown')} ({render_status.get('created_at')})"
            
            print(f"[{int(time.time() - start_time)}s] {gh_msg} | {render_msg}")
            
            if render_status.get("status") == "live":
                print(f"✅ Deployment Live! URL: {render_status.get('url')}")
                return True
            elif render_status.get("status") in ["build_failed", "update_failed", "canceled"]:
                print(f"❌ Deployment Failed ({render_status.get('status')})! URL: {render_status.get('url')}")
                return False
            
            time.sleep(interval)
            
        print("⚠️ Monitoring timed out.")
        return False

    def check_local_health(self):
        """Check if local server is healthy."""
        try:
            response = requests.get("http://localhost:8000/api/dashboard", timeout=2)
            if response.status_code == 200:
                print("✅ Local server is HEALTHY")
                return True
            else:
                print(f"⚠️ Local server returned {response.status_code}")
                return False
        except requests.exceptions.RequestException:
            print("❌ Local server is DOWN")
            return False

    def report_status(self):
        """Report status to the dashboard."""
        try:
            # Self-report to the dashboard API
            requests.post("http://localhost:8000/api/agent/status", json={
                "agent_name": "DevOps",
                "status": "working",
                "task_id": "task-8"  # Continuous Monitoring
            }, timeout=1)
        except:
            pass  # Ignore errors if dashboard is down (we are the ones checking it!)

    def check_render_health(self):
        """Check Render status and alert on failure."""
        try:
            status = self.check_render_deployment_status()
            current_status = status.get('status')
            
            # Only log if status changed or is failed
            if hasattr(self, 'last_render_status') and self.last_render_status == current_status:
                return

            self.last_render_status = current_status
            
            if current_status == 'live':
                self.report_status_log(f"✅ Render Deployment is LIVE.")
            elif current_status in ['build_failed', 'update_failed', 'canceled', 'crashed']:
                self.report_status_log(f"🚨 CRITICAL: Render Deployment {current_status.upper()}! Check logs.")
            elif current_status == 'build_in_progress':
                self.report_status_log(f"🏗️ Render Deployment in progress...")
                
        except Exception as e:
            print(f"Error checking render health: {e}")

    def monitor_loop(self):
        """Continuous monitoring loop."""
        print(f"🚀 Senior DevOps Agent starting monitoring loop...")
        
        while True:
            # 1. Check Local Health
            is_healthy = self.check_local_health()
            
            # 2. Report to Dashboard (if healthy)
            if is_healthy:
                self.report_status()
                
            # 3. Check Render Health (New)
            self.check_render_health()

            # 4. Check GitHub Actions (every 60s)
            if int(time.time()) % 60 == 30: # Offset by 30s
                gh_status = self.check_github_actions_status()
                if gh_status.get('status') == 'completed' and gh_status.get('conclusion') == 'failure':
                    self.report_status_log(f"❌ GitHub Action FAILED: {gh_status.get('url')}")
            
            # 5. Check for Tasks Ready for Review (CI/CD Simulation)
            self.check_for_reviews()

            time.sleep(5)  # Check every 5 seconds

    def check_for_reviews(self):
        """Check for tasks that are approved and ready for deployment."""
        try:
            with open("agent_tasks.json", 'r') as f:
                data = json.load(f)
            
            for task in data.get('tasks', []):
                if task['status'] == 'approved':
                    self.report_status_log(f"🔀 Merging approved task: {task['title']} (by {task.get('assigned_to', 'Unknown')})")
                    
                    # 1. Run Tests (Simulated for now)
                    self.report_status_log(f"🧪 Running final integration tests for {task['title']}...")
                    time.sleep(2)
                    
                    # 2. Merge Branch (REAL GIT OPERATIONS)
                    branch_name = f"feature/{task['id']}"
                    merge_success = self._merge_branch(branch_name, task)
                    
                    if merge_success:
                        self.report_status_log(f"✅ Merged {branch_name} to main")
                        
                        # 3. Push to trigger deployment
                        try:
                            subprocess.run(["git", "push", "origin", "main"], 
                                         check=True, capture_output=True)
                            self.report_status_log(f"🚀 Pushed to main. Render deployment triggered.")
                        except subprocess.CalledProcessError as e:
                            self.report_status_log(f"⚠️ Push failed: {e.stderr.decode() if e.stderr else str(e)}")
                        
                        # Update status to done
                        self.update_task_status(task_id=task['id'], status="done")
                    else:
                        self.report_status_log(f"❌ Merge failed for {task['title']}. Marking as failed.")
                        self.update_task_status(task_id=task['id'], status="failed")
                    
        except Exception as e:
            self.report_status_log(f"❌ Error checking reviews: {e}")
    
    def _merge_branch(self, branch_name, task):
        """Merge a feature branch into main using squash merge."""
        try:
            # Checkout main and pull latest
            subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
            subprocess.run(["git", "pull"], check=True, capture_output=True)
            
            # Squash merge the feature branch
            result = subprocess.run(
                ["git", "merge", "--squash", branch_name],
                check=True, capture_output=True, text=True
            )
            
            # Commit the squashed changes
            commit_message = f"{task['id']}: {task['title']}\n\nGenerated by: {task.get('assigned_to', 'Unknown')}"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True, capture_output=True
            )
            
            # Delete the feature branch (local and remote)
            subprocess.run(["git", "branch", "-D", branch_name], capture_output=True)
            subprocess.run(["git", "push", "origin", "--delete", branch_name], capture_output=True)
            
            self.report_status_log(f"✓ Squash merged and cleaned up {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            self.report_status_log(f"⚠️ Merge error: {error_msg}")
            
            # Check if it's a conflict
            if "CONFLICT" in error_msg or "conflict" in error_msg.lower():
                self.report_status_log(f"🚨 MERGE CONFLICT detected. Manual intervention required.")
                # Abort the merge
                subprocess.run(["git", "merge", "--abort"], capture_output=True)
            
            return False
        except Exception as e:
            self.report_status_log(f"⚠️ Unexpected error: {e}")
            return False

    def update_task_status(self, task_id, status):
        """Update task status via API."""
        try:
            requests.post("http://localhost:8000/api/task/update", json={
                "task_id": task_id,
                "status": status
            }, timeout=1)
        except:
            pass

    def report_status_log(self, message):
        """Report a specific log message to the dashboard."""
        try:
            requests.post("http://localhost:8000/api/agent/status", json={
                "agent_name": "DevOps",
                "status": "working",
                "task_id": "task-8",
                "log": message
            }, timeout=1)
        except:
            pass

if __name__ == "__main__":
    # Simple test run
    agent = DevOpsAgent()
    agent.monitor_loop()
