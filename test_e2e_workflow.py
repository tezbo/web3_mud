#!/usr/bin/env python3
"""
End-to-End Workflow Test File
"""
from datetime import datetime

class WorkflowTest:
    def __init__(self) -> None:
        self.created_at: datetime = datetime.now()
        self.issue_number: int = 3
        self.agent: str = "System Agent"

    def get_info(self) -> dict:
        """
        Returns a dictionary containing test information.
        """
        return {
            "created_at": self.created_at.isoformat(),
            "issue": self.issue_number,
            "agent": self.agent,
            "status": "Successfully created via E2E workflow"
        }

if __name__ == "__main__":
    test = WorkflowTest()
    print("E2E Workflow Test created with info:", test.get_info())