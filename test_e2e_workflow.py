#!/usr/bin/env python3
"""
End-to-End Workflow Test File
"""
from datetime import datetime

class WorkflowTest:
    def __init__(self):
        self.created_at = datetime.now()
        self.issue_number = 3
        self.agent = "System Agent"
    
    def get_info(self):
        return {
            "created_at": self.created_at.isoformat(),
            "issue": self.issue_number,
            "agent": self.agent,
            "status": "Successfully created via E2E workflow"
        }

if __name__ == "__main__":
    test = WorkflowTest()
    print("E2E Workflow Test File")

