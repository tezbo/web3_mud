# WebSocket Client Implementation Guide

## Frontend Socket.IO Client

Simple, maintainable Socket.IO client for the frontend.

### Basic Setup

Add Socket.IO client library to your HTML:

```html
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
```

### Client Implementation

```javascript
class MUDWebSocketClient {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
    }
    
    connect() {
        // Connect to Socket.IO server
        this.socket = io({
            transports: ['websocket', 'polling'], // Fallback to polling if WebSocket fails
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: this.maxReconnectAttempts
        });
        
        // Connection events
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.onConnected();
        });
        
        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.connected = false;
            this.onDisconnected();
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.onConnectionError(error);
        });
        
        // Game events
        this.socket.on('connected', (data) => {
            console.log('Server confirmed connection:', data);
            this.displayMessage(`Connected as ${data.username}`, 'system');
        });
        
        this.socket.on('command_response', (data) => {
            this.handleCommandResponse(data);
        });
        
        this.socket.on('room_message', (data) => {
            this.handleRoomMessage(data);
        });
        
        this.socket.on('room_changed', (data) => {
            this.handleRoomChanged(data);
        });
        
        this.socket.on('error', (data) => {
            this.displayMessage(`Error: ${data.message}`, 'error');
        });
        
        this.socket.on('pong', (data) => {
            // Keep-alive response
            console.debug('Pong received');
        });
    }
    
    sendCommand(command) {
        if (!this.connected) {
            this.displayMessage('Not connected. Please wait...', 'error');
            return;
        }
        
        const requestId = Date.now();
        this.socket.emit('command', {
            command: command,
            id: requestId
        });
        
        return requestId;
    }
    
    handleCommandResponse(data) {
        // Display command response
        if (data.response) {
            this.displayMessage(data.response, 'command_response');
        }
        
        // Handle any events that came with the response
        if (data.events && Array.isArray(data.events)) {
            data.events.forEach(event => {
                this.handleEvent(event);
            });
        }
    }
    
    handleRoomMessage(data) {
        // Display room message (NPC actions, ambiance, etc.)
        this.displayMessage(data.message, data.message_type || 'room');
    }
    
    handleRoomChanged(data) {
        // Player moved to new room
        this.displayMessage(`You moved to ${data.new_room}`, 'system');
    }
    
    handleEvent(event) {
        // Handle various event types
        switch(event.type) {
            case 'npc_action':
                this.displayMessage(event.data.action, 'npc');
                break;
            case 'ambiance':
                this.displayMessage(event.data.message, 'ambiance');
                break;
            // Add more event types as needed
        }
    }
    
    // Override these methods in your implementation
    onConnected() {
        // Called when WebSocket connects
    }
    
    onDisconnected() {
        // Called when WebSocket disconnects
    }
    
    onConnectionError(error) {
        // Called on connection error
    }
    
    displayMessage(message, type) {
        // Override this to display messages in your UI
        console.log(`[${type}] ${message}`);
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
        }
    }
}

// Usage
const mudClient = new MUDWebSocketClient();
mudClient.connect();

// Send command
mudClient.sendCommand('look');
```

### Integration with Existing Code

Replace the polling system with WebSocket:

```javascript
// OLD: Polling
function startAmbiancePolling() {
    setInterval(async () => {
        const res = await fetch('/poll', { method: 'POST', ... });
        // Process messages
    }, 3000);
}

// NEW: WebSocket
const mudClient = new MUDWebSocketClient();
mudClient.displayMessage = (message, type) => {
    // Use your existing appendText function
    appendText(message, false, false, false);
};
mudClient.connect();
```

### Command Integration

Replace HTTP command endpoint with WebSocket:

```javascript
// OLD: HTTP POST
async function sendCommand(cmd) {
    const res = await fetch('/command', {
        method: 'POST',
        body: JSON.stringify({ command: cmd })
    });
    // Process response
}

// NEW: WebSocket
function sendCommand(cmd) {
    mudClient.sendCommand(cmd);
}
```

### Benefits

1. **Real-time**: No polling delay
2. **Efficient**: Server pushes events, no constant polling
3. **Reliable**: Automatic reconnection
4. **Simple**: Clean API, easy to use
5. **Scalable**: Works with multi-instance setup via Redis



---

## Backend expectations

- The backend Socket.IO server is provided by `app.py` in this repository.  
- In local development, it typically runs on `http://localhost:5000` (or the port configured via environment variables).  
- In production (Render), the WebSocket endpoint is served by the `srv-d4gn2sf5r7bs73bcbqfg` service; refer to the Render dashboard for the correct public URL and TLS configuration.

When adjusting Socket.IO namespaces or events, keep the contract between this client and the server-side handlers in `app.py` in sync.
