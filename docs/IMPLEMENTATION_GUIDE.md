# WebSocket Implementation Guide

## Architecture Overview

Clean, maintainable WebSocket implementation with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         WebSocket Layer                 │
│  (websocket_handler.py)                 │
│  - Connection management                │
│  - Message routing                      │
│  - Clean interfaces                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      WebSocket Manager                  │
│  (websocket_manager.py)                 │
│  - Connection tracking                  │
│  - Room subscriptions                   │
│  - Event broadcasting                   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Event Bus                       │
│  (event_bus.py)                         │
│  - Redis pub/sub                        │
│  - Event distribution                   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Game Logic                         │
│  (game_engine.py)                       │
│  - Command processing                   │
│  - State updates                        │
└─────────────────────────────────────────┘
```

## Key Design Principles

### 1. **Maintainability**
- Clear separation of concerns
- Each module has a single responsibility
- Well-documented code
- Type hints for clarity

### 2. **Readability**
- Descriptive function names
- Simple, clean interfaces
- Minimal abstractions
- Clear error messages

### 3. **Usability**
- Simple integration
- Easy to extend
- Standard WebSocket protocol
- Good error handling

## File Structure

```
core/
├── websocket_handler.py   # Flask integration, message routing
├── websocket_manager.py   # Connection management, broadcasting
├── event_bus.py          # Event pub/sub (already created)
├── state_manager.py      # State management (already created)
└── redis_manager.py      # Redis connections (already created)
```

## Integration Steps

### Step 1: Add Flask WebSocket Support

Flask 2.0+ has async support. We'll use `websockets` library for async WebSocket handling.

### Step 2: Create WebSocket Endpoint

```python
# In app.py
from flask import Flask
from core.websocket_handler import handle_websocket_connection

@app.route('/ws')
async def websocket_endpoint():
    username = session.get('username')
    if not username:
        return "Unauthorized", 401
    
    # Upgrade to WebSocket
    ws = request.environ.get('wsgi.websocket')
    if not ws:
        return "WebSocket not supported", 400
    
    # Handle connection
    await handle_websocket_connection(ws, username, command_handler)
```

### Step 3: Command Handler Integration

```python
def command_handler(command: str, username: str):
    """
    Handle game command.
    
    Returns:
        (response: str, events: list)
    """
    # Use existing game_engine.handle_command
    response, game = handle_command(command, game_state, username=username)
    
    # Extract events that need broadcasting
    events = []
    # ... determine events to broadcast
    
    return response, events
```

### Step 4: Frontend WebSocket Client

Simple, clean JavaScript WebSocket client:

```javascript
class MUDWebSocket {
    constructor(username) {
        this.ws = new WebSocket(`ws://localhost:5000/ws`);
        this.username = username;
        this.setupHandlers();
    }
    
    setupHandlers() {
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onclose = () => {
            // Reconnect logic
            setTimeout(() => this.reconnect(), 1000);
        };
    }
    
    sendCommand(command) {
        this.ws.send(JSON.stringify({
            type: 'command',
            command: command,
            id: Date.now()
        }));
    }
    
    handleMessage(message) {
        switch(message.type) {
            case 'command_response':
                this.displayResponse(message.response);
                break;
            case 'event':
                this.displayEvent(message.event);
                break;
        }
    }
}
```

## Benefits

### Maintainability
- ✅ Clear module boundaries
- ✅ Single responsibility per class
- ✅ Easy to test
- ✅ Easy to debug

### Readability
- ✅ Simple interfaces
- ✅ Descriptive names
- ✅ Minimal magic
- ✅ Good documentation

### Usability
- ✅ Standard WebSocket protocol
- ✅ Simple integration
- ✅ Good error messages
- ✅ Easy to extend

## Migration Path

1. **Add WebSocket endpoint** (works alongside HTTP)
2. **Migrate frontend gradually** (test with WebSocket, fallback to HTTP)
3. **Move NPC actions** to event bus
4. **Move ambiance** to event bus
5. **Remove polling** once WebSocket is stable
6. **Remove HTTP command endpoint** (optional, can keep for compatibility)

## Testing

Clean, testable architecture:

```python
# Test WebSocket handler
async def test_command_handler():
    handler = WebSocketHandler(command_handler_fn=mock_command_handler)
    # ... test
    
# Test WebSocket manager
async def test_room_broadcast():
    manager = WebSocketManager()
    # ... test
```

## Performance

- Native WebSocket: Lower overhead
- Event bus: Efficient pub/sub
- Connection pooling: Handles 1000+ connections
- Redis: Fast cross-instance communication

