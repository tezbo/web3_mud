# Scaling Architecture for 1000+ Concurrent Players

## Design Principles for Scale

1. **Stateless Servers**: All application servers are identical, no in-memory state
2. **Shared State Store**: Redis for hot data, database for persistence
3. **Horizontal Scaling**: Add servers, not complexity
4. **Efficient Connections**: Connection pooling, async I/O
5. **Event-Driven**: Redis pub/sub for cross-instance events
6. **Optimistic Updates**: Client shows immediate feedback, server validates

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client 1  │     │   Client 2  │     │  Client N   │
│  (Browser)  │     │  (Browser)  │     │  (Browser)  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Load Balancer│
                    │  (Nginx/HA) │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌─────▼─────┐      ┌────▼────┐
   │ Flask   │       │  Flask    │      │  Flask  │
   │Instance │       │ Instance  │      │Instance │
   │    1    │       │     2     │      │    N    │
   └────┬────┘       └─────┬─────┘      └────┬────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │   Redis   │   │ PostgreSQL │   │   Redis   │
    │  (Cache)  │   │  (Primary) │   │ (Pub/Sub) │
    └───────────┘   └────────────┘   └───────────┘
```

## Component Design

### 1. Redis Usage

#### Redis 1: Cache (Shared State)
- Player game state (hot data)
- Room state (items, NPCs)
- Global game state
- Session data
- **TTL**: 5-15 minutes, refresh on read

#### Redis 2: Pub/Sub (Events)
- Room broadcasts
- Player-specific messages
- NPC actions
- Ambient messages
- System events

**Key Pattern**: Subscribe to `room:{room_id}` and `user:{username}` channels

### 2. Database Strategy

#### Primary Store (PostgreSQL/SQLite)
- User accounts
- Game state (cold data, persisted)
- Quest progress
- Historical data
- **Connection Pooling**: SQLAlchemy with pool_size=20, max_overflow=40

#### Caching Strategy
- **Hot Data**: Redis (player state, room state, active sessions)
- **Warm Data**: Database (loaded on demand, cached)
- **Cold Data**: Database only (historical logs, completed quests)

### 3. WebSocket Management

#### Connection Handling
- **Per-Instance**: Use Flask-SocketIO with Redis adapter
- **Cross-Instance**: Redis pub/sub for broadcasting
- **Connection Limits**: ~500 connections per instance (2 instances for 1000)

#### Message Protocol
```json
// Client → Server
{
  "type": "command",
  "command": "look",
  "id": "req_123"  // Request ID for response matching
}

// Server → Client
{
  "type": "response",
  "id": "req_123",
  "messages": [...]
}

// Server → Client (Broadcast)
{
  "type": "room_message",
  "room_id": "town_square",
  "message": "...",
  "message_type": "npc"
}
```

### 4. State Management

#### Player State
```python
# Redis keys
player:{username}:state      # Full game state (JSON)
player:{username}:location   # Current room
player:{username}:session    # Session metadata

# Database
games table: Full state backup (persisted every N seconds)
```

#### Room State
```python
# Redis keys
room:{room_id}:state         # Room state (items, NPCs)
room:{room_id}:players       # Set of player usernames in room
room:{room_id}:events        # Recent events (for new joiners)
```

#### Global State
```python
# Redis keys
global:world_time           # Game time
global:weather              # Current weather
global:quests               # Quest global state
global:active_players       # Set of active players
```

### 5. Event System

#### Event Types
```python
EVENT_TYPES = {
    "player_move": {"room_id": "...", "username": "..."},
    "npc_action": {"room_id": "...", "npc_id": "...", "action": "..."},
    "ambiance": {"room_id": "...", "message": "..."},
    "player_message": {"room_id": "...", "username": "...", "message": "..."},
    "quest_update": {"username": "...", "quest_id": "..."},
}
```

#### Publishing
```python
# Single room
redis.publish(f"room:{room_id}", json.dumps(event))

# Specific player
redis.publish(f"user:{username}", json.dumps(event))

