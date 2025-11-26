import threading
import time
import json
import sys
from pathlib import Path
from agents.system_architect import SystemArchitectAgent
from agents.devops import DevOpsAgent
from agents.qa_bot import QABotAgent
from agents.code_reviewer import CodeReviewerAgent

# Initialize shared task file
STATUS_FILE = Path('agent_tasks.json')

def init_task_file():
    data = {
        "agents": {},
        "tasks": [
            {
                "id": "story-1.2-verify",
                "title": "Verify Weather and Reputation Systems",
                "description": "Run tests to verify WeatherSystem and ReputationSystem integration.",
                "status": "todo",
                "assigned_to": "QA Bot",
                "type": "verify"
            }
        ],
        "metadata": {
            "workforce_status": "active",
            "messages": []
        }
    }
    with open(STATUS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print("📋 Initialized agent_tasks.json with Story 1.2")

def run_agent(agent_class):
    try:
        agent = agent_class()
        print(f"🚀 Launching {agent.name}...")
        agent.run_loop()
    except Exception as e:
        print(f"❌ {agent_class.__name__} crashed: {e}")

if __name__ == "__main__":
    print("🌟 STARTING AGENT FLEET 🌟")
    
    # 1. Reset tasks
    init_task_file()
    
    # 2. Define fleet
    agents = [
        SystemArchitectAgent,
        DevOpsAgent,
        QABotAgent,
        CodeReviewerAgent
    ]
    
    threads = []
    
    # 3. Launch threads
    for agent_cls in agents:
        t = threading.Thread(target=run_agent, args=(agent_cls,))
        t.daemon = True # Kill when main script exits
        t.start()
        threads.append(t)
        time.sleep(1) # Stagger start
        
    print("\n✅ All agents running in background threads.")
    print("Press Ctrl+C to stop the fleet.\n")
    
    try:
        while True:
            # Monitor status file and print updates
            try:
                with open(STATUS_FILE, 'r') as f:
                    data = json.load(f)
                
                # Print active tasks
                active = [t for t in data.get('tasks', []) if t['status'] == 'in_progress']
                if active:
                    print(f"\r🔨 Active Tasks: {[t['title'] for t in active]}", end="")
                else:
                    print(f"\r💤 Fleet Idle...", end="")
                    
                time.sleep(2)
            except:
                pass
    except KeyboardInterrupt:
        print("\n🛑 Stopping fleet...")
