# Redis Cache - High-Performance Caching Layer

## Overview

Redis provides a high-performance, in-memory caching layer for the Nexus Data Platform, dramatically improving response times and reducing database load.

### Components

- **Redis 7.2**: In-memory data structure store
- **Redis Sentinel**: High-availability monitoring and failover

## Quick Start

### 1. Start Services

```bash
cd infra/docker-stack
docker-compose -f docker-compose-production.yml up -d redis redis-sentinel
```

### 2. Verify Services

```bash
# Test Redis
docker exec -it nexus-redis redis-cli ping
# Expected: PONG

# Test Sentinel
docker exec -it nexus-redis-sentinel redis-cli -p 26379 ping
# Expected: PONG

# Check Sentinel monitoring
docker exec -it nexus-redis-sentinel redis-cli -p 26379 SENTINEL masters
```

## Use Cases

### 1. **API Response Caching**

#### Cache Query Results (Python/FastAPI)

```python
import redis
import json
from functools import wraps

# Initialize Redis client
redis_client = redis.Redis(
    host='redis',
    port=6379,
    decode_responses=True
)

def cache_response(ttl=300):
    """Decorator to cache API responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"api:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator

# Usage in FastAPI
@app.get("/destinations/{destination_id}")
@cache_response(ttl=600)
async def get_destination(destination_id: str):
    # This result will be cached for 10 minutes
    return fetch_from_database(destination_id)
```

### 2. **Session Storage**

```python
import uuid
from datetime import timedelta

class SessionStore:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "session:"
        self.ttl = 86400  # 24 hours
    
    def create_session(self, user_id: str, data: dict) -> str:
        """Create new session"""
        session_id = str(uuid.uuid4())
        session_key = f"{self.prefix}{session_id}"
        
        session_data = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            **data
        }
        
        self.redis.hmset(session_key, session_data)
        self.redis.expire(session_key, self.ttl)
        
        return session_id
    
    def get_session(self, session_id: str) -> dict:
        """Retrieve session data"""
        session_key = f"{self.prefix}{session_id}"
        return self.redis.hgetall(session_key)
    
    def update_session(self, session_id: str, data: dict):
        """Update session data"""
        session_key = f"{self.prefix}{session_id}"
        self.redis.hmset(session_key, data)
        self.redis.expire(session_key, self.ttl)
    
    def delete_session(self, session_id: str):
        """Delete session"""
        session_key = f"{self.prefix}{session_id}"
        self.redis.delete(session_key)

# Usage
session_store = SessionStore(redis_client)
session_id = session_store.create_session('USR123', {'role': 'user'})
```

### 3. **Rate Limiting**

```python
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def is_allowed(self, key: str, max_requests: int, window: int) -> bool:
        """
        Check if request is allowed
        
        Args:
            key: Unique identifier (e.g., user_id, ip_address)
            max_requests: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        current = self.redis.get(f"rate_limit:{key}")
        
        if current is None:
            # First request in window
            self.redis.setex(f"rate_limit:{key}", window, 1)
            return True
        
        if int(current) < max_requests:
            # Increment counter
            self.redis.incr(f"rate_limit:{key}")
            return True
        
        # Rate limit exceeded
        return False

# Usage in FastAPI
rate_limiter = RateLimiter(redis_client)

@app.get("/api/search")
async def search(request: Request):
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip, max_requests=100, window=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Process request
    return {"results": [...]}
```

### 4. **ClickHouse Query Cache**

```python
class QueryCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "query_cache:"
        self.default_ttl = 300  # 5 minutes
    
    def get_or_execute(self, query: str, execute_func, ttl=None):
        """Get cached result or execute query"""
        import hashlib
        
        # Generate cache key from query
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cache_key = f"{self.prefix}{query_hash}"
        
        # Try cache first
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Execute query
        result = execute_func(query)
        
        # Cache result
        self.redis.setex(
            cache_key,
            ttl or self.default_ttl,
            json.dumps(result)
        )
        
        return result

# Usage
query_cache = QueryCache(redis_client)

def fetch_from_clickhouse(query):
    # Execute ClickHouse query
    return client.query(query).result_rows

# Cached query execution
result = query_cache.get_or_execute(
    "SELECT * FROM tourism_analytics WHERE date = today()",
    fetch_from_clickhouse,
    ttl=600
)
```

### 5. **Real-time Analytics Counter**

