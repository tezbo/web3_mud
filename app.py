# CRITICAL: Apply eventlet monkey patching BEFORE any socket-related imports
# This must be done first to patch the standard library for eventlet compatibility
# Required when using eventlet workers or SocketIO with async_mode='eventlet'
import os
try:
    import eventlet
    eventlet.monkey_patch()
except ImportError:
    pass  # eventlet not available, will use sync mode

import json
import sqlite3
import random
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

# Set up logging with timestamps
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from game_engine import (
    new_game_state,
    describe_location,
    handle_command,
    highlight_exits_in_log,
    add_session_welcome,
    get_global_state_snapshot,
    load_global_state_snapshot,
    handle_onboarding_command,
    ONBOARDING_USERNAME_PROMPT,
    ONBOARDING_PASSWORD_PROMPT,
    ONBOARDING_RACE_PROMPT,
    is_admin_user,
    get_current_hour_in_minutes,
    MINUTES_PER_HOUR,
    EXIT_STATES,
    NPCS,
    AVAILABLE_RACES,
    AVAILABLE_BACKSTORIES,
    get_npcs_in_room,
    get_current_game_tick,
    update_player_weather_status,
    process_npc_movements,
)
import ambiance
from core.state_manager import get_state_manager
from core.socketio_handlers import register_socketio_handlers
from game.systems.atmospheric_manager import get_atmospheric_manager
from core.redis_manager import test_redis_connection

app = Flask(__name__)

# Use an environment variable if available (better for real deployments)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
# Configure session cookie settings for better persistence
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours

# Initialize Flask-SocketIO with Redis adapter for multi-instance scaling
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Check if Redis is actually available
use_redis = False
if REDIS_URL:
    try:
        if test_redis_connection():
            use_redis = True
            logger.info(f"Redis connection successful, using Redis for SocketIO message queue: {REDIS_URL}")
        else:
            logger.warning("Redis connection failed, falling back to in-memory SocketIO")
    except Exception as e:
        logger.warning(f"Error checking Redis connection: {e}, falling back to in-memory SocketIO")

try:
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        message_queue=REDIS_URL if use_redis else None,
        async_mode='eventlet',
        logger=True,
        engineio_logger=False,
    )
except Exception as e:
    logger.warning(f"Error initializing SocketIO with Redis: {e}")
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,
        engineio_logger=False,
    )

# Database setup
PERSISTENT_DISK_PATH = os.environ.get("PERSISTENT_DISK_PATH")
if PERSISTENT_DISK_PATH:
    os.makedirs(PERSISTENT_DISK_PATH, exist_ok=True)
    DATABASE = os.path.join(PERSISTENT_DISK_PATH, "users.db")
    STATE_FILE = os.path.join(PERSISTENT_DISK_PATH, "mud_state.json")
else:
    DATABASE = "users.db"
    STATE_FILE = os.path.join(os.path.dirname(__file__), "mud_state.json")


