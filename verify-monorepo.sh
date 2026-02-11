#!/bin/bash

echo "🔍 Nexus Data Platform - Monorepo Structure Verification"
echo "========================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_exists() {
    if [ -e "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

echo "📁 Checking Directory Structure..."
echo ""

# Apps
echo "Apps:"
check_exists "apps/frontend/src/App.tsx"
check_exists "apps/frontend/src/index.tsx"
check_exists "apps/frontend/src/components"
check_exists "apps/frontend/src/services"
check_exists "apps/frontend/package.json"
check_exists "apps/frontend/vite.config.ts"
check_exists "apps/api/main.py"
check_exists "apps/api/requirements.txt"
echo ""

# Pipelines
echo "Pipelines:"
check_exists "pipelines/airflow/dags/tourism_events_pipeline.py"
echo ""

# Jobs
echo "Jobs:"
check_exists "jobs/spark/tourism_processing.py"
echo ""

# Infra
echo "Infrastructure:"
check_exists "infra/docker-stack/docker-compose.yml"
check_exists "infra/docker-stack/health-check.sh"
echo ""

# Shared Packages
echo "Shared Packages:"
check_exists "packages/shared/types.ts"
check_exists "packages/shared/schemas/event.schema.json"
check_exists "packages/shared/schemas/event.avsc"
check_exists "packages/shared/schemas/event.parquet.json"
check_exists "packages/shared/schemas/tour.schema.json"
check_exists "packages/shared/package.json"
echo ""

# Configs
echo "Configuration:"
check_exists "configs/frontend.env.example"
check_exists "configs/api.env.example"
check_exists ".env.example"
echo ""

# Tests
echo "Tests:"
check_exists "tests/api/test_health.py"
check_exists "tests/airflow/test_dag_import.py"
check_exists "tests/spark/test_schema_contracts.py"
check_exists "pytest.ini"
echo ""

# CI/CD
echo "CI/CD:"
check_exists ".github/workflows/ci.yml"
check_exists "requirements-ci.txt"
echo ""

# Documentation
echo "Documentation:"
check_exists "README.md"
check_exists "SETUP_COMPLETE.md"
check_exists "MONOREPO_GUIDE.md"
check_exists "IMPLEMENTATION_GUIDE.md"
echo ""

# Root Config
echo "Root Configuration:"
check_exists "package.json"
check_exists "check-platform.sh"
echo ""

echo "========================================================"
echo "🎯 Verification Complete!"
echo ""
echo "To get started:"
echo "  1. npm install"
echo "  2. npm run frontend:dev"
echo "  3. pip install -r requirements-ci.txt && pytest"
echo ""
