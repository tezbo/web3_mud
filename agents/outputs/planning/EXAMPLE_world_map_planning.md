# Planning Document: World Map Design
**Agent**: Mapmaker  
**Created**: 2024-11-25  
**Status**: PLANNING (awaiting approval)

---

## Objective
Design a high-level world map for Aethermoor showing the three realms, major locations, and travel routes.

---

## Research Completed

### Lore Review
- Read `/world/LORE_PRIMER.md`
- Reviewed realm descriptions and cultural notes
- Identified key geographical features:
  - Sunward: rolling hills, ancient forests, coastal cities
  - Twilight: island archipelago, cliffs, eternal twilight
  - Shadowfen: swamplands, the Scar (reality tear), mist

### Coordination Check
- **Lore Keeper**: Confirmed no existing map conflicts
- **Wordsmith**: Will need descriptions for each region (coordinate later)
- **Personality Designer**: NPCs reference travel times - map should support this
- **Quest Architect**: No active quests depend on specific geography yet

### Current Content Audit
Existing 11 rooms need to be placed on map:
- Town Square, Mara's Inn, Market, Temple, etc.
- **Decision**: These will become "Greymarket" - a Shadowfen city
- Rationale: Neutral starting zone makes sense for new players

---

## Proposed Map Structure

### Realm Layout
```
           SUNWARD KINGDOMS
          (Western Continent)
                  |
                  | The Grey Marches
                  | (Border Region)
                  |
              SHADOWFEN
          (Central Scar Zone)
             /         \
    THE SCAR            Trade Routes
                  |
                  |
          TWILIGHT DOMINION
          (Eastern Archipelago)
```

### Major Locations (15 total to start)

**Sunward Kingdoms** (5 locations):
1. Thornhaven - Capital city (15 rooms planned)
2. Aldric's Rest - Ruined pre-Sundering city (dungeon, 10 rooms)
3. The Grey Marches - Borderland (5 rooms)
4. Silverwood Grove - Ael

thari enclave (5 rooms)
5. Port Sentinel - Coastal fortress (8 rooms)

**Twilight Dominion** (5 locations):
1. The Jade Towers - Singer Council seat (12 rooms)
2. Floating Market - Neutral trade zone (8 rooms)
3. The Obsidian House - Gambling den (6 rooms, web3 integration)
4. Akira's Temple - Spiritual center (7 rooms)
5. Mei-Lin's Gardens - Noble estate (5 rooms)

**Shadowfen** (5 locations):
1. Greymarket - Main hub (EXISTING 11 rooms + 9 new = 20 total)
2. The Mire - Swamp settlements (10 rooms)
3. The Scar (Edge) - Dangerous zone (8 rooms)
4. Smuggler's Rest - Hidden waystation (5 rooms)
5. The Forgotten Archive - Pre-Sundering ruin (dungeon, 12 rooms)

**Total**: 136 rooms across 15 locations

---

## Travel System

### Fast Travel (Story Justification)
- **Waystones**: Ancient pre-Sundering teleportation network (limited)
- Players discover and activate waystones through exploration
- Not all locations have waystones (dungeons never do)

### Standard Travel
- Walking between adjacent locations: 5-10 rooms transition
- Transition rooms have environmental storytelling
- Weather and time-of-day affect travel descriptions

---

## Phased Rollout Plan

### Phase 1: Establish Greymarket (Current)
- Retrofit existing 11 rooms as Greymarket (Shadowfen)
- Add 9 new Greymarket rooms for completeness
- **Deliverable**: Complete starter city

### Phase 2: Add First Realm Content
- Sunward: Thornhaven (15 rooms)
- Twilight: Floating Market (8 rooms)
- **Deliverable**: Players can visit all 3 realms

### Phase 3: Dungeons & Exploration
- Aldric's Rest (Sunward dungeon)
- The Forgotten Archive (Shadowfen dungeon)
- **Deliverable**: PvE content for leveling

### Phase 4: Special Locations
- The Obsidian House (web3 gambling)
- The Jade Towers (Singer content)
- **Deliverable**: Unique features

---

## Artifact Outputs

This planning phase will produce:

1. **World Map** (`/world/maps/world_map.md`)
   - ASCII art overview
   - Region descriptions
   - Travel time estimates

2. **Location Guides** (`/world/maps/[realm]/[location]_guide.md`)
   - Per-location details
   - Room count and layout sketch
   - Notable NPCs/features

3. **Greymarket Retrofit Plan** (`/agents/outputs/planning/greymarket_retrofit.md`)
   - Existing room assignments to Shadowfen culture
   - New rooms needed to complete the city
   - NPC placement

4. **Room Templates** (`/agents/outputs/drafts/mapmaker/room_templates/`)
   - JSON templates for each new room
   - Exit definitions
   - Placeholder descriptions (for Wordsmith to enhance)

---

## Dependencies

**Blockers**:
- None

**Requires Coordination**:
- **Lore Keeper**: Review cultural accuracy of location names
- **Wordsmith**: Write descriptions for map regions
- **Personality Designer**: Plan NPC distribution across locations

**Enables Future Work**:
- Quest Architect can design quests spanning multiple locations
- Worldsmith can write region-specific content
- All agents have spatial context for their work

---

## Validation Tests

Before marking as complete, this work must:
- [ ] Match established lore (3 realms, Sundering geography)
- [ ] Support existing 11 rooms coherently
- [ ] Provide logical travel routes
- [ ] Balance content across realms (no realm starved)
- [ ] Include vertical exploration (dungeons)
- [ ] Leave room for expansion

---

## Next Steps

1. **Get approval** for this plan from Antigravity
2. If approved, create world map artifact
3. Coordinate with Wordsmith on region descriptions
4. Begin Greymarket retrofit planning

---

## Questions for Review

1. **Greymarket placement**: Does starting in Shadowfen make sense narratively?
2. **Room count**: Is 136 rooms too ambitious for initial rollout?
3. **Fast travel**: Are waystones lore-friendly, or should travel be purely walking?

---

**Status**: Ready for review by Antigravity → escalate to Terry if needed