def init_db() -> None:
    """Initialize the database with users and games tables."""
    with sqlite3.connect(DATABASE) as conn:
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
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_rate_limit_user_time 
            ON ai_rate_limits(user_id, request_time)
            """
        )
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
        
        # Initialize default settings
        default_settings = {
            "npc_action_interval_min": ("30", "Minimum seconds between NPC actions (real-world time)"),
            "npc_action_interval_max": ("60", "Maximum seconds between NPC actions (real-world time)"),
            "ambiance_interval_min": ("120", "Minimum seconds between ambiance messages (real-world time)"),
            "ambiance_interval_max": ("240", "Maximum seconds between ambiance messages (real-world time)"),
            "weather_ambiance_interval_min": ("90", "Minimum seconds between weather ambiance messages (real-world time)"),
            "weather_ambiance_interval_max": ("180", "Maximum seconds between weather ambiance messages (real-world time)"),
            "poll_interval": ("3", "Client polling interval in seconds"),
        }
        
        for key, (default_value, description) in default_settings.items():
            cursor.execute(
                "INSERT OR IGNORE INTO game_settings (key, value, description) VALUES (?, ?, ?)",
                (key, default_value, description)
            )
        
        conn.commit()

init_db()

def get_db() -> sqlite3.Connection:
    """Get database connection with WAL mode enabled for better concurrency."""
    conn = sqlite3.connect(DATABASE, timeout=10.0)  # 10 second timeout
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency (allows reads during writes)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

# --- Game Settings Management ---

def get_game_setting(key, default=None):
    """Get a game setting value from the database."""
    conn = get_db()
    try:
        row = conn.execute("SELECT value FROM game_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default
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
        rows = conn.execute("SELECT key, value, description FROM game_settings ORDER BY key").fetchall()
        return {row["key"]: {"value": row["value"], "description": row["description"]} for row in rows}
    finally:
        conn.close()

# --- State Management ---

ACTIVE_GAMES = {}
ACTIVE_SESSIONS = {}

def load_state_from_disk():
    """Load ACTIVE_GAMES and global state from disk."""
    global ACTIVE_GAMES
    if not os.path.exists(STATE_FILE):
        return
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "players" in data and isinstance(data["players"], dict):
            ACTIVE_GAMES = data["players"]
        if "global_state" in data:
            load_global_state_snapshot(data["global_state"])
    except Exception as e:
        print(f"Error loading state from disk: {e}")

def save_state_to_disk():
    """Save ACTIVE_GAMES and global state to disk."""
    try:
        cleaned_games = {}
        for username, game in ACTIVE_GAMES.items():
            cleaned_game = {k: v for k, v in game.items() if not k.startswith("_")}
            cleaned_games[username] = cleaned_game
        
        data = {
            "players": cleaned_games,
            "global_state": get_global_state_snapshot(),
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving state to disk: {e}")

load_state_from_disk()

def broadcast_to_room(sender_username, room_id, text):
    """Broadcast a message to all other players in the same room."""
    # Update logs for polling clients
    for uname, g in ACTIVE_GAMES.items():
        if uname == sender_username:
            continue
        if g.get("location") == room_id:
            g.setdefault("log", [])
            g["log"].append(text)
            g["log"] = g["log"][-50:]
    
    # Emit via SocketIO for real-time clients
    try:
        socketio.emit('room_message', {
            'room_id': room_id,
            'message': text,
            'message_type': 'system'
        }, room=f"room:{room_id}", skip_sid=None) # We don't have SID here easily, so might duplicate if sender is on socket
    except Exception:
        pass

def cleanup_stale_sessions():
    """Remove stale sessions and clean up ACTIVE_GAMES."""
    global ACTIVE_GAMES, ACTIVE_SESSIONS
    cutoff_time = datetime.now() - timedelta(minutes=15)
    stale_usernames = [u for u, s in ACTIVE_SESSIONS.items() if not s.get("last_activity") or s.get("last_activity") < cutoff_time]
    
    for username in stale_usernames:
        if username in ACTIVE_GAMES:
            game = ACTIVE_GAMES[username]
            save_game(game)
            # Notify others
            logout_msg = f"[{username} has been logged out automatically for being idle too long.]"
            broadcast_to_room(username, game.get("location"), logout_msg)
            ACTIVE_GAMES.pop(username, None)
        ACTIVE_SESSIONS.pop(username, None)

def list_active_players():
    """Return a list of dicts with active player information."""
    cleanup_stale_sessions()
    data = []
    seen_usernames = set()
    cutoff_time = datetime.now() - timedelta(minutes=10)
    
    for uname, g in ACTIVE_GAMES.items():
        if uname in seen_usernames:
            continue
        seen_usernames.add(uname)
        session_info = ACTIVE_SESSIONS.get(uname)
        if session_info and session_info.get("last_activity", datetime.min) >= cutoff_time:
            data.append({"username": uname, "location": g.get("location", "town_square")})
    return data

def require_auth(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("welcome"))
        return f(*args, **kwargs)
    return decorated_function

# --- Database Layer Helpers ---

def _db_get_game_state(username):
    conn = get_db()
    try:
        user_row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not user_row: return None
        game_row = conn.execute("SELECT game_state FROM games WHERE user_id = ?", (user_row["id"],)).fetchone()
        return json.loads(game_row["game_state"]) if game_row else None
    finally:
        conn.close()

def _db_save_game_state(username, game_state):
    conn = get_db()
    try:
        user_row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not user_row: return
        conn.execute(
            """
            INSERT INTO games (user_id, game_state, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                game_state = excluded.game_state,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_row["id"], json.dumps(game_state))
        )
        conn.commit()
    finally:
        conn.close()

_state_manager_instance = None
def get_state_manager_instance():
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = get_state_manager(db_get_fn=_db_get_game_state, db_save_fn=_db_save_game_state)
    return _state_manager_instance

