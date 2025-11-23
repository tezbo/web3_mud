"""
onboarding.py

Contains character creation / onboarding prompts and the onboarding state machine.

Extracted from game_engine.py to keep the core engine smaller and more focused.
"""

import re

# Character creation options
AVAILABLE_RACES = {
    "human": {
        "name": "Human",
        "description": "Versatile and adaptable, humans are the most common folk in Hollowvale. You have no special abilities, but your flexibility allows you to excel in any path you choose.",
    },
    "elf": {
        "name": "Elf",
        "description": "Graceful and long-lived, elves have keen senses and a natural affinity for the arcane. You move with an otherworldly elegance.",
    },
    "dwarf": {
        "name": "Dwarf",
        "description": "Sturdy and resilient, dwarves are masters of craft and stone. You have a natural toughness and an eye for detail.",
    },
    "halfling": {
        "name": "Halfling",
        "description": "Small but determined, halflings are known for their luck and resourcefulness. You have a knack for finding opportunities where others see none.",
    },
    "fae-touched": {
        "name": "Fairy",
        "description": "Touched by the magic of the fae realm, you have an otherworldly presence. Reality seems to bend slightly around you.",
    },
    "outlander": {
        "name": "Lyzard",
        "description": "From lands unknown, you are a mystery to most. Your origins are strange, and you carry the weight of distant places.",
    },
}

AVAILABLE_GENDERS = {
    "male": {"name": "Male", "pronoun": "he", "pronoun_cap": "He", "possessive": "his"},
    "female": {"name": "Female", "pronoun": "she", "pronoun_cap": "She", "possessive": "her"},
    "nonbinary": {"name": "Nonbinary", "pronoun": "they", "pronoun_cap": "They", "possessive": "their"},
    "other": {"name": "Other", "pronoun": "they", "pronoun_cap": "They", "possessive": "their"},
}

AVAILABLE_BACKSTORIES = {
    "scarred_past": {
        "name": "Scarred Past",
        "description": "You carry the weight of loss and hardship. Your past has left marks, but also made you stronger.",
    },
    "forgotten_lineage": {
        "name": "Forgotten Lineage",
        "description": "You know little of your true heritage, but sense there is more to your story than meets the eye.",
    },
    "broken_oath": {
        "name": "Broken Oath",
        "description": "You once made a promise you could not keep. The weight of that failure drives you forward.",
    },
    "hopeful_spark": {
        "name": "Hopeful Spark",
        "description": "Despite the darkness in the world, you carry a light within. You believe in better days ahead.",
    },
    "quiet_mystery": {
        "name": "Quiet Mystery",
        "description": "You prefer to keep your past to yourself. There are things you know that others do not.",
    },
    "custom": {
        "name": "Custom",
        "description": "Your story is your own to tell.",
    },
}

STAT_NAMES = {
    "str": "Strength",
    "agi": "Agility",
    "wis": "Wisdom",
    "wil": "Willpower",
    "luck": "Luck",
}

TOTAL_STAT_POINTS = 10

# --- Onboarding Narrative Text ---
# Special marker for delayed messages: [PAUSE:seconds] or [ELLIPSIS:seconds]

ONBOARDING_USERNAME_PROMPT = """[PAUSE:1]
In the endless void between lives, you drift...

[PAUSE:1.5]
Memories fade. Identity dissolves. You are... nothing. And everything.

[PAUSE:2]
A presence stirs in the darkness. Ancient. Patient. Wise.

[PAUSE:1.5]
"Awaken, wandering soul."

The voice echoes through the emptiness, warm yet distant.

[PAUSE:2]
"You have walked the cycle many times. Life. Death. Rebirth. The wheel turns, and you return."

[PAUSE:1.5]
A flicker of light appears in the distance. Growing. Calling.

[PAUSE:2]
"Before you take form once more, you must remember. Who were you? Who will you become?"

[PAUSE:1.5]
The light intensifies, and you feel yourself being drawn forward.

[PAUSE:1]
"What name will you bear in this new life? What identity will you claim?"

[PAUSE:0.5]
Enter your username (this will be your character name):"""

ONBOARDING_PASSWORD_PROMPT = """[PAUSE:1]
"Good. A name is chosen. Now, you must protect it."

[PAUSE:1.5]
The void around you shimmers. You sense other presences—some friendly, some... not.

[PAUSE:2]
"Choose a password. A secret. A key that only you will know. Guard it well."

[PAUSE:1]
Enter your password (minimum 4 characters):"""

