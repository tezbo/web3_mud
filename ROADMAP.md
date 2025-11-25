# Hollowvale MUD - Development Roadmap

## Vision Statement
A text-based multiplayer MUD with AI-powered NPCs, a living world, and classic MUD gameplay. Target: **1000 concurrent players** with smooth, real-time interactions.

---

## Current Status (November 2024)

### ✅ Completed Core Systems
- **World & Movement**: 11 rooms, directional movement, room descriptions with time/weather
- **Player Management**: Login/logout, character creation (onboarding), session management
- **NPCs**: 8+ NPCs with AI-enhanced dialogue, periodic actions, greetings/emotes
- **Economy**: Currency system (gold/silver/copper), merchants, dynamic pricing, loot tables
- **Quest System**: Quest framework with 2 active quests (Mara's Lost Kitchen Knife, Lost Package)
- **Communication**: Player-to-player messaging (`tell` command), room chat (`say`, emotes)
- **Ambiance**: Time-based environmental messages, weather system, day/night cycles
- **Real-time**: WebSocket architecture (Flask-SocketIO + Redis) for live updates
- **Admin Tools**: `goto`, `quests reset`, `settings`, `notify` commands
- **UX**: Color customization, smart auto-scroll, pause markers for narrative text
- **State Management**: Redis-backed caching, database persistence, multi-instance ready

### 🚧 Partially Implemented
- **Combat System**: Help text mentions it, but not implemented yet
- **Architecture**: WebSocket migration done, but some cleanup/polish needed

### ❌ Not Started
- Combat mechanics
- Character progression (levels, stats, skills)
- Crafting system
- More quests and content
- Dungeons/combat areas
- Player housing
- Guilds/parties
- Character classes
- More NPCs and locations

---

## Roadmap: Prioritized by Impact

### 🎯 Phase 1: Core Gameplay Loop (1-2 weeks)
**Goal**: Make the game fun to play for 30+ minutes with clear progression.

#### 1.1 Combat System ⚔️
**Priority**: HIGH | **Impact**: CRITICAL | **Effort**: Medium

- [ ] Implement basic combat mechanics
  - [ ] `attack <target>` command
  - [ ] Health/damage system
  - [ ] Turn-based combat (simple: player attacks, NPC attacks, repeat)
  - [ ] Victory/loss conditions
  - [ ] Combat messages/feedback
- [ ] Weapons and armor system
  - [ ] Weapon stats (damage, speed)
  - [ ] Armor stats (defense)
  - [ ] Equip/unequip commands
  - [ ] Inventory slots (weapon, armor, accessories)
- [ ] Combat balance
  - [ ] Player health calculation (based on stats)
  - [ ] NPC health/damage values
  - [ ] Difficulty scaling
- [ ] Combat rewards
  - [ ] XP gain from combat
  - [ ] Loot drops from defeated enemies
  - [ ] Gold rewards

#### 1.2 Character Progression 📈
**Priority**: HIGH | **Impact**: HIGH | **Effort**: Medium

- [ ] Experience points (XP) system
  - [ ] Track XP in game state
  - [ ] XP sources: combat, quests, exploration
  - [ ] Level-up mechanics
- [ ] Leveling system
  - [ ] XP requirements per level
  - [ ] Stat increases on level up
  - [ ] Level-up messages/rewards
- [ ] Stat system improvements
  - [ ] Stats affect combat (STR → damage, AGI → dodge, etc.)
  - [ ] Stats affect skills (WIS → spell power, etc.)
  - [ ] Stat cap/increases

#### 1.3 More Content 📚
**Priority**: HIGH | **Impact**: HIGH | **Effort**: Low-Medium

- [ ] Add 3-5 more quests
  - [ ] Fetch quests (go to X, bring back Y)
  - [ ] Kill quests (defeat X enemies)
  - [ ] Exploration quests (visit X locations)
  - [ ] Multi-stage quests
- [ ] Add 3-5 more NPCs
  - [ ] Guard (combat trainer, quest giver)
  - [ ] Mage/Alchemist (magic items, potions)
  - [ ] Trader (rare items, quest rewards)
  - [ ] Town crier (news, rumors)
- [ ] Add 3-5 more locations
  - [ ] Combat training area
  - [ ] Forest with monsters
  - [ ] Dungeon entrance
  - [ ] Merchant district
  - [ ] Player hangout area

#### 1.4 Polish & UX Improvements ✨
**Priority**: MEDIUM | **Impact**: MEDIUM | **Effort**: Low

- [ ] Combat feedback improvements
  - [ ] Action bar/combat log
  - [ ] Health bar display
  - [ ] Visual feedback for hits/damage
- [ ] Inventory management
  - [ ] Sort inventory
  - [ ] Drop/use shortcuts
  - [ ] Item descriptions in inventory
- [ ] Better help system
  - [ ] Context-sensitive help
  - [ ] Tutorial quest/guide
  - [ ] In-game hints

---

### 🏗️ Phase 2: Architecture & Polish (1 week)
**Goal**: Clean up technical debt, improve maintainability, prepare for scale.

#### 2.1 Code Organization 🧹
**Priority**: MEDIUM | **Impact**: MEDIUM (Developer Experience) | **Effort**: Medium

- [ ] Modularize `game_engine.py` (10,000+ lines!)
  - [ ] Extract command handlers into `game/commands/`
  - [ ] Extract world logic into `game/world/`
  - [ ] Extract NPC logic into `game/npcs/`
  - [ ] Extract quest logic into `game/quests/`
- [ ] Clean up `app.py`
  - [ ] Extract routes into `api/routes/`
  - [ ] Extract middleware into `api/middleware/`
- [ ] Improve error handling
  - [ ] Consistent error messages
  - [ ] Error logging/alerting
  - [ ] Graceful degradation

#### 2.2 State Management Cleanup 🔧
**Priority**: MEDIUM | **Impact**: MEDIUM | **Effort**: Low

- [ ] Remove legacy code
  - [ ] Remove HTTP polling remnants
  - [ ] Remove `LAST_POLL_STATE`
  - [ ] Remove disk-based state saving (fully migrate to Redis/DB)
- [ ] Consolidate state
  - [ ] Single source of truth for all state
  - [ ] Clear state sync (Redis ↔ Database)
  - [ ] State validation/health checks

#### 2.3 Performance & Scale 🚀
**Priority**: MEDIUM | **Impact**: HIGH (Scale Goal) | **Effort**: Medium

- [ ] Database optimization
  - [ ] Add indexes on frequently queried columns
  - [ ] Connection pooling improvements
  - [ ] Query optimization
- [ ] Redis optimization
  - [ ] Pipeline operations where possible
  - [ ] Key expiration strategies
  - [ ] Memory usage monitoring
- [ ] Load testing
  - [ ] Test with 100+ concurrent users
  - [ ] Identify bottlenecks
  - [ ] Optimize hot paths
- [ ] Monitoring
  - [ ] Add performance metrics (response times, command throughput)
  - [ ] Error tracking (Sentry or similar)
  - [ ] User analytics (command usage, popular areas)

---

### 🎮 Phase 3: Advanced Features (2-3 weeks)
**Goal**: Add depth and replayability.

#### 3.1 Combat Enhancements ⚔️
**Priority**: MEDIUM | **Impact**: MEDIUM | **Effort**: Medium-High

- [ ] Advanced combat
  - [ ] Critical hits
  - [ ] Status effects (poison, stun, etc.)
  - [ ] Combat skills/abilities
  - [ ] Block/dodge mechanics
- [ ] Magic system (if desired)
  - [ ] Spells/abilities
  - [ ] Mana system
  - [ ] Spell books/scrolls
- [ ] PvP (Player vs Player) combat (optional)
  - [ ] Duels
  - [ ] PvP zones
  - [ ] Death penalties

#### 3.2 Crafting System 🔨
**Priority**: MEDIUM | **Impact**: MEDIUM | **Effort**: High

- [ ] Crafting basics
  - [ ] Crafting stations (forge, alchemy table, etc.)
  - [ ] Recipes system
  - [ ] Crafting skills
- [ ] Materials and resources
  - [ ] Gathering nodes (mines, plants, etc.)
  - [ ] Material types and qualities
  - [ ] Material storage
- [ ] Craftable items
  - [ ] Weapons and armor
  - [ ] Potions/consumables
  - [ ] Tools
  - [ ] Decorations

#### 3.3 Social Features 👥
**Priority**: LOW | **Impact**: MEDIUM | **Effort**: Medium

- [ ] Party/group system
  - [ ] Form parties
  - [ ] Shared XP/quests
  - [ ] Party chat
- [ ] Guild system (if desired)
  - [ ] Create/join guilds
  - [ ] Guild chat
  - [ ] Guild quests/activities
- [ ] Friends list
  - [ ] Add friends
  - [ ] Friend status/notifications
  - [ ] Friend chat shortcut

#### 3.4 Housing/Personal Space 🏠
**Priority**: LOW | **Impact**: LOW | **Effort**: High

- [ ] Player homes/rooms
  - [ ] Purchase/rent rooms
  - [ ] Decorate with items
  - [ ] Private storage
- [ ] Furniture system
  - [ ] Placeable items
  - [ ] Functional furniture (storage, crafting)

---

### 🌍 Phase 4: World Expansion (2-4 weeks)
**Goal**: Larger world with more to explore.

#### 4.1 More Locations 🗺️
**Priority**: MEDIUM | **Impact**: HIGH | **Effort**: Low-Medium

- [ ] Expand world map
  - [ ] Add 10-15 new rooms
  - [ ] Create distinct areas (forest, mountains, caves, etc.)
  - [ ] Add landmarks and points of interest
- [ ] Dungeons
  - [ ] Multi-room dungeons
  - [ ] Boss encounters
  - [ ] Dungeon rewards
- [ ] Special locations
  - [ ] Shops (weapon shop, armor shop, general store)
  - [ ] Training areas
  - [ ] Quest hubs

#### 4.2 More NPCs & Quests 📜
**Priority**: MEDIUM | **Impact**: HIGH | **Effort**: Medium

- [ ] 10+ new NPCs
  - [ ] Each with unique personality
  - [ ] Quests, shops, or services
  - [ ] AI-enhanced dialogue
- [ ] 10+ new quests
  - [ ] Story-driven questlines
  - [ ] Daily/repeatable quests
  - [ ] Achievement quests
  - [ ] Multi-stage epic quests

#### 4.3 World Events 🌟
**Priority**: LOW | **Impact**: MEDIUM | **Effort**: Medium

- [ ] Random events
  - [ ] Monster spawns
  - [ ] Treasure discoveries
  - [ ] NPC events
- [ ] Scheduled events
  - [ ] Daily quest resets
  - [ ] Weekly boss spawns
  - [ ] Seasonal events

---

### 🎨 Phase 5: Polish & Production (1-2 weeks)
**Goal**: Make it production-ready and polished.

#### 5.1 Content Polish 📝
**Priority**: MEDIUM | **Impact**: MEDIUM | **Effort**: Low

- [ ] Improve all descriptions
  - [ ] Room descriptions more vivid
  - [ ] Item descriptions more interesting
  - [ ] NPC dialogue more varied
- [ ] Balance tuning
  - [ ] Combat difficulty curves
  - [ ] Economy balance (prices, rewards)
  - [ ] Quest rewards balanced
- [ ] Tutorial/onboarding improvements
  - [ ] Interactive tutorial
  - [ ] Better first-time experience
  - [ ] Help documentation

#### 5.2 Bug Fixes & Testing 🐛
**Priority**: HIGH | **Impact**: HIGH | **Effort**: Medium

- [ ] Comprehensive testing
  - [ ] Test all commands
  - [ ] Test all quests
  - [ ] Test combat system
  - [ ] Test multiplayer interactions
- [ ] Bug fixes
  - [ ] Fix any discovered bugs
  - [ ] Edge case handling
  - [ ] Error recovery

#### 5.3 Production Readiness 🚢
**Priority**: HIGH | **Impact**: HIGH | **Effort**: Medium

- [ ] Security audit
  - [ ] Input validation
  - [ ] SQL injection prevention
  - [ ] XSS prevention
  - [ ] Rate limiting
- [ ] Backup & recovery
  - [ ] Database backups
  - [ ] State backup strategy
  - [ ] Disaster recovery plan
- [ ] Documentation
  - [ ] API documentation
  - [ ] Admin guide
  - [ ] Player guide updates
  - [ ] Developer docs

---

## Quick Wins (Can be done anytime)

These are small features that add value quickly:

- [ ] Auto-save reminder (warn players to save)
- [ ] Command aliases (`k` for `kill`, `i` for `inventory`, etc.)
- [ ] Better error messages ("You can't go that way" → "The door is locked")
- [ ] Item stacking in inventory (show "3x apple" instead of listing 3 times)
- [ ] Quest progress indicators in room descriptions
- [ ] NPC shop UI improvements
- [ ] Better color themes (dark mode, high contrast)
- [ ] Keyboard shortcuts (arrow keys for movement, etc.)
- [ ] Command history (up arrow to repeat last command)
- [ ] Auto-complete for commands/NPC names

---

## Technical Debt Items

- [ ] `game_engine.py` is 10,000+ lines - needs refactoring
- [ ] Legacy polling code still exists in some places
- [ ] Some state still in global dicts instead of Redis
- [ ] Database schema could be normalized better
- [ ] Error handling is inconsistent
- [ ] No automated tests
- [ ] Logging could be more structured

---

## Decision Points Needed

1. **Combat Style**: Turn-based (like classic MUDs) or real-time action? **Recommendation**: Turn-based for text-based MUD.
2. **Magic System**: Do we want magic/spells, or keep it low-fantasy? **Recommendation**: Start simple, add magic later if needed.
3. **PvP**: Allow player vs player combat? **Recommendation**: Optional, with consent (duels).
4. **Death Penalty**: What happens when a player dies? **Recommendation**: Lose some gold, respawn at town square (light penalty).
5. **Character Classes**: Do we want classes (warrior, mage, rogue) or classless system? **Recommendation**: Start classless, add classes later if desired.
6. **Guilds**: Do we want guilds/clans? **Recommendation**: Later feature, not critical for MVP.

---

## Success Metrics

Track these to measure progress:

- **Player Retention**: % of players who return after first session
- **Session Length**: Average minutes per session
- **Daily Active Users**: Players who log in daily
- **Command Diversity**: Are players using variety of commands or just a few?
- **Quest Completion**: % of players who complete at least one quest
- **Social Interaction**: How often do players use `tell`, `say`, group up?

---

## Next Immediate Steps (This Week)

1. **Implement Combat System** (Phase 1.1) - This is the biggest missing piece
2. **Add Character Progression** (Phase 1.2) - Gives players reason to play
3. **Add 2-3 More Quests** (Phase 1.3) - More content = more replayability

**Estimated Time**: 3-5 days for combat + progression + a couple quests

---

## Questions for You

1. What's your vision for this game? Classic MUD nostalgia, or modernized MUD experience?
2. What's the core gameplay loop you want? (Explore → Fight → Loot → Level → Repeat?)
3. What's most important to you right now: **Fun gameplay** or **Technical perfection**?
4. Are you planning to open it to public players soon, or still in closed testing?

Based on your answers, we can adjust priorities!

