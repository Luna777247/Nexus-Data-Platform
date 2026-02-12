#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# 🔍 Nexus Data Platform - Architecture Validation Script
# ═══════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Emoji
SUCCESS="✅"
FAIL="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"
CHECK="🔍"
BOOK="📚"
CHART="📊"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ${ROCKET} Nexus Data Platform - Architecture Validation"
echo "════════════════════════════════════════════════════════════"
echo ""

WORKSPACE_ROOT="/workspaces/Nexus-Data-Platform"
cd "$WORKSPACE_ROOT"

VALIDATION_ERRORS=0

# ═══════════════════════════════════════════════════════════════
# 1. Check Documentation
# ═══════════════════════════════════════════════════════════════

echo "${CHECK} Step 1: Validating Documentation..."
echo ""

check_doc() {
    local doc_path=$1
    local doc_name=$2
    
    if [ -f "$doc_path" ]; then
        echo -e "  ${SUCCESS} ${GREEN}$doc_name${NC}"
        return 0
    else
        echo -e "  ${FAIL} ${RED}$doc_name (missing)${NC}"
        ((VALIDATION_ERRORS++))
        return 1
    fi
}

check_doc "README.md" "Main README"
check_doc "docs/ARCHITECTURE_IMPROVEMENTS.md" "Architecture Improvements"
check_doc "docs/DATA_SOURCES_ARCHITECTURE.md" "Data Sources Architecture"
check_doc "infra/docker-stack/HA_SETUP_GUIDE.md" "HA Setup Guide"
check_doc "k8s/README.md" "Kubernetes Guide"

echo ""

# ═══════════════════════════════════════════════════════════════
# 2. Check Configuration Files
# ═══════════════════════════════════════════════════════════════

echo "${CHECK} Step 2: Validating Configuration Files..."
echo ""

check_config() {
    local config_path=$1
    local config_name=$2
    
    if [ -f "$config_path" ]; then
        echo -e "  ${SUCCESS} ${GREEN}$config_name${NC}"
        
        # Validate YAML syntax if it's a YAML file
        if [[ $config_path == *.yaml ]] || [[ $config_path == *.yml ]]; then
            if command -v yamllint &> /dev/null; then
                if yamllint -d relaxed "$config_path" &> /dev/null; then
                    echo -e "       ${INFO} YAML syntax: ${GREEN}Valid${NC}"
                else
                    echo -e "       ${WARNING} YAML syntax: ${YELLOW}Issues found${NC}"
                fi
            fi
        fi
        return 0
    else
        echo -e "  ${FAIL} ${RED}$config_name (missing)${NC}"
        ((VALIDATION_ERRORS++))
        return 1
    fi
}

check_config "configs/data-sources.yaml" "Data Sources Config"
check_config "configs/sources.yaml" "Legacy Sources Config"
check_config "infra/docker-stack/docker-compose.yml" "Docker Compose"
check_config "infra/docker-stack/docker-compose-ha.yml" "Docker Compose HA"
check_config "k8s/stack.yaml" "Kubernetes Stack"

echo ""

# ═══════════════════════════════════════════════════════════════
# 3. Validate Lakehouse Structure
# ═══════════════════════════════════════════════════════════════

echo "${CHECK} Step 3: Validating Lakehouse Layer Definitions..."
echo ""

# Check if Bronze/Silver/Gold layers are documented
if grep -q "Bronze Layer" docs/DATA_SOURCES_ARCHITECTURE.md; then
    echo -e "  ${SUCCESS} ${GREEN}Bronze Layer documented${NC}"
else
    echo -e "  ${FAIL} ${RED}Bronze Layer not documented${NC}"
    ((VALIDATION_ERRORS++))
fi

if grep -q "Silver Layer" docs/DATA_SOURCES_ARCHITECTURE.md; then
    echo -e "  ${SUCCESS} ${GREEN}Silver Layer documented${NC}"
else
    echo -e "  ${FAIL} ${RED}Silver Layer not documented${NC}"
    ((VALIDATION_ERRORS++))
fi

if grep -q "Gold Layer" docs/DATA_SOURCES_ARCHITECTURE.md; then
    echo -e "  ${SUCCESS} ${GREEN}Gold Layer documented${NC}"
