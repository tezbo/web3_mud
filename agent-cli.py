#!/usr/bin/env python3
import argparse
import requests
import sys
import json

API_URL = "http://localhost:8000/api"

def update_status(agent_name, status, task_id=None):
    """Update agent status via API."""
    url = f"{API_URL}/agent/status"
    payload = {
        "agent_name": agent_name,
        "status": status,
        "task_id": task_id
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Updated {agent_name} status to {status}")
        else:
            print(f"❌ Error updating status: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to dashboard API. Is the server running?")

def update_task(task_id, status):
    """Update task status via API."""
    url = f"{API_URL}/task/update"
    payload = {
        "task_id": task_id,
        "status": status
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Updated task {task_id} to {status}")
        else:
            print(f"❌ Error updating task: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to dashboard API. Is the server running?")

def list_tasks():
    """List all tasks."""
    url = f"{API_URL}/dashboard"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("\n=== AGENT TASKS ===")
            print(f"{'ID':<10} {'STATUS':<15} {'ASSIGNED':<20} {'TITLE'}")
            print("-" * 80)
            for task in data.get('tasks', []):
                assigned = task.get('assigned_to') or "-"
                print(f"{task['id']:<10} {task['status']:<15} {assigned:<20} {task['title']}")
            print("\n=== AGENTS ===")
            for name, info in data.get('agents', {}).items():
                print(f"{name:<20}: {info['status']} ({info.get('current_task_id') or '-'})")
        else:
            print(f"❌ Error fetching tasks: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to dashboard API. Is the server running?")

def main():
    parser = argparse.ArgumentParser(description="Agent Dashboard CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Status command
    status_parser = subparsers.add_parser("status", help="Update agent status")
    status_parser.add_argument("agent", help="Agent name")
    status_parser.add_argument("status", choices=["working", "idle"], help="New status")
    status_parser.add_argument("--task", help="Task ID (optional)")

    # Task command
    task_parser = subparsers.add_parser("task", help="Update task status")
    task_parser.add_argument("id", help="Task ID")
    task_parser.add_argument("status", choices=["todo", "in_progress", "done"], help="New status")

    # List command
    subparsers.add_parser("list", help="List all tasks and agents")

    args = parser.parse_args()

    if args.command == "status":
        update_status(args.agent, args.status, args.task)
    elif args.command == "task":
        update_task(args.id, args.status)
    elif args.command == "list":
        list_tasks()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
