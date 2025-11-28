# Phase 1: Player Weather Status - QA Test Plan

## Test Scenario: Weather Status Accumulation and Display

**Goal:** Verify that player weather status accumulates over time and displays correctly

### Setup
1. Login as test character
2. Set weather to heavy rain: `setweather rain heavy`
3. Ensure you're in town_square (outdoor room)

### Test 1: Weather Accumulation
**Expected:** Weather status should accumulate over time (ticks)
**Steps:**
1. Wait ~1-2 minutes (12-24 in-game minutes = 12-24 ticks)
2. Execute `look me`
3. Look for weather description like "You look a bit damp" or "soaked"

**Success Criteria:**
- [ ] Weather status appears in `look me` output
- [ ] Description is appropriate for rain (wetness-related)

### Test 2: Weather Display When Looking at Others
**Expected:** Weather status shows when looking at other players in outdoor rooms
**Steps:**
1. Have another player in the same outdoor room
2. Execute `look <playername>`
3. Check for weather description with correct pronoun (He/She/They)

**Success Criteria:**
- [ ] Weather shows for other players
- [ ] Correct pronoun used based on their gender

### Test 3: Indoor Decay
**Expected:** Weather status should decay when indoors
**Steps:**
1. Build up wetness outdoors in rain (wait few minutes if needed)
2. Verify weather status with `look me`
3. Go indoors: `south` (to tavern)
4. Wait ~1 minute
5. Check `look me` again

**Success Criteria:**
- [ ] Weather status decreases when indoors
- [ ] Eventually reaches 0

### Test 4: Persistence
**Expected:** Weather status persists across logout/login
**Steps:**
1. Build up weather status outdoors
2. Note the description from `look me`
3. Logout
4. Login again
5. Check `look me`

**Success Criteria:**
- [ ] Weather status preserved
- [ ] Same or similar description appears

## Debug Commands
If weather isn't accumulating:
- Check current weather: `weather`
- Check if you're outdoors: Look at room description
- Manually advance time by waiting longer

## Known Limitations
- Weather updates once per in-game minute (every 5 real-world seconds)
- Need to wait for ticks to progress for accumulation
- Instant commands won't show accumulation without time passing
