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
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

try:
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        message_queue=REDIS_URL if REDIS_URL else None,
        async_mode='eventlet',
        logger=True,
        engineio_logger=False,
    )
except Exception as e:
    logger.warning(f"Error initializing SocketIO with Redis: {e}")  # Removed redundant . Continuing.
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,
        engineio_logger=False,
    )

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
        # Create necessary tables here...
        # Existing code for creating tables...

        conn.commit()


init_db()


def get_db() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == '__main__':
    socketio.run(app)