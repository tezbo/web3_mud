#!/usr/bin/env python3
"""
GitHub Release 1.0 Setup - Master Script
Orchestrates complete GitHub setup for Release 1.0

This script runs all setup steps in sequence:
1. Create GitHub Project with custom fields
2. Create labels
3. Create issues from roadmap (optional)
4. Setup GitHub Actions (optional)

Prerequisites:
1. GitHub Personal Access Token with scopes: repo, project, write:org
2. Install requests: pip install requests

Usage:
    export GITHUB_TOKEN="your_token_here"
    python github_complete_setup.py [--dry-run] [--skip-issues] [--skip-actions]
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def run_script(script_name: str, args: list = None, dry_run: bool = False) -> bool:
    """Run a setup script and return success status"""
    cmd = ["python3", script_name]
    if dry_run:
        cmd.append("--dry-run")
    if args:
        cmd.extend(args)
    
    print(f"\n{'=' * 70}")
    print(f"Running: {' '.join(cmd)}")
    print('=' * 70)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"\n❌ {script_name} failed with code {result.returncode}")
        return False
    
    print(f"\n✅ {script_name} completed successfully")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Complete GitHub setup for Release 1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview all changes
  python github_complete_setup.py --dry-run
  
  # Full setup
  python github_complete_setup.py
  
  # Setup project and labels only (skip issues/actions)
  python github_complete_setup.py --skip-issues --skip-actions
        """
    )
    parser.add_argument("--dry-run", action="store_true", 
                       help="Preview changes without making them")
    parser.add_argument("--skip-project", action="store_true",
                       help="Skip project creation (if already exists)")
    parser.add_argument("--skip-labels", action="store_true",
                       help="Skip labels creation")
    parser.add_argument("--skip-issues", action="store_true",
                       help="Skip issues creation")
    parser.add_argument("--skip-actions", action="store_true",
                       help="Skip GitHub Actions setup")
    args = parser.parse_args()
    
    # Check for GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nTo set it:")
        print("  export GITHUB_TOKEN='your_github_token_here'")
        print("\nTo create a token:")
        print("  1. Go to https://github.com/settings/tokens")
        print("  2. Click 'Generate new token (classic)'")
        print("  3. Select scopes: repo, project, write:org")
        print("  4. Copy the token and set it as environment variable")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("🚀 GITHUB RELEASE 1.0 COMPLETE SETUP")
    print("=" * 70)
    print("\nRepository: tezbo/web3_mud")
    print(f"Mode: {'DRY-RUN (preview only)' if args.dry_run else 'LIVE (making changes)'}")
    print("\nSetup Steps:")
    print("  1. ✓ Create GitHub Project" + (" (SKIP)" if args.skip_project else ""))
    print("  2. ✓ Create Labels" + (" (SKIP)" if args.skip_labels else ""))
    print("  3. ✓ Create Issues" + (" (SKIP)" if args.skip_issues else ""))
    print("  4. ✓ Setup GitHub Actions" + (" (SKIP)" if args.skip_actions else ""))
    
    if not args.dry_run:
        print("\n⚠️  WARNING: This will make changes to your GitHub repository!")
        response = input("\nProceed? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Aborted.")
            sys.exit(0)
    
    success = True
    
    # Step 1: Create GitHub Project
    if not args.skip_project:
        if not run_script("github_project_setup.py", dry_run=args.dry_run):
            print("\n❌ Project setup failed. Aborting.")
            sys.exit(1)
    
    # Step 2: Create Labels
    if not args.skip_labels:
        if not run_script("github_labels_setup.py", dry_run=args.dry_run):
            print("\n❌ Labels setup failed. Aborting.")
            sys.exit(1)
    
    # Step 3: Create Issues (if script exists)
    if not args.skip_issues:
        issues_script = Path(__file__).parent / "github_issues_setup.py"
        if issues_script.exists():
            if not run_script("github_issues_setup.py", dry_run=args.dry_run):
                print("\n⚠️  Issues setup failed, but continuing...")
                success = False
        else:
            print("\n⚠️  Issues setup script not found, skipping...")
    
    # Step 4: Setup GitHub Actions (if script exists)
    if not args.skip_actions:
        actions_script = Path(__file__).parent / "github_actions_setup.py"
        if actions_script.exists():
            if not run_script("github_actions_setup.py", dry_run=args.dry_run):
                print("\n⚠️  Actions setup failed, but continuing...")
                success = False
        else:
            print("\n⚠️  Actions setup script not found, skipping...")
    
    # Final summary
    print("\n" + "=" * 70)
    if args.dry_run:
        print("🏁 DRY-RUN COMPLETE")
        print("=" * 70)
        print("\nNo changes were made. Run without --dry-run to apply changes.")
    else:
        if success:
            print("🎉 SETUP COMPLETE!")
            print("=" * 70)
            print("\n✅ All steps completed successfully!")
            print("\nNext steps:")
            print("  1. View your project: https://github.com/tezbo/web3_mud/projects")
            print("  2. View your labels: https://github.com/tezbo/web3_mud/labels")
            print("  3. Start creating issues or run issues setup script")
            print("  4. Begin Phase 1: Technical Debt & Refactoring")
        else:
            print("⚠️  SETUP COMPLETED WITH WARNINGS")
            print("=" * 70)
            print("\nSome steps had warnings but core setup is complete.")
            print("Review the output above for details.")
    
    print("\n")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
