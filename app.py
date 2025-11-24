import os
import json
import sqlite3
import random
from functools import wraps
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system environment variables

from game_engine import (
    new_game_state,
    describe_location,
    handle_command,
    highlight_exits_in_log,
    add_session_welcome,
    get_global_state_snapshot,
    load_global_state_snapshot,
)

app = Flask(__name__)

# Use an environment variable if available (better for real deployments)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
# Configure session cookie settings for better persistence
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours

# Database setup
# Use persistent disk path if available (for Render deployments)
# Set PERSISTENT_DISK_PATH environment variable to enable persistent storage
PERSISTENT_DISK_PATH = os.environ.get("PERSISTENT_DISK_PATH")
if PERSISTENT_DISK_PATH:
    # Ensure the persistent directory exists
    os.makedirs(PERSISTENT_DISK_PATH, exist_ok=True)
    DATABASE = os.path.join(PERSISTENT_DISK_PATH, "users.db")
    STATE_FILE = os.path.join(PERSISTENT_DISK_PATH, "mud_state.json")
else:
    DATABASE = "users.db"
    STATE_FILE = os.path.join(os.path.dirname(__file__), "mud_state.json")


def init_db():
    """Initialize the database with users and games tables."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            description TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS games (
            user_id INTEGER PRIMARY KEY,
            game_state TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_usage (
            user_id INTEGER PRIMARY KEY,
            token_budget INTEGER DEFAULT 10000,
            tokens_used INTEGER DEFAULT 0,
            requests_count INTEGER DEFAULT 0,
            last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_rate_limits (
            user_id INTEGER NOT NULL,
            request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    # Create index for rate limiting queries
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rate_limit_user_time 
        ON ai_rate_limits(user_id, request_time)
        """
    )
    # Game settings table for admin-configurable parameters
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS game_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Add description column if it doesn't exist (migration for existing databases)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN description TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Initialize default settings if they don't exist
    default_settings = {
        "npc_action_interval_min": ("30", "Minimum seconds between NPC actions (real-world time)"),
        "npc_action_interval_max": ("60", "Maximum seconds between NPC actions (real-world time)"),
        "ambiance_interval_min": ("120", "Minimum seconds between ambiance messages (real-world time)"),
        "ambiance_interval_max": ("240", "Maximum seconds between ambiance messages (real-world time)"),
        "poll_interval": ("3", "Client polling interval in seconds"),
    }
    
    for key, (default_value, description) in default_settings.items():
        cursor.execute(
            "INSERT OR IGNORE INTO game_settings (key, value, description) VALUES (?, ?, ?)",
            (key, default_value, description)
        )
    
    conn.commit()
    conn.close()


# Initialize database when module is imported (works with flask run, WSGI servers, etc.)
init_db()


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# --- Game Settings Management ---

def get_game_setting(key, default=None):
    """Get a game setting value from the database."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT value FROM game_settings WHERE key = ?",
            (key,)
        ).fetchone()
        if row:
            return row["value"]
        return default
    finally:
        conn.close()


def set_game_setting(key, value, description=None):
    """Set a game setting value in the database."""
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO game_settings (key, value, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET 
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, str(value), description)
        )
        conn.commit()
    finally:
        conn.close()


def get_all_game_settings():
    """Get all game settings as a dictionary."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT key, value, description FROM game_settings ORDER BY key"
        ).fetchall()
        return {row["key"]: {"value": row["value"], "description": row["description"]} for row in rows}
    finally:
        conn.close()


# Active games storage for multiplayer support
ACTIVE_GAMES = {}  # username -> game state dict

# Track active sessions (users currently logged in)
# Format: {username: {"last_activity": timestamp, "session_id": str}}
ACTIVE_SESSIONS = {}  # username -> session info

# State file for persistence (set above if PERSISTENT_DISK_PATH is configured)
# NOTE: This uses a local mud_state.json file for persistence. This works fine for
# a single Render instance, but is not suitable for multi-instance scaling where
# multiple servers would need shared state (would require Redis or similar).


def load_state_from_disk():
    """Load ACTIVE_GAMES and global state from disk."""
    global ACTIVE_GAMES
    
    if not os.path.exists(STATE_FILE):
        return  # No state file, use defaults
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Load player states
        if "players" in data and isinstance(data["players"], dict):
            ACTIVE_GAMES = data["players"]
        
        # Load global state
        if "global_state" in data:
            load_global_state_snapshot(data["global_state"])
    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"Error loading state from disk: {e}")
        # Continue with defaults


def save_state_to_disk():
    """Save ACTIVE_GAMES and global state to disk."""
    try:
        # Clean game states (remove any non-serializable fields)
        cleaned_games = {}
        for username, game in ACTIVE_GAMES.items():
            cleaned_game = {}
            for key, value in game.items():
                # Skip internal keys starting with "_"
                if not key.startswith("_"):
                    cleaned_game[key] = value
            cleaned_games[username] = cleaned_game
        
        data = {
            "players": cleaned_games,
            "global_state": get_global_state_snapshot(),
        }
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, OSError) as e:
        print(f"Error saving state to disk: {e}")


# Load state on module import
load_state_from_disk()


def broadcast_to_room(sender_username, room_id, text):
    """Broadcast a message to all other players in the same room."""
    for uname, g in ACTIVE_GAMES.items():
        if uname == sender_username:
            continue
        if g.get("location") == room_id:
            g.setdefault("log", [])
            g["log"].append(text)
            g["log"] = g["log"][-50:]


