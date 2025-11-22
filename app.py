import os
import json
import sqlite3
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
    # Add description column if it doesn't exist (migration for existing databases)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN description TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()


# Initialize database when module is imported (works with flask run, WSGI servers, etc.)
init_db()


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Active games storage for multiplayer support
ACTIVE_GAMES = {}  # username -> game state dict

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


def list_active_players():
    """Return a list of dicts with active player information."""
    data = []
    for uname, g in ACTIVE_GAMES.items():
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
            
            # Check if character exists - if not, need onboarding
            if not game.get("character") or not game.get("character", {}).get("race"):
                conn.close()
                return None
            
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
            # Ensure character object exists (backward compatibility)
            if "character" not in game:
                game["character"] = {
                    "race": "",
                    "gender": "",
                    "stats": {"str": 0, "agi": 0, "wis": 0, "wil": 0, "luck": 0},
                    "backstory": "",
                    "backstory_text": "",
                    "description": "",
                }
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


@app.route("/welcome", methods=["GET", "POST"])
def welcome():
    """Welcome screen with ASCII art and character creation/login menu."""
    # If already logged in, redirect to game
    if "user_id" in session:
        return redirect(url_for("index"))
    
    # Handle login form submission
    login_step = session.get("login_step")
    if request.method == "POST" and login_step:
        if login_step == "username":
            username = request.form.get("username", "").strip()
            if username:
                session["login_username"] = username
                session["login_step"] = "password"
                return render_template("welcome.html", login_mode=True, login_username=username)
            else:
                flash("Please enter your username.", "error")
                return render_template("welcome.html", login_mode=True)
        elif login_step == "password":
            password = request.form.get("password", "")
            username = session.get("login_username", "")
            
            if not password:
                flash("Please enter your password.", "error")
                return render_template("welcome.html", login_mode=True, login_username=username)
            
            # Authenticate user
            conn = get_db()
            user = conn.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            conn.close()
            
            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session.pop("login_step", None)
                session.pop("login_username", None)
                
                # Check if user has character - if not, start onboarding
                game = get_game()
                if game is None or not game.get("character") or not game.get("character", {}).get("race"):
                    # No character - start onboarding (but skip username/password)
                    session["onboarding_step"] = 1
                    session["onboarding_state"] = {"step": 1, "character": {}}
                    return redirect(url_for("index"))
                
                return redirect(url_for("index"))
            else:
                flash("Invalid username or password.", "error")
                session["login_step"] = "username"
                session.pop("login_username", None)
                return render_template("welcome.html", login_mode=True)
    
    if request.method == "POST":
        choice = request.form.get("choice", "").strip()
        choice_upper = choice.upper()
        
        # Handle menu commands
        if choice_upper == "Q":
            # Quit - just show welcome again
            return render_template("welcome.html")
        elif choice_upper == "G":
            return redirect(url_for("guide"))
        elif choice_upper == "N":
            # New character - start onboarding with username/password creation
            session["onboarding_step"] = 0
            session["onboarding_state"] = {"step": 0, "character": {}}
            return redirect(url_for("index"))
        elif choice_upper == "L":
            # Login - start login flow
            session["login_step"] = "username"
            return render_template("welcome.html", login_mode=True)
        else:
            # Assume it's a username - start login flow
            if choice:
                session["login_username"] = choice
                session["login_step"] = "password"
                return render_template("welcome.html", login_mode=True, login_username=choice)
            else:
                flash("Invalid choice. Please enter N, L, G, Q, or your character name.", "error")
    
    return render_template("welcome.html", login_mode=request.args.get("login_mode", False), login_username=session.get("login_username"))


@app.route("/guide")
def guide():
    """Player's guide page - accessible without authentication."""
    return render_template("guide.html", session=session)


