import json
import time
import random
import os
from datetime import datetime

DATA_FILE = 'agent_tasks.json'

AGENTS = [
    "Mapmaker",
    "Wordsmith",
    "Personality Designer"
]

def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_log(agent_name, task_id):
    """Generate a realistic log message based on the agent and task."""
    actions = {
        "Mapmaker": [
            "Calculating room adjacency matrix...",
            "Validating exit paths for sector 7...",
            "Rendering terrain mesh...",
            "Optimizing lightmap baking...",
            "Checking collision boundaries..."
        ],
        "Wordsmith": [
            "Drafting atmospheric description...",
            "Thesaurus lookup: 'gloomy' -> 'oppressive'...",
            "Checking lore consistency with 'Shadowfen'...",
            "Polishing sensory details...",
            "Reviewing grammar and syntax..."
        ],
        "Personality Designer": [
            "Adjusting 'Aggression' trait weight...",
            "Simulating dialogue tree branch...",
            "Defining relationship: 'Hates' -> 'Player'...",
            "Configuring idle behavior loop...",
            "Validating memory retention..."
        ]
    }
    
    base_logs = actions.get(agent_name, ["Processing task...", "Analyzing data...", "Running diagnostics..."])
    return f"[{datetime.utcnow().strftime('%H:%M:%S')}] {random.choice(base_logs)}"

def simulate_work():
    print("Starting workforce simulation...")
    while True:
        data = load_data()
        if not data:
            print("Error loading data, retrying...")
            time.sleep(2)
            continue
            
        updated = False
        
        for agent_name in AGENTS:
            if agent_name in data['agents']:
                agent = data['agents'][agent_name]
                
                # Only simulate if they are supposed to be working
                if agent['status'] == 'working':
                    # Update timestamp
                    agent['last_active'] = datetime.utcnow().isoformat() + "Z"
                    
                    # Generate a log entry
                    if 'logs' not in agent:
                        agent['logs'] = []
                    
                    new_log = generate_log(agent_name, agent.get('current_task_id'))
                    agent['logs'].append(new_log)
                    
                    # Keep only last 20 logs
                    if len(agent['logs']) > 20:
                        agent['logs'] = agent['logs'][-20:]
                    
                    updated = True
                    print(f"Updated {agent_name}: {new_log}")
        
        if updated:
            save_data(data)
            
        # Random sleep between 2 and 5 seconds to simulate natural variation
        time.sleep(random.uniform(2, 5))

if __name__ == "__main__":
    simulate_work()