def cleanup_stale_sessions():
    """
    Remove stale sessions and clean up ACTIVE_GAMES for players who haven't been active.
    Called periodically to keep the active player list accurate.
    Broadcasts logout notifications and saves game state before removal.
    """
    from datetime import datetime, timedelta
    global ACTIVE_GAMES, ACTIVE_SESSIONS
    
    # Remove sessions that haven't been active in 15 minutes
    cutoff_time = datetime.now() - timedelta(minutes=15)
    
    stale_usernames = []
    for username, session_info in ACTIVE_SESSIONS.items():
        last_activity = session_info.get("last_activity")
        if not last_activity or last_activity < cutoff_time:
            stale_usernames.append(username)
    
    # Remove stale sessions and notify other players
    for username in stale_usernames:
        # Save game state before removing
        if username in ACTIVE_GAMES:
            game = ACTIVE_GAMES[username]
            save_game(game)
            
            # Broadcast logout notification to all other players (not just same room)
            logout_msg = f"[{username} has been logged out automatically for being idle too long.]"
            
            # Notify all other players
            for uname, g in ACTIVE_GAMES.items():
                if uname != username:
                    g.setdefault("log", [])
                    g["log"].append(logout_msg)
                    g["log"] = g["log"][-50:]
                    # Save notification to other players' logs (if they have active sessions)
                    try:
                        if uname in ACTIVE_SESSIONS:
                            save_game(g)
                    except Exception:
                        pass  # Skip if can't save
        
        ACTIVE_SESSIONS.pop(username, None)
        # Keep game state in ACTIVE_GAMES for quick reload, but mark as inactive
        # ACTIVE_GAMES.pop(username, None)


def list_active_players():
    """
    Return a list of dicts with active player information.
    Only includes players who have active sessions (logged in and recently active).
    """
    from datetime import datetime, timedelta
    
    # Clean up stale sessions first
    cleanup_stale_sessions()
    
    data = []
    
    # Only show players who have been active in the last 10 minutes
    # This filters out stale entries from players who logged out or closed their browser
    cutoff_time = datetime.now() - timedelta(minutes=10)
    
    for uname, g in ACTIVE_GAMES.items():
        # Check if player has an active session (recently active)
        session_info = ACTIVE_SESSIONS.get(uname)
        if session_info:
            last_activity = session_info.get("last_activity")
            if last_activity and last_activity >= cutoff_time:
                loc_id = g.get("location", "town_square")
                data.append({
                    "username": uname,
                    "location": loc_id,
                })
    
    return data


