#!/usr/bin/env python3
"""
Check Deployment Status Script
"""
import sys
import requests
from agents.devops import DevOpsAgent

def check_status() -> None:
    """
    Connects to the Render API to check the deployment status and analyze logs if the deployment has failed.
    """
    print("🔍 Connecting to Render API...")
    agent = DevOpsAgent()
    
    # Get latest deployment
    status = agent.check_render_deployment_status()
    
    if status.get('status') == 'unknown':
        print(f"❌ Could not determine status: {status.get('error')}")
        return

    print(f"\n📊 Deployment Status: {status.get('status').upper()}")
    print(f"🔗 URL: {status.get('url')}")
    print(f"🕒 Created At: {status.get('created_at')}")
    
    # If failed, analyze logs
    if status.get('status') in ['build_failed', 'update_failed', 'canceled', 'crashed']:
        print("\n🚨 Deployment FAILED. Analyzing logs with AI...")
        
        # Need to find service ID again since check_render_deployment_status doesn't return it directly
        # But we can try to get logs using the deploy ID if we know the service ID
        # Let's rely on the agent's internal service discovery if we call _get_render_logs
        
        # We need the service ID. Let's list services to find it.
        headers = agent.render_headers
        resp = requests.get("https://api.render.com/v1/services", headers=headers, params={"limit": 1})
        if resp.status_code == 200 and resp.json():
            svc = resp.json()[0]['service']
            service_id = svc['id']
            service_name = svc['name']
            
            logs = agent._get_render_logs(service_id, deploy_id=status.get('id'), lines=100)
            if logs:
                analysis = agent._analyze_logs_with_ai(logs, service_name)
                print("\n🤖 AI Analysis:")
                print(f"Root Cause: {analysis.get('root_cause')}")
                print(f"Recommendation: {analysis.get('recommendation')}")
        else:
            print("⚠️ Could not find service ID to fetch logs.")

if __name__ == "__main__":
    check_status()