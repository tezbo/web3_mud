#!/usr/bin/env python3
"""
Run the Code Reviewer Agent against the current git branch.
"""
import sys
import os
import subprocess
import json
from dotenv import load_dotenv

# Add project root to import path if needed
# sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')
load_dotenv()

from agents.code_reviewer import CodeReviewerAgent

def get_git_diff(target_branch="main"):
    """Get the diff between current branch and target."""
    try:
        # Fetch target first to ensure we have latest
        subprocess.run(["git", "fetch", "origin", target_branch], check=False, capture_output=True)
        
        # Get diff
        result = subprocess.run(
            ["git", "diff", f"origin/{target_branch}...HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        return None

def main():
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "main"
        
    print(f"🔍 Generating diff against {target}...")
    diff = get_git_diff(target)
    
    if not diff:
        print("⚠️ No changes detected or git error.")
        return
        
    if len(diff) > 10000:
        print(f"⚠️ Diff is large ({len(diff)} chars). Truncating for AI...")
        diff = diff[:10000] + "\n...[TRUNCATED]..."

    print("🤖 Code Reviewer is analyzing...")
    reviewer = CodeReviewerAgent()
    review = reviewer.review_diff(diff)
    
    print("\n" + "="*60)
    print(f"REVIEW STATUS: {review.get('status', 'UNKNOWN')}")
    print("="*60)
    print(f"\nSUMMARY:\n{review.get('summary', 'No summary provided.')}\n")
    
    issues = review.get('issues', [])
    if issues:
        print("ISSUES:")
        for issue in issues:
            severity = issue.get('severity', 'low').upper()
            icon = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🔵"
            print(f"{icon} [{severity}] {issue.get('category', 'general')}: {issue.get('message')}")
            if issue.get('file'):
                print(f"   File: {issue.get('file')}")
    else:
        print("✅ No issues found.")
        
    print("\n" + "="*60)
    
    # Exit with error if changes requested
    if review.get('status') == 'REQUEST_CHANGES':
        sys.exit(1)

if __name__ == "__main__":
    main()
