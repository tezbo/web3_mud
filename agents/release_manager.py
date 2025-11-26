"""
Release Manager Agent - Handles Git operations and release pipeline.
"""
import subprocess
import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[1]))  # Add project root to path
from agents.agent_framework import AutonomousAgent

class ReleaseManagerAgent(AutonomousAgent):
    """
    Agent responsible for Git operations, merging, and release management.
    This agent is the ONLY one allowed to perform Git write operations.
    """
    
    def __init__(self):
        super().__init__(
            name="Release Manager",
            role="Release & Git Operations",
            capabilities=["git_ops", "merge", "release"]
        )
        # Enable git management for this agent
        self.manage_git = True
        
    def run_loop(self):
        """
        Override run_loop to monitor for tasks ready for release.
        """
        self.log("Starting Release Manager loop...")
        
        while True:
            # Check workforce status
            if self.check_workforce_status() == 'paused':
                time.sleep(5)
                continue
                
            # Look for tasks that are 'review_ready' or a new status 'ready_to_merge'
            # For now, we'll assume 'review_ready' means "Code Reviewer has approved" 
            # OR we can introduce a new status.
            # Let's look for 'approved' tasks (which CodeReviewer sets).
            
            task = self.find_approved_task()
            
            if task:
                self.process_release(task)
            else:
                time.sleep(5)
                
    def find_approved_task(self):
        """Find a task that is approved and needs merging."""
        try:
            import json
            from pathlib import Path
            
            status_file = Path('agent_tasks.json')
            if not status_file.exists():
                return None
                
            with open(status_file, 'r') as f:
                data = json.load(f)
                
            for task in data.get('tasks', []):
                if task['status'] == 'approved':
                    return task
            return None
        except Exception as e:
            self.log(f"Error finding tasks: {e}")
            return None
            
    def process_release(self, task):
        """Process an approved task: commit, push, merge."""
        task_id = task['id']
        self.log(f"🚀 Processing release for task {task_id}: {task['title']}")
        
        try:
            # 1. Commit any pending changes in the workspace
            # Since agents edit files directly in the workspace, we just need to commit them.
            # We assume the workspace is currently in the state left by the agent.
            
            # Check for changes
            status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if not status.stdout.strip():
                self.log(f"ℹ️ No changes to commit for {task_id}. Marking as done.")
                self._update_json(status='done', task_id=task_id)
                return

            # Add all changes (careful with this in production, but okay for this setup)
            subprocess.run(["git", "add", "."], check=True)
            
            # Commit
            commit_msg = f"feat({task_id}): {task['title']}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            self.log(f"✓ Committed changes: {commit_msg}")
            
            # 2. Push to main (or feature branch if we were using them)
            # For now, we are committing directly to the current branch (likely main)
            # to avoid complex merge logic in this first iteration.
            
            # Pull first to avoid conflicts (rebase on top of our new commit)
            try:
                subprocess.run(["git", "pull", "--rebase"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # If rebase fails, abort and try standard pull
                subprocess.run(["git", "rebase", "--abort"], check=False)
                subprocess.run(["git", "pull"], check=True)
            
            # Push
            subprocess.run(["git", "push"], check=True)
            self.log(f"✓ Pushed to remote")
            
            # 3. Mark task as done
            self._update_json(status='done', task_id=task_id)
            self.log(f"✅ Task {task_id} released and marked done.")
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Git error during release: {e}")
            # Optionally mark task as failed or needs_manual_intervention
        except Exception as e:
            self.log(f"❌ Error during release: {e}")

if __name__ == "__main__":
    agent = ReleaseManagerAgent()
    agent.run_loop()