ONBOARDING_RACE_PROMPT = """[PAUSE:1.5]
The light grows stronger. Shapes begin to form in the darkness.

[PAUSE:2]
"Now, tell me... what form calls to you? What bloodline do you remember?"

[PAUSE:1.5]
Images flash before you—fragments of past lives, echoes of distant kin.

[PAUSE:2]
"Choose the vessel that will carry your soul into Hollowvale:"

[PAUSE:1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  • HUMAN
    The most common folk. Versatile, adaptable, unbound by ancient pacts.
    You remember countless lives as farmer, merchant, warrior, scholar.
    In you flows the blood of endless possibility.

  • ELF
    Graceful and long-lived, touched by the magic of the old world.
    You recall lifetimes spent in ancient forests, under starlit skies.
    The arcane whispers to you, and you move with otherworldly elegance.

  • DWARF
    Sturdy and unyielding, forged in the depths of the earth.
    Memories of stone halls and ringing hammers fill your mind.
    You carry the resilience of mountains and the craft of ages.

  • HALFLING
    Small but determined, blessed with luck and resourcefulness.
    You remember cozy hearths, warm meals, and finding joy in simple things.
    Fortune smiles upon you, and opportunity finds you where others see none.

  • FAE-TOUCHED
    Touched by the magic of the fae realm, reality bends around you.
    Fragments of the Otherworld linger in your soul.
    You are not entirely of this realm, and the world knows it.

  • OUTLANDER
    From lands unknown, a mystery even to yourself.
    Your origins are strange, your past a puzzle.
    You carry the weight of distant places and forgotten truths.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PAUSE:1]
Type the name of your race (human, elf, dwarf, halfling, fae-touched, or outlander):"""

ONBOARDING_GENDER_PROMPT = """[PAUSE:1]
The form takes shape. Flesh remembers. Bone aligns.

[PAUSE:1.5]
"But form is only part of who you are. How do you know yourself?"

[PAUSE:2]
"Gender is not merely flesh—it is spirit, identity, the truth of your being."

[PAUSE:1.5]
Choose how you know yourself:

  • MALE
  • FEMALE
  • NONBINARY
  • OTHER

[PAUSE:1]
Type your choice:"""

ONBOARDING_STATS_PROMPT = """[PAUSE:1]
Your essence solidifies. The void recedes.

[PAUSE:2]
"Now, where do your strengths lie? What gifts will you carry into this life?"

[PAUSE:1.5]
You feel power gathering within you—five aspects of your being, waiting to be shaped.

[PAUSE:2]
"Distribute your essence across these attributes. You have 10 points to allocate:"

[PAUSE:1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  STRENGTH (str)    - Physical power, might, the force of your body
  AGILITY (agi)     - Speed, dexterity, reflexes, grace of movement
  WISDOM (wis)      - Knowledge, insight, understanding of the world
  WILLPOWER (wil)   - Mental fortitude, determination, inner strength
  LUCK (luck)       - Fortune, chance, the favor of fate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PAUSE:1]
Enter your stat allocation like this: str 3, agi 2, wis 2, wil 2, luck 1
(All five stats must total exactly 10 points)

Your allocation:"""

ONBOARDING_BACKSTORY_PROMPT = """[PAUSE:1.5]
The form is nearly complete. Almost there...

[PAUSE:2]
"But every soul carries a story. Scars from past lives. Promises made and broken. Hope that endures."

[PAUSE:1.5]
"What tale will you bring with you? What weight will you carry?"

[PAUSE:2]
"Choose the story that defines you:"

[PAUSE:1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  • SCARRED_PAST
    You carry the weight of loss and hardship.
    Your past has left marks, but also made you stronger.
    Pain has shaped you, but it does not define you.

  • FORGOTTEN_LINEAGE
    You know little of your true heritage.
    There are gaps in your memory, mysteries in your blood.
    Something important was lost, and you sense there is more to your story.

  • BROKEN_OATH
    You once made a promise you could not keep.
    The weight of that failure drives you forward.
    Redemption calls to you, or perhaps acceptance.

  • HOPEFUL_SPARK
    Despite the darkness in the world, you carry a light within.
    You believe in better days ahead.
    Hope is your strength, and you refuse to let it die.

  • QUIET_MYSTERY
    You prefer to keep your past to yourself.
    There are things you know that others do not.
    Secrets are your currency, and silence your shield.

  • CUSTOM
    Your story is your own to tell.
    Write it in your own words.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PAUSE:1]
Type your choice (or 'custom' to write your own):"""

