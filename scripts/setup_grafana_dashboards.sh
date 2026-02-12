#!/bin/bash
# Setup Grafana Dashboards for Nexus Data Platform
# Run: ./scripts/setup_grafana_dashboards.sh

set -e

GRAFANA_URL="http://localhost:3001"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin123"
DASHBOARD_DIR="monitoring/grafana/dashboards"

echo "🎨 Setting up Grafana Dashboards for Nexus Data Platform"
echo "=========================================================="

# Wait for Grafana to be ready
echo ""
echo "⏳ Waiting for Grafana to be ready..."
until curl -s "${GRAFANA_URL}/api/health" > /dev/null 2>&1; do
    echo "   Waiting for Grafana at ${GRAFANA_URL}..."
    sleep 2
done
echo "✅ Grafana is ready!"

# Import dashboards
echo ""
echo "📊 Importing dashboards..."

# Dashboard 1: Platform Overview
echo ""
echo "1️⃣  Importing Platform Overview Dashboard..."
curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d @"${DASHBOARD_DIR}/nexus-platform-overview.json" \
  2>/dev/null && echo "   ✅ Platform Overview imported" || echo "   ⚠️  Platform Overview import failed"

# Dashboard 2: DLQ Monitoring
echo ""
echo "2️⃣  Importing DLQ Monitoring Dashboard..."
curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d @"${DASHBOARD_DIR}/nexus-dlq-dashboard.json" \
  2>/dev/null && echo "   ✅ DLQ Monitoring imported" || echo "   ⚠️  DLQ Monitoring import failed"

# Dashboard 3: Schema Registry
echo ""
echo "3️⃣  Importing Schema Registry Dashboard..."
curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d @"${DASHBOARD_DIR}/nexus-schema-registry-dashboard.json" \
  2>/dev/null && echo "   ✅ Schema Registry imported" || echo "   ⚠️  Schema Registry import failed"

# Set Platform Overview as home dashboard
echo ""
echo "🏠 Setting Platform Overview as home dashboard..."
DASHBOARD_UID="nexus-platform-overview"
curl -X PUT "${GRAFANA_URL}/api/org/preferences" \
  -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d "{\"homeDashboardUID\":\"${DASHBOARD_UID}\"}" \
  2>/dev/null && echo "   ✅ Home dashboard set" || echo "   ⚠️  Failed to set home dashboard"

echo ""
echo "=========================================================="
echo "✅ Grafana dashboard setup complete!"
echo ""
echo "📍 Access dashboards:"
echo "   • Platform Overview:  ${GRAFANA_URL}/d/nexus-platform-overview"
echo "   • DLQ Monitoring:     ${GRAFANA_URL}/d/nexus-dlq-monitoring"
echo "   • Schema Registry:    ${GRAFANA_URL}/d/nexus-schema-registry"
echo ""
echo "🔑 Credentials: ${GRAFANA_USER} / ${GRAFANA_PASSWORD}"
echo "=========================================================="
