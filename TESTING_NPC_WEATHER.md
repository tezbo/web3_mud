# Testing NPC Weather Status & Reactions (Phase 2)

## Server Access
The server is running at: `http://localhost:8000`

## Test Plan

### Prerequisites
1. Log in as an admin user (e.g., "agent" or your admin account)
2. Make sure you have the `setweather` command available

### Test 1: NPC Weather Status Accumulation

1. **Go to an outdoor room with an NPC**
   ```
   > look
   ```
   Verify you're in an outdoor room (e.g., "Hollowvale Town Square") with an NPC present (e.g., "Old Storyteller")

2. **Set heavy rain weather**
   ```
   > setweather rain heavy
   ```
   Expected: "Weather set to rain (heavy)."

3. **Wait and check NPC weather status**
   - Wait 10-15 seconds (real time = multiple game ticks)
   - Look at the NPC:
   ```
   > look storyteller
   ```
   Expected: Should see weather description like:
   - "He looks a bit damp." (low wetness)
   - "You can tell he has been standing in the rain for a while." (medium wetness)
   - "He looks thoroughly soaked through." (high wetness)
   - "He is absolutely drenched from head to toe." (maximum wetness)

4. **Wait longer and check again**
   ```
   > look storyteller
   ```
   The wetness should increase over time as you wait in the rain.

### Test 2: NPC Weather Reactions

1. **Stay in the outdoor room with heavy rain**
   ```
   > setweather rain heavy
   ```

2. **Wait for NPC weather reaction**
   - NPCs have a 10% chance per tick to react to weather when affected
   - Wait 30-60 seconds in the room
   - Watch for NPC reaction messages like:
   ```
   [NPC]The Old Storyteller pulls his robes closer. 'The rain tells stories of its own, if you know how to listen.'[/NPC]
   ```

3. **Try different weather types**
   ```
   > setweather heatwave heavy
   ```
   Wait and look for heat-related reactions from Old Storyteller.

### Test 3: Weather Status Decay (Moving Indoors)

1. **Get NPC wet**
   ```
   > setweather rain heavy
   ```
   Wait until NPC shows wet status (e.g., "He looks thoroughly soaked through")

2. **Move indoors with NPC**
   ```
   > go south
   ```
   (Move to The Rusty Tankard Tavern)

3. **Check NPC status indoors**
   ```
   > look storyteller
   ```
   Note: NPCs might not follow you, so you might need to check when the NPC moves indoors.

   Alternatively, move an NPC that's already indoors (like Mara in the tavern):
   ```
   > look mara
   ```
   If she was outside, wetness should decay over time indoors.

### Test 4: Multiple NPCs with Different Pronouns

1. **Test with Mara (she pronoun)**
   ```
   > go south
   > setweather rain heavy
   ```
   Wait, then:
   ```
   > look mara
   ```
   Expected: Weather description should use "she" pronoun:
   - "She looks a bit damp."
   - "She looks thoroughly soaked through."

2. **Test with Patrolling Guard (they pronoun)**
   Find the patrolling guard and check their weather status.

### Test 5: Weather Reactions for Different NPCs

1. **Test Old Storyteller reactions**
   - `setweather rain heavy` → Should react with rain quote
   - `setweather heatwave heavy` → Should react with heatwave quote
   - `setweather snow heavy` → Should react with snow quote

2. **Test Mara reactions**
   - Move to tavern with Mara
   - `setweather rain heavy` → Should react with rain quote
   - `setweather snow moderate` → Should react with snow quote

3. **Test Patrolling Guard reactions**
   - Find patrolling guard
   - `setweather rain moderate` → Should grumble about umbrellas
   - `setweather sleet moderate` → Should comment on sleet

### Expected Results Summary

✅ **NPCs accumulate weather effects** (wetness, cold, heat) when outdoors
✅ **Weather descriptions appear** when looking at NPCs with correct pronouns
✅ **NPCs react to weather** occasionally (10% chance per tick when affected)
✅ **Weather effects decay** when NPCs are indoors
✅ **Different NPCs have different reactions** based on their personality

## Troubleshooting

If NPC weather status isn't showing:
1. Make sure you're in an outdoor room (`look` should show weather description)
2. Make sure the weather is significant (e.g., "rain heavy", not "clear")
3. Wait a bit - weather effects accumulate over time (each command advances time)
4. Check that the NPC is actually outdoors (not all NPCs are in outdoor rooms)

If NPC reactions aren't appearing:
1. Make sure the NPC has weather status effects (look at them first)
2. Wait longer - reactions have a 10% chance per tick
3. Check that the NPC has a reaction defined for that weather type in `npc.py`

## Notes

- Weather effects are tick-based, so they accumulate as you perform commands
- NPCs update their weather status on every player command
- Reactions are broadcast to all players in the room
- Weather descriptions use correct pronouns based on NPC gender

