-- Create analytics database
CREATE DATABASE IF NOT EXISTS analytics;

-- Create events table
CREATE TABLE IF NOT EXISTS analytics.events (
    timestamp DateTime,
    user_id UInt32,
    event_type String,
    amount Float64,
    region String,
    source String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (timestamp, user_id)
PARTITION BY toYYYYMM(timestamp);

-- Create tour recommendations table
CREATE TABLE IF NOT EXISTS analytics.tour_recommendations (
    recommendation_id UUID,
    user_id UInt32,
    tour_id String,
    match_score Float64,
    predicted_rating Float64,
    region String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (user_id, recommendation_id)
PARTITION BY toYYYYMM(created_at);

-- Create regional metrics table
CREATE TABLE IF NOT EXISTS analytics.regional_metrics (
    metric_date Date,
    region String,
    total_bookings UInt64,
    total_revenue Float64,
    avg_booking_value Float64,
    unique_users UInt32,
    anomaly_flag UInt8,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (metric_date, region)
PARTITION BY toYYYYMM(metric_date);

-- Create view for daily aggregations
CREATE VIEW IF NOT EXISTS analytics.daily_event_summary AS
SELECT
    toDate(timestamp) as event_date,
    region,
    event_type,
    count(*) as event_count,
    sum(amount) as total_amount,
    avg(amount) as avg_amount,
    max(amount) as max_amount
FROM analytics.events
GROUP BY event_date, region, event_type;
