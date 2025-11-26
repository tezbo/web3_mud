# Architecture Analysis & Recommendations

## Current Issues

### 1. **State Management Chaos**
Multiple sources of truth that can get out of sync:
- `ACTIVE_GAMES` (in-memory cache)
- Database (`games` table)
- `ROOM_STATE` (global dict)
- `QUEST_GLOBAL_STATE` (global dict)  
- `ACTIVE_SESSIONS` (global dict)
- `LAST_POLL_STATE` (global dict)
- Session storage (`last_log_index`)
- Disk file (`mud_state.json`)

**Problem**: State synchronization is fragile and error-prone.

### 2. **Communication Architecture**
- **HTTP Polling**: Client polls `/poll` every 3 seconds (latency, bandwidth waste)
- **Log Tracking Complexity**: `last_log_index` in session tracks what's been sent (fragile, gets out of sync)
- **Mixed Responsibilities**: Frontend filters/logs, backend tracks indices

**Problem**: Not real-time, complex, inefficient.

### 3. **Separation of Concerns**

#### `app.py` (1517 lines)
Mixing:
- Route handlers (HTTP layer)
- Game state persistence (data layer)
- Session management (auth layer)
- State caching (application layer)
- Log tracking (presentation layer)

#### `game_engine.py` (10000+ lines)
Mixing:
- World data (`WORLD` dict)
- Game logic (commands, movement, interactions)
- State management (ROOM_STATE, QUEST_GLOBAL_STATE)
- NPC logic
- Quest logic

#### Frontend (`index.html`)
Doing:
- Log filtering
- Duplicate removal
- Scroll management
- Pause marker processing
- Color application
- Session text tracking

**Problem**: Tight coupling, hard to test, hard to scale.

### 4. **Performance Issues**
- Multiple state lookups per request
- Log truncation and index tracking
- HTTP overhead for polling
- Frontend processing delays

## Recommended Architecture

### Core Principles

1. **Single Source of Truth**: All state lives in one place (database + Redis for hot data)
2. **Event-Driven**: Server pushes events, client renders (no polling)
3. **Thin Client**: Frontend displays only, minimal processing
4. **Clean Separation**: Routes → Controllers → Services → Repositories
5. **Real-Time**: WebSocket for live updates, HTTP for commands

### Proposed Structure

```
backend/
├── api/
│   ├── routes/
│   │   ├── auth.py          # Login, logout, registration
│   │   ├── commands.py      # Command endpoint (thin)
│   │   └── websocket.py     # WebSocket handler
│   ├── middleware/
│   │   ├── auth.py          # Authentication decorators
│   │   └── session.py       # Session management
│   └── schemas/
│       └── responses.py     # Response models
│
├── core/
│   ├── state/
│   │   ├── game_state.py    # Single source of truth for game state
│   │   ├── room_state.py    # Room/item management
│   │   └── player_state.py  # Player state management
│   ├── events/
│   │   ├── event_bus.py     # Event system (pub/sub)
│   │   ├── event_types.py   # Event definitions
│   │   └── event_handler.py # Event processors
│   └── communication/
│       ├── websocket.py     # WebSocket manager
│       └── broadcast.py     # Room broadcasting
│
├── game/
│   ├── commands/
│   │   ├── registry.py      # Command registration
│   │   ├── handlers/        # Individual command handlers
│   │   └── parser.py        # Command parsing
│   ├── world/
│   │   ├── loader.py        # World data loading
│   │   └── rooms.py         # Room definitions
│   ├── npcs/
│   │   ├── manager.py       # NPC lifecycle
│   │   └── actions.py       # NPC periodic actions
│   ├── quests/
│   │   ├── manager.py       # Quest lifecycle
│   │   └── templates.py     # Quest definitions
│   └── engine.py            # Core game logic (commands dispatch)
│
├── persistence/
│   ├── database.py          # DB connection/setup
│   ├── repositories/
│   │   ├── game_repo.py     # Game state CRUD
│   │   ├── user_repo.py     # User CRUD
│   │   └── settings_repo.py # Settings CRUD
│   └── cache.py             # Redis/cache layer
│
└── app.py                   # Flask app setup (thin)

frontend/
├── js/
│   ├── connection.js        # WebSocket connection
│   ├── command.js           # Command sending
│   ├── render.js            # Message rendering (minimal)
│   ├── scroll.js            # Scroll management
│   └── ui.js                # UI interactions
├── css/
│   └── mud.css              # Styling
└── index.html               # HTML structure (minimal)
```

### Communication Flow

#### Command Flow (HTTP POST)
```
User types command
  ↓
Frontend sends: POST /api/command {command: "look"}
  ↓
Backend: routes/commands.py (thin handler)
  ↓
Backend: game/engine.py (process command)
  ↓
Backend: core/state/game_state.py (update state)
  ↓
Backend: core/events/event_bus.py (emit events)
  ↓
Backend: core/communication/websocket.py (push to client)
  ↓
Frontend: connection.js (receive event)
  ↓
Frontend: render.js (display message)
```

#### Real-Time Updates (WebSocket)
```
Server: NPC action occurs
  ↓
Server: core/events/event_bus.py (emit "npc_action" event)
  ↓
Server: core/communication/websocket.py (broadcast to room)
  ↓
Clients: connection.js (receive event)
  ↓
Clients: render.js (display immediately)
```

### State Management

#### Single Source of Truth
```python
# core/state/game_state.py
class GameState:
    def __init__(self, username):
        self.username = username
        self.location = None
        self.inventory = []
        # ... all player state
        
    @staticmethod
    def load(username):
        # Load from database
        # Cache in Redis
        return state
    
    def save(self):
        # Save to database
        # Update cache
        # Emit state_changed event
```

#### Event Bus
```python
# core/events/event_bus.py
class EventBus:
    def emit(self, event_type, data, room_id=None, username=None):
        # Store event
        # Broadcast via WebSocket if room_id
        # Send to specific user if username
        # Persist if needed
```

### WebSocket Protocol

#### Message Types

**Client → Server:**
```json
{
  "type": "command",
  "command": "look"
}
```

**Server → Client:**
```json
{
  "type": "message",
  "text": "You are in the town square.",
  "timestamp": 1234567890,
  "message_type": "system"  // system, say, emote, npc, ambiance
}

{
  "type": "command_response",
  "command": "look",
  "messages": [
    {"text": "> look", "type": "command"},
    {"text": "You are in...", "type": "system"}
  ]
}
```

### Benefits

1. **Real-Time**: WebSocket eliminates polling latency
2. **Simple**: No log tracking, just event streams
3. **Fast**: Direct state access, minimal processing
4. **Scalable**: Can add Redis pub/sub for multi-instance
5. **Testable**: Each layer can be tested independently
6. **Maintainable**: Clear separation of concerns

### Migration Strategy

**Phase 1: WebSocket Foundation**
1. Add WebSocket endpoint
2. Keep HTTP command endpoint
3. Gradually move real-time updates to WebSocket

**Phase 2: State Consolidation**
1. Create unified state manager
2. Migrate from global dicts to state manager
3. Add event bus

**Phase 3: Refactor Layers**
1. Extract routes from app.py
2. Extract state management
3. Extract game logic into services

**Phase 4: Frontend Simplification**
1. Remove log tracking
2. Remove polling
3. Event-driven rendering

### Immediate Quick Wins

1. **Replace polling with WebSocket** - Biggest performance win
2. **Remove log tracking** - Use events instead of log indices
3. **Extract routes** - Move route handlers to separate files
4. **Event bus** - Replace direct state manipulation with events

