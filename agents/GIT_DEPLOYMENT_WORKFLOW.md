# Git & Deployment Workflow

## Deployment Strategy

### Current Setup
- **Production**: https://web3-mud.onrender.com (auto-deploys from `main` branch)
- **Repository**: /Users/terryroberts/Documents/code/web3_mud

### Git Workflow

**Branch Strategy**:
```
main (production) ← deploy here after testing
  ↑
agent-work (staging) ← agents commit here first
  ↑
feature/* (individual agent tasks)
```

**Workflow**:
1. Agents create content in `feature/agent-[taskname]` branches
2. I test locally and merge to `agent-work`
3. Run full test suite on `agent-work`
4. If tests pass, merge to `main` (triggers auto-deploy)

---

## When to Commit

### Commit Triggers

**After Each Completed Unit**:
- ✅ Single room retrofit complete → commit
- ✅ Set of 11 rooms complete → commit
- ✅ NPC personality set complete → commit
- ✅ Quest designed and validated → commit

**Batch Commits**:
- Multiple related changes (e.g., all 11 Greymarket rooms)
- Use descriptive commit messages with agent attribution

**Example Commits**:
```bash
git commit -m "feat(greymarket): Retrofit 11 rooms to Shadowfen lore

- Rewrite descriptions with sensory details (Wordsmith)
- Add 5 ambient messages per room (Wordsmith)
- Update metadata for realm/location (Lore Keeper)
- Validate cultural consistency (Lore Keeper)

Agent-generated content, reviewed by Antigravity"
```

---

## Pre-Commit Testing

### Automated Checks (Before Any Commit)

1. **Syntax Check**:
```bash
python3 -m py_compile game_engine.py app.py
```

2. **JSON Validation**:
```bash
python3 -c "import json; [json.load(open(f)) for f in Path('world/rooms').glob('*.json')]"
```

3. **Lore Consistency**:
```bash
python3 agents/scripts/validate_lore.py world/rooms/
```

4. **Local Server Test**:
```bash
# Start server, verify it launches
python3 app.py &
sleep 5
curl -f http://localhost:5000 || exit 1
kill %1
```

### Manual Testing Checklist

Before merging to `main`:
- [ ] Create new character
- [ ] Visit 3 retrofitted rooms
- [ ] Talk to 2 NPCs
- [ ] Execute 5 commands (look, go, take, drop, inv)
- [ ] Check console for errors
- [ ] Verify ambient messages appear

---

## Deployment Process

### Step-by-Step

**1. Agent Work Complete**:
```bash
# Agents save to world/rooms/retrofitted/
ls world/rooms/retrofitted/*.json
```

**2. Review Agent Output**:
```bash
# I review each retrofitted room
python3 agents/scripts/review_agent_work.py
```

**3. Move to Live Directory** (if approved):
```bash
# Backup originals
cp -r world/rooms world/rooms.backup-$(date +%Y%m%d)

# Move retrofitted content to live
mv world/rooms/retrofitted/*.json world/rooms/
```

**4. Test Locally**:
```bash
python3 app.py
# Manual 5-minute playthrough
```

**5. Commit & Push**:
```bash
git checkout -b agent-work
git add world/rooms/*.json
git commit -m "feat(greymarket): Agent team room retrofits"
git push origin agent-work
```

**6. Merge to Main** (triggers deploy):
```bash
git checkout main
git merge agent-work
git push origin main
# Render.com auto-deploys
```

**7. Verify Production**:
```bash
# Wait 2-3 minutes for deploy
curl https://web3-mud.onrender.com
# Manual test on live site
```

---

## Rollback Plan

If deployment breaks:

```bash
# Revert last commit
git revert HEAD
git push origin main

# OR restore from backup
rm world/rooms/*.json
cp world/rooms.backup-YYYYMMDD/*.json world/rooms/
git add world/rooms/
git commit -m "fix: Restore rooms from backup"
git push origin main
```

---

## Automation Scripts

### Pre-Commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
echo "🧪 Running pre-commit tests..."

# Syntax check
python3 -m py_compile game_engine.py app.py || exit 1

# JSON validation
python3 -c "
import json
from pathlib import Path
for f in Path('world/rooms').glob('*.json'):
    try:
        json.load(open(f))
    except Exception as e:
        print(f'❌ Invalid JSON: {f}')
        exit(1)
" || exit 1

echo "✅ Pre-commit checks passed"
```

### Review Script

`agents/scripts/review_agent_work.py`:
```python
#!/usr/bin/env python3
"""Review agent-generated content before commit"""
import json
from pathlib import Path

retrofitted = Path('world/rooms/retrofitted')
for room_file in retrofitted.glob('*.json'):
    with open(room_file) as f:
        data = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"📋 {data['name']}")
    print(f"{'='*60}")
    print(data['description'])
    print(f"\n🌫️ Ambient Messages: {len(data.get('ambient_messages', []))}")
    
    # Ask for approval
    response = input("\n✅ Approve? [y/N]: ")
    if response.lower() != 'y':
        print(f"❌ Skipping {room_file.name}")
        continue
    
    # Move to live
    dest = Path('world/rooms') / room_file.name
    room_file.replace(dest)
    print(f"✓ Moved to {dest}")
```

---

## Deployment Schedule

### Daily Cycle

**Morning** (my timezone):
- Review overnight agent work
- Test locally
- Commit approved changes to `agent-work`

**Afternoon**:
- Continue agent tasks
- More frequent small commits to `agent-work`

**Evening**:
- Merge day's work to `main` (1 deploy per day)
- Verify production
- Update task.md

### Emergency Deploys

For critical fixes:
- Immediate commit to `main`
- Skip `agent-work` branch
- Deploy and verify within 10 minutes

---

## Monitoring Production

### Health Checks

After every deploy:
1. Visit https://web3-mud.onrender.com
2. Check Render.com logs for errors
3. Create test character
4. Execute 10 commands
5. Verify no console errors

### Rollback Triggers

Deploy fails if:
- Server won't start (500 error)
- Character creation broken
- Basic commands don't work
- Console shows errors
- Lore inconsistencies found

→ **Immediate rollback + investigate**

---

## This Workflow Ensures

✅ Agent work is tested before production  
✅ Main branch always deployable  
✅ Easy rollback if issues  
✅ Clear attribution of agent vs human work  
✅ Production stability maintained  

**Current Status**: Waiting for agents to finish room retrofits, then will follow this workflow to deploy.