```python
class AnalyticsCounter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def increment_page_view(self, page_url: str):
        """Increment page view counter"""
        key = f"stats:page_views:{page_url}"
        self.redis.incr(key)
    
    def increment_event(self, event_type: str, metadata: dict):
        """Track event with metadata"""
        # Increment counter
        self.redis.incr(f"stats:events:{event_type}")
        
        # Store recent events in list
        event_data = json.dumps({
            'timestamp': datetime.now().isoformat(),
            **metadata
        })
        self.redis.lpush(f"events:{event_type}", event_data)
        self.redis.ltrim(f"events:{event_type}", 0, 999)  # Keep last 1000
    
    def get_top_pages(self, limit=10):
        """Get top viewed pages"""
        # This requires sorted set
        return self.redis.zrevrange('stats:top_pages', 0, limit-1, withscores=True)
    
    def get_stats(self, event_type: str) -> int:
        """Get event count"""
        count = self.redis.get(f"stats:events:{event_type}")
        return int(count) if count else 0

# Usage
analytics = AnalyticsCounter(redis_client)
analytics.increment_page_view('/destinations/halong-bay')
analytics.increment_event('booking_completed', {'user_id': 'USR123', 'amount': 1500})
```

### 6. **Distributed Locking**

```python
import time

class DistributedLock:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def acquire(self, lock_name: str, timeout: int = 10) -> bool:
        """Acquire distributed lock"""
        lock_key = f"lock:{lock_name}"
        lock_value = str(uuid.uuid4())
        
        # Try to acquire lock
        acquired = self.redis.set(
            lock_key,
            lock_value,
            nx=True,  # Only set if doesn't exist
            ex=timeout  # Expire after timeout
        )
        
        if acquired:
            return lock_value
        return None
    
    def release(self, lock_name: str, lock_value: str):
        """Release distributed lock"""
        lock_key = f"lock:{lock_name}"
        
        # Lua script for atomic release
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        self.redis.eval(lua_script, 1, lock_key, lock_value)

# Usage for preventing duplicate processing
lock = DistributedLock(redis_client)

def process_payment(payment_id: str):
    lock_value = lock.acquire(f"payment:{payment_id}", timeout=30)
    
    if not lock_value:
        raise Exception("Payment already being processed")
    
    try:
        # Process payment
        charge_payment(payment_id)
    finally:
        lock.release(f"payment:{payment_id}", lock_value)
```

## Redis CLI Commands

### Basic Operations

```bash
# Connect to Redis
docker exec -it nexus-redis redis-cli

# Set/Get values
SET key "value"
GET key
DEL key

# Set with expiration
SETEX key 300 "value"  # Expires in 300 seconds
TTL key                 # Check remaining TTL

# Hash operations
HSET user:123 name "John" email "john@example.com"
HGET user:123 name
HGETALL user:123

# List operations
LPUSH events "event1"
RPUSH events "event2"
LRANGE events 0 -1

# Set operations
SADD tags "beach" "resort" "luxury"
SMEMBERS tags

# Sorted set operations
ZADD leaderboard 100 "user1"
ZADD leaderboard 200 "user2"
ZREVRANGE leaderboard 0 9 WITHSCORES  # Top 10
```

### Monitoring

```bash
# Monitor real-time commands
MONITOR

# Get server info
INFO
INFO stats
INFO memory

# Check memory usage
MEMORY USAGE key

# Get slow log
SLOWLOG GET 10
```

## Integration with Platform

### 1. **FastAPI Integration**

```python
# apps/api/main.py
from fastapi import FastAPI
import redis.asyncio as redis

app = FastAPI()

# Redis connection pool
redis_pool = redis.ConnectionPool(
    host='redis',
    port=6379,
    decode_responses=True,
    max_connections=20
)

@app.on_event("startup")
async def startup():
    app.state.redis = redis.Redis(connection_pool=redis_pool)

@app.on_event("shutdown")
async def shutdown():
    await app.state.redis.close()
    await redis_pool.disconnect()

# Use in endpoints
@app.get("/cached-data")
async def get_cached_data(request: Request):
    redis_client = request.app.state.redis
    
    cached = await redis_client.get("cached_data")
    if cached:
        return json.loads(cached)
    
    # Fetch and cache
    data = fetch_expensive_data()
    await redis_client.setex("cached_data", 300, json.dumps(data))
    return data
```

### 2. **Spark Integration**

```python
# jobs/spark/gold_to_clickhouse.py
from pyspark.sql import SparkSession
import redis

def cache_aggregation_results(df):
    """Cache aggregation results in Redis"""
    redis_client = redis.Redis(host='redis', port=6379)
    
    # Convert to pandas for easier handling
    results = df.toPandas().to_dict('records')
    
    for row in results:
        key = f"analytics:{row['metric_name']}:{row['date']}"
        redis_client.setex(key, 3600, json.dumps(row))
```

### 3. **Airflow Integration**

```python
# pipelines/airflow/dags/config_driven_pipeline.py
from airflow.providers.redis.hooks.redis import RedisHook

def check_task_lock(**context):
    """Prevent duplicate DAG runs"""
    redis_hook = RedisHook(redis_conn_id='redis_default')
    redis_conn = redis_hook.get_conn()
    
    dag_id = context['dag'].dag_id
    lock_key = f"dag_lock:{dag_id}"
    
    if redis_conn.exists(lock_key):
        raise Exception(f"DAG {dag_id} is already running")
    
    # Set lock (expires in 4 hours)
    redis_conn.setex(lock_key, 14400, 'locked')
```

