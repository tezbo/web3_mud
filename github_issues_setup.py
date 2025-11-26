#!/usr/bin/env python3
"""
GitHub Issues Setup Script
Creates issues from Release 1.0 roadmap

Prerequisites:
1. GitHub Personal Access Token with repo scope
2. Install requests: pip install requests

Usage:
    export GITHUB_TOKEN="your_token_here"
    python github_issues_setup.py [--dry-run]
"""

import os
import sys
import requests
import argparse
from typing import List, Dict


class GitHubIssuesSetup:
    def __init__(self, token: str, owner: str, repo: str, dry_run: bool = False):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.dry_run = dry_run
        self.api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.created_issues = {}  # Track created issues for linking
        
    def create_issue(self, title: str, body: str, labels: List[str]) -> Dict:
        """Create a GitHub issue"""
        payload = {
            "title": title,
            "body": body,
            "labels": labels
        }
        
        if self.dry_run:
            print(f"  [DRY-RUN] Would create: {title}")
            print(f"    Labels: {', '.join(labels)}")
            return {"number": 999, "html_url": "https://github.com/example"}
        
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            issue = response.json()
            print(f"  ✅ Created #{issue['number']}: {title}")
            return issue
        else:
            print(f"  ❌ Failed to create {title}: {response.status_code}")
            print(f"     Response: {response.text}")
            return None
    
    def setup_issues(self):
        """Create all issues from roadmap"""
        print("\n📝 Creating GitHub Issues from Release 1.0 Roadmap\n")
        print(f"Repository: {self.owner}/{self.repo}")
        
        if self.dry_run:
            print("⚠️  DRY-RUN MODE - No issues will be created\n")
        else:
            print()
        
        # Epic 1: Technical Debt & Refactoring Completion
        print("Epic 1: Technical Debt & Refactoring Completion")
        epic1_body = """## Overview
Must stabilize foundation before building immersion features.

## Priority
P0 (Blocker)

## Estimated Effort
2-3 weeks

## Stories
- [ ] Story 1.1: Complete OO Transition Audit
- [ ] Story 1.2: Restore Lost Features from Pre-Refactor
- [ ] Story 1.3: Code Quality & Documentation

## Success Criteria
- [ ] Complete audit document with all legacy code identified
- [ ] Migration plan approved
- [ ] No critical features lost in refactor
- [ ] All restored features verified working
- [ ] 90%+ of public functions have docstrings
"""
        
        epic1 = self.create_issue(
            "Epic: Technical Debt & Refactoring Completion",
            epic1_body,
            ["epic: technical-debt", "priority: p0-blocker"]
        )
        
        if epic1:
            self.created_issues["epic1"] = epic1
            
            # Story 1.1
            story_1_1_body = f"""**Epic:** #{epic1['number']} Technical Debt & Refactoring Completion

## User Story
**As a** developer  
**I want** to identify all legacy code that needs OO refactoring  
**So that** we have a clean, maintainable codebase

## Tasks
- [ ] **Audit all root folder Python files** (`/*.py`) for legacy code
  - [ ] `game_engine.py` - Legacy command handlers (estimate: 76% complete)
  - [ ] `app.py` - Route handlers that should use OO models
  - [ ] `onboarding.py` - Character creation logic
  - [ ] `world_loader.py` - World loading (may be obsolete)
  - [ ] Other root-level `.py` files
- [ ] Document all functions that should be methods on Player/Room/NPC/Item models
- [ ] Create migration plan for each legacy function
- [ ] Identify circular dependency risks
- [ ] Review and restore pre-refactor features that were lost:
  - [ ] Player weather status effects (`get_player_weather_description()` exists but not called)
  - [ ] Reputation system integration with NPC dialogue
  - [ ] NPC visible activities system
  - [ ] Seasonal room overlays
- [ ] Create technical debt backlog document

## Acceptance Criteria
- [ ] Complete audit document with all legacy code identified
- [ ] Migration plan approved
- [ ] No critical features lost in refactor

## Estimated Effort
5 story points

## Owner
Code Reviewer + System Agent
"""
            
            story1_1 = self.create_issue(
                "Story 1.1: Complete OO Transition Audit",
                story_1_1_body,
                ["epic: technical-debt", "priority: p0-blocker", "type: refactor", 
                 "component: backend", "agent: codereviewer", "agent: system"]
            )
            
            # Story 1.2
            story_1_2_body = f"""**Epic:** #{epic1['number']} Technical Debt & Refactoring Completion

## User Story
**As a** player  
**I want** all the immersive features that existed before refactoring  
**So that** I don't lose functionality

## Tasks
- [ ] **Weather Status Effects** - Restore player descriptions based on weather exposure
  - [ ] Verify `get_player_weather_description()` is called in look/who commands
  - [ ] Test: Player standing in rain for 5+ minutes shows "drenched" status
  - [ ] Test: Player in snow shows "shivering" status
- [ ] **Reputation System Integration**
  - [ ] NPCs reference reputation in dialogue
  - [ ] NPCs have different dialogue trees based on reputation levels
  - [ ] Reputation affects NPC willingness to help/trade
- [ ] **NPC Visible Activities**
  - [ ] NPCs perform contextual actions in rooms
  - [ ] Activities based on: personality, time of day, room type, reputation
  - [ ] Examples: blacksmith hammering, innkeeper wiping tables, guard patrolling
  - [ ] Each NPC has custom schedule based on occupation/race/background
- [ ] **Seasonal Room Overlays**
  - [ ] Verify `get_seasonal_room_overlay()` is integrated into room descriptions
  - [ ] Test: Summer vs winter descriptions differ meaningfully

## Acceptance Criteria
- [ ] All features verified working
- [ ] QA Bot tests added for each feature
- [ ] User-facing documentation updated

## Estimated Effort
8 story points

## Owner
System Agent + Code Reviewer
"""
            
            story1_2 = self.create_issue(
                "Story 1.2: Restore Lost Features from Pre-Refactor",
                story_1_2_body,
                ["epic: technical-debt", "priority: p0-blocker", "type: feature",
                 "component: backend", "component: npc", "agent: system", "agent: codereviewer"]
            )
            
            # Story 1.3
            story_1_3_body = f"""**Epic:** #{epic1['number']} Technical Debt & Refactoring Completion

## User Story
**As a** developer  
**I want** clean, documented code  
**So that** the codebase is maintainable

## Tasks
- [ ] Add docstrings to all public functions/methods
- [ ] Remove dead code and commented-out blocks
- [ ] Standardize naming conventions
- [ ] Add type hints to critical functions
- [ ] Create architecture documentation (how systems interact)
- [ ] Document AI NPC system (prompts, context, limitations)
- [ ] Create developer onboarding guide

## Acceptance Criteria
- [ ] 90%+ of public functions have docstrings
- [ ] No linting errors
- [ ] Architecture docs complete

## Estimated Effort
5 story points

## Owner
Code Reviewer
"""
            
            story1_3 = self.create_issue(
                "Story 1.3: Code Quality & Documentation",
                story_1_3_body,
                ["epic: technical-debt", "priority: p0-blocker", "type: documentation",
                 "component: backend", "agent: codereviewer"]
            )
        
        print()
        
        # Epic 2: Immersion - Sensory Richness
        print("Epic 2: Immersion - Sensory Richness")
        epic2_body = """## Overview
Transform descriptions from functional to atmospheric with sensory details.

## Priority
P1 (Critical for Release 1.0)

## Estimated Effort
3-4 weeks

## Stories
- [ ] Story 2.1: Enhance All Room Descriptions with Sensory Details
- [ ] Story 2.2: Dynamic Descriptions (Weather & Time Impact)

## Success Criteria
- [ ] All 11 rooms have 3+ sensory details (smell, sound, texture)
- [ ] Every noun is examinable
- [ ] Weather visibly impacts outdoor room descriptions
- [ ] Time variants feel distinct and atmospheric
- [ ] Immersion score for rooms: 7/10+
"""
        
        epic2 = self.create_issue(
            "Epic: Immersion - Sensory Richness",
            epic2_body,
            ["epic: sensory-richness", "priority: p1-critical"]
        )
        
        if epic2:
            self.created_issues["epic2"] = epic2
            
            # Story 2.1
            story_2_1_body = f"""**Epic:** #{epic2['number']} Immersion - Sensory Richness

## User Story
**As a** player  
**I want** to experience rooms through all five senses  
**So that** I feel immersed in the world

## Tasks
- [ ] **Audit Current Rooms** (11 rooms total)
  - [ ] Identify rooms lacking smell/sound/texture/temperature
  - [ ] Rate each room's sensory richness (1-10)
- [ ] **Enhance Existing Rooms**
  - [ ] Town Square: Add market smells, crowd sounds, cobblestone texture
  - [ ] Tavern: Add ale smell, laughter sounds, warm hearth feel
  - [ ] Smithy: Add metal tang, hammer sounds, heat from forge
  - [ ] Forest: Add pine scent, bird sounds, moss texture
  - [ ] (Continue for all 11 rooms)
- [ ] **Create Sensory Templates**
  - [ ] Document patterns for different room types (urban, nature, indoor, etc.)
  - [ ] Create reusable sensory detail library
- [ ] **Testing Standard: Examinable Nouns**
  - [ ] Every noun in room description must be examinable
  - [ ] Add QA Bot test to verify this
  - [ ] Example: "cobblestones" → `look at cobblestones` returns detailed description

## Acceptance Criteria
- [ ] All 11 rooms have 3+ sensory details (smell, sound, texture)
- [ ] Every noun is examinable
- [ ] QA Bot test passes
- [ ] Immersion score for rooms: 7/10+

## Estimated Effort
8 story points

## Owner
Wordsmith + Lore Keeper
"""
            
            story2_1 = self.create_issue(
                "Story 2.1: Enhance All Room Descriptions with Sensory Details",
                story_2_1_body,
                ["epic: sensory-richness", "priority: p1-critical", "type: feature",
                 "component: room", "agent: wordsmith", "agent: lorekeeper"]
            )
        
        print()
        
        # Epic 3: Immersion - Ambient Life
        print("Epic 3: Immersion - Ambient Life")
        epic3_body = """## Overview
Make the world feel alive with constant ambient activity and NPC actions.

## Priority
P1 (Critical for Release 1.0)

## Estimated Effort
2-3 weeks

## Stories
- [ ] Story 3.1: Boost Ambient Message System
- [ ] Story 3.2: NPC Visible Activities

## Success Criteria
- [ ] Ambient messages appear every 30-60 seconds
- [ ] Messages feel varied and contextual
- [ ] No repetition within 10-message window
- [ ] All NPCs have 5+ defined activities
- [ ] Activities appear contextually (time, weather, reputation)
- [ ] Immersion score for ambiance: 7/10+
"""
        
        epic3 = self.create_issue(
            "Epic: Immersion - Ambient Life",
            epic3_body,
            ["epic: ambient-life", "priority: p1-critical"]
        )
        
        print()
        
        # Summary
        print("=" * 60)
        if self.dry_run:
            print("🏁 DRY-RUN Complete!")
        else:
            print("🎉 Initial Issues Created!")
        print("=" * 60)
        
        issue_count = len([v for v in self.created_issues.values() if v])
        print(f"\nIssues created: {issue_count}")
        
        if not self.dry_run:
            print(f"\nView issues: https://github.com/{self.owner}/{self.repo}/issues")
            print("\nNext: Create remaining epics and stories manually or extend this script")
        
        print("\n")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Create GitHub issues from Release 1.0 roadmap")
    parser.add_argument("--dry-run", action="store_true", help="Preview issues without creating them")
    args = parser.parse_args()
    
    # Get GitHub token from environment
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Repository details
    owner = "tezbo"
    repo = "web3_mud"
    
    # Run setup
    setup = GitHubIssuesSetup(token, owner, repo, dry_run=args.dry_run)
    try:
        success = setup.setup_issues()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
