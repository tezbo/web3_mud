import os
import time
import json
import subprocess
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Melbourne timezone (UTC+11)
MELBOURNE_TZ = timezone(timedelta(hours=11))

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
        timestamp = datetime.now(MELBOURNE_TZ).strftime('%H:%M:%S')
        full_msg = f"[{timestamp}] {message}"
        print(f"[{self.name}] {message}")
        
        # Update JSON
        self._update_json(log_message=full_msg)

    def _update_json(self, status=None, task_id=None, log_message=None):
        """Update the shared agent_tasks.json file with proper locking."""
        import fcntl  # For file locking
        
        try:
            # Open file with exclusive lock to prevent race conditions
            with open(STATUS_FILE, 'r+') as f:
                # Acquire exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                
                try:
                    data = json.load(f)
                    
                    # CRITICAL: Validate and restore if corruption detected
                    corruption_detected = False
                    if 'epics' not in data or len(data.get('epics', [])) == 0:
                        corruption_detected = True
                        print(f"[{self.name}] ⚠️ CORRUPTION: Empty epics detected, restoring from template")
                    if 'tasks' not in data or len(data.get('tasks', [])) == 0:
                        corruption_detected = True
                        print(f"[{self.name}] ⚠️ CORRUPTION: Empty tasks detected, restoring from template")
                    
                    if corruption_detected:
                        # Load template and restore epics/tasks
                        template_file = Path('agent_tasks.template.json')
                        if template_file.exists():
                            with open(template_file, 'r') as tf:
                                template = json.load(tf)
                                if 'epics' not in data or len(data.get('epics', [])) == 0:
                                    data['epics'] = template.get('epics', [])
                                    print(f"[{self.name}] ✓ Restored {len(data['epics'])} epics from template")
                                if 'tasks' not in data or len(data.get('tasks', [])) == 0:
                                    data['tasks'] = template.get('tasks', [])
                                    print(f"[{self.name}] ✓ Restored {len(data['tasks'])} tasks from template")
                        else:
                            print(f"[{self.name}] ❌ Template file not found, cannot restore!")
                    
                    # Ensure all required top-level keys exist
                    if 'metadata' not in data:
                        data['metadata'] = {
                            "vision": "A fully immersive, text-based MUD featuring a rich color system, autonomous NPC agents, and the first major content expansion 'Shadowfen'.",
                            "goals": [],
                            "workforce_status": "active",
                            "messages": []
                        }
                    if 'epics' not in data:
                        data['epics'] = []
                    if 'tasks' not in data:
                        data['tasks'] = []
                    if 'agents' not in data:
                        data['agents'] = {}
                        
                except json.JSONDecodeError:
                    # File is corrupted, restore minimal structure
                    print(f"[{self.name}] WARNING: agent_tasks.json corrupted, restoring structure")
                    data = {
                        "metadata": {
                            "vision": "A fully immersive, text-based MUD featuring a rich color system, autonomous NPC agents, and the first major content expansion 'Shadowfen'.",
                            "goals": [],
                            "workforce_status": "active",
                            "messages": []
                        },
                        "epics": [],
                        "tasks": [],
                        "agents": {}
                    }
                
                # Update agent data
                if self.name not in data['agents']:
                    data['agents'][self.name] = {}
                    
                agent_data = data['agents'][self.name]
                
                if status:
                    agent_data['status'] = status
                if task_id is not None:  # Allow setting to None
                    agent_data['current_task_id'] = task_id
                    
                agent_data['last_active'] = datetime.now(MELBOURNE_TZ).isoformat()
                
                if log_message:
                    if 'logs' not in agent_data:
                        agent_data['logs'] = []
                    agent_data['logs'].append(log_message)
                    agent_data['logs'] = agent_data['logs'][-50:]  # Keep last 50
                    
                # Update task status if we have a current task
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
                            task['updated_at'] = datetime.now(MELBOURNE_TZ).isoformat()
                            break
                
                # Write back to file
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
                
                # Release lock (happens automatically when exiting context)
                
        except FileNotFoundError:
            # File doesn't exist, create it with full structure
            print(f"[{self.name}] WARNING: agent_tasks.json not found, creating new file")
            data = {
                "metadata": {
                    "vision": "A fully immersive, text-based MUD featuring a rich color system, autonomous NPC agents, and the first major content expansion 'Shadowfen'.",
                    "goals": [],
                    "workforce_status": "active",
                    "messages": []
                },
                "epics": [],
                "tasks": [],
                "agents": {
                    self.name: {
                        "status": status or "idle",
                        "current_task_id": task_id,
                        "last_active": datetime.now(MELBOURNE_TZ).isoformat(),
                        "logs": [log_message] if log_message else []
                    }
                }
            }
            with open(STATUS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"[{self.name}] Error updating status: {e}")

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
        """Create a git branch for the task (if enabled)."""
        if not getattr(self, 'manage_git', False):
            self.log(f"ℹ️ Git management disabled. Skipping branch creation for {task_id}")
            return f"feature/{task_id}"

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
        """Commit changes (if enabled)."""
        if not getattr(self, 'manage_git', False):
            self.log(f"ℹ️ Git management disabled. Skipping commit for {task_id}")
            return

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

    def broadcast_message(self, message, msg_type="announcement", reply_to=None, mentions=None):
        """
        Broadcast a message to the workforce chat with enhanced features.
        
        Args:
            message: The message text
            msg_type: Type of message (announcement, question, response, request, alert, status)
            reply_to: ID of message this is replying to
            mentions: List of agent names mentioned (auto-extracted if None)
        """
        import fcntl
        import uuid
        import re
        
        try:
            with open(STATUS_FILE, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                
                data = json.load(f)
                
                if 'metadata' not in data:
                    data['metadata'] = {}
                if 'messages' not in data['metadata']:
                    data['metadata']['messages'] = []
                
                # Extract mentions from message text if not provided
                if mentions is None:
                    mentions = re.findall(r'@(\w+(?:\s+\w+)*)', message)
                
                # Create message object
                msg_obj = {
                    "id": str(uuid.uuid4())[:8],
                    "agent": self.name,
                    "type": msg_type,
                    "message": message,
                    "mentions": mentions,
                    "reply_to": reply_to,
                    "timestamp": datetime.now(MELBOURNE_TZ).strftime('%H:%M:%S'),
                    "read_by": []
                }
                
                data['metadata']['messages'].append(msg_obj)
                
                # Keep last 100 messages
                data['metadata']['messages'] = data['metadata']['messages'][-100:]
                
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"[{self.name}] Error broadcasting: {e}")
    
    def read_messages(self, limit=20):
        """
        Read recent messages from the workforce chat.
        
        Args:
            limit: Maximum number of recent messages to return
            
        Returns:
            List of message objects
        """
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
            
            messages = data.get('metadata', {}).get('messages', [])
            
            # Get last N messages, excluding our own
            recent_messages = messages[-limit:]
            other_messages = [m for m in recent_messages if m.get('agent') != self.name]
            
            return other_messages
        except Exception as e:
            print(f"[{self.name}] Error reading messages: {e}")
            return []
    
    def check_mentions(self, messages):
        """
        Check if any messages mention this agent.
        
        Args:
            messages: List of message objects
            
        Returns:
            List of messages that mention this agent
        """
        mentions = []
        for msg in messages:
            # Check mentions list
            if self.name in msg.get('mentions', []):
                mentions.append(msg)
            # Also check message text for @AgentName
            elif f"@{self.name}" in msg.get('message', ''):
                mentions.append(msg)
        return mentions
    
    def can_answer(self, message):
        """
        Check if this agent can answer a question.
        Override in subclasses to provide domain-specific responses.
        
        Args:
            message: Message object
            
        Returns:
            bool: True if agent can answer
        """
        return False
    
    def generate_response(self, message):
        """
        Generate a response to a message.
        Override in subclasses to provide domain-specific responses.
        
        Args:
            message: Message object
            
        Returns:
            str: Response message, or None if no response
        """
        return None
    
    def handle_messages(self, messages):
        """
        Process incoming messages and respond as appropriate.
        
        Args:
            messages: List of message objects
        """
        # Check for mentions first (high priority)
        mentions = self.check_mentions(messages)
        for msg in mentions:
            self.log(f"📬 Mentioned by {msg['agent']}: {msg['message'][:50]}...")
            response = self.generate_response(msg)
            if response:
                self.broadcast_message(
                    response,
                    msg_type="response",
                    reply_to=msg.get('id')
                )
        
        # Check for questions we can answer
        questions = [m for m in messages if m.get('type') == 'question']
        for q in questions:
            if self.can_answer(q) and q not in mentions:  # Don't double-respond
                response = self.generate_response(q)
                if response:
                    self.broadcast_message(
                        response,
                        msg_type="response",
                        reply_to=q.get('id')
                    )

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
            
            # 0.5. Check Messages (new!)
            try:
                messages = self.read_messages(limit=10)
                if messages:
                    self.handle_messages(messages)
            except Exception as e:
                print(f"[{self.name}] Error handling messages: {e}")

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
