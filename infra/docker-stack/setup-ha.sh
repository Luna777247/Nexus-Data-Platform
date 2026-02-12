#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# 🚀 Quick Start - High Availability Setup
# ═══════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SUCCESS="✅"
FAIL="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ${ROCKET} Nexus Data Platform - HA Setup"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
    echo -e "${FAIL} ${RED}docker-compose not found. Please install it first.${NC}"
    exit 1
fi

# Check system resources
echo "${INFO} Checking system resources..."
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -lt 16 ]; then
    echo -e "${WARNING} ${YELLOW}Warning: Less than 16GB RAM detected. HA setup requires at least 32GB.${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Prompt for migration
echo ""
echo "${INFO} This will deploy High Availability setup with:"
echo "  • Kafka 3-broker cluster"
echo "  • PostgreSQL primary + 2 replicas"
echo "  • MinIO 4-node distributed"
echo "  • Schema Registry"
echo "  • Prometheus + Grafana monitoring"
echo "  • HashiCorp Vault"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Backup existing data if needed
if docker ps | grep -q "nexus-postgres"; then
    echo ""
    echo "${WARNING} Existing Nexus stack detected!"
    read -p "Backup current PostgreSQL data? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "${INFO} Backing up PostgreSQL..."
        mkdir -p ./backups
        docker exec nexus-postgres pg_dump -U admin nexus_data > ./backups/backup_$(date +%Y%m%d_%H%M%S).sql
        echo -e "${SUCCESS} ${GREEN}Backup saved to ./backups/${NC}"
    fi
    
    echo "${INFO} Stopping current stack..."
    docker-compose down
fi

# Start HA stack
echo ""
echo "${INFO} Starting HA stack (this may take 5-10 minutes)..."
docker-compose -f docker-compose-ha.yml up -d

# Wait for critical services
echo ""
echo "${INFO} Waiting for services to initialize..."

wait_for_service() {
    SERVICE=$1
    MAX_WAIT=$2
    WAIT=0
    
    echo -n "  Waiting for ${SERVICE}... "
    
    while [ $WAIT -lt $MAX_WAIT ]; do
        if docker exec $SERVICE true 2>/dev/null; then
            echo -e "${SUCCESS} ${GREEN}OK${NC}"
            return 0
        fi
        sleep 5
        WAIT=$((WAIT + 5))
    done
    
    echo -e "${FAIL} ${RED}TIMEOUT${NC}"
    return 1
}

wait_for_service "nexus-postgres-primary" 60
wait_for_service "nexus-kafka-1" 60
wait_for_service "nexus-minio-1" 60
wait_for_service "nexus-schema-registry" 90
wait_for_service "nexus-prometheus" 30
wait_for_service "nexus-grafana" 30

# Initialize Vault
echo ""
echo "${INFO} Initializing Vault..."
sleep 10

VAULT_INIT=$(docker exec nexus-vault vault operator init -format=json 2>/dev/null || echo "")

if [ -n "$VAULT_INIT" ]; then
    echo "$VAULT_INIT" > ./vault_keys.json
    chmod 600 ./vault_keys.json
    
    echo -e "${SUCCESS} ${GREEN}Vault initialized!${NC}"
    echo "${WARNING} IMPORTANT: Vault keys saved to ./vault_keys.json"
    echo "${WARNING} Store this file securely and DO NOT commit to git!"
    
    # Auto-unseal Vault
    echo "${INFO} Unsealing Vault..."
    UNSEAL_KEYS=$(echo "$VAULT_INIT" | jq -r '.unseal_keys_b64[]')
    COUNT=0
    for key in $UNSEAL_KEYS; do
        if [ $COUNT -lt 3 ]; then
            docker exec nexus-vault vault operator unseal $key > /dev/null
            COUNT=$((COUNT + 1))
        fi
    done
    
    echo -e "${SUCCESS} ${GREEN}Vault unsealed!${NC}"
else
    echo -e "${WARNING} ${YELLOW}Vault already initialized${NC}"