def get_game():
    """Get or create the game state for the current user."""
    user_id = session.get("user_id")
    username = session.get("username", "adventurer")
    
    if not user_id:
        return new_game_state(username)
    
    # Check legacy cache first
    if username in ACTIVE_GAMES and username in ACTIVE_SESSIONS:
        return ACTIVE_GAMES[username]
    
    # Try StateManager
    try:
        state_manager = get_state_manager_instance()
        cached_game = state_manager.get_player_state(username, use_cache=True)
        if cached_game and username in ACTIVE_SESSIONS:
            ACTIVE_GAMES[username] = cached_game
            return cached_game
    except Exception as e:
        logger.warning(f"Error getting game state from StateManager: {e}")
    
    # Fallback to DB
    conn = get_db()
    row = conn.execute("SELECT game_state FROM games WHERE user_id = ?", (user_id,)).fetchone()
    
    if row:
        try:
            game = json.loads(row["game_state"])
            # Validate game state
            if not isinstance(game, dict) or "location" not in game:
                conn.close()
                if not game.get("character"): return None
                game = new_game_state(username)
                ACTIVE_GAMES[username] = game
                save_game(game)
                return game
            
            # Check character
            character = game.get("character")
            if character and isinstance(character, dict) and not character.get("race"):
                conn.close()
                return None # Needs onboarding
            
            # Load description
            user_row = conn.execute("SELECT description FROM users WHERE id = ?", (user_id,)).fetchone()
            conn.close()
            if user_row and user_row["description"]:
                game["user_description"] = user_row["description"]
            
            game["username"] = username
            from economy import initialize_player_gold
            initialize_player_gold(game)
            game.setdefault("notify", {"login": False})
            
            # Save to cache
            try:
                state_manager = get_state_manager_instance()
                state_manager.save_player_state(username, game, sync_to_db=False, use_cache=True)
            except Exception: pass
            
            ACTIVE_GAMES[username] = game
            save_state_to_disk()
            return game
        except Exception:
            conn.close()
            return None
    else:
        conn.close()
        return None

