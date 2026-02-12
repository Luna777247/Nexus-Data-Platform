#!/bin/bash

# ════════════════════════════════════════════════════════════════
# Production Stack Health Check
# ════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

echo "=================================================="
echo "Nexus Data Platform - Production Health Check"
echo "=================================================="

# ════════════════════════════════════════════════════════════════
# Check Kafka Cluster
# ════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Checking Kafka Cluster..."

KAFKA_BROKERS=("nexus-kafka-1" "nexus-kafka-2" "nexus-kafka-3")
KAFKA_HEALTHY=0

for BROKER in "${KAFKA_BROKERS[@]}"; do
    if docker ps | grep -q $BROKER; then
        echo -e "  ${GREEN}✓${NC} $BROKER running"
        ((KAFKA_HEALTHY++))
    else
        echo -e "  ${RED}✗${NC} $BROKER NOT running"
        ((ERRORS++))
    fi
done

echo "  Kafka Cluster: $KAFKA_HEALTHY/3 brokers healthy"

# ════════════════════════════════════════════════════════════════
# Check Spark Streaming Cluster
# ════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Checking Spark Streaming Cluster..."

if docker ps | grep -q nexus-spark-stream-master; then
    echo -e "  ${GREEN}✓${NC} Spark Streaming Master running"
    
    # Check UI
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Spark Streaming UI accessible (http://localhost:8080)"
        
        # Count workers
        WORKERS=$(curl -s http://localhost:8080/json/ | jq -r '.aliveworkers // 0' 2>/dev/null || echo "0")
        if [ "$WORKERS" -ge 2 ]; then
            echo -e "  ${GREEN}✓${NC} Workers: $WORKERS/2 alive"
        else
            echo -e "  ${YELLOW}⚠${NC} Workers: $WORKERS/2 alive (expected 2)"
            ((ERRORS++))
        fi
    else
        echo -e "  ${RED}✗${NC} Spark Streaming UI not accessible"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗${NC} Spark Streaming Master NOT running"
    ((ERRORS++))
fi

# ════════════════════════════════════════════════════════════════
# Check Spark Batch Cluster
# ════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Checking Spark Batch Cluster..."

if docker ps | grep -q nexus-spark-batch-master; then
    echo -e "  ${GREEN}✓${NC} Spark Batch Master running"
    
    # Check UI
    if curl -s http://localhost:8082 > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Spark Batch UI accessible (http://localhost:8082)"
        
        # Count workers
        WORKERS=$(curl -s http://localhost:8082/json/ | jq -r '.aliveworkers // 0' 2>/dev/null || echo "0")
        if [ "$WORKERS" -ge 2 ]; then
            echo -e "  ${GREEN}✓${NC} Workers: $WORKERS/2 alive"
        else
            echo -e "  ${YELLOW}⚠${NC} Workers: $WORKERS/2 alive (expected 2)"
            ((ERRORS++))
        fi
    else
        echo -e "  ${RED}✗${NC} Spark Batch UI not accessible"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗${NC} Spark Batch Master NOT running"
    ((ERRORS++))
fi

# ════════════════════════════════════════════════════════════════
# Check PostgreSQL (Iceberg Catalog)
# ════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Checking PostgreSQL (Iceberg Catalog)..."

if docker ps | grep -q nexus-postgres-iceberg; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL container running"
    
    # Check connectivity
    if docker exec nexus-postgres-iceberg pg_isready -U iceberg > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL accepting connections"
    else
        echo -e "  ${RED}✗${NC} PostgreSQL NOT accepting connections"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗${NC} PostgreSQL container NOT running"
    ((ERRORS++))
fi

# ════════════════════════════════════════════════════════════════
# Check MinIO Cluster
# ════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Checking MinIO Cluster..."

MINIO_NODES=("nexus-minio-1" "nexus-minio-2" "nexus-minio-3" "nexus-minio-4")
MINIO_HEALTHY=0

for NODE in "${MINIO_NODES[@]}"; do
    if docker ps | grep -q $NODE; then
        ((MINIO_HEALTHY++))
    fi
done

echo "  MinIO Cluster: $MINIO_HEALTHY/4 nodes running"

if [ $MINIO_HEALTHY -eq 4 ]; then
    echo -e "  ${GREEN}✓${NC} All MinIO nodes healthy"
else
    echo -e "  ${YELLOW}⚠${NC} Some MinIO nodes down"
    ((ERRORS++))
fi

# Check MinIO API
if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} MinIO API responding"
else
    echo -e "  ${RED}✗${NC} MinIO API not responding"
    ((ERRORS++))
fi

# ════════════════════════════════════════════════════════════════
# Check Prometheus
# ════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Checking Prometheus..."

if docker ps | grep -q nexus-prometheus; then
    echo -e "  ${GREEN}✓${NC} Prometheus container running"
    
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Prometheus API responding"
        
        # Check targets
        TARGETS=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets | length' 2>/dev/null || echo "0")
        echo "  Prometheus scraping $TARGETS targets"
    else
        echo -e "  ${RED}✗${NC} Prometheus API not responding"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗${NC} Prometheus container NOT running"
    ((ERRORS++))
fi

# ════════════════════════════════════════════════════════════════
# Check Grafana
# ════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Checking Grafana..."

if docker ps | grep -q nexus-grafana; then
    echo -e "  ${GREEN}✓${NC} Grafana container running"
    
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Grafana accessible (http://localhost:3000)"
    else
        echo -e "  ${RED}✗${NC} Grafana not accessible"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗${NC} Grafana container NOT running"
    ((ERRORS++))
fi

# ════════════════════════════════════════════════════════════════
# Check OpenMetadata
# ════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Checking OpenMetadata..."

if docker ps | grep -q nexus-openmetadata; then
    echo -e "  ${GREEN}✓${NC} OpenMetadata container running"
    
    if curl -s http://localhost:8585/api/v1/system/status > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} OpenMetadata API responding"
    else
        echo -e "  ${YELLOW}⚠${NC} OpenMetadata API not responding (may be starting)"
    fi
else
    echo -e "  ${RED}✗${NC} OpenMetadata container NOT running"
    ((ERRORS++))
fi

# ════════════════════════════════════════════════════════════════
# Check ClickHouse
# ════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Checking ClickHouse..."

if docker ps | grep -q nexus-clickhouse; then
    echo -e "  ${GREEN}✓${NC} ClickHouse container running"
    
    if curl -s http://localhost:8123/ping > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} ClickHouse API responding"
    else
        echo -e "  ${RED}✗${NC} ClickHouse API not responding"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗${NC} ClickHouse container NOT running"
    ((ERRORS++))
fi

# ════════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════════
echo ""
echo "=================================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! System healthy.${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS issue(s) found. Please investigate.${NC}"
    exit 1
fi