ONBOARDING_COMPLETE = """[PAUSE:2]
The transformation is complete.

[PAUSE:1.5]
Your form solidifies. Your essence takes root. You are... whole.

[PAUSE:2]
The voice grows distant, fading into the void:

[PAUSE:1]
"Your vessel is ready. Your story begins anew."

[PAUSE:1.5]
"Welcome to Hollowvale, {username}."

[PAUSE:2]
"May this life be different. May you find what you seek."

[PAUSE:1.5]
The light intensifies, blinding, overwhelming...

[PAUSE:2]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PAUSE:1]
[ELLIPSIS:2]

[PAUSE:1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PAUSE:1.5]
The world materializes around you.

[PAUSE:1]
Colors flood your vision. Sounds reach your ears. The scent of earth and wood fills your lungs.

[PAUSE:2]
You stand in the Town Square of Hollowvale.

[PAUSE:1]
A frontier town where adventure awaits, where stories are written, where souls find their purpose.

[PAUSE:1.5]
Your journey begins... now."""


def process_onboarding_message(message):
    """
    Process onboarding message with pause markers into a list of timed segments.
    
    Returns a list of dicts: [{"text": "...", "delay": seconds}, ...]
    Special markers:
    - [PAUSE:seconds] - pause before next segment
    - [ELLIPSIS:seconds] - show loading ellipses for duration
    """
    # Split by pause markers
    segments = []
    parts = re.split(r'\[(PAUSE|ELLIPSIS):([\d.]+)\]', message)
    
    current_text = ""
    for i, part in enumerate(parts):
        if part in ["PAUSE", "ELLIPSIS"]:
            # Save current text if any
            if current_text.strip():
                segments.append({"text": current_text.strip(), "delay": 0, "type": "text"})
                current_text = ""
            
            # Get duration from next part
            if i + 1 < len(parts):
                try:
                    duration = float(parts[i + 1])
                    if part == "ELLIPSIS":
                        segments.append({"text": "...", "delay": duration, "type": "ellipsis"})
                    else:
                        segments.append({"text": "", "delay": duration, "type": "pause"})
                except (ValueError, IndexError):
                    pass
        elif not part.isdigit() and not part.replace(".", "").isdigit():
            # Regular text
            current_text += part
    
    # Add any remaining text
    if current_text.strip():
        segments.append({"text": current_text.strip(), "delay": 0, "type": "text"})
    
    # If no segments found, return original message
    if not segments:
        return [{"text": message, "delay": 0, "type": "text"}]
    
    return segments


