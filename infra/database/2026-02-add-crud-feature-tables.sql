-- Migration script for CRUD features: Log, Monitoring, Quality Lineage, User, Setting

-- Log Table
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL,
    level VARCHAR(16) NOT NULL,
    service VARCHAR(64) NOT NULL,
    msg TEXT NOT NULL
);

-- Monitoring Table
CREATE TABLE IF NOT EXISTS monitoring_metrics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

-- Quality Lineage Table
CREATE TABLE IF NOT EXISTS lineage_nodes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    type VARCHAR(32) NOT NULL,
    is_warning BOOLEAN DEFAULT FALSE,
    parent_id INTEGER REFERENCES lineage_nodes(id) ON DELETE SET NULL
);

-- User Table (for User Management)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(128) UNIQUE NOT NULL,
    full_name VARCHAR(128),
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(32) DEFAULT 'user'
);

-- Settings Table
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(64) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);