## Performance Tuning

### 1. **Memory Optimization**

```bash
# Check memory usage
docker exec -it nexus-redis redis-cli INFO memory

# Analyze key patterns
docker exec -it nexus-redis redis-cli --bigkeys

# Sample keys
docker exec -it nexus-redis redis-cli --scan --pattern 'stats:*'
```

### 2. **Eviction Policy**

Current policy: `allkeys-lru` (evicts least recently used keys)

Other options in `redis.conf`:
- `allkeys-lfu`: Least frequently used
- `volatile-lru`: LRU among keys with expiration
- `volatile-ttl`: Evict keys with shortest TTL

### 3. **Persistence Tuning**

```conf
# RDB snapshots (in redis.conf)
save 900 1      # After 15min if ≥1 change
save 300 10     # After 5min if ≥10 changes
save 60 10000   # After 1min if ≥10000 changes

# AOF persistence
appendonly yes
appendfsync everysec  # Balance between performance and durability
```

## High Availability with Sentinel

### Monitoring

```bash
# Check Sentinel status
docker exec -it nexus-redis-sentinel redis-cli -p 26379 SENTINEL masters

# Get master info
docker exec -it nexus-redis-sentinel redis-cli -p 26379 SENTINEL get-master-addr-by-name nexus-redis
```

### Client Configuration (Python)

```python
from redis.sentinel import Sentinel

# Connect via Sentinel
sentinel = Sentinel([('redis-sentinel', 26379)])

# Get master for writes
master = sentinel.master_for('nexus-redis', socket_timeout=0.1)
master.set('key', 'value')

# Get replica for reads
replica = sentinel.slave_for('nexus-redis', socket_timeout=0.1)
value = replica.get('key')
```

## Security (Production)

### 1. **Enable Authentication**

Edit `redis/redis.conf`:
```conf
requirepass your-strong-password-here
```

### 2. **Update Client Code**

```python
redis_client = redis.Redis(
    host='redis',
    port=6379,
    password='your-strong-password-here',
    decode_responses=True
)
```

### 3. **Disable Dangerous Commands**

```conf
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_abc123"
```

## Monitoring & Metrics

### 1. **Key Metrics**

```bash
# Connected clients
INFO clients

# Memory usage
INFO memory

# Hit rate
INFO stats | grep keyspace
```

### 2. **Prometheus Integration**

Redis metrics are exposed via Redis Exporter (can be added if needed).

### 3. **Alerting**

Monitor:
- Memory usage > 80%
- Connected clients > threshold
- Evicted keys increasing
- Slow queries

## Troubleshooting

### Issue: Connection refused

```bash
# Check if Redis is running
docker ps | grep redis

# Check logs
docker logs nexus-redis

# Test connection
docker exec -it nexus-redis redis-cli ping
```

### Issue: High memory usage

```bash
# Find large keys
redis-cli --bigkeys

# Analyze memory
redis-cli MEMORY DOCTOR

# Flush specific pattern
redis-cli --scan --pattern 'old:*' | xargs redis-cli DEL
```

### Issue: Slow performance

```bash
# Check slow log
redis-cli SLOWLOG GET 10

# Monitor commands
redis-cli MONITOR

# Check latency
redis-cli --latency
```

## Backup & Restore

### 1. **RDB Snapshot**

```bash
# Manual snapshot
docker exec -it nexus-redis redis-cli BGSAVE

# Copy snapshot
docker cp nexus-redis:/data/dump.rdb ./backup/
```

### 2. **AOF Backup**

```bash
# Copy AOF file
docker cp nexus-redis:/data/appendonly.aof ./backup/
```

### 3. **Restore**

```bash
# Stop Redis
docker stop nexus-redis

# Copy backup
docker cp ./backup/dump.rdb nexus-redis:/data/

# Start Redis
docker start nexus-redis
```

## Best Practices

1. **Use appropriate data types**: Choose the right data structure for your use case
2. **Set expiration**: Always set TTL to prevent memory bloat
3. **Use pipelining**: Batch multiple commands for better performance
4. **Connection pooling**: Reuse connections instead of creating new ones
5. **Monitor memory**: Set up alerts for high memory usage
6. **Use namespaces**: Prefix keys to organize data (e.g., `user:123`, `session:abc`)
7. **Avoid large values**: Keep values small (<1MB ideal)
8. **Use Lua scripts**: For atomic multi-step operations

## Resources

- **Redis Documentation**: https://redis.io/documentation
- **Redis Commands**: https://redis.io/commands
- **Redis Data Types**: https://redis.io/docs/data-types/
- **Redis Client (Python)**: https://redis-py.readthedocs.io/