def save_game(game):
    """Save the game state."""
    # Get username from game state first (works in background tasks)
    # Fall back to session if available (works in request context)
    username = game.get("username")
    if not username:
        try:
            username = session.get("username", "adventurer")
        except RuntimeError:
            # No request context (background task) - can't save without username
            return
    
    # Get user_id from game state or session
    user_id = game.get("user_id")
    if not user_id:
        try:
            user_id = session.get("user_id")
        except RuntimeError:
            # No request context - try to continue without user_id for in-memory save
            pass
    
    if not username: return
    
    ACTIVE_GAMES[username] = game
    
    try:
        state_manager = get_state_manager_instance()
        # Only sync to DB if we have user_id (i.e., we're in a request context)
        # In background tasks, just update in-memory cache
        sync_to_db = bool(user_id)
        state_manager.save_player_state(username, game, sync_to_db=sync_to_db, use_cache=True)
        
        # Update Redis location
        if "location" in game:
            from core.redis_manager import CacheKeys, set_cached_state
            room_id = game["location"]
            set_cached_state(CacheKeys.player_location(username), room_id, ttl=900)
            
            cache = state_manager._cache
            if cache:
                old_location_key = f"player:{username}:location"
                old_room_id = cache.get(old_location_key)
                if old_room_id and old_room_id != room_id:
                    cache.srem(CacheKeys.room_players(old_room_id), username)
                cache.sadd(CacheKeys.room_players(room_id), username)
    except Exception as e:
        logger.warning(f"Error saving via StateManager: {e}")
        # DB Fallback - use single connection for all updates to avoid locking
        conn = get_db()
        try:
            conn.execute(
                """
                INSERT INTO games (user_id, game_state, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    game_state = excluded.game_state,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, json.dumps(game))
            )
            
            # Update user description in the same transaction
            if "user_description" in game:
                conn.execute("UPDATE users SET description = ? WHERE id = ?", (game["user_description"], user_id))
            
            conn.commit()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                logger.warning(f"Database locked when saving game for {username}, will retry on next save")
                conn.rollback()
            else:
                raise
        finally:
            conn.close()

# --- Routes ---

@app.route("/api/agent_status_legacy")
def api_agent_status():
    status_file = os.path.join("agents", "agent_status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, "r") as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({"error": str(e)})
    return jsonify({})

@app.route("/welcome")
def welcome():
    if "onboarding_step" in session:
        session.pop("onboarding_step", None)
        session.pop("onboarding_state", None)
        session.modified = True
    
    if "user_id" in session and "username" in session:
        if session.get("username") in ACTIVE_SESSIONS:
            return redirect(url_for("index"))
        else:
            session.clear()
            session.modified = True
            
    return render_template("welcome.html")

@app.route("/welcome_command", methods=["POST"])
def welcome_command():
    if "user_id" in session:
        return jsonify({"redirect": url_for("index")})
    
    data = request.get_json() or {}
    cmd = data.get("command", "").strip()
    cmd_upper = cmd.upper()
    
    if cmd_upper == "Q":
        return jsonify({"message": "Type N to create a new character, L to login, or G for the guide."})
    elif cmd_upper == "G":
        return jsonify({"redirect": url_for("guide")})
    elif cmd_upper == "N":
        session["onboarding_step"] = 0
        session["onboarding_state"] = {"step": 0, "character": {}}
        session.permanent = True
        session.modified = True
        return jsonify({"message": "Starting character creation...", "redirect": "/?onboarding=start", "delay": 300})
    elif cmd_upper == "L":
        session["login_step"] = "username"
        return jsonify({"message": "Enter your username:"})
    else:
        login_step = session.get("login_step")
        if login_step == "username":
            if not cmd: return jsonify({"message": "Please enter your username:"})
            session["login_username"] = cmd
            session["login_step"] = "password"
            return jsonify({"message": f"Enter password for {cmd}:"})
        elif login_step == "password":
            password = cmd
            username = session.get("login_username", "")
            if not password: return jsonify({"message": f"Enter password for {username}:"})
            
            conn = get_db()
            user = conn.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,)).fetchone()
            conn.close()
            
            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session.pop("login_step", None)
                session.pop("login_username", None)
                
                # Cleanup disconnected players
                try:
                    from core.socketio_handlers import DISCONNECTED_PLAYERS
                    if user["username"] in DISCONNECTED_PLAYERS:
                        DISCONNECTED_PLAYERS.pop(user["username"])
                except Exception: pass
                
                # Cleanup stale games
                if user["username"] in ACTIVE_GAMES:
                    old_game = ACTIVE_GAMES[user["username"]]
                    try:
                        from core.redis_manager import CacheKeys, get_cache_connection
                        cache = get_cache_connection()
                        if cache and old_game.get("location"):
                            cache.srem(CacheKeys.room_players(old_game["location"]), user["username"])
                    except Exception: pass
                
                ACTIVE_SESSIONS[user["username"]] = {
                    "last_activity": datetime.now(),
                    "session_id": session.get("session_id", id(session)),
                }
                
                try:
                    game = get_game()
                except Exception:
                    return jsonify({"redirect": url_for("index")})
                
                if game and game.get("character") and isinstance(game["character"], dict) and not game["character"].get("race"):
                    session["onboarding_step"] = 1
                    session["onboarding_state"] = {"step": 1, "character": game["character"]}
                
                return jsonify({"redirect": url_for("index")})
            else:
                session["login_step"] = "username"
                session.pop("login_username", None)
                return jsonify({"message": "Invalid username or password.\nEnter your username:"})
        else:
            if cmd:
                session["login_username"] = cmd
                session["login_step"] = "password"
                return jsonify({"message": f"Enter password for {cmd}:"})
            return jsonify({"message": "Invalid choice. Please enter N, L, G, Q, or your character name."})

@app.route("/guide")
def guide():
    return render_template("guide.html", session=session)

@app.route("/")
def index():
    onboarding_step = session.get("onboarding_step")
    if onboarding_step is None and request.args.get("onboarding") == "start":
        session["onboarding_step"] = 0
        session["onboarding_state"] = {"step": 0, "character": {}}
        session.permanent = True
        session.modified = True
        onboarding_step = 0
    
    if onboarding_step is not None and onboarding_step != "complete" and onboarding_step != "":
        if onboarding_step == 0:
            log = [ONBOARDING_USERNAME_PROMPT]
        else:
            onboarding_state = session.get("onboarding_state", {"step": 0, "character": {}})
            current_step = onboarding_state.get("step", 0)
            if current_step == 0: log = [ONBOARDING_USERNAME_PROMPT]
            elif current_step == 0.5: log = [ONBOARDING_PASSWORD_PROMPT]
            elif current_step == 1: log = [ONBOARDING_RACE_PROMPT]
            else: log = ["Continue your character creation..."]
        
        return render_template("index.html", log=highlight_exits_in_log(log), session=session, onboarding=True)
    
    if "user_id" not in session:
        return redirect(url_for("welcome"))
    
    username = session.get("username", "adventurer")
    
    # Check if user was auto-logged out (not in ACTIVE_SESSIONS)
    # If they were, clear their session and redirect to welcome
    if username not in ACTIVE_SESSIONS:
        # User was likely auto-logged out for inactivity
        session.clear()
        session.modified = True
        flash("Your session has expired due to inactivity. Please log in again.", "info")
        return redirect(url_for("welcome"))
    
    ACTIVE_SESSIONS[username] = {
        "last_activity": datetime.now(),
        "session_id": session.get("session_id", id(session)),
    }
    
    game = get_game()
    
    # Tavern lock check
    if game and game.get("location") == "tavern":
        current_minutes = get_current_hour_in_minutes()
        hour_of_day = int(current_minutes // MINUTES_PER_HOUR) % 24
        if (hour_of_day >= 1 and hour_of_day < 10) and not is_admin_user(username, game):
            game["location"] = "town_square"
            game.setdefault("log", []).append("[CYAN]Mara notices you in the locked tavern and shakes her head. 'Sorry, but the tavern's closed right now! Out you go!' She ushers you out the door to the town square.[/CYAN]")
            game["log"] = game["log"][-50:]
            save_game(game)
            broadcast_to_room(username, "town_square", f"{username} appears in the town square, looking slightly bewildered after being ejected from the locked tavern.")
    
    if game and not session.get("welcome_added"):
        add_session_welcome(game, username)
        session["welcome_added"] = True
        save_game(game)
    
    if game is None:
        onboarding_state = session.get("onboarding_state")
        if onboarding_state and onboarding_state.get("step") == 6:
            character = onboarding_state.get("character", {})
            game = new_game_state(username=username, character=character)
            ACTIVE_GAMES[username] = game
            save_game(game)
            save_state_to_disk()
            
            race_name = AVAILABLE_RACES.get(character.get("race", ""), {}).get("name", "traveler")
            backstory_name = AVAILABLE_BACKSTORIES.get(character.get("backstory", ""), {}).get("name", "mystery")
            loc_id = game.get("location", "town_square")
            
            broadcast_to_room(username, loc_id, f"✨ A brilliant flash of light pierces the air, and {username} materializes in the center of the square, their form solidifying from ethereal mist. The cycle has brought another soul to Hollowvale. ✨")
            
            if "old_storyteller" in NPCS:
                storyteller = NPCS["old_storyteller"]
                possessive = getattr(storyteller, 'possessive', 'their')
                storyteller_name = storyteller.name if hasattr(storyteller, 'name') else 'The Old Storyteller'
                game["log"].append(f"The Old Storyteller looks up from {possessive} tales, eyes twinkling with ancient wisdom. '{username}... a {race_name} with a {backstory_name.lower()}...' {storyteller_name} smiles warmly. 'Welcome to Hollowvale. Your story is just beginning. The wheel has turned, and you have returned.'")
            
            game["log"].append(describe_location(game))
            save_game(game)
            session.pop("onboarding_step", None)
            session.pop("onboarding_state", None)
        else:
            session["onboarding_step"] = "start"
            return redirect(url_for("index"))
    
    if len(game.get("log", [])) == 2 and "Type 'look' to see where you are" in game["log"][-1]:
        game["log"].append(describe_location(game))
        save_game(game)
    
    if "last_log_index" not in session:
        session["last_log_index"] = len(game.get("log", [])) - 1
        session.modified = True
    
    from color_system import get_color_settings
    color_settings = get_color_settings(game) if game else {}
    
    return render_template("index.html", log=highlight_exits_in_log(game["log"]), session=session, onboarding=False, color_settings=color_settings)

@app.route("/logout")
def logout():
    username = session.get("username")
    if username and username in ACTIVE_GAMES:
        save_game(ACTIVE_GAMES[username])
        save_state_to_disk()
        broadcast_to_room(username, ACTIVE_GAMES[username].get("location"), f"[{username} has logged out.]")
        ACTIVE_GAMES.pop(username, None)
        ACTIVE_SESSIONS.pop(username, None)
    
    session.pop("welcome_added", None)
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("welcome"))

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json() or {}
    cmd = data.get("command", "")
    username = session.get("username", "adventurer")
    user_id = session.get("user_id")
    
    onboarding_step = session.get("onboarding_step")
    onboarding_state = session.get("onboarding_state")
    
    if user_id and (onboarding_step or onboarding_state):
        if onboarding_step != "complete":
            session.pop("onboarding_step", None)
            session.pop("onboarding_state", None)
            session.modified = True
            onboarding_step = None
    
    if onboarding_step is None and not user_id:
        if "onboarding=start" in request.headers.get("Referer", ""):
            session["onboarding_step"] = 0
            session["onboarding_state"] = {"step": 0, "character": {}}
            session.permanent = True
            session.modified = True
            onboarding_step = 0
        elif request.args.get("onboarding") == "start":
            session["onboarding_step"] = 0
            session["onboarding_state"] = {"step": 0, "character": {}}
            session.permanent = True
            session.modified = True
            onboarding_step = 0
    
    if onboarding_step is not None and onboarding_step != "complete" and onboarding_step != "":
        onboarding_state = session.get("onboarding_state", {"step": onboarding_step if onboarding_step is not None else (0 if not user_id else 1), "character": {}})
        conn = get_db()
        response, updated_state, is_complete, created_user_id = handle_onboarding_command(
            cmd, onboarding_state, username=username if user_id else None, db_conn=conn
        )
        session["onboarding_state"] = updated_state
        
        log = [response] if isinstance(response, str) else response
        processed_log = highlight_exits_in_log(log)
        
        if is_complete:
            if created_user_id:
                session["user_id"] = created_user_id
                session["username"] = updated_state.get("username", "adventurer")
                username = session["username"]
                user_id = created_user_id
            
            session.pop("onboarding_step", None)
            session.pop("onboarding_state", None)
            session.modified = True
            
            character = updated_state.get("character", {})
            game = new_game_state(username=username, character=character)
            ACTIVE_GAMES[username] = game
            save_game(game)
            save_state_to_disk()
            
            race_name = AVAILABLE_RACES.get(character.get("race", ""), {}).get("name", "traveler")
            backstory_name = AVAILABLE_BACKSTORIES.get(character.get("backstory", ""), {}).get("name", "mystery")
            loc_id = game.get("location", "town_square")
            
            broadcast_to_room(username, loc_id, f"✨ A brilliant flash of light pierces the air, and {username} materializes in the center of the square, their form solidifying from ethereal mist. The cycle has brought another soul to Hollowvale. ✨")
            
            if "old_storyteller" in NPCS:
                storyteller = NPCS["old_storyteller"]
                possessive = getattr(storyteller, 'possessive', 'their')
                storyteller_name = storyteller.name if hasattr(storyteller, 'name') else 'The Old Storyteller'
                game["log"].append(f"The Old Storyteller looks up from {possessive} tales, eyes twinkling with ancient wisdom. '{username}... a {race_name} with a {backstory_name.lower()}...' {storyteller_name} smiles warmly. 'Welcome to Hollowvale. Your story is just beginning. The wheel has turned, and you have returned.'")
            
            game["log"].append(describe_location(game))
            save_game(game)
            log = [response]
            conn.close()
        else:
            log = [response]
            conn.close()
        
        if isinstance(log, list) and len(log) == 1 and isinstance(log[0], str) and ('[PAUSE:' in log[0] or '[ELLIPSIS:' in log[0]):
            processed_log = log[0]
        else:
            processed_log = highlight_exits_in_log(log)
            
        session.modified = True
        from color_system import get_color_settings
        color_settings = get_color_settings(game) if user_id and game else {}
        return jsonify({"response": response, "log": processed_log, "onboarding": not is_complete, "color_settings": color_settings})
    
    if not user_id:
        return jsonify({"response": "Please login first.", "log": ["Please login first."], "onboarding": False})
    
    game = get_game()
    if game is None:
        session["onboarding_step"] = 1
        session["onboarding_state"] = {"step": 1, "character": {}}
        return jsonify({"response": "Please complete character creation first.", "log": highlight_exits_in_log([ONBOARDING_RACE_PROMPT]), "onboarding": True})
    
    def broadcast_fn(room_id, text):
        broadcast_to_room(username, room_id, text)
    
    conn = get_db()
    try:
        response, game = handle_command(
            cmd, game, username=username, user_id=user_id, db_conn=conn, broadcast_fn=broadcast_fn, who_fn=list_active_players
        )
        
        # Check for sunrise/sunset transitions
        atmos = get_atmospheric_manager()
        notifications = atmos.check_sunrise_sunset_transitions()
        
        # Broadcast notifications
        for msg_type, msg_text in notifications:
            # Filter broadcast function to only notify players with notify time on (for sunrise/sunset)
            for uname, g in ACTIVE_GAMES.items():
                # For now, broadcast to all outdoor rooms or just all players?
                # The old logic filtered by room_id but we don't have a specific room_id here
                # We'll broadcast to all players who are in outdoor rooms (implied by message content usually)
                # or just check their notify settings
                notify_cfg = g.get("notify", {})
                if notify_cfg.get("time", False):
                    g.setdefault("log", [])
                    g["log"].append(msg_text)
                    g["log"] = g["log"][-50:]
                    # Also emit socket event if possible
                    try:
                        socketio.emit('room_message', {
                            'room_id': g.get("location"),
                            'message': msg_text,
                            'message_type': 'system'
                        }, room=f"user:{uname}")
                    except Exception: pass
        
                    except Exception: pass
        
        if "user_description" in game:
            conn.execute("UPDATE users SET description = ? WHERE id = ?", (game["user_description"], user_id))
            conn.commit()
            
    except Exception as e:
        import traceback
        print(f"Error handling command '{cmd}': {e}")
        print(traceback.format_exc())
        error_msg = f"An error occurred while processing your command. Please try again."
        game.setdefault("log", []).append(error_msg)
        game["log"] = game["log"][-50:]
        response = error_msg
        save_game(game)
        save_state_to_disk()
    finally:
        conn.close()
    
    if response == "__LOGOUT__":
        save_game(game)
        save_state_to_disk()
        broadcast_to_room(username, game.get("location"), f"[{username} has logged out.]")
        ACTIVE_GAMES.pop(username, None)
        ACTIVE_SESSIONS.pop(username, None)
        
        # Note: Session is NOT cleared here - client will redirect to /logout which handles session clearing
        return jsonify({"logout": True, "message": "You have logged out.", "log": []})
    
    session.setdefault("last_log_index", -1)
    last_log_index = session.get("last_log_index", -1)
    current_log = game.get("log", [])
    current_log_length = len(current_log)
    
    if last_log_index >= current_log_length: last_log_index = -1
    
    if last_log_index + 1 <= current_log_length:
        new_log_entries = current_log[last_log_index + 1:]
    else:
        new_log_entries = []
    
    if len(new_log_entries) == 0 and current_log_length > 0:
        if last_log_index >= current_log_length - 1:
            session["last_log_index"] = -1
            session.modified = True
            if current_log_length >= 2: new_log_entries = current_log[-2:]
            elif current_log_length == 1: new_log_entries = current_log[-1:]
    
    if len(new_log_entries) > 0:
        session["last_log_index"] = current_log_length - 1
        session.modified = True
    
    processed_log = highlight_exits_in_log(new_log_entries) if new_log_entries else []
    
    from color_system import get_color_settings
    color_settings = get_color_settings(game)
    
    return jsonify({"response": response, "log": processed_log, "color_settings": color_settings})

LAST_POLL_STATE = {}

@app.route("/poll", methods=["POST"])
@require_auth
def poll_updates():
    username = session.get("username")
    user_id = session.get("user_id")
    if not username or not user_id: return jsonify({"messages": []})
    
    # Optimization & Fix: Don't load game from DB during polling.
    # If the user is not in ACTIVE_GAMES, they are either logged out
    # or the server restarted. In either case, we shouldn't resurrect
    # the game state just for a poll. The user must interact (login/command)
    # to restore state.
    if username not in ACTIVE_GAMES:
        return jsonify({"messages": []})
    
    game = get_game()
    if not game: return jsonify({"messages": []})
    
    # Only add to ACTIVE_SESSIONS if user actually has an active game
    # This prevents logged-out users from being re-added on polling
    if username in ACTIVE_GAMES:
        ACTIVE_SESSIONS[username] = {
            "last_activity": datetime.now(),
            "session_id": session.get("session_id", id(session)),
        }
    
    
    def broadcast_fn(room_id, text):
        broadcast_to_room(username, room_id, text)
    
    # Update weather/player status (but don't accumulate messages)
    atmos = get_atmospheric_manager()
    weather_changed, transition_message = atmos.update()
    # Note: Transition messages are handled in background task, not here
    
    # process_world_clock_events() # Removed as it no longer exists
    update_player_weather_status(game)
    # NPC weather updates now handled in handle_command() via new model methods (Phase 2)
    # cleanup_buried_items() # Removed
    # process_time_based_exit_states() # Removed
    process_npc_movements(broadcast_fn=broadcast_fn)
    
    current_time = datetime.now()
    if username not in LAST_POLL_STATE:
        LAST_POLL_STATE[username] = {
            "last_ambiance_time": current_time,
            "last_npc_action_time": current_time,
        }
    
    poll_state = LAST_POLL_STATE[username]
    new_messages = []
    current_room = game.get("location", "town_square")
    
    npc_interval_min = float(get_game_setting("npc_action_interval_min", "30"))
    npc_interval_max = float(get_game_setting("npc_action_interval_max", "60"))
    
    last_npc_time = poll_state.get("last_npc_action_time", current_time)
    elapsed_npc_seconds = (current_time - last_npc_time).total_seconds()
    
    if elapsed_npc_seconds >= npc_interval_min:
        from npc_actions import get_all_npc_actions_for_room
        npc_ids = get_npcs_in_room(current_room)
        if npc_ids:
            npc_actions = get_all_npc_actions_for_room(current_room, game=game, active_players_fn=list_active_players)
            if npc_actions:
                npc_id, action = random.choice(list(npc_actions.items()))
                action_text = f"[NPC]{action}[/NPC]"
                new_messages.append(action_text)
                broadcast_fn(current_room, action_text)
                next_interval = random.uniform(npc_interval_min, npc_interval_max)
                poll_state["last_npc_action_time"] = current_time - timedelta(seconds=elapsed_npc_seconds - next_interval)
    
    ambiance_interval_min = float(get_game_setting("ambiance_interval_min", "120"))
    ambiance_interval_max = float(get_game_setting("ambiance_interval_max", "240"))
    
    last_ambiance_time = poll_state.get("last_ambiance_time", current_time)
    elapsed_ambiance_seconds = (current_time - last_ambiance_time).total_seconds()
    
    if elapsed_ambiance_seconds >= ambiance_interval_min:
        ambiance_msg = ambiance.process_room_ambiance(game, broadcast_fn=broadcast_fn)
        if ambiance_msg and len(ambiance_msg) > 0:
            new_messages.append(ambiance_msg[0])
            next_interval = random.uniform(ambiance_interval_min, ambiance_interval_max)
            poll_state["last_ambiance_time"] = current_time - timedelta(seconds=elapsed_ambiance_seconds - next_interval)
    
    # Weather messages for outdoor rooms (using old working system)
    # Weather messages are now handled by the background events system
    # (removed duplicate weather message logic from poll_updates)
    
    if new_messages:
        game.setdefault("log", [])
        for msg in new_messages:
            game["log"].append(msg)
        game["log"] = game["log"][-50:]
        save_game(game)
        save_state_to_disk()
    
    processed_messages = highlight_exits_in_log(new_messages) if new_messages else []
    return jsonify({"messages": processed_messages})

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("You must be logged in to access this page.", "error")
            return redirect(url_for("welcome"))
        
        username = session.get("username")
        admin_users = set(os.environ.get("ADMIN_USERS", "admin,tezbo").split(","))
        if username and username.lower() in {u.lower().strip() for u in admin_users}:
            return f(*args, **kwargs)
        
        conn = get_db()
        user = conn.execute("SELECT is_admin FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        conn.close()
        
        if not user or not user["is_admin"]:
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("welcome"))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin")
@require_admin
def admin_dashboard():
    try:
        from ai_client import _token_usage, _user_token_usage, _response_cache
    except ImportError:
        _token_usage = {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "requests": 0, "last_reset": "Never"}
        _user_token_usage = {}
        _response_cache = {}
    
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
    total_ai_users = conn.execute("SELECT COUNT(*) as count FROM ai_usage").fetchone()["count"]
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
    
    rate_limit_stats = conn.execute(
        """
        SELECT user_id, COUNT(*) as request_count
        FROM ai_rate_limits
        WHERE request_time > datetime('now', '-1 hour')
        GROUP BY user_id
        """
    ).fetchall()
    rate_limit_map = {row["user_id"]: row["request_count"] for row in rate_limit_stats}
    conn.close()
    
    global_usage = _token_usage.copy()
    cache_size = len(_response_cache)
    cache_hits = sum(1 for entry in _response_cache.values() if datetime.now() - entry["timestamp"] < timedelta(hours=24))
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
    data = request.get_json() or {}
    user_id = data.get("user_id")
    budget = data.get("budget")
    
    if not user_id or budget is None: return jsonify({"error": "Missing user_id or budget"}), 400
    try:
        budget = int(budget)
        if budget < 0: return jsonify({"error": "Budget must be non-negative"}), 400
    except ValueError: return jsonify({"error": "Budget must be an integer"}), 400
    
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

# Register SocketIO handlers
register_socketio_handlers(socketio, get_game, handle_command, save_game, ACTIVE_GAMES, ACTIVE_SESSIONS)

# Start background event generator (including automatic weather updates)
try:
    from core.background_events import start_background_event_generator
    from game.systems.weather_updates import update_all_weather_statuses
    from game_engine import NPC_STATE
    
    # Create wrapper functions for background events
    def get_all_rooms():
        """Get all room IDs from world definition."""
        from game_engine import WORLD
        return list(WORLD.keys())
    
    def update_weather_statuses():
        """Wrapper to update weather for all players and NPCs, and broadcast transition messages."""
        from game.systems.atmospheric_manager import get_atmospheric_manager
        from game_engine import WORLD
        
        atmos = get_atmospheric_manager()
        weather_changed, transition_message = atmos.update()
        
        # If weather changed and we have a transition message, broadcast to all outdoor rooms
        if weather_changed and transition_message:
            # Get all outdoor rooms
            outdoor_rooms = [room_id for room_id, room_def in WORLD.items() 
                           if room_def.get("outdoor", False)]
            
            # Broadcast transition message to all outdoor rooms
            for room_id in outdoor_rooms:
                try:
                    # Check if room has active players
                    from core.redis_manager import get_cache_connection, CacheKeys
                    cache = get_cache_connection()
                    room_players_key = CacheKeys.room_players(room_id)
                    players = cache.smembers(room_players_key)
                    players = list(players) if players else []
                    
                    if players:
                        # Format message with CYAN tags for visibility
                        formatted_message = f"[CYAN]{transition_message}[/CYAN]"
                        socketio.emit('room_message', {
                            'room_id': room_id,
                            'message': formatted_message,
                            'message_type': 'weather_transition'
                        }, room=f"room:{room_id}")
                except Exception as e:
                    # If Redis unavailable or other error, still try to broadcast via SocketIO
                    # (SocketIO will handle rooms even if Redis is down)
                    try:
                        formatted_message = f"[CYAN]{transition_message}[/CYAN]"
                        socketio.emit('room_message', {
                            'room_id': room_id,
                            'message': formatted_message,
                            'message_type': 'weather_transition'
                        }, room=f"room:{room_id}")
                    except Exception:
                        pass  # Silently fail if SocketIO also unavailable
        
        # Update weather status for all players and NPCs
        update_all_weather_statuses(
            get_active_games_fn=lambda: ACTIVE_GAMES,
            get_active_sessions_fn=lambda: ACTIVE_SESSIONS,
            save_game_fn=save_game,
            get_npc_state_fn=lambda: NPC_STATE,
        )
    
    # Import ambiance processing functions
    from ambiance import process_room_ambiance, process_weather_ambiance
    
    # Start background events (weather updates run every 5 seconds along with other events)
    start_background_event_generator(
        socketio,
        get_game_setting_fn=None,  # Can be added later if needed
        get_all_rooms_fn=get_all_rooms,
        process_ambiance_fn=process_room_ambiance,  # General ambiance (every 2-4 minutes)
        process_weather_ambiance_fn=process_weather_ambiance,  # Weather messages (every 30-60 seconds)
        process_decay_fn=None,  # Decay can be added later
        update_weather_fn=update_weather_statuses,
        get_active_games_fn=lambda: ACTIVE_GAMES,
    )
    logger.info("Background weather updates started")
except Exception as e:
    logger.warning(f"Could not start background event generator: {e}", exc_info=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)