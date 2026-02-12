-- Iceberg Metadata Database Initialization
-- This creates the schema for Iceberg REST Catalog metadata storage

-- Create Iceberg database if needed (optional, can use nexus_data)
CREATE DATABASE IF NOT EXISTS nexus_iceberg;
GRANT ALL PRIVILEGES ON DATABASE nexus_iceberg TO admin;

-- Switch to iceberg database (in psql context)
-- \c nexus_iceberg

-- Create catalog namespaces table
CREATE TABLE IF NOT EXISTS iceberg_namespace (
    catalog_name VARCHAR(255) NOT NULL,
    namespace_level INT NOT NULL,
    namespace_name VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    PRIMARY KEY (catalog_name, namespace_level, namespace_name)
);

-- Create tables metadata
CREATE TABLE IF NOT EXISTS iceberg_tables (
    catalog_name VARCHAR(255) NOT NULL,
    namespace_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    table_location VARCHAR(1024) NOT NULL,
    table_schema TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    PRIMARY KEY (catalog_name, namespace_name, table_name)
);

-- Create table metadata versions
CREATE TABLE IF NOT EXISTS iceberg_table_versions (
    catalog_name VARCHAR(255) NOT NULL,
    namespace_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    version_id BIGINT NOT NULL,
    metadata_location VARCHAR(1024) NOT NULL,
    created_at BIGINT NOT NULL,
    PRIMARY KEY (catalog_name, namespace_name, table_name, version_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_namespace ON iceberg_namespace(catalog_name, namespace_level);
CREATE INDEX IF NOT EXISTS idx_tables ON iceberg_tables(catalog_name, namespace_name);
CREATE INDEX IF NOT EXISTS idx_table_versions ON iceberg_table_versions(catalog_name, namespace_name, table_name);

-- MinIO bucket for storing Iceberg warehouse
-- Note: This SQL won't create MinIO buckets, but below is the command to manually create:
-- aws s3 mb s3://iceberg-warehouse/ --endpoint-url http://minio:9000 --access-key minioadmin --secret-key minioadmin123

-- Grant permissions
GRANT ALL ON iceberg_namespace TO admin;
GRANT ALL ON iceberg_tables TO admin;
GRANT ALL ON iceberg_table_versions TO admin;
