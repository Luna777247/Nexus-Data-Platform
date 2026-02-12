#!/bin/bash
# Iceberg Setup Script
# This script initializes Iceberg warehouse and creates MinIO bucket

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🧊 Apache Iceberg Setup${NC}"
echo "====================================="

# Configuration
MINIO_ENDPOINT="http://localhost:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin123"
BUCKET_NAME="iceberg-warehouse"
ICEBERG_REST_URL="http://localhost:8182"

# Function to check if service is running
check_service() {
    local name=$1
    local url=$2
    
    echo -e "\n${YELLOW}Checking $name...${NC}"
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $name is not responding at $url${NC}"
        return 1
    fi
}

# Check services
if ! check_service "MinIO" "$MINIO_ENDPOINT/minio/health/live"; then
    echo -e "${RED}MinIO is not available. Start Docker Compose first.${NC}"
    exit 1
fi

if ! check_service "Iceberg REST Catalog" "$ICEBERG_REST_URL/v1/config"; then
    echo -e "${RED}Iceberg REST Catalog is not available.${NC}"
    exit 1
fi

# Create MinIO bucket using aws cli or curl
echo -e "\n${YELLOW}Creating MinIO bucket: $BUCKET_NAME${NC}"

# Check if bucket exists using curl
BUCKET_EXISTS=$(curl -s -I \
  -H "Authorization: AWS $MINIO_ACCESS_KEY:$MINIO_SECRET_KEY" \
  "$MINIO_ENDPOINT/$BUCKET_NAME/" 2>/dev/null | head -1)

if echo "$BUCKET_EXISTS" | grep -q "200\|301\|404"; then
    if echo "$BUCKET_EXISTS" | grep -q "404"; then
        echo -e "${YELLOW}Bucket does not exist, creating...${NC}"
        
        # Try to create bucket using mc (MinIO Client) if available
        if command -v mc &> /dev/null; then
            mc alias set nexus "$MINIO_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" --api S3v4
            mc mb nexus/"$BUCKET_NAME" --region us-east-1
            echo -e "${GREEN}✅ Bucket created: $BUCKET_NAME${NC}"
        else
            echo -e "${YELLOW}⚠️  MinIO Client (mc) not found. Create bucket manually:${NC}"
            echo "    mc mb minio/$BUCKET_NAME --region us-east-1"
        fi
    else
        echo -e "${GREEN}✅ Bucket already exists: $BUCKET_NAME${NC}"
    fi
fi

# Create Iceberg namespace
echo -e "\n${YELLOW}Creating Iceberg namespace...${NC}"

NAMESPACE_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": ["tourism_db"],
    "properties": {
      "description": "Tourism data namespace",
      "owner": "data-team"
    }
  }' \
  "$ICEBERG_REST_URL/v1/namespaces")

if echo "$NAMESPACE_RESPONSE" | grep -q "tourism_db"; then
    echo -e "${GREEN}✅ Iceberg namespace created${NC}"
else
    echo -e "${YELLOW}⚠️  Namespace response: $NAMESPACE_RESPONSE${NC}"
fi

# Test PostgreSQL Iceberg metadata store
echo -e "\n${YELLOW}Checking PostgreSQL Iceberg schema...${NC}"

if command -v psql &> /dev/null; then
    TABLES=$(psql -h localhost -U admin -d nexus_iceberg -c \
      "SELECT table_name FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | wc -l)
    
    if [ "$TABLES" -gt 0 ]; then
        echo -e "${GREEN}✅ PostgreSQL Iceberg schema initialized${NC}"
    else
        echo -e "${YELLOW}⚠️  Iceberg schema may need initialization${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  psql not found, skipping PostgreSQL check${NC}"
fi

# Summary
echo -e "\n${GREEN}🧊 Iceberg Setup Status Summary${NC}"
echo "====================================="
echo -e "MinIO Endpoint:        ${GREEN}$MINIO_ENDPOINT${NC}"
echo -e "Iceberg Warehouse:     ${GREEN}s3://$BUCKET_NAME/${NC}"
echo -e "Iceberg REST Catalog:  ${GREEN}$ICEBERG_REST_URL${NC}"
echo -e "Metadata Store:        ${GREEN}PostgreSQL (nexus_iceberg)${NC}"
echo ""
echo -e "Access Iceberg:"
echo -e "  Spark:  ${YELLOW}spark = create_spark_session_with_iceberg()${NC}"
echo -e "  Trino:  ${YELLOW}SELECT * FROM iceberg.tourism_db.events;${NC}"
echo ""
echo -e "${GREEN}✅ Iceberg is ready to use!${NC}"
