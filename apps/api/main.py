"""
Nexus Data Platform - FastAPI Endpoints
REST & GraphQL API for tourism data serving
"""

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from datetime import datetime

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
    
    # Cache for 1 hour
    set_to_cache(cache_key, metrics, ttl=3600)
    
    return metrics

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
async def create_event(event_data: dict, background_tasks: BackgroundTasks):
    """
    Record user event (view, booking, review, etc.)
    
    Events are sent to Kafka queue for real-time processing
    """
    
    logger.info(f"Recording event: {event_data}")
    
    # In production, send to Kafka
    # producer.send('tourism_events', value=event_data)
    
    new_event = {
        'id': f"e_{len(SAMPLE_EVENTS) + 1}",
        'timestamp': datetime.now().isoformat(),
        **event_data
    }
    
    SAMPLE_EVENTS.append(new_event)
    
    # Invalidate cache
    if cache:
        cache.delete('regional_stats')
        cache.delete('tour_performance')
    
    return {
        'status': 'success',
        'event_id': new_event['id'],
        'timestamp': new_event['timestamp']
    }

# ============================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================

@app.post("/api/v1/cache/clear", tags=["Admin"])
async def clear_cache():
    """Clear all cached data"""
    if cache:
        cache.flushall()
        return {'status': 'success', 'message': 'Cache cleared'}
    return {'status': 'error', 'message': 'Cache not available'}

@app.get("/api/v1/cache/stats", tags=["Admin"])
async def cache_stats():
    """Get cache statistics"""
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
