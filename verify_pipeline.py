"""
Verification Script for Release Pipeline
"""
import json
import time
import subprocess
from pathlib import Path

STATUS_FILE = Path('agent_tasks.json')

def update_task_status(task_id, status):
    with open(STATUS_FILE, 'r+') as f:
        data = json.load(f)
        for task in data['tasks']:
            if task['id'] == task_id:
                task['status'] = status
                break
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)
    print(f"Updated {task_id} to {status}")

def verify_pipeline():
    print("Starting Pipeline Verification...")
    
    # 1. Simulate Agent Work
    print("\n[1] Simulating Agent Work...")
    update_task_status("task-test-001", "working")
    time.sleep(1)
    
    # Create a dummy file change
    Path("agents/outputs/test_feature.txt").write_text("This is a test feature.")
    print("Created agents/outputs/test_feature.txt")
    
    update_task_status("task-test-001", "review_ready")
    time.sleep(1)
    
    # 2. Simulate Code Review
    print("\n[2] Simulating Code Review...")
    # In a real scenario, CodeReviewer would do this. We'll manually approve.
    update_task_status("task-test-001", "approved")
    time.sleep(1)
    
    # 3. Trigger Release Manager
    print("\n[3] Triggering Release Manager...")
    # We'll run the Release Manager for a short burst
    try:
        # Run Release Manager in a subprocess with a timeout
        proc = subprocess.Popen(["python3", "agents/release_manager.py"], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a bit for it to process
        print("Release Manager running...")
        time.sleep(10)
        
        proc.terminate()
        try:
            outs, errs = proc.communicate(timeout=5)
            print("Release Manager Output:")
            print(outs)
            if errs:
                print("Errors:", errs)
        except subprocess.TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
            print("Release Manager Output (Killed):")
            print(outs)

    except Exception as e:
        print(f"Error running Release Manager: {e}")
        
    # 4. Verify Result
    print("\n[4] Verifying Result...")
    with open(STATUS_FILE, 'r') as f:
        data = json.load(f)
        for task in data['tasks']:
            if task['id'] == "task-test-001":
                print(f"Final Status: {task['status']}")
                if task['status'] == "done":
                    print("SUCCESS: Pipeline verified!")
                else:
                    print("FAILURE: Task not marked done.")
                break

if __name__ == "__main__":
    verify_pipeline()
