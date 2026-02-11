#!/bin/bash

echo "================================"
echo "🔍 DATA PLATFORM HEALTH CHECK 🔍"
echo "================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test service
test_service() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name... "
    if response=$(curl -s -m 5 "$url"); then
        if [[ $response == *"$expected"* ]]; then
            echo -e "${GREEN}✅ OK${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  SLOW${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

echo "1️⃣  Testing Kafka..."
if docker exec nexus-kafka kafka-broker-api-versions.sh --bootstrap-server kafka:9092 &>/dev/null; then
    echo -e "${GREEN}✅ Kafka is OK${NC}"
else
    echo -e "${RED}❌ Kafka FAILED${NC}"
fi

echo ""
echo "2️⃣  Testing MinIO..."
test_service "MinIO" "http://localhost:9000/minio/health/live" "OK"

echo ""
echo "3️⃣  Testing ClickHouse..."
if docker exec nexus-clickhouse clickhouse-client --query "SELECT version()" &>/dev/null; then
    echo -e "${GREEN}✅ ClickHouse is OK${NC}"
else
    echo -e "${YELLOW}⚠️  ClickHouse starting...${NC}"
fi

echo ""
echo "4️⃣  Testing Elasticsearch..."
test_service "Elasticsearch" "http://localhost:9200/_cluster/health" "green"

echo ""
echo "5️⃣  Testing Redis..."
if redis-cli -h localhost ping | grep -q PONG 2>/dev/null; then
    echo -e "${GREEN}✅ Redis is OK${NC}"
else
    echo -e "${YELLOW}⚠️  Redis starting...${NC}"
fi

echo ""
echo "6️⃣  Testing PostgreSQL..."
if docker exec nexus-postgres pg_isready -U admin &>/dev/null; then
    echo -e "${GREEN}✅ PostgreSQL is OK${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL starting...${NC}"
fi

echo ""
echo "7️⃣  Testing Airflow..."
test_service "Airflow Webserver" "http://localhost:8888/health" "healthy"

echo ""
echo "8️⃣  Testing Superset..."
test_service "Superset Dashboard" "http://localhost:8088/api/v1/me" "username"

echo ""
echo "================================"
echo "✅ TEST SUITE COMPLETE"
echo "================================"
echo ""

# Service URLs
echo "📊 Access URLs:"
echo ""
echo "Airflow:       http://localhost:8888"
echo "MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)"
echo "ClickHouse:    http://localhost:8123"
echo "Elasticsearch: http://localhost:9200"
echo "Redis CLI:     redis-cli -h localhost -a redis123"
echo "Superset:      http://localhost:8088 (admin/admin123)"
echo "PostgreSQL:    psql -h localhost -U admin"
echo ""
