# GitHub Setup Automation - Quick Reference

## Automated Setup (Recommended)

Complete GitHub setup for Release 1.0 in one command:

```bash
# 1. Set your GitHub token
export GITHUB_TOKEN="your_token_here"

# 2. Preview changes (dry-run)
python github_complete_setup.py --dry-run

# 3. Run the actual setup
python github_complete_setup.py
```

## What Gets Created

### Step 1: GitHub Project
- Project name: "Aethermoor MUD - Release 1.0"
- 6 custom fields: Epic, Priority, Effort, Owner, Sprint, Due Date  
- Linked to repository

### Step 2: Labels (34 total)
- **Epic Labels** (7): technical-debt, sensory-richness, ambient-life, ai-npcs, world-expansion, polish, testing
- **Priority Labels** (4): p0-blocker, p1-critical, p2-important, p3-nice-to-have
- **Type Labels** (5): bug, feature, refactor, documentation, test
- **Component Labels** (7): backend, frontend, npc, room, combat, quest, ai
- **Status Labels** (4): blocked, needs-review, in-progress, ready
- **Agent Labels** (7): system, codereviewer, wordsmith, lorekeeper, personalitydesigner, questarchitect, mapmaker

## Individual Scripts

Run setup steps individually:

```bash
# Project only
python github_project_setup.py

# Labels only  
python github_labels_setup.py

# Preview labels without creating
python github_labels_setup.py --dry-run
```

## Prerequisites

1. **GitHub Personal Access Token**
   ```
   Go to: https://github.com/settings/tokens
   Scopes: repo, project, write:org
   ```

2. **Python requests library**
   ```bash
   pip install requests
   ```

## Troubleshooting

**Token errors:**
- Verify token has correct scopes
- Check token isn't expired
- Use classic token (not fine-grained)

**Permission errors:**
- Must have admin access to repository
- For org repos, need org permissions

**Dry-run first:**
Always run with `--dry-run` first to preview changes!

## Next Steps After Setup

1. View project: https://github.com/tezbo/web3_mud/projects
2. View labels: https://github.com/tezbo/web3_mud/labels  
3. Start creating issues from roadmap
4. Begin Phase 1: Technical Debt & Refactoring