def handle_onboarding_command(command, onboarding_state, username=None, db_conn=None):
    """
    Handle commands during the onboarding process.
    
    Args:
        command: User's command input
        onboarding_state: Dict with onboarding_step and character data
        username: Player's username (optional, may be None during account creation)
        db_conn: Optional database connection for creating user account
    
    Returns:
        tuple: (response_text, updated_onboarding_state, is_complete, created_user_id)
    """
    step = onboarding_state.get("step", 0)
    character = onboarding_state.get("character", {})
    command_lower = command.strip().lower()
    created_user_id = None
    
    if step == 0:  # Username creation
        username_input = command.strip()
        if not username_input:
            return "Please enter a username.", onboarding_state, False, None
        if len(username_input) < 2:
            return "Username must be at least 2 characters long.", onboarding_state, False, None
        if len(username_input) > 20:
            return "Username must be 20 characters or less.", onboarding_state, False, None
        
        # Check if username already exists
        if db_conn:
            existing = db_conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username_input,)
            ).fetchone()
            if existing:
                return f"Username '{username_input}' is already taken. Please choose another.", onboarding_state, False, None
        
        onboarding_state["username"] = username_input
        onboarding_state["step"] = 0.5  # Next: password
        return ONBOARDING_PASSWORD_PROMPT, onboarding_state, False, None
    
    elif step == 0.5:  # Password creation
        password_input = command
        if not password_input:
            return "Please enter a password.", onboarding_state, False, None
        if len(password_input) < 4:
            return "Password must be at least 4 characters long.", onboarding_state, False, None
        
        onboarding_state["password"] = password_input
        onboarding_state["step"] = 1  # Next: race
        return ONBOARDING_RACE_PROMPT, onboarding_state, False, None
    
    elif step == 1:  # Race selection
        if command_lower in AVAILABLE_RACES:
            character["race"] = command_lower
            onboarding_state["character"] = character
            onboarding_state["step"] = 2
            return ONBOARDING_GENDER_PROMPT, onboarding_state, False, None
        else:
            return "Please choose a valid race: human, elf, dwarf, halfling, fae-touched, or outlander", onboarding_state, False, None
    
    elif step == 2:  # Gender selection
        if command_lower in AVAILABLE_GENDERS:
            character["gender"] = command_lower
            onboarding_state["character"] = character
            onboarding_state["step"] = 3
            return ONBOARDING_STATS_PROMPT, onboarding_state, False, None
        else:
            return "Please choose a valid gender: male, female, nonbinary, or other", onboarding_state, False, None
    
    elif step == 3:  # Stat allocation
        # Parse stat allocation: "str 3, agi 2, wis 2, wil 2, luck 1"
        stats = {"str": 0, "agi": 0, "wis": 0, "wil": 0, "luck": 0}
        try:
            # Split by comma and parse each stat
            parts = [p.strip() for p in command_lower.split(",")]
            for part in parts:
                if not part:
                    continue
                # Match pattern like "str 3" or "str:3" or "str=3"
                match = re.match(r'(\w+)\s*[:=]?\s*(\d+)', part)
                if match:
                    stat_name = match.group(1).lower()
                    stat_value = int(match.group(2))
                    if stat_name in stats:
                        stats[stat_name] = stat_value
                    else:
                        return f"Unknown stat: {stat_name}. Valid stats are: str, agi, wis, wil, luck", onboarding_state, False, None
            
            # Validate total
            total = sum(stats.values())
            if total != TOTAL_STAT_POINTS:
                return f"Your stats must total exactly {TOTAL_STAT_POINTS} points. You allocated {total} points. Please try again.", onboarding_state, False, None
            
            # Check for negative values
            if any(v < 0 for v in stats.values()):
                return "Stat values cannot be negative. Please try again.", onboarding_state, False, None
            
            character["stats"] = stats
            onboarding_state["character"] = character
            onboarding_state["step"] = 4
            return ONBOARDING_BACKSTORY_PROMPT, onboarding_state, False, None
        except Exception as e:
            return f"Invalid stat format. Please use: str 3, agi 2, wis 2, wil 2, luck 1", onboarding_state, False, None
    
    elif step == 4:  # Backstory selection
        if command_lower == "custom":
            onboarding_state["step"] = 5  # Custom backstory input
            return "Tell me your story in your own words (keep it brief, 1-2 sentences):", onboarding_state, False, None
        elif command_lower in AVAILABLE_BACKSTORIES:
            character["backstory"] = command_lower
            character["backstory_text"] = AVAILABLE_BACKSTORIES[command_lower]["description"]
            onboarding_state["character"] = character
            onboarding_state["step"] = 6  # Complete
            
            # Create user account now that character is complete
            if db_conn and onboarding_state.get("username") and onboarding_state.get("password"):
                from werkzeug.security import generate_password_hash
                username_final = onboarding_state["username"]
                password_hash = generate_password_hash(onboarding_state["password"])
                try:
                    cursor = db_conn.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username_final, password_hash)
                    )
                    db_conn.commit()
                    created_user_id = cursor.lastrowid
                except Exception as e:
                    return f"Error creating account: {str(e)}", onboarding_state, False, None
            
            final_username = onboarding_state.get("username", username or "adventurer")
            return ONBOARDING_COMPLETE.format(username=final_username), onboarding_state, True, created_user_id
        else:
            return "Please choose a valid backstory or type 'custom' to write your own.", onboarding_state, False, None
    
    elif step == 5:  # Custom backstory input
        if command_lower and len(command_lower) > 5:
            character["backstory"] = "custom"
            character["backstory_text"] = command.strip()  # Keep original case
            onboarding_state["character"] = character
            onboarding_state["step"] = 6  # Complete
            
            # Create user account now that character is complete
            if db_conn and onboarding_state.get("username") and onboarding_state.get("password"):
                from werkzeug.security import generate_password_hash
                username_final = onboarding_state["username"]
                password_hash = generate_password_hash(onboarding_state["password"])
                try:
                    cursor = db_conn.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username_final, password_hash)
                    )
                    db_conn.commit()
                    created_user_id = cursor.lastrowid
                except Exception as e:
                    return f"Error creating account: {str(e)}", onboarding_state, False, None
            
            final_username = onboarding_state.get("username", username or "adventurer")
            return ONBOARDING_COMPLETE.format(username=final_username), onboarding_state, True, created_user_id
        else:
            return "Please provide a brief backstory (at least a few words).", onboarding_state, False, None
    
    return "Invalid command during onboarding.", onboarding_state, False, None, None

