#!/usr/bin/env python3
"""
GitHub Labels Setup Script
Automates creation of labels for Release 1.0 issue tracking

Prerequisites:
1. GitHub Personal Access Token with repo scope
2. Install requests: pip install requests

Usage:
    export GITHUB_TOKEN="your_token_here"
    python github_labels_setup.py [--dry-run]
"""

import os
import sys
import requests
import argparse
from typing import List, Dict


class GitHubLabelsSetup:
    def __init__(self, token: str, owner: str, repo: str, dry_run: bool = False):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.dry_run = dry_run
        self.api_url = f"https://api.github.com/repos/{owner}/{repo}/labels"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
    def get_existing_labels(self) -> Dict[str, str]:
        """Get existing labels in the repository"""
        response = requests.get(self.api_url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get labels: {response.status_code} - {response.text}")
        
        labels = response.json()
        return {label["name"]: label["color"] for label in labels}
    
    def create_label(self, name: str, color: str, description: str = "") -> bool:
        """Create a label"""
        payload = {
            "name": name,
            "color": color.lstrip("#"),
            "description": description
        }
        
        if self.dry_run:
            print(f"  [DRY-RUN] Would create: {name} ({color})")
            return True
        
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            print(f"  ✅ Created: {name}")
            return True
        elif response.status_code == 422:
            # Label already exists, try to update it
            return self.update_label(name, color, description)
        else:
            print(f"  ❌ Failed to create {name}: {response.status_code} - {response.text}")
            return False
    
    def update_label(self, name: str, color: str, description: str = "") -> bool:
        """Update an existing label"""
        url = f"{self.api_url}/{name}"
        payload = {
            "color": color.lstrip("#"),
            "description": description
        }
        
        if self.dry_run:
            print(f"  [DRY-RUN] Would update: {name} ({color})")
            return True
        
        response = requests.patch(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            print(f"  ✅ Updated: {name}")
            return True
        else:
            print(f"  ❌ Failed to update {name}: {response.status_code}")
            return False
    
    def delete_label(self, name: str) -> bool:
        """Delete a label"""
        url = f"{self.api_url}/{name}"
        
        if self.dry_run:
            print(f"  [DRY-RUN] Would delete: {name}")
            return True
        
        response = requests.delete(url, headers=self.headers)
        
        if response.status_code == 204:
            print(f"  ✅ Deleted: {name}")
            return True
        else:
            print(f"  ❌ Failed to delete {name}: {response.status_code}")
            return False
    
    def setup_labels(self):
        """Main setup method"""
        print("\n🏷️  Starting GitHub Labels Setup for Release 1.0\n")
        print(f"Repository: {self.owner}/{self.repo}")
        
        if self.dry_run:
            print("⚠️  DRY-RUN MODE - No changes will be made\n")
        else:
            print()
        
        # Define all labels
        labels = [
            # Epic Labels (Blue - #0052CC)
            ("epic: technical-debt", "0052CC", "Technical debt and refactoring"),
            ("epic: sensory-richness", "0052CC", "Sensory details and descriptions"),
            ("epic: ambient-life", "0052CC", "Ambient messages and NPC activities"),
            ("epic: ai-npcs", "0052CC", "AI-enhanced NPC improvements"),
            ("epic: world-expansion", "0052CC", "New rooms and NPCs"),
            ("epic: polish", "0052CC", "UI/UX polish and styling"),
            ("epic: testing", "0052CC", "QA and testing"),
            
            # Priority Labels (Red to Green gradient)
            ("priority: p0-blocker", "B60205", "Critical blocker"),
            ("priority: p1-critical", "D93F0B", "Critical for release"),
            ("priority: p2-important", "FBCA04", "Important"),
            ("priority: p3-nice-to-have", "0E8A16", "Nice to have"),
            
            # Type Labels (Purple - #7057FF)
            ("type: bug", "7057FF", "Something isn't working"),
            ("type: feature", "7057FF", "New feature or enhancement"),
            ("type: refactor", "7057FF", "Code refactoring"),
            ("type: documentation", "7057FF", "Documentation update"),
            ("type: test", "7057FF", "Testing related"),
            
            # Component Labels (Gray - #536471)
            ("component: backend", "536471", "Backend/game engine"),
            ("component: frontend", "536471", "UI/templates"),
            ("component: npc", "536471", "NPC system"),
            ("component: room", "536471", "Room system"),
            ("component: combat", "536471", "Combat system"),
            ("component: quest", "536471", "Quest system"),
            ("component: ai", "536471", "AI integration"),
            
            # Status Labels (Orange - #FF6B6B)
            ("status: blocked", "FF6B6B", "Blocked by dependency"),
            ("status: needs-review", "FF6B6B", "Awaiting review"),
            ("status: in-progress", "FF6B6B", "Currently being worked on"),
            ("status: ready", "FF6B6B", "Ready to start"),
            
            # Agent Labels (Teal - #00D0BE)
            ("agent: system", "00D0BE", "System Agent"),
            ("agent: codereviewer", "00D0BE", "Code Reviewer"),
            ("agent: wordsmith", "00D0BE", "Wordsmith"),
            ("agent: lorekeeper", "00D0BE", "Lore Keeper"),
            ("agent: personalitydesigner", "00D0BE", "Personality Designer"),
            ("agent: questarchitect", "00D0BE", "Quest Architect"),
            ("agent: mapmaker", "00D0BE", "Mapmaker"),
        ]
        
        # Get existing labels
        print("Checking existing labels...")
        existing = self.get_existing_labels()
        print(f"Found {len(existing)} existing labels\n")
        
        # Create labels by category
        categories = [
            ("Epic Labels", 0, 7),
            ("Priority Labels", 7, 11),
            ("Type Labels", 11, 16),
            ("Component Labels", 16, 23),
            ("Status Labels", 23, 27),
            ("Agent Labels", 27, 34),
        ]
        
        total_created = 0
        total_updated = 0
        total_failed = 0
        
        for category_name, start_idx, end_idx in categories:
            print(f"{category_name}:")
            for name, color, description in labels[start_idx:end_idx]:
                if name in existing:
                    if existing[name].upper() == color.upper():
                        print(f"  ⚪ Exists: {name}")
                    else:
                        if self.update_label(name, color, description):
                            total_updated += 1
                        else:
                            total_failed += 1
                else:
                    if self.create_label(name, color, description):
                        total_created += 1
                    else:
                        total_failed += 1
            print()
        
        # Summary
        print("=" * 60)
        if self.dry_run:
            print("🏁 DRY-RUN Complete!")
        else:
            print("🎉 Labels Setup Complete!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  Created: {total_created}")
        print(f"  Updated: {total_updated}")
        print(f"  Failed: {total_failed}")
        print(f"  Total labels: {len(labels)}")
        
        if not self.dry_run:
            print(f"\nView labels: https://github.com/{self.owner}/{self.repo}/labels")
        
        print("\n")
        
        return total_failed == 0


def main():
    parser = argparse.ArgumentParser(description="Setup GitHub labels for Release 1.0")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without making them")
    args = parser.parse_args()
    
    # Get GitHub token from environment
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nTo set it:")
        print("  export GITHUB_TOKEN='your_github_token_here'")
        sys.exit(1)
    
    # Repository details
    owner = "tezbo"
    repo = "web3_mud"
    
    # Run setup
    setup = GitHubLabelsSetup(token, owner, repo, dry_run=args.dry_run)
    try:
        success = setup.setup_labels()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
