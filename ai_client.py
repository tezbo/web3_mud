"""
AI client module for NPC dialogue generation.

This module provides a clean interface for generating NPC replies,
using OpenAI's API for AI-enhanced NPCs.
"""

import os
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict

from utils.prompt_loader import load_prompt


def _get_npc_dialogue_system_prompt(npc_name, npc_title, personality, room_name, room_description, npc_home, reputation_desc, reputation, username, stats=None, traits=None):
    """Load and format the NPC dialogue system prompt."""
    # Build stats summary if available
    stats_text = ""
    if stats:
        faction = stats.get("faction", "unknown")
        max_hp = stats.get("max_hp", 10)
        # Describe role/toughness without raw numbers
        if max_hp >= 25:
            toughness = "very tough and resilient"
        elif max_hp >= 20:
            toughness = "tough and capable"
        elif max_hp >= 15:
            toughness = "moderately capable"
        else:
            toughness = "relatively ordinary"
        stats_text = f"\nROLE: You are part of the {faction} faction. You are {toughness}."
    
    # Build traits summary if available
    traits_text = ""
    if traits:
        trait_descs = []
        if traits.get("authority", 0) >= 0.6:
            trait_descs.append("authoritative")
        if traits.get("kindness", 0) >= 0.6:
            trait_descs.append("kind-hearted")
        elif traits.get("kindness", 0) <= 0.3:
            trait_descs.append("somewhat cold")
        if traits.get("aggression", 0) >= 0.5:
            trait_descs.append("aggressive")
        elif traits.get("aggression", 0) <= 0.2:
            trait_descs.append("peaceful")
        if traits.get("curiosity", 0) >= 0.6:
            trait_descs.append("curious")
        if traits.get("patience", 0) >= 0.7:
            trait_descs.append("patient")
        
        if trait_descs:
            traits_text = f"\nTEMPERAMENT: You tend to be {', '.join(trait_descs)}."
    
    fallback = f"""You are {npc_name}, {npc_title}, in a medieval fantasy text-based MUD game.

PERSONALITY: {personality}{stats_text}{traits_text}
LOCATION: You are currently in {room_name} - {room_description}
HOME: {npc_home}

REPUTATION WITH PLAYER: {reputation_desc} (Reputation score: {reputation})

IMPORTANT RULES:
- Keep responses SHORT (1-2 sentences max, under 100 words)
- Stay in character as {npc_name}
- Use natural, conversational dialogue
- If reacting to something the player said, acknowledge it naturally
- Reference past conversations if relevant
- Match your personality: {personality}
- Format as: "{npc_name} [action/expression]. '[dialogue]'"
- Example: "Mara looks up from wiping a table. 'Well, what do you need?'"

The player's name is {username}."""
    
    return load_prompt(
        "npc_dialogue_system.txt",
        fallback_text=fallback,
        npc_name=npc_name,
        npc_title=npc_title,
        personality=personality,
        room_name=room_name,
        room_description=room_description,
        npc_home=npc_home,
        reputation_desc=reputation_desc,
        reputation=reputation,
        username=username
    )


def _get_npc_dialogue_user_message(is_reaction, username, player_input):
    """Load and format the NPC dialogue user message."""
    if is_reaction:
        fallback = f"The player ({username}) just said in the room: \"{player_input}\"\n\nHow do you react? Keep it brief and in character."
        return load_prompt(
            "npc_dialogue_user_reaction.txt",
            fallback_text=fallback,
            username=username,
            player_input=player_input
        )
    else:
        fallback = f"The player ({username}) is talking directly to you. They said: \"{player_input}\"\n\nHow do you respond? Keep it brief and in character."
        return load_prompt(
            "npc_dialogue_user_talk.txt",
            fallback_text=fallback,
            username=username,
            player_input=player_input
        )

# Try to import OpenAI (optional dependency)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# Global token usage tracking (shared across all users)
_token_usage = {
    "total_tokens": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "requests": 0,
    "last_reset": datetime.now().isoformat(),
}

# Per-user token tracking (optional, for future per-user budgets)
_user_token_usage = {}

# Rate limiting: track requests per user per hour
_rate_limit_window = timedelta(hours=1)
_max_requests_per_hour = int(os.environ.get("AI_MAX_REQUESTS_PER_HOUR", "60"))  # Default 60 requests/hour
_user_request_times = defaultdict(list)  # {username: [list of request timestamps]}

# Response cache: cache common responses to reduce API calls
_response_cache = {}
_cache_max_size = 100
_cache_ttl = timedelta(hours=24)  # Cache for 24 hours


