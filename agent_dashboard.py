from flask import Blueprint, render_template, jsonify, request
import json
import os
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

DATA_FILE = 'agent_tasks.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"epics": [], "tasks": [], "agents": {}}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"epics": [], "tasks": [], "agents": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@dashboard_bp.route('/dashboard')
def dashboard_view():
    return render_template('agent_dashboard.html')

@dashboard_bp.route('/api/dashboard')
def get_dashboard_data():
    data = load_data()
    return jsonify(data)

@dashboard_bp.route('/api/agent/status', methods=['POST'])
def update_agent_status():
    data = load_data()
    payload = request.json
    
    agent_name = payload.get('agent_name')
    status = payload.get('status')
    task_id = payload.get('task_id')
    
    if not agent_name:
        return jsonify({"error": "Agent name required"}), 400
        
    if agent_name not in data['agents']:
        data['agents'][agent_name] = {}
        
    data['agents'][agent_name].update({
        "status": status,
        "current_task_id": task_id,
        "last_active": datetime.utcnow().isoformat() + "Z"
    })

    # Handle logs
    log_message = payload.get('log')
    if log_message:
        if 'logs' not in data['agents'][agent_name]:
            data['agents'][agent_name]['logs'] = []
        
        # Add timestamp if not present in message
        if not log_message.startswith('['):
            timestamp = datetime.utcnow().strftime('%H:%M:%S')
            log_message = f"[{timestamp}] {log_message}"
            
        data['agents'][agent_name]['logs'].append(log_message)
        
        # Keep last 50 logs
        if len(data['agents'][agent_name]['logs']) > 50:
             data['agents'][agent_name]['logs'] = data['agents'][agent_name]['logs'][-50:]
    
    # Also update task status if provided
    if task_id:
        for task in data['tasks']:
            if task['id'] == task_id:
                if status == 'working':
                    task['status'] = 'in_progress'
                    task['assigned_to'] = agent_name
                elif status == 'idle':
                    # Don't change task status if agent goes idle, unless completed
                    pass
                task['updated_at'] = datetime.utcnow().isoformat() + "Z"
                break
    
    save_data(data)
    return jsonify({"success": True})

@dashboard_bp.route('/api/task/update', methods=['POST'])
def update_task():
    data = load_data()
    payload = request.json
    
    task_id = payload.get('task_id')
    new_status = payload.get('status')
    
    if not task_id or not new_status:
        return jsonify({"error": "Task ID and status required"}), 400
        
    for task in data['tasks']:
        if task['id'] == task_id:
            task['status'] = new_status
            task['updated_at'] = datetime.utcnow().isoformat() + "Z"
            
            # If task is done, clear agent assignment
            if new_status == 'done':
                for agent_name, agent_data in data['agents'].items():
                    if agent_data.get('current_task_id') == task_id:
                        agent_data['current_task_id'] = None
                        agent_data['status'] = 'idle'
            
            save_data(data)
            return jsonify({"success": True})
            
    return jsonify({"error": "Task not found"}), 404
