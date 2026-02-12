#!/bin/bash

# ════════════════════════════════════════════════════════════════
# Create Dead Letter Queue (DLQ) Topics in Kafka
# ════════════════════════════════════════════════════════════════

set -e

KAFKA_CONTAINER="nexus-kafka-1"
BOOTSTRAP_SERVER="localhost:9092"
REPLICATION_FACTOR=3
PARTITIONS=3

echo "=================================================="
echo "Creating DLQ Topics in Kafka"
echo "=================================================="

# DLQ Topics
DLQ_TOPICS=(
    "dlq_schema_validation_errors"
    "dlq_processing_errors"
    "dlq_failed_messages"
)

for TOPIC in "${DLQ_TOPICS[@]}"; do
    echo ""
    echo "📝 Creating topic: $TOPIC"
    
    docker exec $KAFKA_CONTAINER kafka-topics \
        --create \
        --bootstrap-server $BOOTSTRAP_SERVER \
        --replication-factor $REPLICATION_FACTOR \
        --partitions $PARTITIONS \
        --topic $TOPIC \
        --if-not-exists \
        --config retention.ms=604800000 \
        --config compression.type=gzip
    
    if [ $? -eq 0 ]; then
        echo "✅ Topic $TOPIC created successfully"
    else
        echo "⚠️  Topic $TOPIC may already exist or error occurred"
    fi
done

echo ""
echo "=================================================="
echo "Verifying DLQ Topics"
echo "=================================================="

docker exec $KAFKA_CONTAINER kafka-topics \
    --list \
    --bootstrap-server $BOOTSTRAP_SERVER | grep dlq

echo ""
echo "✅ DLQ Topics setup complete!"
echo ""
echo "To check topic details:"
echo "  docker exec $KAFKA_CONTAINER kafka-topics --describe --topic <topic-name> --bootstrap-server $BOOTSTRAP_SERVER"
