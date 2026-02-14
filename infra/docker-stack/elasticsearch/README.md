# Elasticsearch & Kibana - Search & Analytics

## Overview

Elasticsearch and Kibana provide powerful search, analytics, and visualization capabilities for the Nexus Data Platform.

### Components

- **Elasticsearch 8.11.0**: Distributed search and analytics engine
- **Kibana 8.11.0**: Data visualization and exploration platform

## Quick Start

### 1. Start Services

```bash
cd infra/docker-stack
docker-compose -f docker-compose-production.yml up -d elasticsearch kibana
```

### 2. Verify Services

**Elasticsearch:**
```bash
curl http://localhost:9200
curl http://localhost:9200/_cluster/health
```

**Kibana:**
- URL: http://localhost:5601
- Wait 1-2 minutes for Kibana to initialize

## Use Cases

### 1. **Log Aggregation & Search**

#### Index Application Logs
```bash
# Index a log entry
curl -X POST "http://localhost:9200/nexus-logs/_doc" -H 'Content-Type: application/json' -d'
{
  "timestamp": "2026-02-13T10:00:00Z",
  "level": "ERROR",
  "service": "kafka-consumer",
  "message": "Failed to process message",
  "trace_id": "abc123",
  "user_id": "USR001"
}'
```

#### Search Logs
```bash
# Search for errors in the last hour
curl -X GET "http://localhost:9200/nexus-logs/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" }},
        { "range": { "timestamp": { "gte": "now-1h" }}}
      ]
    }
  },
  "sort": [{ "timestamp": "desc" }],
  "size": 100
}'
```

### 2. **Full-Text Search for Tourism Data**

#### Create Tourism Index
```bash
curl -X PUT "http://localhost:9200/tourism-destinations" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "destination_name": { "type": "text", "analyzer": "standard" },
      "description": { "type": "text" },
      "category": { "type": "keyword" },
      "rating": { "type": "float" },
      "location": { "type": "geo_point" },
      "tags": { "type": "keyword" },
      "created_at": { "type": "date" }
    }
  }
}'
```

#### Index Tourism Data
```bash
curl -X POST "http://localhost:9200/tourism-destinations/_doc" -H 'Content-Type: application/json' -d'
{
  "destination_name": "Ha Long Bay",
  "description": "UNESCO World Heritage Site with stunning limestone karsts",
  "category": "Natural Wonder",
  "rating": 4.8,
  "location": { "lat": 20.9101, "lon": 107.1839 },
  "tags": ["beach", "unesco", "cruise", "kayaking"],
  "created_at": "2026-02-13T10:00:00Z"
}'
```

#### Search Destinations
```bash
# Full-text search for beaches
curl -X GET "http://localhost:9200/tourism-destinations/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "beach unesco",
      "fields": ["destination_name^2", "description", "tags"]
    }
  }
}'
```

### 3. **Clickstream Analytics**

#### Index User Clicks
```bash
curl -X POST "http://localhost:9200/clickstream/_doc" -H 'Content-Type: application/json' -d'
{
  "user_id": "USR123",
  "session_id": "SES456",
  "event_type": "page_view",
  "page_url": "/destinations/halong-bay",
  "timestamp": "2026-02-13T10:15:30Z",
  "device_type": "mobile",
  "referrer": "google.com"
}'
```

#### Aggregate Click Data
```bash
curl -X GET "http://localhost:9200/clickstream/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "popular_pages": {
      "terms": { "field": "page_url.keyword", "size": 10 }
    },
    "events_over_time": {
      "date_histogram": {
        "field": "timestamp",
        "calendar_interval": "hour"
      }
    }
  }
}'
```

### 4. **User Search History**

#### Index Search Queries
```bash
curl -X POST "http://localhost:9200/search-history/_doc" -H 'Content-Type: application/json' -d'
{
  "user_id": "USR123",
  "query": "beach resorts vietnam",
  "results_count": 15,
  "clicked_result": "RES789",
  "timestamp": "2026-02-13T10:20:00Z"
}'
```

## Kibana Dashboards

### 1. Create Index Patterns

1. Go to **Stack Management → Index Patterns**
2. Create patterns:
   - `nexus-logs*` for application logs
   - `tourism-destinations*` for destination data
   - `clickstream*` for user interactions
   - `search-history*` for search analytics

### 2. Example Dashboards

#### A. **Platform Health Dashboard**

**Visualizations:**
1. **Error Rate**: Line chart showing errors over time
2. **Service Status**: Pie chart of log levels by service
3. **Top Errors**: Data table of most common error messages
4. **Response Times**: Histogram of API response times

**Create in Kibana:**
- Discover → Select `nexus-logs*`
- Visualize → Create visualizations
- Dashboard → Combine visualizations

#### B. **Tourism Analytics Dashboard**

**Visualizations:**
1. **Popular Destinations**: Bar chart of most searched/viewed destinations
2. **Geographic Distribution**: Map showing destination locations
3. **Rating Distribution**: Histogram of destination ratings
4. **Category Breakdown**: Pie chart of destination categories

#### C. **User Engagement Dashboard**

**Visualizations:**
1. **Page Views Over Time**: Area chart of page views
2. **Device Breakdown**: Donut chart of mobile vs desktop
3. **Top Landing Pages**: Data table of entry points
4. **User Journey**: Sankey diagram of navigation paths

### 3. Sample Kibana Queries (KQL)

```kql
# Find all errors in the API service
service: "fastapi" AND level: "ERROR"

# Search for slow queries (>1s)
response_time > 1000 AND event_type: "query"

# Find searches with no results
results_count: 0 AND NOT query: ""

# Mobile users from last 24 hours
device_type: "mobile" AND timestamp >= now-24h
```