def _check_rate_limit(username, user_id=None, db_conn=None):
    """Check if user has exceeded rate limit. Returns (allowed, message)."""
    if not username:
        return True, None
    
    now = datetime.now()
    # Clean old requests outside the window
    _user_request_times[username] = [
        req_time for req_time in _user_request_times[username]
        if now - req_time < _rate_limit_window
    ]
    
    # Also track in database for admin dashboard
    if user_id and db_conn:
        try:
            db_conn.execute(
                "INSERT INTO ai_rate_limits (user_id, request_time) VALUES (?, ?)",
                (user_id, now)
            )
            # Clean old entries (older than 1 hour)
            db_conn.execute(
                "DELETE FROM ai_rate_limits WHERE request_time < datetime('now', '-1 hour')"
            )
        except Exception:
            pass  # Don't fail if DB tracking fails
    
    # Check if limit exceeded
    if len(_user_request_times[username]) >= _max_requests_per_hour:
        return False, f"Rate limit exceeded. Maximum {_max_requests_per_hour} AI requests per hour."
    
    return True, None


def _check_token_budget(user_id, db_conn=None):
    """Check if user has token budget remaining. Returns (allowed, remaining, message)."""
    if not user_id or not db_conn:
        return True, None, None
    
    try:
        row = db_conn.execute(
            "SELECT token_budget, tokens_used FROM ai_usage WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if row:
            budget = row["token_budget"]
            used = row["tokens_used"]
            remaining = budget - used
            
            if remaining <= 0:
                return False, remaining, "Your AI token budget has been exhausted. Please contact an administrator."
            return True, remaining, None
        else:
            # No budget set - unlimited
            return True, None, None
    except Exception:
        # If database check fails, allow the request
        return True, None, None


def _get_cache_key(npc_id, player_input, npc_memory_hash):
    """Generate a cache key for the request."""
    # Create a hash of the input for caching
    cache_str = f"{npc_id}:{player_input}:{npc_memory_hash}"
    return hashlib.md5(cache_str.encode()).hexdigest()


def _check_cache(cache_key):
    """Check if response is in cache. Returns cached response or None."""
    if cache_key in _response_cache:
        cached_entry = _response_cache[cache_key]
        if datetime.now() - cached_entry["timestamp"] < _cache_ttl:
            return cached_entry["response"]
        else:
            # Expired, remove from cache
            del _response_cache[cache_key]
    return None


def _add_to_cache(cache_key, response):
    """Add response to cache."""
    # Clean cache if it's too large
    if len(_response_cache) >= _cache_max_size:
        # Remove oldest entries
        sorted_cache = sorted(_response_cache.items(), key=lambda x: x[1]["timestamp"])
        for key, _ in sorted_cache[:_cache_max_size // 2]:
            del _response_cache[key]
    
    _response_cache[cache_key] = {
        "response": response,
        "timestamp": datetime.now(),
    }


def generate_npc_reply(npc, room, game, username, player_input, recent_log=None, user_id=None, db_conn=None):
    """
    Generate an NPC reply using AI (or placeholder logic).
    
    Args:
        npc: NPC metadata dict from NPCS
        room: room definition dict from WORLD for the current room
        game: full game state dict (contains npc_memory and reputation)
        username: current player's username (string)
        player_input: the raw player command / utterance that triggered this dialogue
        recent_log: optional list of recent log lines (strings)
        user_id: optional user ID for budget checking
        db_conn: optional database connection for budget checking
    
    Returns:
        tuple: (response_string, error_message_or_none)
    """
    # Get NPC ID from game context (set by game_engine)
    npc_id = game.get("_current_npc_id")
    
    # Get memory and reputation for this NPC
    npc_memory = game.get("npc_memory", {}).get(npc_id, []) if npc_id else []
    reputation = game.get("reputation", {}).get(npc_id, 0) if npc_id else 0
    
    npc_name = npc.get("name", "Someone")
    personality = npc.get("personality", "friendly")
    npc_title = npc.get("title", npc_name)
    npc_home = npc.get("home", "unknown")
    npc_stats = npc.get("stats")  # Optional stats dict
    npc_traits = npc.get("traits")  # Optional traits dict
    
    # Check if this is a reaction to something said (not a direct talk command)
    is_reaction = not player_input.startswith("talk to")
    
    # Check rate limiting
    rate_allowed, rate_message = _check_rate_limit(username, user_id=user_id, db_conn=db_conn)
    if not rate_allowed:
        return _fallback_reply(npc_name, personality, username, is_reaction, npc_memory, reputation), rate_message
    
    # Check token budget
    budget_allowed, remaining, budget_message = _check_token_budget(user_id, db_conn)
    if not budget_allowed:
        return _fallback_reply(npc_name, personality, username, is_reaction, npc_memory, reputation), budget_message
    
    # Check cache (only for simple queries without much context)
    if len(npc_memory) < 3:  # Only cache if conversation is relatively new
        memory_hash = str(len(npc_memory))  # Simple hash for cache key
        cache_key = _get_cache_key(npc_id, player_input.lower(), memory_hash)
        cached_response = _check_cache(cache_key)
        if cached_response:
            return cached_response, None
    
    # Check if OpenAI is available and API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_AVAILABLE or not api_key:
        # Fallback to placeholder implementation
        return _fallback_reply(npc_name, personality, username, is_reaction, npc_memory, reputation), "AI service is not configured."
    
    try:
        # Build context for the AI
        client = OpenAI(api_key=api_key)
        
        # Build conversation history from memory
        conversation_history = []
        if npc_memory:
            for mem in npc_memory[-5:]:  # Last 5 interactions for context
                if mem.get("type") == "talked":
                    conversation_history.append({
                        "role": "user",
                        "content": mem.get("player_input", "")
                    })
                    conversation_history.append({
                        "role": "assistant",
                        "content": mem.get("response", "")
                    })
                elif mem.get("type") == "said":
                    conversation_history.append({
                        "role": "user",
                        "content": f"Player said: {mem.get('message', '')}"
                    })
                    conversation_history.append({
                        "role": "assistant",
                        "content": mem.get("response", "")
                    })
        
        # Build system prompt
        # Updated reputation descriptions to match new thresholds
        reputation_desc = ""
        if reputation >= 100:
            reputation_desc = "You have an exceptional relationship with this player - they are a true friend and ally. You trust them completely."
        elif reputation >= 50:
            reputation_desc = "You have a very strong positive relationship with this player - you trust and like them a great deal."
        elif reputation >= 25:
            reputation_desc = "You have a positive relationship with this player - you trust and like them."
        elif reputation >= 15:
            reputation_desc = "You have a moderately positive impression of this player - you think well of them."
        elif reputation >= 10:
            reputation_desc = "You have a slightly positive impression of this player - they seem decent."
        elif reputation > 0:
            reputation_desc = "You have a neutral-to-positive impression of this player."
        elif reputation == 0:
            reputation_desc = "You don't know this player well yet."
        elif reputation >= -10:
            reputation_desc = "You have a slightly negative impression of this player - you're a bit wary."
        elif reputation >= -25:
            reputation_desc = "You have a negative impression of this player - you don't trust them much."
        elif reputation >= -50:
            reputation_desc = "You have a strongly negative relationship with this player - you're very wary and dislike them."
        else:
            reputation_desc = "You have an extremely negative relationship with this player - you consider them an enemy or threat."
        
        # Build system prompt using template
        room_name = room.get('name', 'a room')
        room_description = room.get('description', '')[:200]
        system_prompt = _get_npc_dialogue_system_prompt(
            npc_name, npc_title, personality, room_name, room_description,
            npc_home, reputation_desc, reputation, username,
            stats=npc_stats, traits=npc_traits
        )
        
        # Build user message using template
        user_message = _get_npc_dialogue_user_message(is_reaction, username, player_input)
        
        # Make API call
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        # Record request time for rate limiting
        if username:
            _user_request_times[username].append(datetime.now())
        
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),  # Default to cheaper model
            messages=messages,
            max_tokens=150,
            temperature=0.8,
        )
        
        # Track token usage
        usage = response.usage
        error_message = None
        
        if usage:
            tokens_used = usage.total_tokens
            
            # Global tracking
            _token_usage["total_tokens"] += tokens_used
            _token_usage["prompt_tokens"] += usage.prompt_tokens
            _token_usage["completion_tokens"] += usage.completion_tokens
            _token_usage["requests"] += 1
            
            # Per-user tracking
            if username:
                if username not in _user_token_usage:
                    _user_token_usage[username] = {
                        "total_tokens": 0,
                        "requests": 0,
                    }
                _user_token_usage[username]["total_tokens"] += tokens_used
                _user_token_usage[username]["requests"] += 1
            
            # Update database token budget
            if user_id and db_conn:
                try:
                    db_conn.execute(
                        """
                        INSERT INTO ai_usage (user_id, tokens_used, requests_count)
                        VALUES (?, ?, 1)
                        ON CONFLICT(user_id) DO UPDATE SET
                            tokens_used = tokens_used + ?,
                            requests_count = requests_count + 1
                        """,
                        (user_id, tokens_used, tokens_used)
                    )
                    db_conn.commit()
                except Exception as db_error:
                    print(f"Database error updating token usage: {db_error}")
            
            # Check if budget exceeded after this request
            if user_id and db_conn:
                budget_allowed, remaining, _ = _check_token_budget(user_id, db_conn)
                if not budget_allowed:
                    error_message = "Your AI token budget has been exhausted after this request."
        
        ai_response = response.choices[0].message.content.strip()
        
        # Ensure response is properly formatted
        if not ai_response.startswith(npc_name):
            ai_response = f"{npc_name} {ai_response}"
        
        # Add to cache
        if len(npc_memory) < 3:
            memory_hash = str(len(npc_memory))
            cache_key = _get_cache_key(npc_id, player_input.lower(), memory_hash)
            _add_to_cache(cache_key, ai_response)
        
        return ai_response, error_message
        
    except Exception as e:
        # Check for specific error types
        error_str = str(e).lower()
        
        # Handle quota/rate limit errors
        if "quota" in error_str or "rate limit" in error_str or "insufficient_quota" in error_str:
            print(f"OpenAI quota/rate limit exceeded: {e}")
            error_msg = "AI service quota exceeded. Please try again later."
            return _fallback_reply(npc_name, personality, username, is_reaction, npc_memory, reputation), error_msg
        elif "invalid" in error_str and "api key" in error_str:
            print(f"OpenAI API key error: {e}")
            error_msg = "AI service configuration error."
            return _fallback_reply(npc_name, personality, username, is_reaction, npc_memory, reputation), error_msg
        else:
            # Other errors - fallback to placeholder
            print(f"AI API error: {e}")  # Debug logging
            error_msg = "AI service temporarily unavailable. Using fallback response."
            return _fallback_reply(npc_name, personality, username, is_reaction, npc_memory, reputation), error_msg