def require_auth(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # Redirect to welcome screen for better first-time user experience
            return redirect(url_for("welcome"))
        return f(*args, **kwargs)
    return decorated_function

# --- Game state persistence (database layer) ---


def get_game():
    """Get or create the game state for the current user from database."""
    user_id = session.get("user_id")
    username = session.get("username", "adventurer")
    
    if not user_id:
        # Fallback: if not logged in, return new game state (shouldn't happen with @require_auth)
        return new_game_state(username)
    
    # Check in-memory cache first
    if username in ACTIVE_GAMES:
        return ACTIVE_GAMES[username]
    
    conn = get_db()
    row = conn.execute(
        "SELECT game_state FROM games WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    
    if row:
        try:
            game = json.loads(row["game_state"])
            # Defensive: if game is corrupted, start fresh
            if not isinstance(game, dict) or "location" not in game:
                conn.close()
                # Check if character exists - if not, need onboarding
                if not game.get("character"):
                    return None
                game = new_game_state(username)
                ACTIVE_GAMES[username] = game
                save_game(game)
                save_state_to_disk()
                return game
            
            # Check if character exists and has race - if character exists but no race, need onboarding
            # If character doesn't exist at all, it's backward compatibility - allow through (don't force onboarding)
            # Only require onboarding if character object exists but is incomplete
            character = game.get("character")
            if character and isinstance(character, dict) and character.get("race"):
                # Character object exists and has race - good to go
                pass
            elif character and isinstance(character, dict) and not character.get("race"):
                # Character object exists but no race - need onboarding
                conn.close()
                return None
            # If no character object or empty character, it's backward compatibility - allow through
            
            # Load user description from users table
            user_row = conn.execute(
                "SELECT description FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            conn.close()
            if user_row and user_row["description"]:
                game["user_description"] = user_row["description"]
            # Ensure gold and notify are initialized
            from economy import initialize_player_gold
            initialize_player_gold(game)
            game.setdefault("notify", {"login": False})
            # Don't auto-create character object - allow backward compatibility
            # Character object will be created during onboarding for new users
            # Existing users without character objects can play normally
            # Store in memory
            ACTIVE_GAMES[username] = game
            save_state_to_disk()
            return game
        except (json.JSONDecodeError, TypeError):
            # If JSON is corrupted, check if we need onboarding
            conn.close()
            return None
    else:
        # No game state exists - check if character exists (onboarding complete)
        # If no character, user needs onboarding
        # For now, return None to indicate onboarding needed
        # The index route will handle this
        conn.close()
        return None


def save_game(game):
    """Save the game state to database for the current user and update in-memory cache."""
    user_id = session.get("user_id")
    username = session.get("username", "adventurer")
    if not user_id:
        # Shouldn't happen with @require_auth, but handle gracefully
        return
    
    # Update in-memory cache
    ACTIVE_GAMES[username] = game
    
    game_json = json.dumps(game)
    conn = get_db()
    conn.execute(
        """
        INSERT INTO games (user_id, game_state, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            game_state = excluded.game_state,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, game_json)
    )
    # Also save user description if it was updated
    if "user_description" in game:
        conn.execute(
            "UPDATE users SET description = ? WHERE id = ?",
            (game["user_description"], user_id)
        )
    conn.commit()
    conn.close()


# --- Routes ---


@app.route("/welcome")
def welcome():
    """Welcome screen with ASCII art and character creation/login menu."""
    # If already logged in, redirect to game
    if "user_id" in session:
        return redirect(url_for("index"))
    
    # Clear any stale onboarding state when showing welcome screen
    # This ensures users see the welcome screen, not onboarding
    if "onboarding_step" in session:
        session.pop("onboarding_step", None)
        session.pop("onboarding_state", None)
        session.modified = True
    
    return render_template("welcome.html")


@app.route("/welcome_command", methods=["POST"])
def welcome_command():
    """Handle text-based commands from welcome screen."""
    # If already logged in, redirect to game
    if "user_id" in session:
        return jsonify({"redirect": url_for("index")})
    
    data = request.get_json() or {}
    cmd = data.get("command", "").strip()
    cmd_upper = cmd.upper()
    
    # Handle menu commands
    if cmd_upper == "Q":
        return jsonify({"message": "Type N to create a new character, L to login, or G for the guide."})
    elif cmd_upper == "G":
        return jsonify({"redirect": url_for("guide")})
    elif cmd_upper == "N":
        # New character - start onboarding with username/password creation
        session["onboarding_step"] = 0
        session["onboarding_state"] = {"step": 0, "character": {}}
        # Force session save - set permanent to ensure cookie is sent
        session.permanent = True
        session.modified = True
        # Return message and redirect - use query parameter as fallback
        # in case session cookie isn't set before redirect
        return jsonify({
            "message": "Starting character creation...",
            "redirect": "/?onboarding=start",
            "delay": 300
        })
    elif cmd_upper == "L":
        # Login - prompt for username
        session["login_step"] = "username"
        return jsonify({"message": "Enter your username:"})
    else:
        # Check if we're in login flow
        login_step = session.get("login_step")
        
        if login_step == "username":
            # User entered username, now ask for password
            if not cmd:
                return jsonify({"message": "Please enter your username:"})
            session["login_username"] = cmd
            session["login_step"] = "password"
            return jsonify({"message": f"Enter password for {cmd}:"})
        
        elif login_step == "password":
            # User entered password, authenticate
            password = cmd
            username = session.get("login_username", "")
            
            if not password:
                return jsonify({"message": f"Enter password for {username}:"})
            
            # Authenticate user
            conn = get_db()
            user = conn.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            conn.close()
            
            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                username = user["username"]
                session["username"] = username
                session.pop("login_step", None)
                session.pop("login_username", None)
                
                # Track active session on login
                from datetime import datetime
                ACTIVE_SESSIONS[username] = {
                    "last_activity": datetime.now(),
                    "session_id": session.get("session_id", id(session)),
                }
                
                # Check if user has character - if not, start onboarding
                # get_game() requires user_id in session, which we just set
                try:
                    game = get_game()
                except Exception as e:
                    # If get_game fails, just proceed to index
                    return jsonify({"redirect": url_for("index")})
                
                if game is None:
                    # No game state at all - this is fine, user can play without character data (backward compatibility)
                    # Only start onboarding if they explicitly want to create character
                    return jsonify({"redirect": url_for("index")})
                
                # Check if character object exists and is incomplete
                # Only require onboarding if character object exists but has no race
                # If no character object exists, it's backward compatibility - allow through
                character = game.get("character")
                if character and isinstance(character, dict):
                    # Character object exists - check if it has race
                    if not character.get("race"):
                        # Character object exists but no race - need to complete onboarding
                        session["onboarding_step"] = 1
                        session["onboarding_state"] = {"step": 1, "character": character}
                        return jsonify({"redirect": url_for("index")})
                    # Character has race - good to go
                
                # User has valid game state (with or without character object) - proceed to game
                return jsonify({"redirect": url_for("index")})
            else:
                session["login_step"] = "username"
                session.pop("login_username", None)
                return jsonify({"message": "Invalid username or password.\nEnter your username:"})
        
        else:
            # Assume it's a username - start login flow
            if cmd:
                session["login_username"] = cmd
                session["login_step"] = "password"
                return jsonify({"message": f"Enter password for {cmd}:"})
            else:
                return jsonify({"message": "Invalid choice. Please enter N, L, G, Q, or your character name."})


@app.route("/guide")
def guide():
    """Player's guide page - accessible without authentication."""
    return render_template("guide.html", session=session)


@app.route("/")
def index():
    # Check if user is in onboarding (allow without login for new character creation)
    onboarding_step = session.get("onboarding_step")
    
    # Also check query parameter as fallback if session isn't set yet
    # Only set session if query parameter is explicitly present
    if onboarding_step is None and request.args.get("onboarding") == "start":
        session["onboarding_step"] = 0
        session["onboarding_state"] = {"step": 0, "character": {}}
        session.permanent = True
        session.modified = True
        onboarding_step = 0
    
    # Check explicitly for None - onboarding_step can be 0 (which is falsy but valid)
    # Only show onboarding if we have a valid onboarding step AND user is not logged in
    # OR if user is logged in but has incomplete character
    if onboarding_step is not None and onboarding_step != "complete" and onboarding_step != "":
        # User is in onboarding - show onboarding screen
        from game_engine import ONBOARDING_USERNAME_PROMPT, ONBOARDING_PASSWORD_PROMPT, ONBOARDING_RACE_PROMPT
        
        # Initialize onboarding if needed
        if onboarding_step == 0:
            onboarding_state = {
                "step": 0,
                "character": {}
            }
            session["onboarding_state"] = onboarding_state
            session["onboarding_step"] = 0
            session.permanent = True
            session.modified = True
            log = [ONBOARDING_USERNAME_PROMPT]
        else:
            onboarding_state = session.get("onboarding_state", {"step": 0, "character": {}})
            # Show current step prompt
            current_step = onboarding_state.get("step", 0)
            if current_step == 0:
                log = [ONBOARDING_USERNAME_PROMPT]
            elif current_step == 0.5:
                log = [ONBOARDING_PASSWORD_PROMPT]
            elif current_step == 1:
                log = [ONBOARDING_RACE_PROMPT]
            else:
                log = ["Continue your character creation..."]
        
        processed_log = highlight_exits_in_log(log)
        return render_template("index.html", log=processed_log, session=session, onboarding=True)
    
    # If not logged in and not in onboarding, redirect to welcome
    # Only redirect if we're not in onboarding (onboarding_step is None or "complete")
    if "user_id" not in session:
        # Clear any stale onboarding state if user is not in onboarding
        if onboarding_step is None or onboarding_step == "complete":
            return redirect(url_for("welcome"))
    
    # Track active session when user accesses the game
    if "user_id" in session:
        from datetime import datetime
        username = session.get("username", "adventurer")
        ACTIVE_SESSIONS[username] = {
            "last_activity": datetime.now(),
            "session_id": session.get("session_id", id(session)),
        }
    
    # Ensure game exists (this loads from DB or creates new)
    game = get_game()
    
    # Check if non-admin player is in tavern during locked hours (1am-10am) and eject them
    if game and "user_id" in session:
        from game_engine import is_admin_user, get_current_hour_in_minutes, MINUTES_PER_HOUR, EXIT_STATES
        username = session.get("username", "adventurer")
        
        # Check if player is in tavern
        if game.get("location") == "tavern":
            # Check if door is locked (1am-10am)
            door_state = EXIT_STATES.get("tavern", {}).get("north", {})
            current_minutes = get_current_hour_in_minutes()
            hour_of_day = int(current_minutes // MINUTES_PER_HOUR) % 24
            should_be_locked = (hour_of_day >= 1 and hour_of_day < 10)
            
            # If door should be locked and player is not admin, eject them
            if should_be_locked and not is_admin_user(username, game):
                # Move player to town square
                game["location"] = "town_square"
                
                # Add ejection message from Mara
                ejection_msg = "[CYAN]Mara notices you in the locked tavern and shakes her head. 'Sorry, but the tavern's closed right now! Out you go!' She ushers you out the door to the town square.[/CYAN]"
                game.setdefault("log", [])
                game["log"].append(ejection_msg)
                game["log"] = game["log"][-50:]  # Keep log from growing too large
                
                # Save game state
                save_game(game)
                save_state_to_disk()
                
                # Broadcast to other players in town square
                broadcast_to_room(username, "town_square", f"{username} appears in the town square, looking slightly bewildered after being ejected from the locked tavern.")
    
    # If game exists and user just logged in, add session welcome
    # Check if this is a returning user (game exists but no recent welcome message)
    # Use a session flag to track if we've already added the welcome for this login
    if game and "user_id" in session:
        # Check if we need to add a welcome message
        # Only add if we haven't added it yet this session
        if not session.get("welcome_added"):
            from game_engine import add_session_welcome
            add_session_welcome(game, session.get("username", "adventurer"))
            session["welcome_added"] = True
            save_game(game)
    
    # If no game state and onboarding is complete, create new game
    if game is None:
        # Check if onboarding was just completed
        onboarding_state = session.get("onboarding_state")
        if onboarding_state and onboarding_state.get("step") == 6:
            # Onboarding complete - create game with character
            character = onboarding_state.get("character", {})
            game = new_game_state(username=session.get("username", "adventurer"), character=character)
            ACTIVE_GAMES[session.get("username")] = game
            save_game(game)
            save_state_to_disk()
            
            # Create cinematic entrance
            from game_engine import NPCS, AVAILABLE_RACES, AVAILABLE_BACKSTORIES, describe_location
            from game_engine import get_npcs_in_room
            # Note: broadcast_to_room is defined at module level in app.py, not in game_engine
            
            username_final = session.get("username", "adventurer")
            race_name = AVAILABLE_RACES.get(character.get("race", ""), {}).get("name", "traveler")
            backstory_name = AVAILABLE_BACKSTORIES.get(character.get("backstory", ""), {}).get("name", "mystery")
            
            # Get player's starting location
            loc_id = game.get("location", "town_square")
            
            # Broadcast dramatic entrance to other players in the room
            entrance_message = f"✨ A brilliant flash of light pierces the air, and {username_final} materializes in the center of the square, their form solidifying from ethereal mist. The cycle has brought another soul to Hollowvale. ✨"
            broadcast_to_room(username_final, loc_id, entrance_message)
            
            # Add special Old Storyteller greeting for the new player
            if "old_storyteller" in NPCS:
                storyteller = NPCS["old_storyteller"]
                possessive = getattr(storyteller, 'possessive', 'their')
                greeting = f"The Old Storyteller looks up from {possessive} tales, eyes twinkling with ancient wisdom. '{username_final}... a {race_name} with a {backstory_name.lower()}...' {storyteller.name if hasattr(storyteller, 'name') else 'The Old Storyteller'} smiles warmly. 'Welcome to Hollowvale. Your story is just beginning. The wheel has turned, and you have returned.'"
                game["log"].append(greeting)
            
            # Add location description
            game["log"].append(describe_location(game))
            save_game(game)
            
            # Clear onboarding from session
            session.pop("onboarding_step", None)
            session.pop("onboarding_state", None)
        else:
            # Start onboarding
            session["onboarding_step"] = "start"
            return redirect(url_for("index"))
    
    # For brand new games (just initial welcome messages), add location description
    if len(game.get("log", [])) == 2 and "Type 'look' to see where you are" in game["log"][-1]:
        game["log"].append(describe_location(game))
        save_game(game)
    
    # Initialize last_log_index for new sessions (tracks what we've already sent to client)
    # This ensures that when the page loads showing all log entries, we track that so
    # subsequent commands only return new entries
    if "last_log_index" not in session:
        session["last_log_index"] = len(game.get("log", [])) - 1
        session.modified = True
    
    # Process log to highlight Exits in yellow
    processed_log = highlight_exits_in_log(game["log"])
    # Get color settings for user
    from color_system import get_color_settings
    color_settings = get_color_settings(game) if game else {}
    
    return render_template("index.html", log=processed_log, session=session, onboarding=False, color_settings=color_settings)


# /login route removed - login is now text-based via /welcome screen
# Admin login is available at /admin/login


# Registration is now handled text-based via /welcome screen
# Removed /register route - all registration happens through onboarding flow


@app.route("/logout")
def logout():
    """Logout handler."""
    username = session.get("username")
    
    # Save game state before logout
    if username and username in ACTIVE_GAMES:
        save_game(ACTIVE_GAMES[username])
        save_state_to_disk()
        
        # Broadcast logout notification to all other players (not just those with notify login)
        logout_msg = f"[{username} has logged out.]"
        for uname, g in ACTIVE_GAMES.items():
            if uname != username:
                g.setdefault("log", [])
                g["log"].append(logout_msg)
                g["log"] = g["log"][-50:]
                # Save notification to other players' logs (if they have active sessions)
                try:
                    if uname in ACTIVE_SESSIONS:
                        save_game(g)
                except Exception:
                    pass  # Skip if can't save
        
        # Remove from active games and sessions
        ACTIVE_GAMES.pop(username, None)
        ACTIVE_SESSIONS.pop(username, None)
    
    # Clear welcome flag on logout so it shows again on next login
    session.pop("welcome_added", None)
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("welcome"))


@app.route("/command", methods=["POST"])
def command():
    # Allow commands during onboarding (before login)
    # But also allow normal commands if logged in
    data = request.get_json() or {}
    cmd = data.get("command", "")
    username = session.get("username", "adventurer")
    user_id = session.get("user_id")
    
    # Check if user is in onboarding (for new character creation - may not be logged in yet)
    # IMPORTANT: Do this BEFORE checking for user_id/login, as users aren't logged in during onboarding
    # But also IMPORTANT: Skip onboarding check if user is logged in (onboarding should be complete)
    onboarding_step = session.get("onboarding_step")
    onboarding_state = session.get("onboarding_state")
    
    # If user is logged in, clear any stale onboarding state (onboarding should be complete)
    if user_id and (onboarding_step or onboarding_state):
        if onboarding_step != "complete":
            logging.info(f"Clearing stale onboarding state for logged-in user {username}")
            session.pop("onboarding_step", None)
            session.pop("onboarding_state", None)
            session.modified = True
            onboarding_step = None
            onboarding_state = None
    
    # Debug: Log session state to help diagnose issues
    import logging
    logging.info(f"Command route - cmd: '{cmd}', onboarding_step: {onboarding_step}, onboarding_state exists: {onboarding_state is not None}, user_id: {user_id}, session keys: {list(session.keys())}, referer: {request.headers.get('Referer', '')}")
    
    # Fallback 1: if onboarding_state exists but onboarding_step doesn't, infer onboarding_step from state
    # But only if user is not logged in
    if onboarding_step is None and onboarding_state and not user_id:
        step = onboarding_state.get("step")
        if step is not None:
            onboarding_step = step
            session["onboarding_step"] = step
            session.modified = True
            logging.info(f"Inferred onboarding_step from state: {onboarding_step}")
    
    # Fallback 2: Check referer URL for onboarding parameter (if session cookie wasn't sent)
    if onboarding_step is None and not user_id:
        referer = request.headers.get("Referer", "")
        if "onboarding=start" in referer:
            logging.info("Detected onboarding from Referer header, initializing session")
            session["onboarding_step"] = 0
            session["onboarding_state"] = {"step": 0, "character": {}}
            session.permanent = True
            session.modified = True
            onboarding_step = 0
            onboarding_state = session["onboarding_state"]
    
    # Fallback 3: Also check query parameter as fallback if session isn't set yet (for GET requests)
    if onboarding_step is None and request.args.get("onboarding") == "start":
        session["onboarding_step"] = 0
        session["onboarding_state"] = {"step": 0, "character": {}}
        session.permanent = True
        session.modified = True
        onboarding_step = 0
        onboarding_state = session["onboarding_state"]
        logging.info("Initialized onboarding from query parameter")
    
    # If in onboarding, handle onboarding commands (user may not be logged in yet)
    # Check explicitly for None - onboarding_step can be 0 (which is falsy but valid)
    if onboarding_step is not None and onboarding_step != "complete" and onboarding_step != "":
        logging.info(f"Processing onboarding command at step {onboarding_step} for command: '{cmd}'")
        # Handle onboarding commands for new character creation
        from game_engine import handle_onboarding_command
        
        # Get onboarding state from session (already retrieved above, but may need to refresh)
        onboarding_state = session.get("onboarding_state", {"step": onboarding_step if onboarding_step is not None else (0 if not user_id else 1), "character": {}})
        
        # Get database connection for account creation (if not logged in) or character updates
        conn = get_db()
        
        # Process onboarding command
        # If user is logged in but in onboarding, they're completing character creation (skip username/password)
        onboarding_username = username if user_id else None
        response, updated_state, is_complete, created_user_id = handle_onboarding_command(
            cmd, onboarding_state, username=onboarding_username, db_conn=conn
        )
        session["onboarding_state"] = updated_state
        
        # Prepare response log - handle pause markers in onboarding messages
        log = [response] if isinstance(response, str) else response
        processed_log = highlight_exits_in_log(log)
        
        if is_complete:
            # Account was created during onboarding
            if created_user_id:
                session["user_id"] = created_user_id
                session["username"] = updated_state.get("username", "adventurer")
                username = session["username"]
                user_id = created_user_id
            
            # Clear onboarding state completely after completion
            session.pop("onboarding_step", None)
            session.pop("onboarding_state", None)
            session.modified = True
            # Create game state with character
            character = updated_state.get("character", {})
            game = new_game_state(username=username, character=character)
            ACTIVE_GAMES[username] = game
            save_game(game)
            save_state_to_disk()
            
            # Create cinematic entrance
            from game_engine import NPCS, AVAILABLE_RACES, AVAILABLE_BACKSTORIES, describe_location
            
            race_name = AVAILABLE_RACES.get(character.get("race", ""), {}).get("name", "traveler")
            backstory_name = AVAILABLE_BACKSTORIES.get(character.get("backstory", ""), {}).get("name", "mystery")
            
            # Get player's starting location
            loc_id = game.get("location", "town_square")
            
            # Broadcast dramatic entrance to other players in the room
            entrance_message = f"✨ A brilliant flash of light pierces the air, and {username} materializes in the center of the square, their form solidifying from ethereal mist. The cycle has brought another soul to Hollowvale. ✨"
            broadcast_to_room(username, loc_id, entrance_message)
            
            # Add special Old Storyteller greeting for the new player
            if "old_storyteller" in NPCS:
                storyteller = NPCS["old_storyteller"]
                possessive = getattr(storyteller, 'possessive', 'their')
                storyteller_name = storyteller.name if hasattr(storyteller, 'name') else 'The Old Storyteller'
                greeting = f"The Old Storyteller looks up from {possessive} tales, eyes twinkling with ancient wisdom. '{username}... a {race_name} with a {backstory_name.lower()}...' {storyteller_name} smiles warmly. 'Welcome to Hollowvale. Your story is just beginning. The wheel has turned, and you have returned.'"
                game["log"].append(greeting)
            
            # Add location description
            game["log"].append(describe_location(game))
            save_game(game)
            
            # Return completion message with pauses as a single string for frontend processing
            # Only include the response and new game log entries, not the entire history
            # The response already contains the pause markers, which the frontend will process
            # Don't include game["log"] here as it would duplicate messages and include pause markers
            log = [response]
            conn.close()
        else:
            # Return onboarding response as a string (with pause markers) for frontend processing
            log = [response]
            conn.close()
        
        # For onboarding messages with pause markers, return as single string for frontend processing
        # Frontend will handle the pause markers and display progressively
        if isinstance(log, list) and len(log) == 1 and isinstance(log[0], str) and ('[PAUSE:' in log[0] or '[ELLIPSIS:' in log[0]):
            # Return as single string for pause processing
            processed_log = log[0]
        else:
            processed_log = highlight_exits_in_log(log)
        # Ensure session is saved before returning
        session.modified = True
        # Get color settings for user (if logged in)
        color_settings = {}
        if user_id and game:
            from color_system import get_color_settings
            color_settings = get_color_settings(game)
        
        # Return onboarding status (False if complete, True if still in progress)
        return jsonify({"response": response, "log": processed_log, "onboarding": not is_complete, "color_settings": color_settings})
    
    # Normal game command handling - require authentication
    # Log why we're requiring login (for debugging)
    if not user_id:
        logging.warning(f"Command '{cmd}' rejected - no user_id in session. Session keys: {list(session.keys())}")
        return jsonify({"response": "Please login first.", "log": ["Please login first."], "onboarding": False})
    
    game = get_game()
    if game is None:
        # No game state - check if character exists, if not start onboarding (skip username/password)
        session["onboarding_step"] = 1
        session["onboarding_state"] = {"step": 1, "character": {}}
        from game_engine import ONBOARDING_RACE_PROMPT
        log = [ONBOARDING_RACE_PROMPT]
        processed_log = highlight_exits_in_log(log)
        return jsonify({"response": "Please complete character creation first.", "log": processed_log, "onboarding": True})
    
    # Create broadcast function for this user
    # Import broadcast_to_room at module level and reference it directly
    # to avoid closure issues - it's already defined at module level
    def broadcast_fn(room_id, text):
        broadcast_to_room(username, room_id, text)
    
    # Get database connection for AI token tracking
    conn = get_db()
    try:
        try:
            response, game = handle_command(
                cmd,
                game,
                username=username,
                user_id=user_id,
                db_conn=conn,
                broadcast_fn=broadcast_fn,
                who_fn=list_active_players,
            )
            
            # Check for sunrise/sunset transitions and bell tolling
            from game_engine import check_sunrise_sunset_transitions, check_bell_tolling
            
            # Filter broadcast function to only notify players with notify time on (for sunrise/sunset)
            def filtered_broadcast_fn(room_id, text):
                for uname, g in ACTIVE_GAMES.items():
                    if g.get("location") == room_id:
                        notify_cfg = g.get("notify", {})
                        if notify_cfg.get("time", False):
                            g.setdefault("log", [])
                            g["log"].append(text)
                            g["log"] = g["log"][-50:]
            
            # Check sunrise/sunset (only for players with notify time on)
            check_sunrise_sunset_transitions(
                broadcast_fn=filtered_broadcast_fn,
                who_fn=list_active_players
            )
            
            # Check bell tolling (always broadcasts to all players, no notify filter needed)
            check_bell_tolling(
                broadcast_fn=broadcast_fn,
                who_fn=list_active_players
            )
            
            # NPC periodic actions are now handled automatically in handle_command
            # via process_npc_periodic_actions() which shows accumulated actions
            # based on elapsed time since last action
            
            # If description was updated, save it to database immediately
            if "user_description" in game:
                conn.execute(
                    "UPDATE users SET description = ? WHERE id = ?",
                    (game["user_description"], user_id)
                )
                conn.commit()
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Error handling command '{cmd}': {e}")
            print(traceback.format_exc())
            
            # Return a user-friendly error message
            game.setdefault("log", [])
            error_msg = f"An error occurred while processing your command. Please try again."
            game["log"].append(error_msg)
            game["log"] = game["log"][-50:]
            response = error_msg
            save_game(game)
            save_state_to_disk()
            processed_log = highlight_exits_in_log(game["log"])
            return jsonify({"response": response, "log": processed_log}), 200
    finally:
        conn.close()
    
    # Check if user confirmed logout
    if response == "__LOGOUT__":
        # Save game state before logout
        save_game(game)
        save_state_to_disk()
        
        # Broadcast logout notification to all other players (not just those with notify login)
        logout_msg = f"[{username} has logged out.]"
        for uname, g in ACTIVE_GAMES.items():
            if uname != username:
                g.setdefault("log", [])
                g["log"].append(logout_msg)
                g["log"] = g["log"][-50:]
                # Save notification to other players' logs
                try:
                    if uname in ACTIVE_SESSIONS:
                        save_game(g)
                except Exception:
                    pass  # Skip if can't save
        
        # Remove this user from ACTIVE_GAMES and ACTIVE_SESSIONS
        ACTIVE_GAMES.pop(username, None)
        ACTIVE_SESSIONS.pop(username, None)
        
        # Return special response to trigger logout on client
        return jsonify({"logout": True, "message": "You have logged out.", "log": []})
    
    save_game(game)
    save_state_to_disk()
    
    # Only return NEW log messages from this command, not the entire log history
    # Track the last log index we've sent to this client
    # IMPORTANT: Get log length AFTER save_game() to ensure we have the latest log state
    session.setdefault("last_log_index", -1)
    last_log_index = session.get("last_log_index", -1)
    
    # Reload game state to ensure we have the latest log after save
    game = get_game()
    current_log = game.get("log", [])
    current_log_length = len(current_log)
    
    # If last_log_index is beyond the current log length (due to log truncation), reset it
    # Log is truncated to last 50 entries, so we need to account for that
    if last_log_index >= current_log_length:
        # Log was truncated - start from beginning of current log
        last_log_index = -1
    
    # Get new log entries (everything after last_log_index)
    # Use >= instead of < to ensure we include entries even when index is exactly at the boundary
    if last_log_index + 1 <= current_log_length:
        new_log_entries = current_log[last_log_index + 1:]
    else:
        new_log_entries = []
    
    # If no new entries but there are log entries, check if we need to reset the index
    # This handles the case where the log was truncated or reloaded
    if len(new_log_entries) == 0 and current_log_length > 0:
        # If last_log_index points beyond current log, reset it
        if last_log_index >= current_log_length:
            # Return the last few entries as a fallback
            new_log_entries = current_log[-3:] if current_log_length >= 3 else current_log
            last_log_index = current_log_length - len(new_log_entries) - 1
    
    # Always update the last log index to point to the end of current log
    # This ensures we track what we've sent, even if there were no new entries
    session["last_log_index"] = current_log_length - 1
    session.modified = True
    
    # Process only new log entries to highlight Exits in yellow
    processed_log = highlight_exits_in_log(new_log_entries) if new_log_entries else []
    
    # Debug logging (can remove later)
    import logging
    logging.info(f"Command '{cmd}': last_log_index={last_log_index}, current_log_length={current_log_length}, new_entries={len(new_log_entries)}, response_length={len(response) if response else 0}")
    if len(new_log_entries) == 0:
        logging.warning(f"No new log entries for command '{cmd}'! Log content (last 3): {current_log[-3:] if len(current_log) >= 3 else current_log}")
    
    # Get color settings for user
    from color_system import get_color_settings
    color_settings = get_color_settings(game)
    
    return jsonify({"response": response, "log": processed_log, "color_settings": color_settings})


# Track last poll timestamp per player for ambiance/NPC messages
# Format: {username: {"last_ambiance_time": datetime, "last_npc_action_time": datetime}}
LAST_POLL_STATE = {}


@app.route("/poll", methods=["POST"])
@require_auth
def poll_updates():
    """
    Poll endpoint for real-time ambiance and NPC action updates.
    Returns new messages that have appeared since last poll.
    Messages appear automatically based on elapsed real-world time.
    """
    import logging
    logging.info("Poll endpoint called")
    
    username = session.get("username")
    user_id = session.get("user_id")
    
    logging.info(f"Poll request from user: {username}, user_id: {user_id}")
    
    if not username or not user_id:
        logging.warning("Poll request without username or user_id")
        return jsonify({"messages": []})
    
    game = get_game()
    if not game:
        logging.warning(f"Poll request but no game state for {username}")
        return jsonify({"messages": []})
    
    # Update session activity
    from datetime import datetime, timedelta
    ACTIVE_SESSIONS[username] = {
        "last_activity": datetime.now(),
        "session_id": session.get("session_id", id(session)),
    }
    
    # Create broadcast function for this user
    def broadcast_fn(room_id, text):
        broadcast_to_room(username, room_id, text)
    
    # Get current game time
    from game_engine import get_current_game_tick, update_weather_if_needed
    from game_engine import update_player_weather_status, update_npc_weather_statuses
    from game_engine import cleanup_buried_items, process_time_based_exit_states
    from game_engine import process_npc_movements
    import ambiance
    
    current_tick = get_current_game_tick()
    current_time = datetime.now()
    
    # Update weather/player status (but don't accumulate messages)
    update_weather_if_needed()
    update_player_weather_status(game)
    update_npc_weather_statuses()
    cleanup_buried_items()
    
    # Process time-based exit states
    process_time_based_exit_states(broadcast_fn=broadcast_fn, who_fn=list_active_players)
    
    # Process NPC movements
    process_npc_movements(broadcast_fn=broadcast_fn)
    
    # Initialize poll state if needed
    if username not in LAST_POLL_STATE:
        LAST_POLL_STATE[username] = {
            "last_ambiance_time": current_time,
            "last_npc_action_time": current_time,
        }
    
    poll_state = LAST_POLL_STATE[username]
    new_messages = []
    current_room = game.get("location", "town_square")
    
    # Check for NPC actions - use configurable interval from settings
    npc_interval_min = float(get_game_setting("npc_action_interval_min", "30"))
    npc_interval_max = float(get_game_setting("npc_action_interval_max", "60"))
    
    last_npc_time = poll_state.get("last_npc_action_time", current_time)
    elapsed_npc_seconds = (current_time - last_npc_time).total_seconds()
    
    # NPC actions at configurable interval
    if elapsed_npc_seconds >= npc_interval_min:
        from game_engine import get_npcs_in_room
        from npc_actions import get_all_npc_actions_for_room
        
        npc_ids = get_npcs_in_room(current_room)
        if npc_ids:
            npc_actions = get_all_npc_actions_for_room(current_room, game=game, active_players_fn=list_active_players)
            if npc_actions:
                # Show one random NPC action
                npc_id, action = random.choice(list(npc_actions.items()))
                action_text = f"[NPC]{action}[/NPC]"
                new_messages.append(action_text)
                
                # Broadcast to other players in the room
                broadcast_fn(current_room, action_text)
                
                # Update last NPC action time (randomize interval between min and max)
                next_interval = random.uniform(npc_interval_min, npc_interval_max)
                poll_state["last_npc_action_time"] = current_time - timedelta(seconds=elapsed_npc_seconds - next_interval)
    
    # Check for ambiance messages - use configurable interval from settings
    ambiance_interval_min = float(get_game_setting("ambiance_interval_min", "120"))
    ambiance_interval_max = float(get_game_setting("ambiance_interval_max", "240"))
    
    last_ambiance_time = poll_state.get("last_ambiance_time", current_time)
    elapsed_ambiance_seconds = (current_time - last_ambiance_time).total_seconds()
    
    # Ambiance at configurable interval
    if elapsed_ambiance_seconds >= ambiance_interval_min:
        # Generate one ambiance message
        ambiance_msg = ambiance.process_room_ambiance(game, broadcast_fn=broadcast_fn)
        if ambiance_msg and len(ambiance_msg) > 0:
            new_messages.append(ambiance_msg[0])  # process_room_ambiance returns a list
            
            # Update last ambiance time (randomize interval between min and max)
            next_interval = random.uniform(ambiance_interval_min, ambiance_interval_max)
            poll_state["last_ambiance_time"] = current_time - timedelta(seconds=elapsed_ambiance_seconds - next_interval)
    
    # Add new messages to game log
    if new_messages:
        game.setdefault("log", [])
        for msg in new_messages:
            game["log"].append(msg)
        game["log"] = game["log"][-50:]
        
        # Save game state
        save_game(game)
        save_state_to_disk()
    
    # Process messages for display
    processed_messages = highlight_exits_in_log(new_messages) if new_messages else []
    
    import logging
    if processed_messages:
        logging.info(f"Poll returning {len(processed_messages)} messages to {username}")
    else:
        logging.debug(f"Poll returning no messages for {username} (elapsed_npc={elapsed_npc_seconds:.1f}s, elapsed_ambiance={elapsed_ambiance_seconds:.1f}s)")
    
    return jsonify({"messages": processed_messages})


def require_admin(f):
    """Decorator to require admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("You must be logged in to access this page.", "error")
            return redirect(url_for("welcome"))
        
        username = session.get("username")
        
        # Check environment variable first (ADMIN_USERS)
        admin_users = set(os.environ.get("ADMIN_USERS", "admin,tezbo").split(","))
        if username and username.lower() in {u.lower().strip() for u in admin_users}:
            return f(*args, **kwargs)
        
        # Check database is_admin field
        conn = get_db()
        user = conn.execute(
            "SELECT is_admin FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()
        conn.close()
        
        if not user or not user["is_admin"]:
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("welcome"))
        
        return f(*args, **kwargs)
    return decorated_function


@app.route("/admin")
@require_admin
def admin_dashboard():
    """Admin dashboard for monitoring AI usage."""
    # Import here to avoid circular imports
    try:
        from ai_client import _token_usage, _user_token_usage, _response_cache
    except ImportError:
        _token_usage = {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "requests": 0, "last_reset": "Never"}
        _user_token_usage = {}
        _response_cache = {}
    
    conn = get_db()
    
    # Get overall statistics
    total_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
    total_ai_users = conn.execute("SELECT COUNT(*) as count FROM ai_usage").fetchone()["count"]
    
    # Get per-user usage from database
    user_usage = conn.execute(
        """
        SELECT u.id, u.username, 
               COALESCE(a.token_budget, 10000) as token_budget,
               COALESCE(a.tokens_used, 0) as tokens_used,
               COALESCE(a.requests_count, 0) as requests_count,
               a.last_reset
        FROM users u
        LEFT JOIN ai_usage a ON u.id = a.user_id
        ORDER BY a.tokens_used DESC
        """
    ).fetchall()
    
    # Get rate limit statistics
    rate_limit_stats = conn.execute(
        """
        SELECT user_id, COUNT(*) as request_count
        FROM ai_rate_limits
        WHERE request_time > datetime('now', '-1 hour')
        GROUP BY user_id
        """
    ).fetchall()
    
    rate_limit_map = {row["user_id"]: row["request_count"] for row in rate_limit_stats}
    
    # Global token usage
    global_usage = _token_usage.copy()
    
    # Cache statistics
    cache_size = len(_response_cache)
    from datetime import datetime, timedelta
    cache_hits = sum(1 for entry in _response_cache.values() 
                     if datetime.now() - entry["timestamp"] < timedelta(hours=24))
    
    conn.close()
    
    # Get default token budget from environment variable
    default_budget = int(os.environ.get("AI_DEFAULT_TOKEN_BUDGET", "10000"))
    
    return render_template(
        "admin.html",
        total_users=total_users,
        total_ai_users=total_ai_users,
        user_usage=user_usage,
        rate_limit_map=rate_limit_map,
        global_usage=global_usage,
        cache_size=cache_size,
        cache_hits=cache_hits,
        max_requests_per_hour=os.environ.get("AI_MAX_REQUESTS_PER_HOUR", "60"),
        default_budget=default_budget,
    )


@app.route("/admin/set_budget", methods=["POST"])
@require_admin
def set_budget():
    """Set token budget for a user."""
    data = request.get_json() or {}
    user_id = data.get("user_id")
    budget = data.get("budget")
    
    if not user_id or budget is None:
        return jsonify({"error": "Missing user_id or budget"}), 400
    
    try:
        budget = int(budget)
        if budget < 0:
            return jsonify({"error": "Budget must be non-negative"}), 400
    except ValueError:
        return jsonify({"error": "Budget must be an integer"}), 400
    
    conn = get_db()
    conn.execute(
        """
        INSERT INTO ai_usage (user_id, token_budget, tokens_used)
        VALUES (?, ?, 0)
        ON CONFLICT(user_id) DO UPDATE SET token_budget = ?
        """,
        (user_id, budget, budget)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Budget set to {budget} tokens"})


@app.route("/admin/reset_usage", methods=["POST"])
@require_admin
def reset_usage():
    """Reset token usage for a user."""
    data = request.get_json() or {}
    user_id = data.get("user_id")
    
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    
    conn = get_db()
    conn.execute(
        """
        UPDATE ai_usage 
        SET tokens_used = 0, requests_count = 0, last_reset = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """,
        (user_id,)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Usage reset successfully"})


@app.route("/admin/set_default_budget", methods=["POST"])
@require_admin
def set_default_budget():
    """Set default token budget for all users without a budget."""
    data = request.get_json() or {}
    budget = data.get("budget")
    
    if budget is None:
        return jsonify({"error": "Missing budget"}), 400
    
    try:
        budget = int(budget)
        if budget < 0:
            return jsonify({"error": "Budget must be non-negative"}), 400
    except ValueError:
        return jsonify({"error": "Budget must be an integer"}), 400
    
    conn = get_db()
    
    # Update all users without a budget set
    conn.execute(
        """
        INSERT INTO ai_usage (user_id, token_budget, tokens_used)
        SELECT id, ?, 0
        FROM users
        WHERE id NOT IN (SELECT user_id FROM ai_usage)
        """,
        (budget,)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Default budget of {budget} tokens applied to all users without budgets"})


if __name__ == "__main__":
    # For local development
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)