@app.route("/")
def index():
    # If not logged in, redirect to welcome
    if "user_id" not in session:
        return redirect(url_for("welcome"))
    
    # Check if user is in onboarding
    onboarding_step = session.get("onboarding_step")
    if onboarding_step and onboarding_step != "complete":
        # User is in onboarding - show onboarding screen
        from game_engine import ONBOARDING_USERNAME_PROMPT, handle_onboarding_command
        
        # Initialize onboarding if needed
        if onboarding_step == 0:
            onboarding_state = {
                "step": 0,
                "character": {}
            }
            session["onboarding_state"] = onboarding_state
            log = [ONBOARDING_USERNAME_PROMPT]
        else:
            onboarding_state = session.get("onboarding_state", {"step": 0, "character": {}})
            # Show current step prompt
            current_step = onboarding_state.get("step", 0)
            if current_step == 0:
                log = [ONBOARDING_USERNAME_PROMPT]
            elif current_step == 0.5:
                from game_engine import ONBOARDING_PASSWORD_PROMPT
                log = [ONBOARDING_PASSWORD_PROMPT]
            elif current_step == 1:
                from game_engine import ONBOARDING_RACE_PROMPT
                log = [ONBOARDING_RACE_PROMPT]
            else:
                log = ["Continue your character creation..."]
        
        processed_log = highlight_exits_in_log(log)
        return render_template("index.html", log=processed_log, session=session, onboarding=True)
    
    # Ensure game exists (this loads from DB or creates new)
    game = get_game()
    
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
            
            # Add special Old Storyteller greeting
            from game_engine import NPCS, AVAILABLE_RACES, AVAILABLE_BACKSTORIES, describe_location
            if "old_storyteller" in NPCS:
                storyteller = NPCS["old_storyteller"]
                race_name = AVAILABLE_RACES.get(character.get("race", ""), {}).get("name", "traveler")
                backstory_name = AVAILABLE_BACKSTORIES.get(character.get("backstory", ""), {}).get("name", "mystery")
                possessive = getattr(storyteller, 'possessive', 'their')
                greeting = f"The Old Storyteller looks up from {possessive} tales and smiles warmly. 'Ah, a {race_name} with a {backstory_name.lower()}... Welcome to Hollowvale, {session.get('username')}. Your story is just beginning.'"
                game["log"].append(greeting)
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
    # Process log to highlight Exits in yellow
    processed_log = highlight_exits_in_log(game["log"])
    return render_template("index.html", log=processed_log, session=session, onboarding=False)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page and handler."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            flash("Please provide both username and password.", "error")
            return render_template("login.html")
        
        conn = get_db()
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            username = user["username"]
            
            # Get or create game state
            game = get_game()
            
            # Add session welcome to existing game state if it exists
            if game:
                add_session_welcome(game, username)
                # Add current location description
                game.setdefault("log", [])
                game["log"].append(describe_location(game))
                save_game(game)
            
            # Broadcast login notification to other players who have it enabled
            for uname, g in ACTIVE_GAMES.items():
                if uname == username:
                    continue
                notify_cfg = g.get("notify", {})
                if notify_cfg.get("login"):
                    g.setdefault("log", [])
                    g["log"].append(f"[{username} has logged in]")
                    g["log"] = g["log"][-50:]
                    save_game(g)
            
            save_state_to_disk()
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")
            return render_template("login.html")
    
    # If already logged in, redirect to game
    if "user_id" in session:
        return redirect(url_for("index"))
    
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registration page and handler."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not username or not password:
            flash("Please provide both username and password.", "error")
            return render_template("login.html", show_register=True)
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("login.html", show_register=True)
        
        if len(password) < 4:
            flash("Password must be at least 4 characters long.", "error")
            return render_template("login.html", show_register=True)
        
        conn = get_db()
        # Check if username already exists
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        
        if existing:
            conn.close()
            flash("Username already exists. Please choose another.", "error")
            return render_template("login.html", show_register=True)
        
        # Create new user
        password_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        conn.close()
        
        # Log the user in automatically after registration
        user = conn.execute(
            "SELECT id, username FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()
        
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            # Start onboarding immediately
            session["onboarding_step"] = "start"
            return redirect(url_for("index"))
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    
    return render_template("login.html", show_register=True)


@app.route("/logout")
def logout():
    """Logout handler."""
    username = session.get("username")
    
    # Broadcast logout notification before clearing session
    if username and username in ACTIVE_GAMES:
        for uname, g in ACTIVE_GAMES.items():
            if uname == username:
                continue
            notify_cfg = g.get("notify", {})
            if notify_cfg.get("login"):
                g.setdefault("log", [])
                g["log"].append(f"[{username} has logged out]")
                g["log"] = g["log"][-50:]
                save_game(g)
        
        # Remove from active games
        ACTIVE_GAMES.pop(username, None)
    
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/command", methods=["POST"])
def command():
    # Allow commands during onboarding (before login)
    # But also allow normal commands if logged in
    data = request.get_json() or {}
    cmd = data.get("command", "")
    username = session.get("username", "adventurer")
    user_id = session.get("user_id")
    
    # Check if user is in onboarding (but not logged in yet - this is for new character creation)
    onboarding_step = session.get("onboarding_step")
    if onboarding_step and onboarding_step != "complete" and not user_id:
        # Handle onboarding commands for new character creation
        from game_engine import handle_onboarding_command
        
        onboarding_state = session.get("onboarding_state", {"step": 0 if not user_id else 1, "character": {}})
        
        # Get database connection for account creation (if not logged in) or character updates
        conn = get_db()
        
        # Process onboarding command
        # If user is logged in but in onboarding, they're completing character creation (skip username/password)
        onboarding_username = username if user_id else None
        response, updated_state, is_complete, created_user_id = handle_onboarding_command(
            cmd, onboarding_state, username=onboarding_username, db_conn=conn
        )
        session["onboarding_state"] = updated_state
        
        if is_complete:
            # Account was created during onboarding
            if created_user_id:
                session["user_id"] = created_user_id
                session["username"] = updated_state.get("username", "adventurer")
                username = session["username"]
                user_id = created_user_id
            
            session["onboarding_step"] = "complete"
            # Create game state with character
            character = updated_state.get("character", {})
            game = new_game_state(username=username, character=character)
            ACTIVE_GAMES[username] = game
            save_game(game)
            save_state_to_disk()
            
            # Add special Old Storyteller greeting
            from game_engine import NPCS, AVAILABLE_RACES, AVAILABLE_BACKSTORIES, describe_location
            if "old_storyteller" in NPCS:
                storyteller = NPCS["old_storyteller"]
                race_name = AVAILABLE_RACES.get(character.get("race", ""), {}).get("name", "traveler")
                backstory_name = AVAILABLE_BACKSTORIES.get(character.get("backstory", ""), {}).get("name", "mystery")
                # Old Storyteller is a dict, use 'their' as default
                possessive = 'their'
                greeting = f"The Old Storyteller looks up from {possessive} tales and smiles warmly. 'Ah, a {race_name} with a {backstory_name.lower()}... Welcome to Hollowvale, {username}. Your story is just beginning.'"
                game["log"].append(greeting)
                game["log"].append(describe_location(game))
                save_game(game)
            
            log = game["log"]
            conn.close()
        else:
            # Add delay dots for narrative effect
            log = response.split("\n")
            # Add dots between paragraphs for dramatic effect
            formatted_log = []
            for i, line in enumerate(log):
                formatted_log.append(line)
                if line.strip() and i < len(log) - 1 and log[i+1].strip():
                    formatted_log.append("...")
            log = formatted_log
        
        processed_log = highlight_exits_in_log(log)
        return jsonify({"response": response, "log": processed_log, "onboarding": not is_complete})
    
    # Normal game command handling - require authentication
    if not user_id:
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
        # Before removing the user, notify others who have login notifications turned on
        for uname, g in ACTIVE_GAMES.items():
            if uname == username:
                continue
            notify_cfg = g.get("notify", {})
            if notify_cfg.get("login"):
                g.setdefault("log", [])
                g["log"].append(f"[{username} has logged out]")
                g["log"] = g["log"][-50:]
                save_game(g)
        
        # Remove this user from ACTIVE_GAMES
        ACTIVE_GAMES.pop(username, None)
        
        # Save game state before logout
        save_game(game)
        save_state_to_disk()
        
        # Return special response to trigger logout on client
        return jsonify({"logout": True, "message": "You have logged out.", "log": []})
    
    save_game(game)
    save_state_to_disk()
    # Process log to highlight Exits in yellow
    processed_log = highlight_exits_in_log(game["log"])
    return jsonify({"response": response, "log": processed_log})


def require_admin(f):
    """Decorator to require admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("You must be logged in to access this page.", "error")
            return redirect(url_for("login"))
        
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
            return redirect(url_for("index"))
        
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


if __name__ == "__main__":
    # For local development
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)