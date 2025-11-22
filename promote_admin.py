#!/usr/bin/env python3
"""
One-time script to promote a user to admin.
Can be run locally or on Render via Render Shell.

Usage:
    python3 promote_admin.py tezbo
"""

import sys
import sqlite3
import os

DATABASE = os.environ.get("DATABASE", "users.db")


def promote_to_admin(username):
    """Promote a user to admin status."""
    if not username:
        print("Error: Username required")
        print("Usage: python3 promote_admin.py <username>")
        return False
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if user exists
        user = cursor.execute(
            "SELECT id, username, is_admin FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        
        if not user:
            print(f"Error: User '{username}' not found in database")
            conn.close()
            return False
        
        user_id, db_username, current_admin = user
        print(f"Found user: {db_username} (ID: {user_id}, Current admin: {current_admin})")
        
        if current_admin:
            print(f"User '{username}' is already an admin")
            conn.close()
            return True
        
        # Promote to admin
        cursor.execute(
            "UPDATE users SET is_admin = 1 WHERE username = ?",
            (username,)
        )
        conn.commit()
        conn.close()
        
        print(f"✓ Successfully promoted '{username}' to admin")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 promote_admin.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    success = promote_to_admin(username)
    sys.exit(0 if success else 1)