## Index Management

### 1. **Index Lifecycle Policies**

Create policy for log rotation:
```bash
curl -X PUT "http://localhost:9200/_ilm/policy/nexus-logs-policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "50GB",
            "max_age": "7d"
          }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": { "delete": {} }
      }
    }
  }
}'
```

### 2. **Index Templates**

```bash
curl -X PUT "http://localhost:9200/_index_template/nexus-logs-template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["nexus-logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
      "index.lifecycle.name": "nexus-logs-policy"
    },
    "mappings": {
      "properties": {
        "timestamp": { "type": "date" },
        "level": { "type": "keyword" },
        "service": { "type": "keyword" },
        "message": { "type": "text" }
      }
    }
  }
}'
```

## Integration with Platform

### 1. **From Spark Jobs**

```python
from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch(['http://elasticsearch:9200'])

# Index data from Gold layer
def index_to_elasticsearch(df, index_name):
    for row in df.collect():
        doc = row.asDict()
        es.index(index=index_name, document=doc)

# Example: Index tourism analytics
tourism_df = spark.read.parquet("s3://gold/tourism_analytics/")
index_to_elasticsearch(tourism_df, "tourism-destinations")
```

### 2. **From FastAPI**

```python
from elasticsearch import AsyncElasticsearch

# In main.py
es_client = AsyncElasticsearch(['http://elasticsearch:9200'])

@app.post("/search/destinations")
async def search_destinations(query: str):
    result = await es_client.search(
        index="tourism-destinations",
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["destination_name^2", "description"]
                }
            }
        }
    )
    return result['hits']['hits']
```

### 3. **From Airflow (Logging)**

```python
from airflow.providers.elasticsearch.hooks.elasticsearch import ElasticsearchHook

# In DAG
def log_to_elasticsearch(**context):
    es_hook = ElasticsearchHook(elasticsearch_conn_id='elasticsearch_default')
    
    doc = {
        'dag_id': context['dag'].dag_id,
        'task_id': context['task'].task_id,
        'execution_date': context['execution_date'].isoformat(),
        'status': 'success',
        'duration': 123.45
    }
    
    es_hook.index(index='airflow-logs', body=doc)
```

## Performance Tuning

### 1. **Memory Settings**

Adjust in `docker-compose-production.yml`:
```yaml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms2g -Xmx2g"  # Increase for production
  deploy:
    resources:
      limits:
        memory: 4G  # Increase heap + overhead
```

### 2. **Query Optimization**

```bash
# Use filters instead of queries for exact matches
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "service": "fastapi" }},
        { "range": { "timestamp": { "gte": "now-1h" }}}
      ]
    }
  }
}

# Use aggregations for analytics
{
  "size": 0,
  "aggs": {
    "hourly_errors": {
      "date_histogram": {
        "field": "timestamp",
        "calendar_interval": "hour"
      },
      "aggs": {
        "error_count": {
          "filter": { "term": { "level": "ERROR" }}
        }
      }
    }
  }
}
```

### 3. **Shard Management**

- Use 1 shard for small indices (<50GB)
- Use 1 replica for HA (0 for dev)
- Avoid over-sharding (reduces performance)

## Security (Production)

### 1. **Enable Security**

Edit `elasticsearch/elasticsearch.yml`:
```yaml
xpack.security.enabled: true
xpack.security.http.ssl.enabled: true
xpack.security.transport.ssl.enabled: true
```

### 2. **Set Passwords**

```bash
docker exec -it nexus-elasticsearch /usr/share/elasticsearch/bin/elasticsearch-setup-passwords auto
```

### 3. **Configure Kibana**

Edit `kibana/kibana.yml`:
```yaml
elasticsearch.username: "kibana_system"
elasticsearch.password: "your-password"
```

## Monitoring

### 1. **Cluster Health**

```bash
curl http://localhost:9200/_cluster/health?pretty
```

### 2. **Node Stats**

```bash
curl http://localhost:9200/_nodes/stats?pretty
```

### 3. **Index Stats**

```bash
curl http://localhost:9200/_cat/indices?v
```

### 4. **Prometheus Metrics**

Elasticsearch exposes metrics for Prometheus scraping.

## Troubleshooting

### Issue: Elasticsearch won't start

**Solution:**
```bash
# Check logs
docker logs nexus-elasticsearch

# Increase vm.max_map_count (Linux)
sudo sysctl -w vm.max_map_count=262144

# Check disk space
df -h
```

### Issue: Kibana shows "Elasticsearch unavailable"

**Solution:**
```bash
# Wait for Elasticsearch to be ready
curl http://localhost:9200/_cluster/health

# Restart Kibana
docker restart nexus-kibana
```

### Issue: Low performance

**Solution:**
- Increase heap size (ES_JAVA_OPTS)
- Reduce replica count for dev
- Use filters instead of queries
- Optimize mapping (use `keyword` for exact match)

## Backup & Restore

### 1. **Create Snapshot Repository**

```bash
curl -X PUT "http://localhost:9200/_snapshot/nexus_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backup"
  }
}'
```

### 2. **Take Snapshot**

```bash
curl -X PUT "http://localhost:9200/_snapshot/nexus_backup/snapshot_1?wait_for_completion=true"
```

### 3. **Restore Snapshot**

```bash
curl -X POST "http://localhost:9200/_snapshot/nexus_backup/snapshot_1/_restore"
```

## Resources

- **Elasticsearch Documentation**: https://www.elastic.co/guide/en/elasticsearch/reference/8.11/index.html
- **Kibana Documentation**: https://www.elastic.co/guide/en/kibana/8.11/index.html
- **Query DSL**: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
- **Aggregations**: https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html