# All instances
redis.publish("global", json.dumps(event))
```

### 6. Performance Optimizations

#### Database
- **Connection Pooling**: SQLAlchemy pool with proper sizing
- **Indexes**: username, user_id, room_id, quest_id
- **Batch Writes**: Buffer state saves, batch commit
- **Read Replicas**: If using PostgreSQL (future)

#### Redis
- **Pipeline Operations**: Batch Redis commands
- **Pipelining**: Multiple commands in one round-trip
- **Compression**: Compress large state objects
- **Key Expiration**: Auto-expire stale data

#### Application
- **Async I/O**: Use async/await for I/O operations
- **Background Tasks**: Celery for heavy operations
- **Rate Limiting**: Per-user command rate limits
- **Request Batching**: Batch multiple updates

### 7. Monitoring & Observability

#### Metrics to Track
- WebSocket connections per instance
- Commands per second
- Redis hit/miss ratio
- Database query latency
- Event propagation latency
- Player state size

#### Logging
- Structured logging (JSON)
- Request IDs for tracing
- Error aggregation (Sentry)
- Performance profiling

## Implementation Plan

### Phase 1: Foundation (Current Sprint)
1. Add Flask-SocketIO + Redis adapter
2. Create event bus with Redis pub/sub
3. Add Redis connection and caching layer
4. Create unified state manager
5. Replace polling with WebSocket

### Phase 2: State Migration (Next Sprint)
1. Migrate ACTIVE_GAMES to Redis
2. Migrate ROOM_STATE to Redis
3. Migrate global state to Redis
4. Add database persistence layer
5. Implement state sync (Redis → DB)

### Phase 3: Scaling Preparation (Future)
1. Add connection pooling
2. Implement rate limiting
3. Add monitoring/observability
4. Load testing (1000 concurrent users)
5. Optimize bottlenecks

### Phase 4: Production Hardening (Future)
1. Multi-instance deployment
2. Database read replicas
3. Redis cluster (if needed)
4. CDN for static assets
5. Auto-scaling configuration

## Resource Estimates (1000 Concurrent Players)

### Server Resources (Per Instance)
- **CPU**: 2-4 cores
- **Memory**: 2-4 GB RAM
- **Network**: 100 Mbps
- **Instances**: 2-3 (for redundancy + load distribution)

### Redis
- **Memory**: 4-8 GB (for cache + pub/sub)
- **CPU**: 2 cores
- **Network**: 100 Mbps

### Database
- **Storage**: 50-100 GB (depends on logs/retention)
- **Memory**: 4-8 GB
- **CPU**: 2-4 cores

### Total Infrastructure
- **Application Servers**: 2-3 instances
- **Redis**: 1 instance (can scale to cluster)
- **Database**: 1 instance (can add read replicas)
- **Load Balancer**: 1 instance

## Cost Optimization

1. **Spot Instances**: Use for non-critical components
2. **Reserved Instances**: For predictable workloads
3. **Auto-Scaling**: Scale down during low traffic
4. **Data Retention**: Archive old logs, limit history
5. **Caching**: Aggressive caching reduces DB load

## Failure Handling

### Redis Failure
- **Graceful Degradation**: Fall back to database
- **Circuit Breaker**: Stop writing to Redis if down
- **Reconnection**: Auto-reconnect with exponential backoff

### Database Failure
- **Read-Only Mode**: Serve from cache only
- **Queue Commands**: Buffer writes, replay on recovery
- **Backup Strategy**: Regular backups, point-in-time recovery

### Instance Failure
- **Health Checks**: Load balancer detects unhealthy instances
- **Session Migration**: Redis-based sessions survive instance failure
- **State Recovery**: Recover from database on new instance

## Migration Strategy

### Zero-Downtime Migration
1. Add Redis alongside existing system
2. Dual-write to both old and new system
3. Gradually migrate reads to Redis
4. Switch writes to Redis only
5. Remove old system

### Rollback Plan
- Keep old polling system until WebSocket is stable
- Feature flag for new/old architecture
- Monitor error rates, rollback if needed