def _fallback_reply(npc_name, personality, username, is_reaction, npc_memory, reputation):
    """Fallback placeholder implementation when AI is unavailable."""
    if is_reaction:
        # This is a reaction to something said in the room
        if "gruff" in personality.lower():
            if reputation > 0:
                return f"{npc_name} looks up from their work. 'I heard that. Makes sense, I suppose.'"
            elif reputation < 0:
                return f"{npc_name} glares at you. 'I don't appreciate that kind of talk.'"
            else:
                return f"{npc_name} glances over. 'Hmm, interesting.'"
        elif "kind" in personality.lower():
            if reputation > 0:
                return f"{npc_name} smiles. 'I agree, {username}. That's a good point.'"
            else:
                return f"{npc_name} nods thoughtfully. 'I see what you mean.'"
        else:
            return f"{npc_name} looks in your direction, considering your words."
    else:
        # Direct talk command
        # Check if we have memory of previous conversations
        if npc_memory:
            if "gruff" in personality.lower():
                if reputation > 0:
                    return f"{npc_name} gives you a knowing look. 'Back again, {username}? What is it this time?'"
                else:
                    return f"{npc_name} looks at you. 'You again. What do you want?'"
            elif "kind" in personality.lower():
                if reputation > 0:
                    return f"{npc_name} greets you warmly. 'Welcome back, {username}! Good to see you again.'"
                else:
                    return f"{npc_name} smiles. 'Hello again, {username}. How can I help?'"
        else:
            # First interaction
            if "gruff" in personality.lower():
                if username:
                    return f"{npc_name} looks at you with a gruff expression. 'Well, {username}, what do you need?'"
                return f"{npc_name} looks at you with a gruff expression. 'Well, what do you need?'"
            elif "kind" in personality.lower():
                if username:
                    return f"{npc_name} smiles warmly. 'Hello, {username}! How can I help you today?'"
                return f"{npc_name} smiles warmly. 'Hello! How can I help you today?'"
            else:
                if username:
                    return f"{npc_name} looks at you. 'Greetings, {username}. What brings you here?'"
                return f"{npc_name} looks at you. 'Greetings. What brings you here?'"


def get_token_usage():
    """
    Get current token usage statistics.
    
    Returns:
        dict: Token usage statistics
    """
    return _token_usage.copy()


def get_user_token_usage(username):
    """
    Get token usage for a specific user.
    
    Args:
        username: The username to get usage for
    
    Returns:
        dict: User's token usage, or None if user not found
    """
    return _user_token_usage.get(username, None)


def reset_token_usage():
    """Reset global token usage statistics."""
    global _token_usage
    _token_usage = {
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "requests": 0,
        "last_reset": datetime.now().isoformat(),
    }