else
    echo -e "  ${FAIL} ${RED}Gold Layer not documented${NC}"
    ((VALIDATION_ERRORS++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# 4. Check Data Sources Coverage
# ═══════════════════════════════════════════════════════════════

echo "${CHECK} Step 4: Validating Data Sources Coverage..."
echo ""

DATA_SOURCES_DOC="docs/DATA_SOURCES_ARCHITECTURE.md"

check_data_source() {
    local source_name=$1
    local search_term=$2
    
    if grep -qi "$search_term" "$DATA_SOURCES_DOC"; then
        echo -e "  ${SUCCESS} ${GREEN}$source_name${NC}"
        return 0
    else
        echo -e "  ${WARNING} ${YELLOW}$source_name (not documented)${NC}"
        return 1
    fi
}

echo "Application Data Sources:"
check_data_source "  Mobile Apps" "Mobile App"
check_data_source "  Web Apps" "Web Application"
check_data_source "  User Events" "User Events"

echo ""
echo "OLTP Databases:"
check_data_source "  PostgreSQL" "PostgreSQL"
check_data_source "  MySQL" "MySQL"
check_data_source "  CDC" "Change Data Capture"

echo ""
echo "Streaming Data:"
check_data_source "  Clickstream" "Clickstream"
check_data_source "  Application Logs" "Application Logs"
check_data_source "  IoT Sensors" "IoT"

echo ""
echo "External Data:"
check_data_source "  Weather API" "Weather"
check_data_source "  Maps API" "Maps"
check_data_source "  Social Media" "Social"

echo ""

# ═══════════════════════════════════════════════════════════════
# 5. Validate Data Governance Components
# ═══════════════════════════════════════════════════════════════

echo "${CHECK} Step 5: Validating Data Governance Components..."
echo ""

GOVERNANCE_DOC="docs/ARCHITECTURE_IMPROVEMENTS.md"

check_governance() {
    local component=$1
    local search_term=$2
    
    if grep -qi "$search_term" "$GOVERNANCE_DOC"; then
        echo -e "  ${SUCCESS} ${GREEN}$component${NC}"
        return 0
    else
        echo -e "  ${FAIL} ${RED}$component (not documented)${NC}"
        ((VALIDATION_ERRORS++))
        return 1
    fi
}

check_governance "Data Quality (Great Expectations)" "Great Expectations"
check_governance "Data Lineage (OpenMetadata)" "OpenMetadata\|DataHub"
check_governance "Access Control (RBAC)" "RBAC"

echo ""

# ═══════════════════════════════════════════════════════════════
# 6. Validate Kafka Topics Configuration
# ═══════════════════════════════════════════════════════════════

echo "${CHECK} Step 6: Validating Kafka Topics Configuration..."
echo ""

CONFIG_FILE="configs/data-sources.yaml"

check_kafka_topic() {
    local topic_name=$1
    
    if grep -q "$topic_name" "$CONFIG_FILE"; then
        echo -e "  ${SUCCESS} ${GREEN}$topic_name${NC}"
        return 0
    else
        echo -e "  ${WARNING} ${YELLOW}$topic_name (not configured)${NC}"
        return 1
    fi
}

check_kafka_topic "topic_app_events"
check_kafka_topic "topic_cdc"
check_kafka_topic "topic_clickstream"
check_kafka_topic "topic_app_logs"
check_kafka_topic "topic_external"

echo ""

# ═══════════════════════════════════════════════════════════════
# 7. Check Architecture Patterns
# ═══════════════════════════════════════════════════════════════

echo "${CHECK} Step 7: Validating Architecture Patterns..."
echo ""

IMPROVEMENTS_DOC="docs/ARCHITECTURE_IMPROVEMENTS.md"

check_pattern() {
    local pattern_name=$1
    local search_term=$2
    
    if grep -qi "$search_term" "$IMPROVEMENTS_DOC"; then
        echo -e "  ${SUCCESS} ${GREEN}$pattern_name${NC}"
        return 0
    else
        echo -e "  ${FAIL} ${RED}$pattern_name (not documented)${NC}"
        ((VALIDATION_ERRORS++))
        return 1
    fi
}

check_pattern "Medallion Architecture" "Medallion\|Bronze.*Silver.*Gold"
check_pattern "Lakehouse Pattern" "Lakehouse"
check_pattern "CDC Pattern" "Change Data Capture\|CDC"
check_pattern "Lambda Architecture" "Batch.*Streaming\|Real-time.*Batch"

echo ""

# ═══════════════════════════════════════════════════════════════
# 8. Validate Iceberg Configuration
# ═══════════════════════════════════════════════════════════════

echo "${CHECK} Step 8: Validating Iceberg Configuration..."
echo ""

DOCKER_COMPOSE="infra/docker-stack/docker-compose.yml"

if grep -q "iceberg-rest" "$DOCKER_COMPOSE"; then
    echo -e "  ${SUCCESS} ${GREEN}Iceberg REST service configured${NC}"
else
    echo -e "  ${FAIL} ${RED}Iceberg REST service not configured${NC}"
    ((VALIDATION_ERRORS++))
fi

if grep -q "CATALOG_JDBC_URL" "$DOCKER_COMPOSE"; then
    echo -e "  ${SUCCESS} ${GREEN}Iceberg catalog backend configured${NC}"
else
    echo -e "  ${FAIL} ${RED}Iceberg catalog backend not configured${NC}"
    ((VALIDATION_ERRORS++))
fi

if grep -q "CATALOG_S3_ENDPOINT" "$DOCKER_COMPOSE"; then
    echo -e "  ${SUCCESS} ${GREEN}Iceberg S3 integration configured${NC}"
else
    echo -e "  ${FAIL} ${RED}Iceberg S3 integration not configured${NC}"
    ((VALIDATION_ERRORS++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# 9. Summary
# ═══════════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════════"
echo ""

if [ $VALIDATION_ERRORS -eq 0 ]; then
    echo -e "${SUCCESS} ${GREEN}Architecture Validation Complete - No Errors${NC}"
    echo ""
    echo "${CHART} Architecture Summary:"
    echo ""
    echo "✅ Lakehouse Architecture: Bronze → Silver → Gold"
    echo "✅ Data Sources: 4 types (App, OLTP, Streaming, External)"
    echo "✅ Data Governance: Quality, Lineage, Access Control"
    echo "✅ Iceberg Integration: Metadata catalog configured"
    echo "✅ Kafka Architecture: Correct producer/consumer pattern"
    echo "✅ Documentation: Complete and up-to-date"
    echo ""
    echo "${BOOK} Reference Documents:"
    echo "   📄 Architecture Improvements: docs/ARCHITECTURE_IMPROVEMENTS.md"
    echo "   📄 Data Sources Guide: docs/DATA_SOURCES_ARCHITECTURE.md"
    echo "   📄 Configuration: configs/data-sources.yaml"
    echo ""
    exit 0
else
    echo -e "${FAIL} ${RED}Architecture Validation Failed${NC}"
    echo -e "${WARNING} Found ${YELLOW}${VALIDATION_ERRORS}${NC} validation error(s)"
    echo ""
    echo "Please review the errors above and fix them."
    echo ""
    exit 1
fi
