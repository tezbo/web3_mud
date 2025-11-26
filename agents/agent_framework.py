import os
import time
import json
import subprocess
import random
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

STATUS_FILE = Path('agent_tasks.json')

class AutonomousAgent:
    def __init__(self, name, role, capabilities):
        self.name = name
        self.role = role
        self.capabilities = capabilities  # List of task types or keywords
        self.current_task = None
        
    def log(self, message):
        """Log a message to the dashboard."""
        timestamp = datetime.utcnow().strftime('%H:%M:%S')
        full_msg = f"[{timestamp}] {message}"
        print(f"[{self.name}] {message}")
        
        # Update JSON
        self._update_json(log_message=full_msg)

    def _update_json(self, status=None, task_id=None, log_message=None):
        """Update the shared agent_tasks.json file."""
        try:
            if STATUS_FILE.exists():
                with open(STATUS_FILE, 'r') as f:
                    data = json.load(f)
            else:
                data = {"agents": {}, "tasks": []}
                
            if self.name not in data['agents']:
                data['agents'][self.name] = {}
                
            agent_data = data['agents'][self.name]
            
            if status:
                agent_data['status'] = status
            if task_id is not None: # Allow setting to None
                agent_data['current_task_id'] = task_id
                
            agent_data['last_active'] = datetime.utcnow().isoformat() + "Z"
            
            if log_message:
                if 'logs' not in agent_data:
                    agent_data['logs'] = []
                agent_data['logs'].append(log_message)
                agent_data['logs'] = agent_data['logs'][-50:]
                
            # Also update task status if we have a current task
            if self.current_task and status:
                for task in data.get('tasks', []):
                    if task['id'] == self.current_task['id']:
                        if status == 'working':
                            task['status'] = 'in_progress'
                            task['assigned_to'] = self.name
                        elif status == 'review_ready':
                            task['status'] = 'review_ready'
                        elif status == 'done':
                            task['status'] = 'done'
                        task['updated_at'] = datetime.utcnow().isoformat() + "Z"
                        break
            
            with open(STATUS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error updating status: {e}")

    def find_task(self):
        """Find a TODO task suitable for this agent."""
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
                
            for task in data.get('tasks', []):
                if task['status'] == 'todo':
                    # Check if task matches capabilities
                    # Simple matching: check if assigned_to matches role OR title contains keywords
                    if task.get('assigned_to') == self.name:
                        return task
                    # Fallback: if unassigned, check keywords
                    if not task.get('assigned_to'):
                        for cap in self.capabilities:
                            if cap.lower() in task['title'].lower():
                                return task
            return None
        except Exception:
            return None

    def create_branch(self, task_id):
        """Create a git branch for the task."""
        branch_name = f"feature/{task_id}"
        self.log(f"🌿 Creating branch {branch_name}...")
        try:
            # Checkout main and pull latest
            subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
            subprocess.run(["git", "pull"], check=True, capture_output=True)
            
            # Check if branch already exists
            result = subprocess.run(["git", "branch", "--list", branch_name], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                # Branch exists, check it out
                subprocess.run(["git", "checkout", branch_name], check=True, capture_output=True)
                self.log(f"✓ Checked out existing branch {branch_name}")
            else:
                # Create new branch
                subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
                self.log(f"✓ Created new branch {branch_name}")
        except subprocess.CalledProcessError as e:
            self.log(f"⚠️ Git error: {e.stderr.decode() if e.stderr else str(e)}")
        except Exception as e:
            self.log(f"⚠️ Git error: {e}")
        return branch_name

    def commit_work(self, task_id, message):
        """Commit changes."""
        self.log(f"💾 Committing changes: {message}")
        try:
            # Add only agent output files (not logs, temp files, etc.)
            subprocess.run(["git", "add", "agents/outputs/"], check=True, capture_output=True)
            
            # Check if there are changes to commit
            result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
            if result.returncode != 0:  # There are changes
                subprocess.run(["git", "commit", "-m", f"{task_id}: {message}"], 
                             check=True, capture_output=True)
                self.log(f"✓ Committed changes")
                
                # Push the feature branch
                branch_name = f"feature/{task_id}"
                subprocess.run(["git", "push", "-u", "origin", branch_name], 
                             check=True, capture_output=True)
                self.log(f"✓ Pushed to origin/{branch_name}")
            else:
                self.log(f"ℹ️ No changes to commit")
        except subprocess.CalledProcessError as e:
            self.log(f"⚠️ Git error: {e.stderr.decode() if e.stderr else str(e)}")
        except Exception as e:
            self.log(f"⚠️ Git error: {e}")

    def check_workforce_status(self):
        """Check if the workforce is active or paused."""
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
            return data.get('metadata', {}).get('workforce_status', 'active')
        except:
            return 'active'

    def broadcast_message(self, message):
        """Broadcast a message to the workforce chat."""
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
            
            if 'metadata' not in data:
                data['metadata'] = {}
            if 'messages' not in data['metadata']:
                data['metadata']['messages'] = []
                
            msg_entry = {
                "agent": self.name,
                "message": message,
                "timestamp": datetime.utcnow().strftime('%H:%M:%S')
            }
            data['metadata']['messages'].append(msg_entry)
            # Keep last 50 messages
            data['metadata']['messages'] = data['metadata']['messages'][-50:]
            
            with open(STATUS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error broadcasting message: {e}")

    def run_loop(self):
        """Main autonomous loop."""
        self.log(f"🚀 Agent {self.name} online and polling for tasks...")
        
        last_status = "active"
        
        while True:
            # 0. Check Workforce Status
            status = self.check_workforce_status()
            if status == 'paused':
                if last_status != 'paused':
                    self.log("⏸️ Workforce paused. Idling...")
                    self._update_json(status="paused")
                    last_status = 'paused'
                time.sleep(5)
                continue
            
            if last_status == 'paused':
                self.log("▶️ Workforce resumed!")
                last_status = 'active'

            # 1. Find Task
            if not self.current_task:
                task = self.find_task()
                if task:
                    self.current_task = task
                    self.log(f"📋 Picked up task: {task['title']}")
                    self.broadcast_message(f"I'm starting work on: {task['title']}")
                    self._update_json(status="working", task_id=task['id'])
                    
                    # Create Branch
                    self.create_branch(task['id'])
                    
                    # Execute Task (Abstract method)
                    try:
                        self.execute_task(task)
                        
                        # Commit
                        self.commit_work(task['id'], f"Completed {task['title']}")
                        
                        # Mark Ready for Review
                        self.log(f"✅ Task complete. Marking for review.")
                        self.broadcast_message(f"Finished {task['title']}! Ready for review.")
                        self._update_json(status="review_ready")
                        self.current_task = None # Done with this cycle
                        
                    except Exception as e:
                        self.log(f"❌ Error executing task: {e}")
                        self.broadcast_message(f"I failed on {task['title']}: {e}")
                        self._update_json(status="failed")
                        self.current_task = None
                else:
                    # No tasks, idle
                    # self.log("💤 No tasks found. Idling...") # Too spammy
                    self._update_json(status="idle")
                    time.sleep(5)
            else:
                time.sleep(5)

    def execute_task(self, task):
        """Override this method to implement specific agent logic."""
        raise NotImplementedError
