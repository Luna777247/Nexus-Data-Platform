"""
Nexus Data Platform - FastAPI Endpoints
REST & GraphQL API for tourism data serving
"""

from dotenv import load_dotenv
import os

# Load .env.local if exists (for local dev outside Docker)
env_local_path = os.path.join(os.path.dirname(__file__), ".env.local")
if os.path.exists(env_local_path):
    load_dotenv(env_local_path)
    print(f"✅ Loaded environment from {env_local_path}")

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
import redis
import json
import yaml
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

# RBAC imports
from auth import (
    login_for_access_token, 
    LoginRequest, 
    Token,
    get_current_active_user,
    require_permissions,
    require_roles,
    log_audit_event
)
from rbac import User, Permission, Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHARED_SCHEMA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared", "schemas")
)
TOUR_SCHEMA_PATH = os.path.join(SHARED_SCHEMA_DIR, "tour.schema.json")

def _load_schema_fields(path: str, fallback: List[str]) -> set:
    try:
        with open(path, "r") as schema_file:
            schema = json.load(schema_file)
        return set(schema.get("properties", {}).keys())
    except Exception as exc:
        logger.warning(f"⚠️  Could not load shared schema: {exc}")
        return set(fallback)

TOUR_SCHEMA_FIELDS = _load_schema_fields(
    TOUR_SCHEMA_PATH,
    ["id", "name", "region", "price", "rating", "tags"]
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_SOURCES_PATH = os.path.join(REPO_ROOT, "conf", "sources.yaml")
SOURCES_PATH = os.getenv("CONFIG_SOURCES_PATH", DEFAULT_SOURCES_PATH)

DATA_SOURCES_DB_HOST = os.getenv("DATA_SOURCES_DB_HOST", "postgres")
DATA_SOURCES_DB_PORT = int(os.getenv("DATA_SOURCES_DB_PORT", "5432"))
DATA_SOURCES_DB_USER = os.getenv("DATA_SOURCES_DB_USER", "admin")
DATA_SOURCES_DB_PASSWORD = os.getenv("DATA_SOURCES_DB_PASSWORD", "admin123")
DATA_SOURCES_DB_NAME = os.getenv("DATA_SOURCES_DB_NAME", "nexus_data")

# ============================================
# Initialize FastAPI App
# ============================================

app = FastAPI(
    title="Nexus Data Platform API",
    description="Tourism Data Platform serving layer",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Initialize Redis Cache
# ============================================

try:
    cache = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
        password=os.getenv("REDIS_PASSWORD", "redis123")
    )
    cache.ping()
    logger.info("✅ Connected to Redis")
except Exception as e:
    logger.warning(f"⚠️  Could not connect to Redis: {e}")
    cache = None

# ============================================
# Initialize Kafka Producer
# ============================================

kafka_producer = None
try:
    kafka_producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(","),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',  # Wait for all replicas
        retries=3,
        max_in_flight_requests_per_connection=1,  # Ensure ordering
    )
    # Test connection
    kafka_producer.send("topic_user_events", value={"test": "connection"}).get(timeout=5)
    logger.info("✅ Connected to Kafka at " + os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
except Exception as e:
    logger.warning(f"⚠️  Could not connect to Kafka: {e}")
    kafka_producer = None

# ============================================
# Data Models
# ============================================

class TourData:
    """Sample tour data structure"""
    def __init__(self, tour_id, name, region, price, rating, tags):
        self.tour_id = tour_id
        self.name = name
        self.region = region
        self.price = price
        self.rating = rating
        self.tags = tags
    
    def to_dict(self):
        data = {
            "id": self.tour_id,
            "name": self.name,
            "region": self.region,
            "price": self.price,
            "rating": self.rating,
            "tags": self.tags
        }
        return {key: value for key, value in data.items() if key in TOUR_SCHEMA_FIELDS}

# ============================================
# Sample Data
# ============================================

SAMPLE_TOURS = [
    TourData("t1", "Hanoi City Tour", "VN", 59.99, 4.8, ["cultural", "city", "history"]),
    TourData("t2", "Halong Bay Cruise", "VN", 199.99, 4.9, ["adventure", "nature", "sea"]),
    TourData("t3", "Sapa Trekking", "VN", 149.99, 4.7, ["hiking", "nature", "mountain"]),
    TourData("t4", "Singapore Marina Bay", "SG", 79.99, 4.6, ["city", "modern", "views"]),
    TourData("t5", "Bangkok Street Food", "TH", 49.99, 4.5, ["food", "cultural", "nightlife"]),
    TourData("t6", "Bali Beach Resort", "ID", 199.99, 4.8, ["beach", "relaxation", "tropical"]),
]

SAMPLE_EVENTS = [
    {"id": "e1", "user_id": 101, "tour_id": "t1", "event_type": "booking", "amount": 59.99, "region": "VN"},
    {"id": "e2", "user_id": 102, "tour_id": "t2", "event_type": "view", "amount": 0, "region": "VN"},
    {"id": "e3", "user_id": 103, "tour_id": "t4", "event_type": "booking", "amount": 79.99, "region": "SG"},
]

# ============================================
# Data Sources Storage
# ============================================

class DataSourceCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    source_id: str
    source_name: str
    source_type: str
    location: str
    enabled: bool = True
    kafka_topic: Optional[str] = None
    target_table: Optional[str] = None
    schedule_interval: Optional[str] = None
    category: Optional[str] = None
    method: Optional[str] = None
    auth_type: Optional[str] = None
    format: Optional[str] = None
    required_fields: Optional[List[str]] = None


class DataSourceUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    location: Optional[str] = None
    enabled: Optional[bool] = None
    kafka_topic: Optional[str] = None
    target_table: Optional[str] = None
    schedule_interval: Optional[str] = None
    category: Optional[str] = None
    method: Optional[str] = None
    auth_type: Optional[str] = None
    format: Optional[str] = None
    required_fields: Optional[List[str]] = None


class GlobalConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")


def _get_db_connection():
    return psycopg2.connect(
        host=DATA_SOURCES_DB_HOST,
        port=DATA_SOURCES_DB_PORT,
        user=DATA_SOURCES_DB_USER,
        password=DATA_SOURCES_DB_PASSWORD,
        dbname=DATA_SOURCES_DB_NAME,
    )


def _ensure_data_sources_table():
    create_sql = """
        CREATE TABLE IF NOT EXISTS data_sources (
            source_id TEXT PRIMARY KEY,
            source_name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """
    with _get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(create_sql)


def _normalize_source_payload(payload: Dict) -> Dict:
    normalized = dict(payload)
    source_id = normalized.get("source_id")
    if source_id:
        normalized.setdefault("kafka_topic", f"topic_{source_id}")
        normalized.setdefault("target_table", f"bronze_{source_id}")
    normalized.setdefault("schedule_interval", "@daily")
    normalized.setdefault("enabled", True)
    return normalized


def _row_to_source(row: Dict) -> Dict:
    source = dict(row.get("config") or {})
    source.setdefault("source_id", row.get("source_id"))
    source.setdefault("source_name", row.get("source_name"))
    source.setdefault("source_type", row.get("source_type"))
    source.setdefault("enabled", row.get("enabled"))
    return source


def _fetch_sources_from_db(enabled_only: Optional[bool] = None) -> List[Dict]:
    query = "SELECT source_id, source_name, source_type, enabled, config FROM data_sources"
    params = []
    if enabled_only is True:
        query += " WHERE enabled = TRUE"
    elif enabled_only is False:
        query += " WHERE enabled = FALSE"

    with _get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
    return [_row_to_source(row) for row in rows]


def _load_yaml_global_config() -> Dict:
    if not os.path.exists(SOURCES_PATH):
        return {}
    try:
        with open(SOURCES_PATH, "r") as yaml_file:
            config = yaml.safe_load(yaml_file) or {}
        return config.get("global", {})
    except Exception as exc:
        logger.warning(f"Could not load global config from YAML: {exc}")
        return {}


def _write_sources_yaml_with_global(sources: List[Dict], global_config: Dict):
    payload = {
        "global": global_config,
        "sources": sources,
    }
    os.makedirs(os.path.dirname(SOURCES_PATH), exist_ok=True)
    with open(SOURCES_PATH, "w") as yaml_file:
        yaml.safe_dump(payload, yaml_file, sort_keys=False)


def _write_sources_yaml(sources: List[Dict]):
    global_config = _load_yaml_global_config()
    _write_sources_yaml_with_global(sources, global_config)


def _seed_sources_from_yaml():
    if not os.path.exists(SOURCES_PATH):
        return
    try:
        with open(SOURCES_PATH, "r") as yaml_file:
            config = yaml.safe_load(yaml_file) or {}
    except Exception as exc:
        logger.warning(f"Could not read YAML sources for seeding: {exc}")
        return

    sources = config.get("sources", [])
    if not sources:
        return

    with _get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM data_sources")
            count = cursor.fetchone()[0]
            if count > 0:
                return

            insert_sql = """
                INSERT INTO data_sources (source_id, source_name, source_type, enabled, config)
                VALUES (%s, %s, %s, %s, %s)
            """
            for source in sources:
                normalized = _normalize_source_payload(source)
                cursor.execute(
                    insert_sql,
                    (
                        normalized.get("source_id"),
                        normalized.get("source_name"),
                        normalized.get("source_type"),
                        normalized.get("enabled", True),
                        Json(normalized),
                    ),
                )

# ============================================
# Helper Functions
# ============================================

def get_from_cache(key: str):
    """Get data from Redis cache"""
    if cache:
        try:
            data = cache.get(key)
            if data:
                logger.info(f"Cache HIT: {key}")
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache error: {e}")
    return None

def set_to_cache(key: str, data: dict, ttl: int = 3600):
    """Set data in Redis cache"""
    if cache:
        try:
            cache.setex(key, ttl, json.dumps(data))
            logger.info(f"Cache SET: {key}")
        except Exception as e:
            logger.warning(f"Cache error: {e}")

# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API status"""
    return {
        "status": "🚀 Nexus Data Platform API is running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs"
    }

# ============================================
# HEALTH & STATUS ENDPOINTS
# ============================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    cache_status = "✅ Connected" if cache else "⚠️  Disconnected"
    
    return {
        "status": "healthy",
        "services": {
            "api": "✅ Running",
            "cache": cache_status,
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics", tags=["Metrics"])
async def get_metrics():
    """Get platform metrics"""
    cache_key = "platform_metrics"
    
    # Try cache first
    cached = get_from_cache(cache_key)
    if cached:
        return cached
    
    metrics = {
        "total_tours": len(SAMPLE_TOURS),
        "total_events": len(SAMPLE_EVENTS),
        "regions": ["VN", "SG", "TH", "ID"],
        "regions_count": 4,
        "avg_tour_price": sum(t.price for t in SAMPLE_TOURS) / len(SAMPLE_TOURS),
        "avg_tour_rating": sum(t.rating for t in SAMPLE_TOURS) / len(SAMPLE_TOURS),
        "cached_at": datetime.now().isoformat()
    }
    
    # Cache for 5 minutes
    set_to_cache(cache_key, metrics, ttl=300)
    return metrics

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.post("/api/v1/auth/login", response_model=Token, tags=["Authentication"])
async def login(login_data: LoginRequest):
    """
    User login - Returns JWT access token
    
    **Demo Credentials:**
    - admin / password123
    - engineer / password123
    - scientist / password123
    - analyst / password123
    - viewer / password123
    - api_client / password123
    """
    return await login_for_access_token(login_data)


@app.get("/api/v1/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user information"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "roles": [role.value for role in current_user.roles],
        "permissions": [perm.value for perm in current_user.get_permissions()],
        "active": current_user.active
    }


@app.get("/api/v1/auth/permissions", tags=["Authentication"])
async def get_user_permissions(current_user: User = Depends(get_current_active_user)):
    """Get permissions for current user"""
    permissions = current_user.get_permissions()
    return {
        "username": current_user.username,
        "roles": [role.value for role in current_user.roles],
        "permissions": sorted([perm.value for perm in permissions])
    }
    
    # Cache for 1 hour
    set_to_cache(cache_key, metrics, ttl=3600)
    
    return metrics

# ============================================
# DATA SOURCES ENDPOINTS
# ============================================

@app.get("/api/v1/data-sources", tags=["Data Sources"])
async def list_data_sources(enabled: Optional[bool] = None):
    try:
        sources = _fetch_sources_from_db(enabled_only=enabled)
    except Exception as exc:
        logger.error(f"Failed to load data sources: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load data sources")
    return {"data": sources, "count": len(sources)}


@app.post("/api/v1/data-sources", tags=["Data Sources"])
async def create_data_source(
    payload: DataSourceCreate,
    current_user: User = Depends(require_permissions(Permission.MANAGE_PIPELINES))
):
    """Create new data source - Requires DATA_ENGINEER or ADMIN role"""
    log_audit_event(current_user, "CREATE", f"data_source:{payload.source_id}")
    source = _normalize_source_payload(payload.model_dump(exclude_none=True))
    insert_sql = """
        INSERT INTO data_sources (source_id, source_name, source_type, enabled, config)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        with _get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    insert_sql,
                    (
                        source["source_id"],
                        source["source_name"],
                        source["source_type"],
                        source.get("enabled", True),
                        Json(source),
                    ),
                )
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Source already exists")
    except Exception as exc:
        logger.error(f"Failed to create data source: {exc}")
        raise HTTPException(status_code=500, detail="Failed to create data source")

    try:
        _write_sources_yaml(_fetch_sources_from_db())
    except Exception as exc:
        logger.warning(f"Failed to export sources to YAML: {exc}")

    return {"status": "success", "data": source}


# ============================================
# GLOBAL CONFIG ENDPOINTS (must be before /{source_id} routes)
# ============================================

@app.get("/api/v1/data-sources/global", tags=["Data Sources"])
async def get_global_config():
    return {"global": _load_yaml_global_config()}


@app.put("/api/v1/data-sources/global", tags=["Data Sources"])
async def update_global_config(
    payload: GlobalConfigUpdate,
    current_user: User = Depends(require_roles(Role.ADMIN, Role.DATA_ENGINEER))
):
    """Update global config - Requires ADMIN or DATA_ENGINEER role"""
    log_audit_event(current_user, "UPDATE", "global_config")
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided")

    global_config = _load_yaml_global_config()
    global_config.update(update_data)

    try:
        sources = _fetch_sources_from_db()
        _write_sources_yaml_with_global(sources, global_config)
    except Exception as exc:
        logger.error(f"Failed to update global config: {exc}")
        raise HTTPException(status_code=500, detail="Failed to update global config")

    return {"status": "success", "global": global_config}


@app.post("/api/v1/data-sources/export", tags=["Data Sources"])
async def export_data_sources(include_content: bool = False):
    try:
        sources = _fetch_sources_from_db()
        _write_sources_yaml(sources)
    except Exception as exc:
        logger.error(f"Failed to export sources: {exc}")
        raise HTTPException(status_code=500, detail="Failed to export sources")

    response = {
        "status": "success",
        "path": SOURCES_PATH,
        "count": len(sources),
    }

    if include_content:
        try:
            with open(SOURCES_PATH, "r") as yaml_file:
                response["content"] = yaml_file.read()
        except Exception as exc:
            logger.warning(f"Failed to read exported YAML: {exc}")

    return response


# ============================================
# DATA SOURCE CRUD WITH DYNAMIC PATH (must be after /global routes)
# ============================================

@app.put("/api/v1/data-sources/{source_id}", tags=["Data Sources"])
async def update_data_source(source_id: str, payload: DataSourceUpdate):
    update_data = payload.model_dump(exclude_none=True)
    update_data.pop("source_id", None)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided")

    with _get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT source_id, source_name, source_type, enabled, config FROM data_sources WHERE source_id = %s",
                (source_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Source not found")

            current = _row_to_source(row)
            current.update(update_data)
            normalized = _normalize_source_payload(current)

            cursor.execute(
                """
                UPDATE data_sources
                SET source_name = %s,
                    source_type = %s,
                    enabled = %s,
                    config = %s,
                    updated_at = NOW()
                WHERE source_id = %s
                """,
                (
                    normalized.get("source_name"),
                    normalized.get("source_type"),
                    normalized.get("enabled", True),
                    Json(normalized),
                    source_id,
                ),
            )

    try:
        _write_sources_yaml(_fetch_sources_from_db())
    except Exception as exc:
        logger.warning(f"Failed to export sources to YAML: {exc}")

    return {"status": "success", "data": normalized}


@app.delete("/api/v1/data-sources/{source_id}", tags=["Data Sources"])
async def delete_data_source(source_id: str):
    with _get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM data_sources WHERE source_id = %s", (source_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Source not found")

    try:
        _write_sources_yaml(_fetch_sources_from_db())
    except Exception as exc:
        logger.warning(f"Failed to export sources to YAML: {exc}")

    return {"status": "success", "source_id": source_id}


# ============================================
# TOURS ENDPOINTS
# ============================================

@app.get("/api/v1/tours", tags=["Tours"])
async def list_tours(
    region: Optional[str] = Query(None),
    min_price: float = Query(0),
    max_price: float = Query(10000),
    limit: int = Query(10, le=100),
    skip: int = Query(0),
):
    """
    Get list of tours with optional filters
    
    Query parameters:
    - region: Filter by region (VN, SG, TH, ID)
    - min_price/max_price: Price range filter
    - limit: Max results (default 10, max 100)
    - skip: Offset for pagination
    """
    
    cache_key = f"tours:{region}:{min_price}:{max_price}:{limit}:{skip}"
    cached = get_from_cache(cache_key)
    if cached:
        return cached
    
    # Filter tours
    filtered = SAMPLE_TOURS
    
    if region:
        filtered = [t for t in filtered if t.region == region.upper()]
    
    filtered = [t for t in filtered if min_price <= t.price <= max_price]
    
    # Apply pagination
    filtered = filtered[skip : skip + limit]
    
    result = {
        "data": [t.to_dict() for t in filtered],
        "count": len(filtered),
        "skip": skip,
        "limit": limit
    }
    
    set_to_cache(cache_key, result, ttl=3600)
    return result

@app.get("/api/v1/tours/{tour_id}", tags=["Tours"])
async def get_tour(tour_id: str):
    """Get detailed tour information"""
    
    cache_key = f"tour:{tour_id}"
    cached = get_from_cache(cache_key)
    if cached:
        return cached
    
    for tour in SAMPLE_TOURS:
        if tour.tour_id == tour_id:
            result = {
                **tour.to_dict(),
                "description": f"Professional {tour.name} experience",
                "inclusions": ["Accommodation", "Meals", "Transport", "Guide"],
                "reviews_count": 150,
                "bookings_count": 342,
            }
            set_to_cache(cache_key, result, ttl=3600)
            return result
    
    raise HTTPException(status_code=404, detail=f"Tour {tour_id} not found")

# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@app.get("/api/v1/analytics/regional-stats", tags=["Analytics"])
async def regional_stats(
    region: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """
    Get regional analytics and metrics
    
    Returns statistics by region:
    - Total bookings
    - Revenue
    - Average booking value
    - Unique users
    """
    
    cache_key = f"regional_stats:{region}"
    cached = get_from_cache(cache_key)
    if cached:
        return cached
    
    # Calculate stats from sample data
    regional_data = {}
    for event in SAMPLE_EVENTS:
        r = event['region']
        if r not in regional_data:
            regional_data[r] = {
                'bookings': 0,
                'revenue': 0,
                'events': 0,
                'users': set()
            }
        
        regional_data[r]['events'] += 1
        regional_data[r]['users'].add(event['user_id'])
        
        if event['event_type'] == 'booking':
            regional_data[r]['bookings'] += 1
            regional_data[r]['revenue'] += event['amount']
    
    # Format response
    result = []
    for r, stats in regional_data.items():
        if region and r != region:
            continue
        
        result.append({
            'region': r,
            'total_bookings': stats['bookings'],
            'total_revenue': stats['revenue'],
            'unique_users': len(stats['users']),
            'avg_booking_value': stats['revenue'] / stats['bookings'] if stats['bookings'] > 0 else 0,
            'conversion_rate': stats['bookings'] / stats['events'] * 100 if stats['events'] > 0 else 0
        })
    
    response = {
        'data': result,
        'generated_at': datetime.now().isoformat()
    }
    
    set_to_cache(cache_key, response, ttl=3600)
    return response

@app.get("/api/v1/analytics/tour-performance", tags=["Analytics"])
async def tour_performance():
    """Get tour performance metrics"""
    
    cache_key = "tour_performance"
    cached = get_from_cache(cache_key)
    if cached:
        return cached
    
    performance = []
    for tour in SAMPLE_TOURS:
        tour_events = [e for e in SAMPLE_EVENTS if e['tour_id'] == tour.tour_id]
        bookings = len([e for e in tour_events if e['event_type'] == 'booking'])
        revenue = sum(e['amount'] for e in tour_events if e['event_type'] == 'booking')
        
        performance.append({
            'tour_id': tour.tour_id,
            'name': tour.name,
            'region': tour.region,
            'views': len(tour_events),
            'bookings': bookings,
            'revenue': revenue,
            'conversion_rate': bookings / len(tour_events) * 100 if tour_events else 0,
            'avg_rating': tour.rating
        })
    
    response = {
        'data': performance,
        'timestamp': datetime.now().isoformat()
    }
    
    set_to_cache(cache_key, response, ttl=3600)
    return response

# ============================================
# RECOMMENDATIONS ENDPOINT
# ============================================

@app.get("/api/v1/recommendations", tags=["Recommendations"])
async def get_recommendations(
    user_id: int = Query(...),
    limit: int = Query(5, le=20),
):
    """
    Get personalized tour recommendations for a user
    
    Uses hybrid filtering (collaborative + content-based)
    """
    
    cache_key = f"recommendations:user:{user_id}:{limit}"
    cached = get_from_cache(cache_key)
    if cached:
        return cached
    
    # Simple recommendation logic
    user_events = [e for e in SAMPLE_EVENTS if e['user_id'] == user_id]
    user_regions = set(e['region'] for e in user_events)
    
    # Get tours from user's regions with high rating
    recommendations = [
        {
            **t.to_dict(),
            'match_score': 0.85,  # Would be computed by ML model
            'reason': 'Popular in your region' if t.region in user_regions else 'Trending',
        }
        for t in SAMPLE_TOURS
    ]
    
    # Sort by match score and limit
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    recommendations = recommendations[:limit]
    
    result = {
        'user_id': user_id,
        'recommendations': recommendations,
        'generated_at': datetime.now().isoformat()
    }
    
    set_to_cache(cache_key, result, ttl=600)  # 10 min cache
    return result

# ============================================
# EVENTS ENDPOINTS
# ============================================

@app.post("/api/v1/events", tags=["Events"])
async def create_event(
    event_data: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permissions(Permission.INGEST_DATA))
):
    """
    Record user event (view, booking, review, etc.)
    
    Events are sent to Kafka queue for real-time processing
    Requires INGEST_DATA permission
    """
    
    log_audit_event(current_user, "INGEST", f"event:{event_data.get('type', 'unknown')}")
    logger.info(f"Recording event from user {current_user.username}: {event_data}")
    
    new_event = {
        'id': f"e_{len(SAMPLE_EVENTS) + 1}",
        'timestamp': datetime.now().isoformat(),
        **event_data
    }
    
    # Send to Kafka (async, non-blocking)
    if kafka_producer:
        try:
            # Determine topic based on event type
            event_type = event_data.get('event_type', 'unknown')
            if event_type == 'booking':
                topic = 'topic_booking_events'
            else:
                topic = 'topic_user_events'
            
            future = kafka_producer.send(topic, value=new_event)
            
            def log_kafka_result(metadata):
                logger.info(f"Event sent to Kafka - Topic: {metadata.topic}, Partition: {metadata.partition}, Offset: {metadata.offset}")
            
            def log_kafka_error(exc):
                logger.error(f"Failed to send event to Kafka: {exc}")
            
            future.add_callback(log_kafka_result)
            future.add_errback(log_kafka_error)
            
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
    else:
        logger.warning("Kafka producer not available, event recorded locally only")
    
    SAMPLE_EVENTS.append(new_event)
    
    # Invalidate cache
    if cache:
        cache.delete('regional_stats')
        cache.delete('tour_performance')
    
    return {
        'status': 'success',
        'event_id': new_event['id'],
        'timestamp': new_event['timestamp'],
        'kafka_sent': kafka_producer is not None
    }

# ============================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================

@app.post("/api/v1/cache/clear", tags=["Admin"])
async def clear_cache(current_user: User = Depends(require_roles(Role.ADMIN))):
    """Clear all cached data - Requires ADMIN role"""
    log_audit_event(current_user, "CLEAR", "cache")
    if cache:
        cache.flushall()
        return {'status': 'success', 'message': 'Cache cleared'}
    return {'status': 'error', 'message': 'Cache not available'}

@app.get("/api/v1/cache/stats", tags=["Admin"])
async def cache_stats(current_user: User = Depends(require_permissions(Permission.VIEW_METRICS))):
    """Get cache statistics - Requires VIEW_METRICS permission"""
    if cache:
        info = cache.info()
        return {
            'connected_clients': info.get('connected_clients'),
            'used_memory': info.get('used_memory_human'),
            'total_commands_processed': info.get('total_commands_processed'),
        }
    return {'status': 'error', 'message': 'Cache not available'}

# ============================================
# GRAPHQL SCHEMA
# ============================================

@app.get("/api/v1/graphql/schema", tags=["GraphQL"])
async def graphql_schema():
    """Get GraphQL schema"""
    return {
        "schema": """
        type Query {
            tours(region: String, limit: Int): [Tour!]!
            tour(id: ID!): Tour
            regionalStats(region: String): [RegionalStat!]!
            recommendations(userId: Int!, limit: Int): [Tour!]!
        }
        
        type Tour {
            id: ID!
            name: String!
            region: String!
            price: Float!
            rating: Float!
            tags: [String!]!
        }
        
        type RegionalStat {
            region: String!
            totalBookings: Int!
            totalRevenue: Float!
            uniqueUsers: Int!
            avgBookingValue: Float!
        }
        """
    }

# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================
# STARTUP & SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("🚀 Nexus Data Platform API Starting")
    logger.info("=" * 50)
    logger.info("✅ API is ready")
    logger.info(f"   OpenAPI Docs: http://localhost:8000/docs")
    logger.info(f"   ReDoc: http://localhost:8000/redoc")
    try:
        _ensure_data_sources_table()
        _seed_sources_from_yaml()
        logger.info("✅ Data sources table is ready")
    except Exception as exc:
        logger.warning(f"⚠️  Data sources storage not ready: {exc}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Nexus Data Platform API Shutting Down")

# ============================================
# RUN THE APP
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