fi

# Check cluster status
echo ""
echo "${INFO} Checking cluster health..."

# Kafka
echo -n "  Kafka cluster... "
KAFKA_TOPICS=$(docker exec nexus-kafka-1 kafka-topics.sh \
    --bootstrap-server kafka-1:29092 --list 2>/dev/null | wc -l)
if [ "$KAFKA_TOPICS" -ge 3 ]; then
    echo -e "${SUCCESS} ${GREEN}OK (${KAFKA_TOPICS} topics)${NC}"
else
    echo -e "${WARNING} ${YELLOW}DLQ topics may not be created yet${NC}"
fi

# PostgreSQL replication
echo -n "  PostgreSQL replication... "
REPLICAS=$(docker exec nexus-postgres-primary psql -U admin -tAc \
    "SELECT count(*) FROM pg_stat_replication;" 2>/dev/null || echo "0")
if [ "$REPLICAS" -ge 1 ]; then
    echo -e "${SUCCESS} ${GREEN}OK (${REPLICAS} replicas)${NC}"
else
    echo -e "${WARNING} ${YELLOW}Replicas not connected yet${NC}"
fi

# MinIO cluster
echo -n "  MinIO cluster... "
if curl -sf http://localhost:9000/minio/health/cluster > /dev/null 2>&1; then
    echo -e "${SUCCESS} ${GREEN}OK${NC}"
else
    echo -e "${WARNING} ${YELLOW}Cluster forming...${NC}"
fi

# Schema Registry
echo -n "  Schema Registry... "
if curl -sf http://localhost:8081/subjects > /dev/null 2>&1; then
    echo -e "${SUCCESS} ${GREEN}OK${NC}"
else
    echo -e "${FAIL} ${RED}NOT READY${NC}"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ${SUCCESS} HA Stack Deployment Complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📊 Access Services:"
echo "  • Airflow:         http://localhost:8888 (admin/admin)"
echo "  • Prometheus:      http://localhost:9090"
echo "  • Grafana:         http://localhost:3001 (admin/admin123)"
echo "  • Vault:           http://localhost:8200"
echo "  • Schema Registry: http://localhost:8081"
echo "  • MinIO:           http://localhost:9001 (minioadmin/minioadmin123)"
echo "  • Superset:        http://localhost:8088 (admin/admin123)"
echo ""
echo "🔧 Next Steps:"
echo "  1. Configure Grafana dashboards"
echo "  2. Register schemas in Schema Registry"
echo "  3. Setup Vault secrets for applications"
echo "  4. Review HA_SETUP_GUIDE.md for details"
echo ""
echo "🔍 Validate setup:"
echo "  ./validate-ha-setup.sh"
echo ""

# Create .env reminder
if [ ! -f .env ]; then
    echo "${INFO} Creating .env file reminder..."
    cat > .env << 'EOF'
# ═══════════════════════════════════════════════════════════════
# Nexus Data Platform - HA Environment Variables
# ═══════════════════════════════════════════════════════════════

# Kafka Cluster
KAFKA_BOOTSTRAP_SERVERS=kafka-1:29092,kafka-2:29093,kafka-3:29094
KAFKA_REPLICATION_FACTOR=3
KAFKA_MIN_INSYNC_REPLICAS=2

# PostgreSQL HA
POSTGRES_PRIMARY_HOST=postgres-primary
POSTGRES_REPLICA_1_HOST=postgres-replica-1
POSTGRES_REPLICA_2_HOST=postgres-replica-2
POSTGRES_PORT=5432

# MinIO Distributed
MINIO_ENDPOINT=http://minio-1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# Schema Registry
SCHEMA_REGISTRY_URL=http://schema-registry:8081

# Vault
VAULT_ADDR=http://vault:8200
# VAULT_TOKEN=<get from vault_keys.json>

# Monitoring
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
EOF
    echo -e "${SUCCESS} ${GREEN}.env file created${NC}"
fi

echo "════════════════════════════════════════════════════════════"
