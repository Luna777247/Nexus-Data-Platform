#!/bin/bash

echo "🔍 Checking Nexus Data Platform Status..."
echo ""

echo "1. FastAPI Server (Port 8000):"
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "   ✅ FastAPI is running"
    curl -s http://localhost:8000/health | head -3
else
    echo "   ❌ FastAPI is not responding"
fi
echo ""

echo "2. React Dev Server:"
REACT_PORT=$(ps aux | grep vite | grep -v grep | grep -o 'localhost:[0-9]*' | head -1 | cut -d':' -f2)
if [ -n "$REACT_PORT" ]; then
    echo "   ✅ React is running on port $REACT_PORT"
    echo "   🌐 Access at: http://localhost:$REACT_PORT"
else
    echo "   ❌ React server not found"
fi
echo ""

echo "3. Docker Services:"
docker-compose -f /workspaces/Nexus-Data-Platform/infra/docker-stack/docker-compose.yml ps --format "table {{.Service}}\t{{.Status}}" 2>/dev/null | grep -E "(Service|airflow|postgres|clickhouse|minio|redis)" | head -10
echo ""

echo "✅ Platform Status Check Complete!"
