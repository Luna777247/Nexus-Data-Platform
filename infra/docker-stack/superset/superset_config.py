"""
Apache Superset Configuration for Nexus Data Platform
Custom configuration for BI & Data Visualization
"""

import os
from datetime import timedelta

# ============================================
# Security & Authentication
# ============================================

SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'nexus_superset_secret_key_change_in_production_2026')

# Flask App Builder configuration
FAB_ADD_SECURITY_VIEWS = True
FAB_ADD_SECURITY_API = True

# Session configuration
PERMANENT_SESSION_LIFETIME = timedelta(days=31)

# ============================================
# Database Configuration
# ============================================

SQLALCHEMY_DATABASE_URI = os.environ.get(
    'SQLALCHEMY_DATABASE_URI',
    'postgresql+psycopg2://superset:superset123@superset-postgres:5432/superset'
)

# ============================================
# Cache Configuration (using default FileSystemCache)
# ============================================

CACHE_CONFIG = {
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': '/app/superset_home/cache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_'
}

# Data cache
DATA_CACHE_CONFIG = CACHE_CONFIG.copy()
DATA_CACHE_CONFIG['CACHE_DEFAULT_TIMEOUT'] = 3600  # 1 hour

# ============================================
# Feature Flags
# ============================================

FEATURE_FLAGS = {
    # Enable advanced features
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ENABLE_TEMPLATE_REMOVE_FILTERS": True,
    
    # SQL Lab features
    "SQLLAB_BACKEND_PERSISTENCE": True,
    "SQL_VALIDATORS_BY_ENGINE": True,
    
    # Alert & Report features
    "ALERT_REPORTS": True,
    
    # UX improvements
    "LISTVIEWS_DEFAULT_CARD_VIEW": True,
    "ENABLE_EXPLORE_DRAG_AND_DROP": True,
    
    # Advanced analytics
    "ENABLE_ADVANCED_DATA_TYPES": True,
}

# ============================================
# Web Server Configuration
# ============================================

SUPERSET_WEBSERVER_PORT = 8088
SUPERSET_WEBSERVER_TIMEOUT = 300

# Maximum rows returned for any analytical database query
ROW_LIMIT = 50000

# Maximum rows displayed in SQL Lab UI
DISPLAY_SQL_MAX_ROW = 10000

# ============================================
# Security Configuration
# ============================================

# CORS configuration
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['*']
}

# HTTP headers
HTTP_HEADERS = {
    'X-Frame-Options': 'SAMEORIGIN',
    'X-Content-Type-Options': 'nosniff',
}

# ============================================
# Email Configuration (Optional)
# ============================================

# SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
# SMTP_STARTTLS = True
# SMTP_SSL = False
# SMTP_USER = os.environ.get('SMTP_USER', 'your-email@gmail.com')
# SMTP_PORT = 587
# SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
# SMTP_MAIL_FROM = os.environ.get('SMTP_MAIL_FROM', 'superset@nexus.com')

# ============================================
# Async Query Configuration
# ============================================

# Enable asynchronous query execution
GLOBAL_ASYNC_QUERIES_TRANSPORT = "polling"
GLOBAL_ASYNC_QUERIES_POLLING_DELAY = 500

# ============================================
# SQL Lab Configuration
# ============================================

SQLLAB_ASYNC_TIME_LIMIT_SEC = 300
SQLLAB_TIMEOUT = 300
SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT = 10

# Save queries in SQL Lab
SQLLAB_SAVE_WARNING_MESSAGE = None
SQLLAB_DEFAULT_DBID = None

# ============================================
# CSV & Excel Export Configuration
# ============================================

CSV_EXPORT = {
    "encoding": "utf-8",
}

EXCEL_EXPORT = {
    "encoding": "utf-8",
}

# ============================================
# Logging Configuration
# ============================================

ENABLE_TIME_ROTATE = True
TIME_ROTATE_LOG_LEVEL = "INFO"
FILENAME = os.path.join("/app/superset_home", "superset.log")

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"

# ============================================
# Custom Database Connections
# ============================================

# These will be pre-configured for easy access to platform databases

SQLALCHEMY_EXAMPLES_URI = None  # Disable examples

# Pre-configured database URIs (users can add via UI)
# PostgreSQL (Iceberg Catalog)
NEXUS_POSTGRES_URI = "postgresql://admin:admin123@postgres-iceberg:5432/iceberg_catalog"

# ClickHouse (Analytics)
NEXUS_CLICKHOUSE_URI = "clickhouse://default:clickhouse123@clickhouse:8123/analytics"

# Note: Users will need to add these connections via Superset UI:
# Database -> + Database -> and enter the connection strings above

# ============================================
# Custom CSS/JS (Optional)
# ============================================

# CUSTOM_CSS = "/app/superset_home/custom.css"

# ============================================
# Rate Limiting (Optional)
# ============================================

# RATELIMIT_ENABLED = True
# RATELIMIT_APPLICATION = "10000 per hour"

# ============================================
# Thumbnails
# ============================================

THUMBNAIL_SELENIUM_USER = "admin"
THUMBNAIL_CACHE_CONFIG = {
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': '/app/superset_home/thumbnail_cache',
    'CACHE_DEFAULT_TIMEOUT': 86400,  # 24 hours
}

# ============================================
# Timezone
# ============================================

import pytz
DEFAULT_TIME_ZONE = pytz.timezone('UTC')

# ============================================
# Dashboard Import/Export
# ============================================

PREVENT_UNSAFE_DB_CONNECTIONS = False

# ============================================
# Custom Welcome Message
# ============================================

LOGO_TARGET_PATH = '/'
FAVICONS = [{"href": "/static/assets/images/favicon.png"}]

# Custom welcome message
WELCOME_PAGE_LAST_TAB = "recent"
